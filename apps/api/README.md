# `apps/api` — MultiBench API

A thin Postgres-backed service that will serve the multibrowser SPA's data (corpus, results, raw)
and host the read-write **review** backend. Per Spec 92. **Git stays the source of truth**; the
serving tiers are a rebuildable cache, the review store is authoritative operational data.

> **Status: Phase 1 — bare scaffold.** No serving tables, no ingest, no review tables, no
> `/api/version` yet. This phase stands up the service shape (Hono + Drizzle + Postgres), the PGlite
> test rig, the CORS/cross-site-cookie topology, and Railway config. Later phases add the review
> slice (Phase 2+) and the deferred serving tiers (Phase 5+).

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
`X-CSRF-Token` header) for state-changing authed requests. Signup is gated by one shared
`REVIEW_INVITE_CODE` (fail-closed if unset). No email-enumeration / rate-limit hardening at this scale.

## Data durability

The review store is authoritative (not rebuildable from git). At this test-tool scale, **Railway's
managed-Postgres built-in backups suffice** — there is no custom backup/restore tooling.

## Deployment

Railway (NIXPACKS), `engines.node >= 20`. **Provisioning of the Railway service + Postgres is gated
on an architect-confirmed cost envelope** (Spec 92 constraint) and is done deliberately, not from CI.
