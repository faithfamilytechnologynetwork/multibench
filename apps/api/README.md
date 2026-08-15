# `apps/api` — MultiBench API

A thin Postgres-backed service that will serve the multibrowser SPA's data (corpus, results, raw)
and host the read-write **review** backend. Per Spec 92. **Git stays the source of truth**; the
serving tiers are a rebuildable cache, the review store is authoritative operational data.

> **Status: Phase 2 — review store + auth.** The service hosts the review store (reviewers, sessions,
> reviews/drafts, submissions) and email/password auth (below). No serving tables, no ingest, no
> `/api/version` yet — the deferred serving tiers arrive in Phase 5+.

## Stack

- **Hono** — HTTP framework (routing/middleware).
- **Drizzle** — the ORM and **single schema authority**. Migrations are explicit:
  `drizzle-kit generate` → **review the SQL** → apply. **Never `db:push` against live data.**
- **node-postgres** (`pg`) in production; **PGlite** (in-process Postgres) for tests — no external
  database is required to run `pnpm test`.
- **tsx** runs the TypeScript directly (no emit step); `pnpm build` is a typecheck.

## Scripts

| Command | What it does |
|---|---|
| `pnpm dev` | Run with reload (`tsx watch`). |
| `pnpm start` | Run the server (`tsx src/server.ts`) — the Railway start command. |
| `pnpm build` | Typecheck (`tsc --noEmit`). |
| `pnpm test` | Run the vitest suite (PGlite-backed). |

## Configuration

Copy `.env.example` → `.env`. Unlike the multibrowser SPA, this service **holds secrets**
(`DATABASE_URL`); they live in the Railway environment, never in the SPA. `ALLOWED_ORIGINS` is the
CORS allow-list for credentialed cross-site requests (the SPA origin must be listed for the Phase-2
session cookie). Never use `*` with credentials.

## Endpoints

- `GET /api/health` — 200 `{status:"ok"}` when Postgres responds, 503 otherwise (drives the Railway
  health check).
- `POST /api/auth/signup` — email + password, gated by the shared `REVIEW_INVITE_CODE`. Sets an
  httpOnly session cookie + a CSRF cookie.
- `POST /api/auth/login` · `POST /api/auth/logout` · `GET /api/auth/me`.
- `DELETE /api/account` — deletes the reviewer (cascades to sessions/drafts/submissions). Authenticated
  + CSRF.

**Auth model** (Waleed, 2026-08-15, test-tool scale): email + password (argon2id), **no magic-link, no
email**. Sessions are server-side rows (revocation = row delete); cookies are httpOnly + `Secure` +
`SameSite=None` (SPA and API are cross-site). CSRF is double-submit (`mb_csrf` cookie echoed in the
`X-CSRF-Token` header) for state-changing authed requests. Because the SPA is on a different origin
and cannot read the API-origin `mb_csrf` cookie via JS, the CSRF token is also returned in the
signup/login response body and via `GET /api/auth/csrf`; the client holds it in memory and echoes it in
the header. Signup is gated by one shared `REVIEW_INVITE_CODE` (fail-closed if unset). No
email-enumeration / rate-limit hardening at this scale. Expired session rows are not actively pruned
(they are rejected on use by the `expires_at` check); at this scale that's fine — add a periodic prune
if the `sessions` table ever grows.

## Data durability

The review store is authoritative (not rebuildable from git). At this test-tool scale, **Railway's
managed-Postgres built-in backups suffice** — there is no custom backup/restore tooling.

## Migrations

Schema changes follow **generate → review → apply**, and Drizzle is the single schema authority:

1. Edit `src/schema/*`, then `pnpm exec drizzle-kit generate --name <change>` to emit a new
   `drizzle/NNNN_*.sql`.
2. **Review the generated SQL in the PR** — that PR review is the human gate on schema changes.
3. **Apply**: Railway's `preDeployCommand` (`railway.json`) runs `pnpm migrate` (a small runtime
   migrator, `src/migrate.ts`, using drizzle-orm's programmatic migrator over the committed `drizzle/`
   files) **inside Railway on each deploy**, before the new version goes live. It applies only the
   committed, reviewed SQL — it is **not `db:push`** (which diffs the live schema) — and is idempotent
   (drizzle records applied migrations, so re-runs are no-ops). A failed migration fails the deploy.
   This mechanism is chosen because the managed Postgres has no public proxy, so migrations can't be
   applied from a developer's machine.

**Fallback**: if a deploy-time migration ever needs to be decoupled (e.g. a large or risky change
applied out of band), drop `preDeployCommand` for that release and apply the reviewed SQL manually via
`psql` against the database, then deploy. `db:push` is never used against live data.

## Deployment

Railway (NIXPACKS), `engines.node >= 20`. **Provisioning of the Railway service + Postgres is gated
on an architect-confirmed cost envelope** (Spec 92 constraint) and is done deliberately, not from CI.
