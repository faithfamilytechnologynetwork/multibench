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
CORS allow-list for credentialed requests; it lists the one SPA origin. (Since 2026-08-16 the browser
reaches this API only through the SPA's same-origin proxy, so CORS is no longer load-bearing — kept
for defense-in-depth and a possible future direct caller. Never use `*` with credentials.)

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

The review store is authoritative (not rebuildable from git), so a backup **schedule** is configured
(availability of the feature is not the same as active backups): the `multibench-api` Postgres volume
has a **daily** Railway backup schedule (cron `7 14 * * *` UTC, ~6-day retention). Restore is via the
Railway dashboard/API. No custom backup/restore tooling beyond that at this test-tool scale; adjust the
schedule/retention on the volume if the data grows in value.

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

### Topology (2026-08-16): one public origin, private API

Both services live in the **`multibrowser` Railway project**. The **multibrowser** service is the
ONLY browser-facing origin; its edge server (`apps/multibrowser/server/index.mjs`) reverse-proxies
`/api/*` to **this** API over Railway's **private network**. The API service has **no public domain**
— it is unreachable from the internet. Consequences:

- The session cookie is **first-party** (browser ↔ one origin), so third-party-cookie blocking never
  applies. `VITE_API_BASE` is therefore **empty** (same-origin `/api/...`).
- `ALLOWED_ORIGINS` is still set to the SPA origin and cookies keep `SameSite=None; Secure` **for now**
  — they work first-party unchanged. Simplifying `SameSite=None → Lax` and shrinking CORS to nothing
  is a safe follow-up cleanup, deliberately deferred to keep this change focused.

### Services & variables (in the `multibrowser` project)

| Service | Public domain | Key vars |
|---|---|---|
| `multibrowser` (edge + SPA) | **yes** (the one origin) | `API_ORIGIN=http://multibench-api.railway.internal:8080`; `VITE_API_BASE` **unset** |
| `multibench-api` (this) | **no** (private only) | `DATABASE_URL=${{Postgres.DATABASE_URL}}`, `REVIEW_INVITE_CODE`, `ALLOWED_ORIGINS=<SPA origin>`, `PORT=8080` |
| `Postgres` | no | managed template |

`PORT=8080` is pinned on the API so the edge server's private target
(`multibench-api.railway.internal:8080`) is deterministic.

### Deploy ordering — do it in this order

1. **Provision** (once): a managed `Postgres` + an empty `multibench-api` service **inside the
   `multibrowser` project**. Set the API vars above. Do **not** create a public domain for the API
   (`railway domain` with no subcommand *creates* one — use `railway domain list`).
2. **Deploy the API** (`railway up` from `apps/api`, targeting the `multibench-api` service). Its
   `preDeployCommand` migrates the fresh DB. Confirm `railway logs` shows `api listening on :8080` and
   the 4 tables exist.
3. **Deploy the edge/SPA** (`railway up` from `apps/multibrowser`, targeting the `multibrowser`
   service). The build bakes an empty `VITE_API_BASE` (same-origin); the edge server forwards `/api/*`
   to the private API. No ordering hazard remains — the SPA calls its own origin.

> **`railway up` links per-directory.** The CLI resolves the target project from the working
> directory's saved link, **not** a global one. Before deploying, `cd` into the app dir and
> `railway link -p multibrowser -e production -s <service>`, or a stale link silently deploys to the
> wrong project. Pass `-s <service>` to `railway up` to pin the service.

**Post-deploy completion gate:** verify **login + draft save + submit** through the one public origin
in a **real Safari and Chrome**, and confirm the API host is **not** reachable from the public
internet (it has no domain). First-party cookies need no third-party-cookie exception, but a real
browser is still the final check.
