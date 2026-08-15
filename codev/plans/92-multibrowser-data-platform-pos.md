# Plan: Multibrowser data platform — Postgres serving layer (review-first, serving tiers deferred)

**Specification**: [codev/specs/92-multibrowser-data-platform-pos.md](../specs/92-multibrowser-data-platform-pos.md)

## Executive Summary

The spec's approach is a **Postgres serving layer + a thin TypeScript API** (`apps/api`) behind the
SPA's `lib/queries.ts` hook seam, with Python `analysis ingest` loading committed exporter outputs
into a Drizzle-owned schema. Git stays the source of truth; serving tiers are a rebuildable cache;
the operational review store is a distinct authoritative data class.

**Re-cut (architect / Waleed, 2026-08-15): REVIEW-FIRST, bare-minimum slice.** The read-write review
backend ships first as the smallest useful thing; the whole serving-layer migration
(corpus/results/raw ingest + SPA swap) is **kept in this plan but deferred to trailing phases/PRs in
the same project**. Rationale: the review slice is the near-term need (~5 users), it is small, and it
proves the service shape without the weight of ingest, retention, and the SPA cutover.

The plan is **thirteen phases across six PRs**. The first two PRs are the bare-minimum review slice;
the remaining four PRs are the deferred serving tiers and the deferred review coordination features.

### Bare-minimum review slice (ships first)

- **PR 1 — infra + review schema + auth**: service scaffold, review-store schema (after Ben's
  sign-off), and email+password auth.
- **PR 2 — persistence swap + submission**: `lib/review.ts` localStorage→API draft persistence, and
  private immutable submission.

### Deferred (kept in plan, shipped later, same project)

- **PR 3 results · PR 4 raw · PR 5 corpus** — the serving-tier Drizzle schema + Python ingest +
  drift-guard + `/api/version` + fingerprint-URL scheme (all **cut from the bare-minimum Phase 1** and
  moved here intact), then per-tier ingest + SPA swap; PR 5 deletes `lib/github.ts` and reaches the
  **zero-runtime-GitHub-reads** end state.
- **PR 6 review coordination** — assignment machinery + coordinator aggregation/dashboards.

### Decisions settled here

- **Web framework vs ORM — clarifying the architect's inline question.** *Hono and Drizzle are not
  alternatives — they are different layers.* **Drizzle** is the ORM (typed SQL + `drizzle-kit`
  migrations, the baked decision); it does not serve HTTP. You still need an HTTP framework on top.
  The popular TS options are **Express** (most conventional, largest ecosystem, weaker built-in TS
  types), **Fastify** (fast, schema-first, mature), and **Hono** (modern, tiny, best-in-class TS
  types, runs fine on Node/Railway). For a ~5-user review backend any of the three is fine.
  **Recommendation: Hono** (smallest surface + strongest types), with **Express as the
  boring-conventional fallback**. *Flagged for architect confirmation at this gate* — say the word and
  it's Express.
- **Auth (Waleed's explicit simplification, ~5 users): email + password, NO magic-link, NO email
  transport at all.** No `mail/` dir, no transport decision. Account creation **without email
  confirmation**: email + password hashed with **argon2id** (bcrypt acceptable), **httpOnly `Secure`
  `SameSite=None` cross-site cookie sessions** (SPA and API are separate Railway origins), sessions
  **revocable**; keep **CSRF** and **server-side per-reviewer isolation**. Signup is gated by **one
  shared invite-code env var** (`REVIEW_INVITE_CODE`) for public-endpoint hygiene — **flagged for
  Waleed to veto**.
- **Ceremony calibrated down — it's a TEST TOOL (Waleed addendum, ~5 users).** **Cheap hygiene kept**:
  password hashing (argon2id), httpOnly cookie sessions, per-reviewer isolation, CSRF, invite-code
  gate. **Dropped**: verified backup/restore + restore-check script (Railway's managed-Postgres
  built-in backups suffice — one README line); account deletion is a **trivial endpoint or a
  documented SQL one-liner**; **no** email-enumeration / rate-limit hardening.
- **Ben (@benolio) gate STANDS**: the review-schema migration (Phase 2) is written **only after his
  sign-off on the #85 data model.**
- **Cost gate — re-estimated for review-only.** The review-only DB is tiny (no raw shards, no
  retention, negligible egress): order-of-magnitude is **one small always-on API service + one small
  Postgres**. Exact Railway envelope is **brought to the architect before any provisioning** (Phase
  1); serving-tier storage/egress cost is re-estimated when PR 3+ approaches.
- Deferred serving-tier specifics (unchanged from the prior cut, retained for when those phases run):
  `/api/version` `no-store`; **fingerprint-qualified immutable content URLs**; **committed-tree-bound
  ingest** (refuse dirty paths); **retention N=2** transactional prune scoped per dataset lineage;
  the **drift-guard cross-registered in `.codev/checks/test.sh`** (no test-CI exists); **PGlite**
  (TS) + **`pytest-postgresql`** (Python) test databases.

## Phases (Machine Readable)

<!-- REQUIRED: porch parses this JSON to track phase progress. Keep in sync. -->

```json
{
  "phases": [
    {"id": "phase_1", "title": "API service scaffold (Hono + Drizzle + Postgres, PGlite rig, Railway, topology)"},
    {"id": "phase_2", "title": "Review schema + email/password auth (after Ben sign-off) — opens PR 1"},
    {"id": "phase_3", "title": "Review draft persistence swap (localStorage→API, sync→async, conflict-safe)"},
    {"id": "phase_4", "title": "Review private immutable submission — opens PR 2"},
    {"id": "phase_5", "title": "DEFERRED: serving schema + ingest/drift infra + /api/version + fingerprint URLs"},
    {"id": "phase_6", "title": "DEFERRED: results tier ingest (committed-tree-bound)"},
    {"id": "phase_7", "title": "DEFERRED: results API + SPA swap + provenance display — opens PR 3"},
    {"id": "phase_8", "title": "DEFERRED: raw tier ingest + retention pruning"},
    {"id": "phase_9", "title": "DEFERRED: raw API + SPA swap, retire baked bundle — opens PR 4"},
    {"id": "phase_10", "title": "DEFERRED: corpus tier ingest"},
    {"id": "phase_11", "title": "DEFERRED: corpus API + SPA swap, delete github.ts (zero GitHub reads) — opens PR 5"},
    {"id": "phase_12", "title": "DEFERRED: review assignment machinery"},
    {"id": "phase_13", "title": "DEFERRED: review aggregation + coordinator dashboards — opens PR 6"}
  ]
}
```

**PR boundaries**: PR 1 = Phases 1–2 (infra + schema + auth); PR 2 = Phases 3–4 (persistence +
submission); PR 3 = Phases 5–7 (results); PR 4 = Phases 8–9 (raw); PR 5 = Phases 10–11 (corpus); PR 6
= Phases 12–13 (review coordination). Each PR branches from the integration branch
(`git fetch origin main && git checkout -b <branch> origin/main`), recorded with
`porch done 92 --pr <N> --branch <name>` and `--merged <N>`.

---

## Bare-minimum review slice

### Phase 1: API service scaffold (Hono + Drizzle + Postgres, PGlite rig, Railway, topology)

**Dependencies**: **Cost gate cleared with the architect** (review-only Railway envelope brought to
them **before** provisioning)

#### Objective
Stand up `apps/api` as a bare service scaffold — no serving tables, no ingest, no review tables yet —
with the DB access layer, the PGlite test rig, Railway service + Postgres, and the CORS/cross-site-cookie
topology the auth phase needs. This is deliberately minimal per the re-cut.

#### Files to Create / Modify
- `apps/api/package.json` (Hono [pending architect confirm], drizzle-orm, node-postgres,
  `@electric-sql/pglite` for tests; **`engines.node >= 20`**), `tsconfig.json`, `drizzle.config.ts`
- `apps/api/src/server.ts`, `src/routes/health.ts`, `src/db.ts` (pool), `src/cors.ts`
  (allowed-origins, credentialed)
- `apps/api/railway.json`, `.env.example` (`DATABASE_URL`, allowed-origins; **no** serving/version
  vars yet), `apps/api/README.md`
- `.codev/checks/test.sh` — add the `apps/api` suite line (the Python cross-registration comes with
  the deferred drift-guard in Phase 5)

#### Deliverables
- [ ] **Cost gate cleared** (architect-confirmed review-only envelope) **before** Railway provisioning
- [ ] `apps/api` builds; `/api/health` serves against a Postgres pool; `engines.node >= 20`
- [ ] Railway service + managed Postgres provisioned; env `DATABASE_URL`; SPA stays secret-free
- [ ] CORS allowed-origins + credentialed-request topology in place (for the cross-site cookie auth)
- [ ] PGlite vitest rig runs with no external DB
- [ ] Tests for this phase

#### Acceptance Criteria
- [ ] `pnpm -C apps/api build && pnpm -C apps/api test` green (PGlite)
- [ ] No serving-tier tables, no ingest, no `/api/version` present (scope discipline)
- [ ] Build and tests passing

#### Test Plan
Unit: health route; CORS origin allow/deny. Integration: server boots against a PGlite DB. Manual:
Railway service reachable; Node 20 engine enforced.

---

### Phase 2: Review schema + email/password auth (after Ben sign-off) — opens PR 1

**Dependencies**: Phase 1; **Ben (@benolio) sign-off on the #85 review data model before the migration
is written**

#### Objective
Add the operational review store and simple password auth. **Opens PR 1.**

#### Files to Create / Modify
- `apps/api/src/schema/review.ts` (reviewers (email, argon2id hash), sessions (revocable), reviews
  (versioned drafts: `version`/`updated_at` for optimistic concurrency), submissions (immutable
  snapshots)), `apps/api/drizzle/0000_*.sql` (generated + reviewed)
- `apps/api/src/auth/` (signup gated by `REVIEW_INVITE_CODE`; password hash/verify via argon2id;
  httpOnly `Secure` `SameSite=None` revocable cookie sessions; CSRF; server-side per-reviewer
  isolation middleware — **no rate-limit/enumeration hardening**), `src/routes/auth.ts`
- `apps/api/src/routes/account.ts` (**trivial account-deletion** endpoint — or a documented SQL
  one-liner in `README.md` if simpler)
- `apps/api/README.md` — one line noting **Railway managed-Postgres backups suffice** (no custom
  backup/restore tooling)
- `apps/api/src/**/*.test.ts` (signup/login/logout, invite-code gate, isolation, account-deletion — PGlite)

#### Deliverables
- [ ] Review tables migrated (generated + reviewed; **no `db:push`**); operational store noted as a
      distinct data class (Railway backups suffice — no restore-check script)
- [ ] Email+password signup (invite-code-gated) + login + logout; argon2id hashing; revocable
      cross-site cookie sessions; CSRF; per-reviewer isolation
- [ ] **`REVIEW_INVITE_CODE` flagged for Waleed to veto**; **no magic-link, no `mail/` dir**; **no
      rate-limit/enumeration hardening**
- [ ] Trivial account-deletion endpoint (or documented SQL one-liner)
- [ ] Tests for this phase; **PR 1 opened** with Phases 1–2

#### Acceptance Criteria
- [ ] Auth happy path + wrong-password + missing/invalid invite-code + reviewer-isolation +
      account-deletion tests pass
- [ ] No email/magic-link code anywhere; migration reviewed
- [ ] Build and tests passing

#### Test Plan
Unit: password hash/verify; invite-code gate; CSRF; session revocation; authz isolation; account
deletion. Integration: signup→login→cross-origin session→private endpoint; cross-reviewer denied.

---

### Phase 3: Review draft persistence swap (localStorage→API, sync→async, conflict-safe)

**Dependencies**: Phase 2

#### Objective
Swap `lib/review.ts` persistence from the **synchronous** localStorage store to the API — a
sync→async conversion with optimistic updates and cross-device conflict handling — behind Spec 83's
zod-tolerant loader. (Persistence seam only; submission is Phase 4.)

**Added requirement — out-of-sample review (Waleed, 2026-08-15):** the review `state.scenarios` map
must accept **ANY** scenario id, not only `sampleIds` (`sampleIds` is *required*, not *allowed*).
Update the SPA `TraditionReview` zod shape + persistence accordingly, and add **(a)** an affordance to
open a non-sampled scenario in review mode (same 4 checks) and **(b)** progress semantics —
**completion counts the required sample only**; extras show separately as "+N beyond sample". The
report's out-of-sample commentary section lands with submission (Phase 4). Backend needs no change:
the Phase-2 `reviews.state` JSONB already stores this verbatim.

#### Files to Create / Modify
- `apps/multibrowser/src/lib/review.ts` (async persistence; optimistic update + reconcile; keep the
  tolerant zod loader; `version`-based conflict resolution replacing the `storage`-event sync),
  `src/lib/reviewApi.ts` (client; `VITE_API_BASE`), `.env.example`
- `apps/api/src/routes/review.ts` (draft save/load with optimistic-concurrency `version` checks),
  route tests
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

### Phase 4: Review private immutable submission — opens PR 2

**Dependencies**: Phase 3

#### Objective
Add **private, immutable submission** (opt-in publish-to-issue) — completing the bare-minimum review
slice. **Opens PR 2.** (Assignment machinery is deferred to Phase 12.)

**Out-of-sample (Waleed, 2026-08-15):** the generated report lists **out-of-sample commentary in its
own section**, distinct from the required-sample reviews.

#### Files to Create / Modify
- `apps/api/src/routes/review.ts` (submit → immutable snapshot), route tests
- `apps/multibrowser/src/lib/reviewReport.ts` (private submission path; publish-to-issue becomes
  explicit opt-in — the existing GitHub links stay), review submit components
- `apps/multibrowser/src/**/*.test.ts` (immutable submission)

#### Deliverables
- [ ] Submissions private by default (opt-in publish), **immutable once submitted**
- [ ] Tests for this phase; **PR 2 opened** with Phases 3–4

#### Acceptance Criteria
- [ ] A submitted review cannot be mutated; publish is opt-in; identity never public unless published
- [ ] Build and tests passing

#### Test Plan
Unit: immutability guard. Integration: submit → private snapshot; opt-in publish path.

---

## DEFERRED — serving tiers (kept in plan, shipped in later PRs, same project)

> These phases were the original core of this project; per the 2026-08-15 re-cut they ship **after**
> the bare-minimum review slice. Content is retained intact so they can be picked up without
> re-deciding. Each still respects the baked decisions (Drizzle migrations, Python ingest, fail-visible
> no-fallback, tier-per-PR) and the iter-1 review fixes.

### Phase 5: DEFERRED — serving schema + ingest/drift infra + /api/version + fingerprint URLs

**Dependencies**: Phase 1 (service); scheduled when the architect greenlights the serving migration

#### Objective
Add everything cut from the bare-minimum Phase 1: the **table-level Drizzle schema for all serving
tiers** (corpus/results/raw + provenance) and its reviewed migration, the **schema-drift contract
test cross-registered in `.codev/checks/test.sh`**, the **`pytest-postgresql`** ingest test rig, the
**`/api/version`** endpoint (`no-store`), and the **fingerprint-qualified immutable content-URL
scheme**.

#### Files to Create / Modify
- `apps/api/src/schema/` — `runs.ts` (run_id, tier, dataset_lineage, commit_sha, source_fingerprint,
  content_fingerprint?, ingested_at), `corpus.ts`, `results.ts`, `raw.ts` (`bytea` gz), migration
- `apps/api/src/routes/version.ts` (`no-store`), `apps/api/scripts/schema-contract.ts` →
  `contract.snapshot.json`
- `.codev/checks/test.sh` — cross-register: touching `apps/api` schema *or* `workflows/analysis` runs
  the Python contract test
- `workflows/analysis/analysis/db_contract.py`, `workflows/analysis/pyproject.toml`
  (`psycopg`, `pytest-postgresql`)

#### Deliverables
- [ ] Serving-tier schema migrated (generated + reviewed); `contract.snapshot.json` emitted; drift
      test cross-registered and no-DB; `/api/version` + fingerprint-URL scheme fixed and documented
- [ ] Tests for this phase

#### Acceptance Criteria
- [ ] Touching only `apps/api/src/schema` triggers the Python contract test via `test.sh`; migration reviewed
- [ ] Build and tests passing

#### Test Plan
Unit: contract snapshot vs schema; version envelope; content-URL scheme. Integration: migration on PGlite.

---

### Phase 6: DEFERRED — results tier ingest (committed-tree-bound)

**Dependencies**: Phase 5

#### Objective
`analysis ingest --tier results`: load a committed `results/<run-id>/` from the **clean committed tree**
at the stamped commit SHA (refuse dirty relevant paths), idempotent, transactional, per-tier
independent; prove DB values equal exporter shard values and that provenance reproduces identical
payloads.

#### Files to Create / Modify
- `workflows/analysis/analysis/ingest.py` (psycopg writer; results readers; committed-tree read +
  dirty-path guard), `analysis/cli.py` (`ingest` subcommand)
- `workflows/analysis/tests/test_ingest_results.py`, `tests/test_schema_contract.py`

#### Deliverables
- [ ] `--tier results` loads from the committed tree; dirty paths refused; re-run unchanged is a no-op;
      changed input replaces the run's rows in one transaction
- [ ] Stamped `commit_sha` provably identifies the loaded bytes; fingerprint equals the committed manifest's
- [ ] Round-trip (DB == shard) + provenance-rebuild tests; tests for this phase

#### Acceptance Criteria
- [ ] Idempotency, dirty-path refusal, transactional replace, round-trip, provenance-rebuild pass
      (`pytest-postgresql`, `DATABASE_URL`-gated)
- [ ] Build and tests passing

#### Test Plan
Unit: dirty-path guard; contract drift; fingerprint equality. Integration: ingest fixture results into
ephemeral PG; payload byte-equality on re-ingest.

---

### Phase 7: DEFERRED — results API + SPA swap + provenance display — opens PR 3

**Dependencies**: Phase 6

#### Objective
Serve the score tier from the API and repoint the SPA's results fetchers — first serving tier —
holding the paper-reconciliation guard, introducing the **`fakeApi` test harness**, the version-signal,
fail-visible notice, **SPA provenance display**, and **read-endpoint abuse bounds**. **Opens PR 3.**

#### Files to Create / Modify
- `apps/api/src/routes/results.ts` (fingerprint-qualified URLs + `immutable`; abuse bounds),
  `src/ratelimit.ts`, route tests
- `apps/multibrowser/src/lib/api.ts`, `lib/queries.ts` (results loaders → API; results freshness via
  `/api/version`; keys → `runId`+`fingerprint`), `lib/constants.ts`, `.env.example`
- `apps/multibrowser/src/test/fakeApi.ts` (new harness); rewrite `results.data.test.ts`,
  `queries.hooks.test.tsx` (results paths)
- `apps/multibrowser/src/components/` fail-visible notice + provenance-display component
- Reconciliation guard test against API-served numbers

#### Deliverables
- [ ] `/results` reads from the API; leaderboard reconciles with the paper (guard green against API data)
- [ ] `/api/version` drives results freshness; API-down shows a fail-visible notice (no GitHub fallback)
- [ ] `fakeApi` harness exists; results route tests pass against it; provenance shown; reads abuse-bounded
- [ ] Per-tier drop-and-rebuild byte-equality; tests for this phase; **PR 3 opened** with Phases 5–7

#### Acceptance Criteria
- [ ] `pnpm -C apps/multibrowser test` green against `fakeApi`; reconciliation guard passes
- [ ] **Intermediate state note**: SPA now runs two freshness signals (GitHub SHA poll for
      corpus/raw + `/api/version` for results); GitHub budget still consumed until Phase 11
- [ ] Build and tests passing

#### Test Plan
Unit: results fetchers hit fingerprint-qualified endpoints; provenance render; rate-limit bound.
Integration: results routes over `fakeApi`; drop-and-rebuild. Manual: deployed `/results`.

---

### Phase 8: DEFERRED — raw tier ingest + retention pruning

**Dependencies**: Phase 5, Phase 6

#### Objective
`analysis ingest --tier raw`: gz shards as `bytea`, content-fingerprint-stamped, size-ceiling-enforced,
**raw-only-run capable** (AFB), plus **retention N=2 pruning** scoped per dataset lineage.

#### Files to Create / Modify
- `analysis/ingest.py` (raw path reusing `export_raw`/`raw_writer` readers; gz verbatim; transactional
  prune keeping last N=2 per dataset lineage, oldest-first), `analysis/cli.py` (`--tier raw`)
- `workflows/analysis/tests/test_ingest_raw.py` (AFB raw-only + retention fixtures)

#### Deliverables
- [ ] `--tier raw` loads gz → `bytea`; ceilings enforced before any write; content fingerprint stamped
- [ ] Raw-only run (AFB) ingests with no cross-tier mismatch; cross-tier equality only when both tiers exist
- [ ] Retention N=2 prunes oldest MB run, transactional, **never evicts AFB**; tests for this phase

#### Acceptance Criteria
- [ ] Raw round-trip byte-identical; 3rd MB run prunes 1st but leaves AFB; ceiling breach aborts pre-write
- [ ] Build and tests passing

#### Test Plan
Unit: gz preservation; ceilings; raw-only; retention ordering + lineage scoping. Integration: ingest
raw + AFB into ephemeral PG; assert prune.

---

### Phase 9: DEFERRED — raw API + SPA swap, retire baked bundle — opens PR 4

**Dependencies**: Phase 8, Phase 7

#### Objective
Serve raw shards from the API and **delete the entire Spec 51 dual-source workaround**;
`/raw/<runId>` (incl. AFB) renders from the API. **Opens PR 4.**

#### Files to Create / Modify
- `apps/api/src/routes/raw.ts` (`content-encoding: gzip`; fingerprint-qualified + `immutable`; abuse bounds), tests
- `apps/multibrowser/src/lib/rawSource.ts` (new `ApiRawSource`; remove `BakedRawSource`,
  `GitHubRawSource`, `resolveRawSource`, `isHtmlResponse`), `lib/queries.ts` (raw → API),
  `lib/constants.ts` — **remove `RAW_SOURCE_QK` from `RAW_PERSIST_EXCLUDED` only; KEEP
  `RAW_SCENARIO_QK`** (≈0.7 MB shards would blow the localStorage cache — documented scar)
- Rewrite `rawScenario.test.ts`, `rawData.test.ts` onto `fakeApi`
- **Delete**: `scripts/bake-and-deploy.sh`, `.railwayignore`; update `src/deploy.test.ts`

#### Deliverables
- [ ] Raw viewer + `/raw/<runId>` (AFB) read from the API; dual-source + baked bundle gone; provenance shown
- [ ] No `bake-and-deploy` / `.railwayignore` / `no-gitignore` / `isHtmlResponse` / `GitHubRawSource` residue;
      `RAW_SCENARIO_QK` exclusion retained
- [ ] The two Spec 51 raw-dual-source `lessons-critical` entries retired (via MAINTAIN)
- [ ] Tests for this phase; **PR 4 opened** with Phases 8–9

#### Acceptance Criteria
- [ ] `pnpm -C apps/multibrowser test` green; raw routes render over `fakeApi`; residue grep clean
- [ ] Build and tests passing

#### Test Plan
Unit: `ApiRawSource` + gz decode; immutable header. Integration: raw + AFB over `fakeApi`;
drop-and-rebuild. Manual: deployed `/raw/<runId>` for MB + AFB.

---

### Phase 10: DEFERRED — corpus tier ingest

**Dependencies**: Phase 5

#### Objective
`analysis ingest --tier corpus` reusing `load_corpus`, with a **`traditions/`-tree content-hash** as
provenance (no exporter manifest/judgment fingerprint exists for corpus).

#### Files to Create / Modify
- `analysis/ingest.py` (corpus path via `load_corpus`; content hash over the tree at the committed SHA;
  dirty-path guard), `analysis/cli.py` (`--tier corpus`)
- `workflows/analysis/tests/test_ingest_corpus.py`

#### Deliverables
- [ ] `--tier corpus` loads traditions/scenarios/prose with a content-hash + commit-SHA stamp;
      re-ingest at the same tree is a no-op; a changed file changes the hash; tests for this phase

#### Acceptance Criteria
- [ ] Corpus round-trip equals `load_corpus`; content-hash deterministic + change-sensitive
- [ ] Build and tests passing

#### Test Plan
Unit: content-hash determinism/sensitivity; idempotency; dirty-path guard. Integration: ingest real
`traditions/`; sampled round-trip.

---

### Phase 11: DEFERRED — corpus API + SPA swap, delete github.ts (zero GitHub reads) — opens PR 5

**Dependencies**: Phase 10, Phase 9

#### Objective
Serve corpus from the API, repoint the last fetchers, and **delete `lib/github.ts` and `useLatestSha`
entirely** — reaching the **zero-runtime-GitHub-reads** end state. **Opens PR 5.**

#### Files to Create / Modify
- `apps/api/src/routes/corpus.ts` (traditions/tradition/scenario/scenario-meta/guidance;
  fingerprint-qualified + version-keyed), route tests
- `apps/multibrowser/src/lib/queries.ts` (corpus loaders → API; remove SHA-pinning), **delete
  `lib/github.ts`** and **`lib/github.test.ts`**
- `lib/rateLimit.ts` → API-error notice module (re-exports `RateLimitError`, imported by the routes);
  `lib/queryClient.ts` → API-error retry analogue; `RateLimitBanner.tsx` → API notice
- **9 `useLatestSha` sites** updated (8 tier routes **+ `routes/RootLayout.tsx`**)
- `src/test/fakeRepo.ts` (remove `TreeEntry`); update `queries.hooks.test.tsx`, `results.data.test.ts`
- `src/deploy.test.ts` — guard scoped to **runtime data hosts** (`api.github.com`,
  `raw.githubusercontent.com`) so `lib/reviewReport.ts` opt-in `github.com` links are **not** flagged

#### Deliverables
- [ ] Corpus reads from the API; `lib/github.ts`, `useLatestSha`, SHA poll deleted; no runtime
      data-host reference remains; review opt-in GitHub links preserved
- [ ] queryClient retry policy updated; 9 routes render unchanged with the fail-visible notice
- [ ] **Full drop-and-rebuild** across all serving tiers byte-equal; cross-tier fingerprint mismatch
      surfaced; tests for this phase; **PR 5 opened** with Phases 10–11

#### Acceptance Criteria
- [ ] `pnpm -C apps/multibrowser test` green; guard finds no runtime-data-host reference in `src`
- [ ] Build and tests passing

#### Test Plan
Unit: corpus fetchers → API; retry analogue; runtime-host guard (allows reviewReport links).
Integration: corpus over `fakeApi`; full drop-and-rebuild. Manual: full browse, API-only backend.

---

## DEFERRED — review coordination (last PR)

### Phase 12: DEFERRED — review assignment machinery

**Dependencies**: Phase 4 (submission), Phase 2 (schema/auth)

#### Objective
Add **assignment** with defined status transitions (assigned → in-progress → submitted) and an explicit
"complete" definition. (Deferred from the bare-minimum slice.)

#### Files to Create / Modify
- `apps/api/src/schema/review.ts` (assignments table; migration), `src/routes/review.ts` (assignment
  CRUD + transitions), route tests
- `apps/multibrowser/src/` assignment view components + tests

#### Deliverables
- [ ] Assignment lifecycle with enforced transitions + a "complete" definition; tests for this phase

#### Acceptance Criteria
- [ ] Transition state machine enforced; assignment reflects reviewer progress
- [ ] Build and tests passing

#### Test Plan
Unit: transition state machine. Integration: assignment lifecycle end-to-end.

---

### Phase 13: DEFERRED — review aggregation + coordinator dashboards — opens PR 6

**Dependencies**: Phase 12

#### Objective
Add **aggregation / dashboard** views (per-tradition completion, coordinator aggregates) and ship the
review coordination features. **Opens PR 6.**

#### Files to Create / Modify
- `apps/api/src/routes/review.ts` (aggregation endpoints; coordinator-scoped), route tests
- `apps/multibrowser/src/` review dashboard/aggregation components + tests

#### Deliverables
- [ ] Aggregation/dashboard reflects submitted reviews; coordinator sees aggregates without authoring
      another's review; tests for this phase; **PR 6 opened** with Phases 12–13

#### Acceptance Criteria
- [ ] `pnpm -C apps/multibrowser test` + `pnpm -C apps/api test` green; aggregation correctness test passes
- [ ] Build and tests passing

#### Test Plan
Unit: aggregation math; coordinator scoping. Integration: submit → aggregation view. Manual: dashboard
on deployed SPA.

## Risks and Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Ben's #85 sign-off delays Phase 2 (schema is gated on it) | Medium | Medium | Phase 1 (scaffold) has no schema dependency and proceeds meanwhile; escalate the sign-off early. |
| Cross-site cookie/CORS misconfig between separate Railway origins | Medium | High | `SameSite=None; Secure` + explicit allowed-origin (not wildcard) + credentialed requests; tested in Phase 1/2. |
| Invite-code gate is too weak / unwanted | Low | Low | It is one shared env var, flagged for Waleed's veto; trivially removable. |
| Losing authoritative review data (not rebuildable from git) | Low | Medium | Railway managed-Postgres built-in backups (test-tool scale; no custom restore tooling per the addendum). |
| Deferred serving phases drift from these decisions before they run | Medium | Medium | Decisions retained verbatim in Phases 5–11; iter-1 review fixes preserved. |
| Deleting `github.ts` breaks unlisted dependents (Phase 11) | Medium | High | Phase 11 lists all: `rateLimit.ts`, `queryClient.ts`, `test/fakeRepo.ts`, github test files, 9 `useLatestSha` sites incl. `RootLayout`. |
| Unsafe immutable caching on stable URLs (serving tiers) | Medium | High | Fingerprint-qualified content URLs + `immutable`; `/api/version` `no-store` (Phase 5). |
| Multi-PR-per-project friction with porch's gate model | Medium | Medium | Sequential-PR recipe + `porch done --pr/--merged`; confirm the `pr`-gate × multi-PR mechanics with the architect before Phase 2 opens PR 1. |
| Cost overrun once serving tiers land | Medium | Medium | Review-only envelope now; re-estimate storage/egress before PR 3 (raw shards, retention). |

## Documentation Updates

- `apps/api/README.md` — service, DB access, migration discipline (`drizzle-kit generate` → review →
  apply; never `db:push`), auth (email+password, invite-code, sessions, CSRF), a one-line
  Railway-managed-backups note, CORS/cookie topology. Serving-tier docs (ingest, version, content-URL)
  added when Phase 5+ lands.
- `results/README.md`, `results-raw/README.md`, `traditions/README.md` — updated as those tiers cut
  over (Phases 7, 9, 11).
- `codev/resources/arch-critical.md` / `lessons-critical.md` — serving-layer fact + retire the two raw
  dual-source lessons when Phase 9 lands (via MAINTAIN).
- `apps/multibrowser/.env.example` — `VITE_API_BASE` (review client Phase 3; replaces GitHub knobs by Phase 11).
