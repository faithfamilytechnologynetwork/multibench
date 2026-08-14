# Plan: Multibrowser data platform — Postgres serving layer for corpus, results, raw, and review tiers

**Specification**: [codev/specs/92-multibrowser-data-platform-pos.md](../specs/92-multibrowser-data-platform-pos.md)

## Executive Summary

The spec's chosen approach (Approach 1) is a **Postgres serving layer + a thin TypeScript API** (new
`apps/api`) behind the SPA's existing `lib/queries.ts` hook seam, with a **Python `analysis ingest`**
loading committed exporter outputs (and, for corpus, `load_corpus`) into a **Drizzle-owned schema**,
guarded by a schema-drift contract test. Git stays the source of truth; the serving tiers are a
rebuildable cache; the operational review store is a distinct authoritative data class.

This plan sequences the work as **four tier-sliced PRs** (the architect's call —
`results → raw → corpus → review`), each a shippable integration, decomposed into **eleven phases**
(atomic commits). The tier order is lowest-risk-first: prove ingest/serve/reconcile on the score
tier (which carries the paper-reconciliation guard), spend the proven pattern retiring the Spec 51
raw dual-source workaround, then move the highest-traffic corpus tier (which finally deletes
`lib/github.ts` and reaches the **zero-runtime-GitHub-reads** end state), then add the read-write
review slice last.

**Plan-level decisions settled here** (spec Open Questions + iter-1 review):

- **API framework: Hono** on Node (thin, TS-native, first-class with Drizzle + `node-postgres`);
  Fastify is the fallback if middleware needs outgrow Hono. *(OQ 2)*
- **Freshness signal: `GET /api/version`** returns per-tier `{runId?, commitSha, fingerprint,
  ingestedAt}`, served **revalidated / no-store** (cheap, always fresh). **Content endpoints are
  fingerprint-qualified in the URL path** (e.g. `/api/results/:runId/:fingerprint/...`) so they can
  carry `Cache-Control: immutable` **safely** — a re-ingest changes the fingerprint and therefore the
  URL, so no stale cache is ever served. TanStack keys never stand in for HTTP/CDN cache correctness.
  *(OQ 1, OQ 7; codex #1)*
- **Table-level Drizzle schema for all serving tiers is the first deliverable** (architect note):
  Phase 1 defines + migrates the corpus/results/raw serving tables + provenance in one reviewed
  migration. **Review-tier tables are a later migration (Phase 8), settled with Ben (@benolio)
  first.**
- **Raw retention N = 2**, implemented as a **transactional prune step in ingest**, scoped **per
  dataset lineage** (MB runs and the AFB raw-only dataset are distinct lineages) so retention never
  evicts AFB. *(OQ 4; codex #3, claude #7)*
- **Review auth first slice: magic-link only**; GitHub OAuth is a deferred follow-up. *(OQ 6)*
- **Magic-link email transport is chosen with Ben/architect before the review PR and must NOT
  collide with the global `resend`-CLI rule** — default a dedicated transactional provider
  (Postmark/SES), never direct `api.resend.com`. *(spec Constraint)*

**Cross-cutting infrastructure decided in Phase 1** (from iter-1 review, so the plan is
implementable, not aspirational):

- **The drift-guard must actually run.** There is **no test CI** in this repo (only
  `.github/workflows/validate.yml` → `tradition_validator validate-all`); porch's per-builder
  dispatcher runs only the *touched* app's suite. So the schema-drift contract test is **cross-
  registered in `.codev/checks/test.sh`**: touching `apps/api` (schema) *also* runs the Python
  contract test, and touching `workflows/analysis` runs it too. *(claude #1)*
- **Test-Postgres mechanism**: **PGlite** (in-process Postgres) for `apps/api` vitest; the Python
  contract test needs **no DB** (it diffs `contract.snapshot.json` against ingest's required
  columns); ingest **round-trip/integration** tests use **`pytest-postgresql`** (ephemeral cluster),
  `DATABASE_URL`-gated to skip cleanly where unavailable. *(claude #2)*
- **Ingest is committed-tree-bound**: ingest reads files from the **clean committed tree** at the
  stamped commit SHA (or **refuses** when relevant tier paths are dirty), so `commitSha` provably
  identifies the exact bytes loaded and a rebuild is reproducible. *(codex #2)*
- **API↔SPA topology**: separate Railway origins → the API sets **CORS allowed-origins**, and the
  review slice uses **`SameSite`/`Secure` cross-site cookies** with credentialed SPA requests
  (Phase 8). *(codex #5)*
- **Intermediate cutover state is explicit**: during Phases 3–6 the SPA runs on **two freshness
  signals** — the GitHub commit-SHA poll for not-yet-cut tiers and `/api/version` for cut tiers — so
  the unauth GitHub budget is still consumed until **Phase 7** deletes `useLatestSha`. Each tier's
  query keys move from `sha`-keyed to `runId`+`fingerprint`-keyed as it cuts over. *(claude #5)*

**Cost gate (a Phase 1 precondition, not a free-floating note):** Phase 1's Railway provisioning of
always-on compute + Postgres is **blocked until** the monthly cost envelope (compute + DB storage at
N=2 + egress) is confirmed with the architect **against actuals**, not estimates (spec Constraint;
project budget-overshoot history). *(claude #8)*

## Phases (Machine Readable)

<!-- REQUIRED: porch parses this JSON to track phase progress. Keep in sync. -->

```json
{
  "phases": [
    {"id": "phase_1", "title": "Serving API service + Drizzle schema + test/drift infrastructure"},
    {"id": "phase_2", "title": "Results tier ingest (committed-tree-bound)"},
    {"id": "phase_3", "title": "Results API + SPA swap + provenance display (PR 1)"},
    {"id": "phase_4", "title": "Raw tier ingest + retention pruning"},
    {"id": "phase_5", "title": "Raw API + SPA swap, retire baked bundle (PR 2)"},
    {"id": "phase_6", "title": "Corpus tier ingest"},
    {"id": "phase_7", "title": "Corpus API + SPA swap, delete github.ts — zero GitHub reads (PR 3)"},
    {"id": "phase_8", "title": "Review schema + auth + topology (settled with Ben)"},
    {"id": "phase_9", "title": "Review persistence swap (sync→async, resumable, conflict-safe)"},
    {"id": "phase_10", "title": "Review private submission + assignment"},
    {"id": "phase_11", "title": "Review aggregation + dashboard views (PR 4)"}
  ]
}
```

**PR boundaries**: Phase 3 opens/ships PR 1 (results); Phase 5 → PR 2 (raw); Phase 7 → PR 3
(corpus); Phase 11 → PR 4 (review, containing Phases 8–11). Each PR branches from the integration
branch per the sequential-PR recipe (`git fetch origin main && git checkout -b <branch> origin/main`),
recorded with `porch done 92 --pr <N> --branch <name>` and `--merged <N>`.

## Phase Breakdown

### Phase 1: Serving API service + Drizzle schema + test/drift infrastructure

**Dependencies**: **Cost gate cleared with the architect** (precondition on the Railway-provisioning
deliverable below)

#### Objective
Stand up `apps/api` (Hono + Drizzle + `node-postgres`) with the **table-level Drizzle schema for all
serving tiers** and its first reviewed migration, the version endpoint, the **content-addressed
endpoint URL scheme**, and — critically — the **test-Postgres + cross-registered drift-guard
infrastructure** that every later phase relies on. No tier is served yet.

#### Files to Create / Modify
- `apps/api/package.json` (Hono, drizzle-orm, node-postgres, `@electric-sql/pglite` for tests),
  `tsconfig.json`, `drizzle.config.ts`
- `apps/api/src/schema/` — `runs.ts` (run + provenance: run_id, tier, dataset_lineage, commit_sha,
  source_fingerprint, content_fingerprint?, ingested_at), `corpus.ts`, `results.ts`, `raw.ts`
  (`bytea` gz + content_fingerprint). **No review tables yet.**
- `apps/api/drizzle/0000_*.sql` — generated + reviewed first migration
- `apps/api/src/server.ts`, `src/routes/health.ts`, `src/routes/version.ts` (per-tier provenance;
  `no-store`), `src/db.ts` (pool), `src/cors.ts` (allowed-origins)
- `apps/api/scripts/schema-contract.ts` → `apps/api/src/schema/contract.snapshot.json`
- `apps/api/railway.json`, `.env.example`, `apps/api/README.md`
- `.codev/checks/test.sh` — add the `apps/api` suite **and cross-register**: touching `apps/api`
  schema *or* `workflows/analysis` runs the Python contract test
- `apps/api/src/**/*.test.ts` (PGlite-backed: migration applies; version envelope; contract snapshot)

#### Deliverables
- [ ] **Cost gate cleared** (architect-confirmed envelope vs actuals) **before** Railway provisioning
- [ ] `apps/api` builds; `/api/health` + `/api/version` serve against a pool; content-URL scheme
      (`/:runId/:fingerprint/...`) fixed and documented
- [ ] Drizzle schema covers all serving tiers at table level; migration **generated then reviewed**
      (no `db:push`); `contract.snapshot.json` emitted
- [ ] Railway service + managed Postgres provisioned; env `DATABASE_URL`; SPA stays secret-free
- [ ] Test-Postgres wired (PGlite for TS); drift-guard cross-registered in `test.sh`
- [ ] Tests for this phase

#### Acceptance Criteria
- [ ] `pnpm -C apps/api build && pnpm -C apps/api test` green (PGlite, no external DB)
- [ ] Touching only `apps/api/src/schema` triggers the Python contract test via `test.sh`
- [ ] Build and tests passing

#### Test Plan
Unit: contract snapshot matches schema; version envelope shape; CORS origins. Integration: migration
applies on a PGlite DB. Manual: `test.sh` dispatch matrix (api-only change runs contract test).

---

### Phase 2: Results tier ingest (committed-tree-bound)

**Dependencies**: Phase 1

#### Objective
Add `analysis ingest` (Typer subcommand) for the **score tier**: load a committed `results/<run-id>/`
into Postgres, **reading from the clean committed tree at the stamped commit SHA** (refuse dirty
relevant paths), idempotent, transactional, per-tier independent. Prove DB values equal exporter shard
values and that stamped provenance reproduces identical payloads.

#### Files to Create / Modify
- `workflows/analysis/analysis/ingest.py` (psycopg writer; results loaders reusing `export_results`
  output readers; committed-tree read + dirty-path guard), `analysis/cli.py` (`ingest` subcommand)
- `workflows/analysis/pyproject.toml` (`psycopg`, `pytest-postgresql`), `analysis/db_contract.py`
  (assert `apps/api/src/schema/contract.snapshot.json`)
- `workflows/analysis/tests/test_ingest_results.py`, `tests/test_schema_contract.py`

#### Deliverables
- [ ] `analysis ingest <run-id> --tier results` loads from the committed tree; dirty relevant paths
      are refused; re-run unchanged is a no-op (fingerprint match); changed input replaces the run's
      rows in one transaction
- [ ] Stamped `commit_sha` provably identifies the loaded bytes; stamped fingerprint equals the
      committed `manifest.json` fingerprint
- [ ] Schema-drift contract test fails on column divergence (runs with **no DB**)
- [ ] Round-trip test (DB values == exporter shard values); **provenance-rebuild test** (re-ingest at
      the same commit reproduces byte-equal serialized payloads)
- [ ] Tests for this phase

#### Acceptance Criteria
- [ ] Idempotency, dirty-path refusal, transactional replace, round-trip, and provenance-rebuild tests
      pass (`pytest-postgresql`, `DATABASE_URL`-gated skip)
- [ ] Ingest touches only the results tier
- [ ] Build and tests passing

#### Test Plan
Unit: dirty-path guard; contract drift; fingerprint equality. Integration: ingest a fixture
`results/<run-id>/` into an ephemeral PG; assert row values + payload byte-equality on re-ingest.

---

### Phase 3: Results API + SPA swap + provenance display (PR 1)

**Dependencies**: Phase 2

#### Objective
Serve the score tier from the API and repoint the SPA's results fetchers — the first end-to-end tier —
holding the paper-reconciliation guard, introducing the **`fakeApi` test harness**, the version-signal,
the fail-visible notice, **SPA provenance display**, and **read-endpoint abuse bounds**. **Opens PR 1.**

#### Files to Create / Modify
- `apps/api/src/routes/results.ts` (runs list, manifest, shard; fingerprint-qualified URLs +
  `immutable`; abuse bounds / basic rate limiting), route tests
- `apps/api/src/ratelimit.ts` (public-read abuse bounds, shared by later read routes)
- `apps/multibrowser/src/lib/api.ts` (new fetch boundary; `VITE_API_BASE`), `lib/queries.ts` (results
  loaders → API; results freshness via `/api/version`; results keys → `runId`+`fingerprint`),
  `lib/constants.ts`, `.env.example`
- `apps/multibrowser/src/test/fakeApi.ts` (new harness — models the API, not git-trees/raw),
  `renderApp.tsx` wiring; rewrite `results.data.test.ts`, `queries.hooks.test.tsx` (results paths)
- `apps/multibrowser/src/components/` — fail-visible notice for results routes; a **provenance
  display** component (commit SHA + fingerprint for the served tier)
- Reconciliation guard test run against API-served numbers

#### Deliverables
- [ ] `/results` reads from the API; no `api.github.com`/`raw` calls for the score tier
- [ ] Leaderboard mean-of-means reconciles with the paper (guard green against API data)
- [ ] `/api/version` drives results freshness; API-down shows a fail-visible notice (no GitHub fallback)
- [ ] `fakeApi` harness exists; results route tests pass against it (not "unchanged" — rewritten)
- [ ] Provenance (SHA + fingerprint) shown in the UI for the results tier; read endpoints abuse-bounded
- [ ] Per-tier **drop-and-rebuild** check: drop results rows, re-ingest, served payload byte-equal
- [ ] Tests for this phase; **PR 1 opened** with Phases 1–3

#### Acceptance Criteria
- [ ] `pnpm -C apps/multibrowser test` green against `fakeApi`; reconciliation guard passes; results
      routes unchanged in layout
- [ ] Build and tests passing

#### Test Plan
Unit: results fetchers hit fingerprint-qualified endpoints; provenance render; rate-limit bound.
Integration: results route tests over `fakeApi`; drop-and-rebuild byte-equality. Manual: deployed
`/results` against the live API.

---

### Phase 4: Raw tier ingest + retention pruning

**Dependencies**: Phase 1 (schema), Phase 2 (ingest scaffolding)

#### Objective
Extend `analysis ingest` to the **raw tier**: gz shards as `bytea`, content-fingerprint-stamped,
size-ceiling-enforced, **raw-only-run capable** (AFB), plus **retention N=2 pruning** scoped per
dataset lineage.

#### Files to Create / Modify
- `analysis/ingest.py` (raw path reusing `export_raw`/`raw_writer` readers; gz bytes verbatim; prune
  step keeping last N=2 run-ids **per dataset lineage**, transactional, oldest-first),
  `analysis/cli.py` (`--tier raw`; default ingests whichever tiers a run has)
- `workflows/analysis/tests/test_ingest_raw.py` (incl. AFB raw-only fixture + a retention fixture)

#### Deliverables
- [ ] `--tier raw` loads gz shards → `bytea`; content fingerprint stamped; per-shard ≤1 MB / per-run
      ≤200 MB ceilings enforced **before any write**
- [ ] Raw-only run (AFB, no `results/`) ingests with **no cross-tier mismatch error**; cross-tier
      fingerprint equality asserted only when both tiers exist
- [ ] **Retention N=2 pruning** removes the oldest MB run beyond N, transactionally, and **never evicts
      the AFB lineage**
- [ ] Idempotent + transactional; tests for this phase

#### Acceptance Criteria
- [ ] Raw round-trip: stored gz bytes decode byte-identical to the exporter's transcripts+verdicts
- [ ] AFB raw-only fixture ingests cleanly; a 3rd MB run prunes the 1st but leaves AFB; ceiling breach
      aborts before writing
- [ ] Build and tests passing

#### Test Plan
Unit: gz byte preservation; ceiling enforcement; raw-only path; retention ordering + lineage scoping.
Integration: ingest fixture raw + AFB into ephemeral PG; assert prune result.

---

### Phase 5: Raw API + SPA swap, retire baked bundle (PR 2)

**Dependencies**: Phase 4, Phase 3 (`lib/api.ts`, `fakeApi`, version-signal)

#### Objective
Serve raw shards from the API and **delete the entire Spec 51 dual-source workaround**. `/raw/<runId>`
(including AFB) renders from the API. **Opens PR 2.**

#### Files to Create / Modify
- `apps/api/src/routes/raw.ts` (catalog + shard; `content-encoding: gzip`; fingerprint-qualified URL
  + `immutable`; abuse bounds), route tests
- `apps/multibrowser/src/lib/rawSource.ts` (new `ApiRawSource`; **remove** `BakedRawSource`,
  `GitHubRawSource`, `resolveRawSource`, `isHtmlResponse`), `lib/queries.ts` (raw loaders → API),
  `lib/constants.ts` — **remove `RAW_SOURCE_QK` from `RAW_PERSIST_EXCLUDED` only; KEEP
  `RAW_SCENARIO_QK`** (API shards are still ~0.7 MB — dropping it kills the localStorage cache, a
  documented scar)
- Rewrite `rawScenario.test.ts`, `rawData.test.ts` (they import `GitHubRawSource`) onto `fakeApi`
- **Delete**: `apps/multibrowser/scripts/bake-and-deploy.sh`, `apps/multibrowser/.railwayignore`
- `apps/multibrowser/src/deploy.test.ts` (drop baked-bundle assertions)

#### Deliverables
- [ ] Raw viewer + `/raw/<runId>` (AFB) read from the API; dual-source resolver + baked bundle gone
- [ ] No `railway up --no-gitignore` / `.railwayignore` / `isHtmlResponse` residue
- [ ] Provenance (SHA + fingerprint) shown for the raw tier
- [ ] The two Spec 51 raw-dual-source `lessons-critical` entries retired (via MAINTAIN)
- [ ] Tests for this phase; **PR 2 opened** with Phases 4–5

#### Acceptance Criteria
- [ ] `pnpm -C apps/multibrowser test` green; raw routes render transcripts+verdicts over `fakeApi`
- [ ] `grep` shows no `bake-and-deploy`, `.railwayignore`, `no-gitignore`, `isHtmlResponse`,
      `GitHubRawSource` residue; `RAW_SCENARIO_QK` exclusion retained
- [ ] Build and tests passing

#### Test Plan
Unit: `ApiRawSource` catalog/shard + gz decode; immutable-URL cache header. Integration: raw + AFB
routes over `fakeApi`; drop-and-rebuild raw byte-equality. Manual: deployed `/raw/<runId>` for an MB
run and the AFB run.

---

### Phase 6: Corpus tier ingest

**Dependencies**: Phase 1 (schema)

#### Objective
Ingest the **corpus** by reusing `analysis/loaders.py::load_corpus`, with a **`traditions/`-tree
content-hash** as provenance (no exporter manifest/judgment fingerprint exists for corpus).

#### Files to Create / Modify
- `analysis/ingest.py` (corpus path via `load_corpus`; content hash over the `traditions/` tree at the
  committed SHA; committed-tree read + dirty-path guard), `analysis/cli.py` (`--tier corpus`)
- `workflows/analysis/tests/test_ingest_corpus.py`

#### Deliverables
- [ ] `--tier corpus` loads traditions/scenarios/prose → DB with a content-hash + commit-SHA stamp
- [ ] Re-ingest at the same tree is a no-op; a changed tradition file changes the hash
- [ ] Idempotent + transactional; tests for this phase

#### Acceptance Criteria
- [ ] Corpus round-trip: DB-served tradition/scenario/prose equals what `load_corpus` reads
- [ ] Content-hash provenance is deterministic + change-sensitive
- [ ] Build and tests passing

#### Test Plan
Unit: content-hash determinism/sensitivity; idempotency; dirty-path guard. Integration: ingest real
`traditions/` into ephemeral PG; sampled tradition/scenario round-trips.

---

### Phase 7: Corpus API + SPA swap, delete github.ts — zero GitHub reads (PR 3)

**Dependencies**: Phase 6, Phase 5 (`lib/api.ts`, `fakeApi` fully in place)

#### Objective
Serve corpus from the API, repoint the last fetchers, and **delete `lib/github.ts` and `useLatestSha`
entirely** — reaching the **zero-runtime-GitHub-reads** end state. **Opens PR 3.**

#### Files to Create / Modify
- `apps/api/src/routes/corpus.ts` (traditions list, tradition, scenario, scenario-meta, guidance;
  fingerprint-qualified + version-keyed), route tests
- `apps/multibrowser/src/lib/queries.ts` (corpus loaders → API; remove SHA-pinning plumbing),
  **delete `apps/multibrowser/src/lib/github.ts`** and **`src/lib/github.test.ts`**
- `apps/multibrowser/src/lib/rateLimit.ts` → replace with an **API-error notice** module (it re-exports
  `RateLimitError` from `github.ts` and is imported by the 9 route pages)
- `apps/multibrowser/src/lib/queryClient.ts` — replace the `RateLimitError`-based retry predicate with
  an **API-error analogue**
- `apps/multibrowser/src/components/RateLimitBanner.tsx` → fail-visible **API notice** component
- **9 call sites** of `useLatestSha` updated (the 8 tier routes **plus `routes/RootLayout.tsx`**)
- `apps/multibrowser/src/test/fakeRepo.ts` — remove/replace the `TreeEntry` import (now `fakeApi`);
  update `queries.hooks.test.tsx`, `results.data.test.ts` residual GitHub references
- `apps/multibrowser/src/deploy.test.ts` — assert no **runtime data-host** string
  (`api.github.com`, `raw.githubusercontent.com`) is referenced in `src`; the guard is **scoped to
  runtime hosts** so the legitimate opt-in `github.com` issue/edit/blob links in `lib/reviewReport.ts`
  are not flagged

#### Deliverables
- [ ] All corpus browsing reads from the API; `lib/github.ts`, `useLatestSha`, and the SHA poll deleted
- [ ] No `api.github.com` / `raw.githubusercontent.com` runtime reference remains in the SPA; the
      review report's opt-in GitHub links are preserved
- [ ] The 9 routes render unchanged in layout with the fail-visible notice; queryClient retry policy
      updated
- [ ] **Full drop-and-rebuild**: drop the whole serving DB, re-ingest all three tiers at a fixed
      commit, every served payload byte-equal; cross-tier fingerprint mismatch is surfaced in the UI
- [ ] Tests for this phase; **PR 3 opened** with Phases 6–7

#### Acceptance Criteria
- [ ] `pnpm -C apps/multibrowser test` green; a guard test finds no runtime-data-host reference in `src`
- [ ] Build and tests passing

#### Test Plan
Unit: corpus fetchers → API; queryClient retry analogue; runtime-host guard (allows `reviewReport`
opt-in links). Integration: corpus routes over `fakeApi`; full drop-and-rebuild byte-equality. Manual:
full browse of a deployed SPA with the API as the only backend.

---

### Phase 8: Review schema + auth + topology (settled with Ben)

**Dependencies**: Phase 1 (service); **Ben (@benolio) sign-off on the review data model before this
migration is written**

#### Objective
Add the **operational review store** and authentication: a second reviewed migration, magic-link auth
+ revocable sessions, server-side per-reviewer authorization, cross-origin cookie topology, a **PII
deletion path**, and **verified backup/restore**. **Opens PR 4.**

#### Files to Create / Modify
- `apps/api/src/schema/review.ts` (reviewers, assignments, reviews (versioned drafts with a
  `version`/`updated_at` for optimistic concurrency), submissions (immutable snapshots)),
  `apps/api/drizzle/0001_*.sql` (generated + reviewed)
- `apps/api/src/auth/` (magic-link issue/verify — single-use, expiring; httpOnly **`Secure`+`SameSite`
  cross-site** revocable sessions; CSRF; email-enumeration + rate-limit bounds; validated redirects),
  `src/routes/auth.ts`
- `apps/api/src/mail/` (transactional transport — chosen with Ben/architect; **not** the `resend` CLI
  path; no direct `api.resend.com`)
- `apps/api/src/routes/account.ts` (**PII deletion** endpoint), backup/restore runbook +
  `apps/api/scripts/restore-check.ts`
- `apps/api/src/**/*.test.ts` (auth, session, isolation, PII-deletion, restore tests — PGlite)

#### Deliverables
- [ ] Review tables migrated (generated + reviewed; no `db:push`); operational store documented as a
      distinct data class with backup/restore + retention
- [ ] Magic-link login end-to-end; tokens single-use + expiring; sessions revocable; cross-origin
      cookies correct
- [ ] Server-side authz isolates each reviewer's records; a coordinator role reads aggregates only
- [ ] **PII deletion path** implemented + tested; **backup restores cleanly** (verified, not just documented)
- [ ] Tests for this phase

#### Acceptance Criteria
- [ ] Auth happy path + expired/reused-token rejection + reviewer-isolation + PII-deletion + restore
      tests pass; email transport avoids the `resend` CLI path
- [ ] Build and tests passing

#### Test Plan
Unit: token single-use/expiry; session revocation; CSRF; redirect validation; authz isolation; PII
deletion. Integration: login → cross-origin session → private-endpoint access; cross-reviewer denied;
backup → restore round-trip.

---

### Phase 9: Review persistence swap (sync→async, resumable, conflict-safe)

**Dependencies**: Phase 8

#### Objective
Swap `lib/review.ts` persistence from the **synchronous** localStorage store to the API — a
**sync→async conversion** with optimistic updates and cross-device conflict handling — behind Spec
83's zod-tolerant loader. (This is the persistence seam; submission is Phase 10.)

#### Files to Create / Modify
- `apps/multibrowser/src/lib/review.ts` (async persistence against the API; optimistic update +
  reconcile; keep the tolerant zod loader; `version`-based conflict resolution replacing the raw
  `storage`-event sync), `src/lib/reviewApi.ts` (client)
- `apps/api/src/routes/review.ts` (draft save/load with optimistic-concurrency `version` checks)
- `apps/multibrowser/src/**/*.test.ts` (async persistence, resumability, conflict, tolerant load)

#### Deliverables
- [ ] Review intake persists to the API; resumable across devices for the authenticated reviewer
- [ ] Optimistic updates; a stale write is detected via `version` and reconciled, not lost
- [ ] The zod-tolerant loader still degrades a corrupt subfield to a default
- [ ] Tests for this phase

#### Acceptance Criteria
- [ ] `pnpm -C apps/multibrowser test` green; two-device resume + conflict tests pass
- [ ] Build and tests passing

#### Test Plan
Unit: async store; optimistic update/rollback; tolerant load. Integration: device-A save → device-B
resume; concurrent edit → version conflict resolved.

---

### Phase 10: Review private submission + assignment

**Dependencies**: Phase 9

#### Objective
Add **private, immutable submission** (opt-in publish-to-issue) and **assignment** with defined status
transitions.

#### Files to Create / Modify
- `apps/api/src/routes/review.ts` (submit → immutable snapshot; assignment CRUD + status transitions
  assigned→in-progress→submitted), route tests
- `apps/multibrowser/src/lib/reviewReport.ts` (private submission path; publish-to-issue becomes
  explicit opt-in — the existing GitHub links stay), review route components (assignment view)
- `apps/multibrowser/src/**/*.test.ts` (immutable submission, assignment transitions)

#### Deliverables
- [ ] Submissions private by default (opt-in publish), **immutable once submitted**
- [ ] Assignment with defined status transitions and an explicit "complete" definition
- [ ] Tests for this phase

#### Acceptance Criteria
- [ ] A submitted review cannot be mutated; assignment transitions enforced; publish is opt-in
- [ ] Build and tests passing

#### Test Plan
Unit: immutability guard; transition state machine. Integration: submit → private snapshot; opt-in
publish path; assignment lifecycle.

---

### Phase 11: Review aggregation + dashboard views (PR 4)

**Dependencies**: Phase 10

#### Objective
Add **aggregation / dashboard** views (per-tradition completion, coordinator aggregates) and ship the
review slice. **Ships PR 4.**

#### Files to Create / Modify
- `apps/api/src/routes/review.ts` (aggregation endpoints; coordinator-scoped), route tests
- `apps/multibrowser/src/` review dashboard/aggregation components
- `apps/multibrowser/src/**/*.test.ts` (aggregation reflects submissions; coordinator scoping)

#### Deliverables
- [ ] Aggregation/dashboard views reflect submitted reviews; per-tradition completion visible
- [ ] Coordinator sees aggregates without authoring another's review
- [ ] Tests for this phase; **PR 4 opened** with Phases 8–11

#### Acceptance Criteria
- [ ] `pnpm -C apps/multibrowser test` + `pnpm -C apps/api test` green; aggregation correctness test passes
- [ ] Build and tests passing

#### Test Plan
Unit: aggregation math; coordinator scoping. Integration: submit reviews → aggregation view; full
review of a tradition end-to-end. Manual: dashboard on the deployed SPA.

## Risks and Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Drift-guard has no CI to run in | Medium | High | Cross-register in `.codev/checks/test.sh` (Phase 1) so an `apps/api` schema change *and* a `workflows/analysis` change both run the Python contract test; no-DB contract test. |
| No test-Postgres → red checks for every builder | Medium | High | PGlite for `apps/api` vitest; `pytest-postgresql` (`DATABASE_URL`-gated) for ingest; contract test needs no DB (Phase 1/2). |
| Deleting `github.ts` breaks unlisted dependents (Phase 7) | Medium | High | Phase 7 lists all: `rateLimit.ts`, `queryClient.ts`, `test/fakeRepo.ts`, github test files, 9 `useLatestSha` sites incl. `RootLayout`. |
| Unsafe immutable caching on stable URLs | Medium | High | Fingerprint-qualified content URLs + `immutable`; `/api/version` `no-store`; re-ingest changes the URL. |
| Provenance not tied to loaded bytes | Low | High | Ingest reads the clean committed tree / refuses dirty paths; provenance-rebuild test. |
| Retention N=2 evicts AFB or never runs | Medium | Medium | Transactional prune step scoped per dataset lineage; retention fixture test (3rd MB run prunes 1st, AFB survives). |
| Multi-PR-per-project friction with porch's gate model | Medium | Medium | Sequential-PR recipe + `porch done --pr/--merged`; raise with the architect before Phase 3 opens PR 1 if the `pr` gate assumes a single PR. |
| Review data model diverges from Ben's intent | Medium | Medium | Phase 8 migration gated on Ben's sign-off; #85 stays the tracking issue. |
| Magic-link email collides with the `resend`-CLI rule | Medium | Medium | Transport decided with Ben/architect; dedicated transactional provider; never direct `api.resend.com`. |
| Reconciliation drifts once DB-served | Low | High | Ingest loads pre-aggregated outputs only; keep the committed-vs-paper guard, run against API data (Phase 3). |
| Always-on cost overrun | Medium | Medium | Cost gate is a Phase 1 precondition (vs actuals); retention N as the lever. |

## Documentation Updates

- `apps/api/README.md` — new: service, schema, migration discipline (`drizzle-kit generate` → review →
  apply; never `db:push`), ingest/committed-tree contract, version + content-URL scheme, test-Postgres
  + drift-guard, CORS/cookie topology.
- `results/README.md`, `results-raw/README.md` — API-served description; retire the dual-source/baked-
  bundle section (Phases 3, 5).
- `traditions/README.md` — corpus served from the DB (Phase 7); git stays authoring/source.
- `codev/resources/arch-critical.md` — new serving-layer fact; `lessons-critical.md` — **remove the two
  raw dual-source lessons** once Phase 5 lands (via MAINTAIN, respecting the hot-tier cap).
- `apps/multibrowser/.env.example` — `VITE_API_BASE` replaces the GitHub `VITE_*` knobs by Phase 7.
