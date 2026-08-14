# Plan: Multibrowser data platform — Postgres serving layer for corpus, results, raw, and review tiers

**Specification**: [codev/specs/92-multibrowser-data-platform-pos.md](../specs/92-multibrowser-data-platform-pos.md)

## Executive Summary

The spec's chosen approach (Approach 1) is a **Postgres serving layer + a thin TypeScript API** (new
`apps/api`) behind the SPA's existing `lib/queries.ts` hook seam, with a **Python `analysis ingest`**
loading committed exporter outputs (and, for corpus, `load_corpus`) into a **Drizzle-owned schema**,
guarded by a schema-drift contract test. Git stays the source of truth; the serving tiers are a
rebuildable cache; the operational review store is a distinct authoritative data class.

This plan sequences the work as **four tier-sliced PRs** (the architect's explicit call —
`results → raw → corpus → review`), each a shippable integration, decomposed into **nine phases**
(atomic commits). The tier order is lowest-risk-first: prove ingest/serve/reconcile on the score
tier (which already carries the paper-reconciliation guard), spend the proven pattern retiring the
Spec 51 raw dual-source workaround, then move the highest-traffic corpus tier (which finally deletes
`lib/github.ts` and reaches the **zero-runtime-GitHub-reads** end state), then add the read-write
review slice last.

**Plan-level decisions settled here** (spec Open Questions):
- **API framework: Hono** on the Node runtime (thin, TS-native, first-class with Drizzle +
  `node-postgres`); Fastify is the fallback if middleware needs outgrow Hono. *(OQ 2)*
- **Freshness signal: a single `GET /api/version` endpoint** returning per-tier
  `{runId?, commitSha, fingerprint, ingestedAt}`; the SPA polls it, replacing the GitHub commit-SHA
  poll, and per-tier query keys carry the fingerprint (already the raw-tier pattern). *(OQ 1)*
- **Table-level Drizzle schema for all serving tiers is the first deliverable** (architect note):
  Phase 1 defines and migrates the corpus/results/raw serving tables + provenance in one reviewed
  migration. **Review-tier tables are a later migration (Phase 8), settled with Ben (@benolio)
  first.**
- **Raw retention N = 2** in the DB (mirrors Spec 51's committed-tier retention); the sizing lever
  for the cost ceiling. *(OQ 4)*
- **Review auth first slice: magic-link only**; GitHub OAuth is a deferred follow-up (keeps the
  review PR's scope/cost bounded). *(OQ 6)*
- **Magic-link email transport is chosen with Ben/architect before the review PR and must NOT
  collide with the global `resend`-CLI rule** — the default is a dedicated transactional provider
  (e.g. Postmark/SES), never direct `api.resend.com` calls. *(spec Constraint)*
- **Read-endpoint caching: fingerprint-keyed `ETag` + immutable `Cache-Control`** on corpus/score/raw
  responses; public read, abuse-bounded. *(OQ 7)*

**Pre-always-on gate (not a phase):** before the API + Postgres run always-on, the monthly cost
envelope (compute + DB storage at N=2 + egress) is confirmed with the architect **against actuals**,
not estimates (spec Constraint; project budget-overshoot history).

## Phases (Machine Readable)

<!-- REQUIRED: porch parses this JSON to track phase progress. Keep in sync. -->

```json
{
  "phases": [
    {"id": "phase_1", "title": "Serving API service + Drizzle schema foundation"},
    {"id": "phase_2", "title": "Results tier ingest"},
    {"id": "phase_3", "title": "Results API + SPA swap (PR 1)"},
    {"id": "phase_4", "title": "Raw tier ingest"},
    {"id": "phase_5", "title": "Raw API + SPA swap, retire baked bundle (PR 2)"},
    {"id": "phase_6", "title": "Corpus tier ingest"},
    {"id": "phase_7", "title": "Corpus API + SPA swap, delete github.ts — zero GitHub reads (PR 3)"},
    {"id": "phase_8", "title": "Review schema + auth (settled with Ben)"},
    {"id": "phase_9", "title": "Review intake, assignment + aggregation, SPA swap (PR 4)"}
  ]
}
```

**PR boundaries**: Phase 3 opens/ships PR 1 (results); Phase 5 → PR 2 (raw); Phase 7 → PR 3
(corpus); Phase 9 → PR 4 (review). Each PR branches from the integration branch per the sequential-PR
recipe (`git fetch origin main && git checkout -b <next-branch> origin/main`), recorded with
`porch done 92 --pr <N> --branch <name>` and `--merged <N>`.

## Phase Breakdown

### Phase 1: Serving API service + Drizzle schema foundation

**Dependencies**: None

#### Objective
Stand up the new `apps/api` service (Hono + Drizzle + `node-postgres`) with the **table-level Drizzle
schema for all serving tiers** and its first reviewed migration — the architect's first deliverable —
plus health/version endpoints, the schema-contract snapshot the Python ingest will assert against,
Railway wiring, and test-dispatcher registration. No tier is served yet; this is the foundation the
next phases build on.

#### Files to Create / Modify
- `apps/api/package.json`, `apps/api/tsconfig.json`, `apps/api/drizzle.config.ts`
- `apps/api/src/schema/` — Drizzle table defs: `runs.ts` (run + provenance: run_id, tier, commit_sha,
  source_fingerprint, content_fingerprint?, ingested_at), `corpus.ts`, `results.ts`, `raw.ts`
  (raw shard rows with `bytea` gz + content_fingerprint). **No review tables yet.**
- `apps/api/drizzle/0000_*.sql` — the generated + reviewed first migration
- `apps/api/src/server.ts`, `apps/api/src/routes/health.ts`, `apps/api/src/routes/version.ts`
  (`/api/version` returns per-tier provenance; empty/absent tiers report null)
- `apps/api/src/db.ts` (pool), `apps/api/scripts/schema-contract.ts` (emits
  `apps/api/src/schema/contract.snapshot.json` — the language-neutral column descriptor)
- `apps/api/railway.json`, `apps/api/.env.example`, `apps/api/README.md`
- `.codev/checks/test.sh` — add the `apps/api` suite line to the registry
- `apps/api/src/**/*.test.ts` — schema-contract snapshot test, health/version route tests

#### Deliverables
- [ ] `apps/api` builds and serves `/api/health` + `/api/version` locally against a Postgres pool
- [ ] Drizzle schema covers all serving tiers at table level; migration is **generated then reviewed**
      (no `db:push`); `contract.snapshot.json` is emitted from the schema
- [ ] Railway service + managed Postgres provisioned; env-based `DATABASE_URL`; SPA stays secret-free
- [ ] `.codev/checks/test.sh` runs the api suite only when `apps/api` is touched
- [ ] Tests for this phase

#### Acceptance Criteria
- [ ] `pnpm -C apps/api build && pnpm -C apps/api test` green; migration SQL present and reviewed
- [ ] `/api/version` returns a well-formed per-tier provenance envelope (all-null before any ingest)
- [ ] Build and tests passing

#### Test Plan
Unit: schema-contract snapshot matches the Drizzle schema; version envelope shape. Integration: server
boots against a throwaway Postgres (migration applies cleanly). Manual: `railway` service reachable.

---

### Phase 2: Results tier ingest

**Dependencies**: Phase 1

#### Objective
Add `analysis ingest` (Python, Typer subcommand) for the **score tier**: load a committed
`results/<run-id>/` export into Postgres, stamped with commit SHA + source fingerprint, **idempotent**,
**transactional**, and **per-tier independent**. Prove DB values equal the exporter shard values.

#### Files to Create / Modify
- `workflows/analysis/analysis/ingest.py` (new: DB writer via `psycopg`, run/results loaders reusing
  `export_results` output readers), `analysis/cli.py` (register `ingest` subcommand)
- `workflows/analysis/pyproject.toml` (add `psycopg` dep), `analysis/db_contract.py` (load + assert
  `apps/api/src/schema/contract.snapshot.json`)
- `workflows/analysis/tests/test_ingest_results.py`, `tests/test_schema_contract.py`

#### Deliverables
- [ ] `analysis ingest <run-id> --tier results` loads `results/<run-id>/` → DB; re-run with unchanged
      input is a no-op (fingerprint match); changed input replaces the run's rows in one transaction
- [ ] Stamped fingerprint equals the committed `manifest.json` fingerprint
- [ ] Schema-drift contract test fails if ingest's required columns diverge from `contract.snapshot.json`
- [ ] Round-trip test: DB-served score values equal exporter shard values
- [ ] Tests for this phase

#### Acceptance Criteria
- [ ] Idempotency, transactional-replace, and round-trip tests pass under `uv --project workflows/analysis run pytest`
- [ ] Ingest touches only the results tier (no assumption that raw/corpus are present)
- [ ] Build and tests passing

#### Test Plan
Unit: idempotency (double-ingest = no change), fingerprint equality, transactional replace, contract
drift caught. Integration: ingest a fixture `results/<run-id>/` into a throwaway DB, assert row values.

---

### Phase 3: Results API + SPA swap (PR 1)

**Dependencies**: Phase 2

#### Objective
Serve the score tier from the API and repoint the SPA's results fetchers to it — the first end-to-end
tier — holding the paper-reconciliation guard and introducing the version-signal + fail-visible notice.
**Opens PR 1.**

#### Files to Create / Modify
- `apps/api/src/routes/results.ts` (runs list, manifest, shard; fingerprint-keyed ETag + immutable
  cache), route tests
- `apps/multibrowser/src/lib/api.ts` (new fetch boundary → API base URL from `VITE_API_BASE`),
  `lib/queries.ts` (results loaders `loadResultsRuns/Run/Shard` + `useLatestSha`→version-signal for
  this tier), `lib/constants.ts`, `.env.example`
- `apps/multibrowser/src/components/` — fail-visible notice wiring for the results routes (no redesign)
- Reconciliation guard test updated to run against API-served numbers

#### Deliverables
- [ ] `/results` in the SPA reads from the API; no `api.github.com`/`raw` calls for the score tier
- [ ] Leaderboard mean-of-means reconciles with the paper (guard green against API data)
- [ ] Version endpoint drives results freshness; API-down shows a fail-visible notice (no GitHub fallback)
- [ ] Tests for this phase; **PR 1 opened** with Phases 1–3
- [ ] Tests for this phase

#### Acceptance Criteria
- [ ] `pnpm -C apps/multibrowser test` green with the API mock injected via `fetchImpl`
- [ ] Reconciliation guard passes; results routes render unchanged in layout
- [ ] Build and tests passing

#### Test Plan
Unit: results fetchers hit API endpoints (mocked); version-keyed cache. Integration: SPA results route
tests over the API mock. Manual: deployed SPA `/results` against the live API.

---

### Phase 4: Raw tier ingest

**Dependencies**: Phase 1 (schema), Phase 2 (ingest scaffolding)

#### Objective
Extend `analysis ingest` to the **raw tier**: store gz shards as `bytea` keyed by (run, tradition,
scenario), stamped with the content fingerprint, size-ceiling-enforced, and supporting **raw-only runs**
(the Spec 54 AFB dataset — no score tier).

#### Files to Create / Modify
- `analysis/ingest.py` (raw-tier path reusing `export_raw`/`raw_writer` readers; gz bytes preserved
  verbatim), `analysis/cli.py` (`--tier raw`, and a default that ingests whichever tiers a run has)
- `apps/api/src/schema/raw.ts` already exists (Phase 1) — confirm shape suffices
- `workflows/analysis/tests/test_ingest_raw.py` (incl. an AFB raw-only fixture)

#### Deliverables
- [ ] `analysis ingest <run-id> --tier raw` loads gz shards → `bytea`; content fingerprint stamped;
      per-shard ≤1 MB / per-run ≤200 MB ceilings enforced before any write
- [ ] Raw-only run (AFB, no `results/`) ingests with **no cross-tier mismatch error**
- [ ] Cross-tier fingerprint equality asserted only when both score + raw tiers exist
- [ ] Idempotent + transactional; tests for this phase

#### Acceptance Criteria
- [ ] Raw round-trip: stored gz bytes decode to the exporter's transcripts+verdicts, byte-identical
- [ ] AFB raw-only fixture ingests cleanly; size-ceiling breach aborts before writing
- [ ] Build and tests passing

#### Test Plan
Unit: gz byte preservation, ceiling enforcement, raw-only path, cross-tier gating. Integration: ingest
a fixture `results-raw/<run-id>/` + the AFB fixture into a throwaway DB.

---

### Phase 5: Raw API + SPA swap, retire baked bundle (PR 2)

**Dependencies**: Phase 4, Phase 3 (`lib/api.ts`, version-signal)

#### Objective
Serve raw shards from the API and **delete the entire Spec 51 dual-source workaround**. `/raw/<runId>`
(including AFB) renders from the API. **Opens PR 2.**

#### Files to Create / Modify
- `apps/api/src/routes/raw.ts` (catalog + shard endpoints; `content-encoding: gzip`;
  fingerprint-keyed ETag/immutable cache), route tests
- `apps/multibrowser/src/lib/rawSource.ts` (new `ApiRawSource`; remove `BakedRawSource`,
  `GitHubRawSource`, `resolveRawSource`, HTML-content-type sniffing), `lib/queries.ts` (raw loaders →
  API), `lib/constants.ts` (drop `RAW_PERSIST_EXCLUDED` baked bits as appropriate)
- **Delete**: `apps/multibrowser/scripts/bake-and-deploy.sh`, `apps/multibrowser/.railwayignore`
- `apps/multibrowser/src/deploy.test.ts` (drop baked-bundle assertions; assert no bake path exists)

#### Deliverables
- [ ] Raw viewer + `/raw/<runId>` (AFB) read from the API; dual-source resolver and baked bundle gone
- [ ] `railway up --no-gitignore` no longer referenced anywhere; no HTML-content-type sniffing remains
- [ ] The two Spec 51 raw-dual-source `lessons-critical` entries are removed/retired (via MAINTAIN)
- [ ] Tests for this phase; **PR 2 opened** with Phases 4–5

#### Acceptance Criteria
- [ ] `pnpm -C apps/multibrowser test` green; raw routes render transcripts+verdicts over the API mock
- [ ] `grep` shows no `bake-and-deploy`, `.railwayignore`, `no-gitignore`, or `isHtmlResponse` residue
- [ ] Build and tests passing

#### Test Plan
Unit: `ApiRawSource` catalog/shard fetch + gz decode; ETag behavior. Integration: raw + AFB route tests
over the API mock. Manual: deployed `/raw/<runId>` for both an MB run and the AFB run.

---

### Phase 6: Corpus tier ingest

**Dependencies**: Phase 1 (schema)

#### Objective
Ingest the **corpus** (traditions + scenarios + prose) into Postgres by reusing
`analysis/loaders.py::load_corpus`, with a **`traditions/`-tree content-hash** as its provenance (the
corpus has no exporter manifest or judgment fingerprint).

#### Files to Create / Modify
- `analysis/ingest.py` (corpus path via `load_corpus`; compute a stable content hash over the
  `traditions/` tree at the ingest commit), `analysis/cli.py` (`--tier corpus`)
- `workflows/analysis/tests/test_ingest_corpus.py`

#### Deliverables
- [ ] `analysis ingest --tier corpus` loads traditions/scenarios/prose → DB with a content-hash stamp
- [ ] Re-ingest at the same tree is a no-op; a changed tradition file changes the hash
- [ ] Idempotent + transactional; tests for this phase

#### Acceptance Criteria
- [ ] Corpus round-trip: DB-served tradition/scenario/prose equals the files `load_corpus` reads
- [ ] Content-hash provenance is deterministic and change-sensitive
- [ ] Build and tests passing

#### Test Plan
Unit: content-hash determinism + sensitivity, idempotency. Integration: ingest the real `traditions/`
into a throwaway DB, assert a sampled tradition/scenario round-trips.

---

### Phase 7: Corpus API + SPA swap, delete github.ts — zero GitHub reads (PR 3)

**Dependencies**: Phase 6, Phase 5 (`lib/api.ts` fully in place)

#### Objective
Serve the corpus from the API, repoint the last SPA fetchers, and **delete `lib/github.ts` and
`useLatestSha` entirely** — reaching the spec's **zero-runtime-GitHub-reads** end state. **Opens PR 3.**

#### Files to Create / Modify
- `apps/api/src/routes/corpus.ts` (traditions list, tradition, scenario, scenario-meta, guidance;
  fingerprint/version-keyed cache), route tests
- `apps/multibrowser/src/lib/queries.ts` (corpus loaders → API; remove SHA-pinning plumbing),
  **delete `apps/multibrowser/src/lib/github.ts`**
- `apps/multibrowser/src/components/RateLimitBanner.tsx` → replaced by the API fail-visible notice
  component; update the **8 route pages** that render it and call `useLatestSha`
- `apps/multibrowser/src/deploy.test.ts` (assert no GitHub host string is referenced anywhere in `src`)

#### Deliverables
- [ ] All corpus browsing reads from the API; `lib/github.ts` and `useLatestSha` are deleted
- [ ] Freshness comes solely from `/api/version`; no `api.github.com`/`raw.githubusercontent.com`
      reference remains in the SPA
- [ ] The 8 routes render unchanged in layout with the fail-visible notice
- [ ] Tests for this phase; **PR 3 opened** with Phases 6–7

#### Acceptance Criteria
- [ ] `pnpm -C apps/multibrowser test` green; a repo grep finds no GitHub-host runtime reference in `src`
- [ ] Build and tests passing

#### Test Plan
Unit: corpus fetchers → API (mocked); version signal drives all tiers. Integration: corpus route tests
over the API mock; a guard test asserting zero GitHub-host references. Manual: full browse of a
deployed SPA with the API as the only backend.

---

### Phase 8: Review schema + auth (settled with Ben)

**Dependencies**: Phase 1 (service), **and coordination sign-off from Ben (@benolio) on the review
data model before this phase's migration is written**

#### Objective
Add the **operational review store** and authentication: a second reviewed migration for
reviewers/assignments/reviews/submissions, magic-link auth + revocable sessions, and server-side
per-reviewer authorization. Private by default; this is the first read-write, PII-bearing slice.
**Opens PR 4.**

#### Files to Create / Modify
- `apps/api/src/schema/review.ts` (reviewers, assignments, reviews (versioned drafts), submissions
  (immutable snapshots)), `apps/api/drizzle/0001_*.sql` (generated + reviewed)
- `apps/api/src/auth/` (magic-link issue/verify — single-use, expiring; httpOnly revocable sessions;
  CSRF; email-enumeration + rate-limit bounds; validated redirects), `apps/api/src/routes/auth.ts`
- `apps/api/src/mail/` (transactional email transport — **chosen with Ben/architect, not colliding
  with the `resend` CLI rule; no direct `api.resend.com`**)
- `apps/api/src/**/*.test.ts` (auth, session, isolation tests)

#### Deliverables
- [ ] Review tables migrated (generated + reviewed; no `db:push`); operational store is a distinct
      data class with backup/restore + retention documented
- [ ] Magic-link login works end-to-end; tokens single-use + expiring; sessions revocable
- [ ] Server-side authz isolates each reviewer's records; a coordinator role reads aggregates only
- [ ] Tests for this phase

#### Acceptance Criteria
- [ ] Auth happy path + expired/reused-token rejection + reviewer-isolation tests pass
- [ ] Email transport does not route through the `resend` CLI's guarded broadcast path
- [ ] Build and tests passing

#### Test Plan
Unit: token single-use/expiry, session revocation, CSRF, redirect validation, authz isolation.
Integration: full login → session → private-endpoint access; cross-reviewer access denied.

---

### Phase 9: Review intake, assignment + aggregation, SPA swap (PR 4)

**Dependencies**: Phase 8

#### Objective
Swap the review UI's persistence from `localStorage` to the API behind Spec 83's zod-tolerant loader,
add private submission + assignment + aggregation views, and ship the review slice. **Ships PR 4.**

#### Files to Create / Modify
- `apps/api/src/routes/review.ts` (draft save/load, submit (immutable), assignments, aggregation),
  route tests
- `apps/multibrowser/src/lib/review.ts` (persistence seam → API behind the existing tolerant loader —
  "the submit panel is the only seam to replace"), `lib/reviewReport.ts` (private submission path;
  publish-to-issue becomes explicit opt-in)
- Review route components: resumable cross-device state; assignment + aggregation/dashboard views
- `apps/multibrowser/src/**/*.test.ts` (persistence swap, resumability, immutable submission)

#### Deliverables
- [ ] Review intake persists to the API; resumable across devices for the authenticated reviewer
- [ ] Submissions are private by default (opt-in publish), immutable once submitted
- [ ] Assignment + aggregation views with defined status transitions and a "complete" definition
- [ ] Tests for this phase; **PR 4 opened** with Phases 8–9

#### Acceptance Criteria
- [ ] `pnpm -C apps/multibrowser test` green; the zod-tolerant loader still degrades corrupt subfields
- [ ] Reviewer A cannot see reviewer B's drafts/submissions through the UI
- [ ] Build and tests passing

#### Test Plan
Unit: persistence-seam swap, tolerant load, immutable-submission guard. Integration: two-device resume;
private submit; assignment/aggregation reflect submitted reviews. Manual: full review of a tradition.

## Risks and Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Multi-PR-per-project friction with porch's gate/phase model | Medium | Medium | Follow the sequential-PR recipe (branch off integration, `porch done --pr/--merged`); raise with the architect early if the `pr` gate assumes a single PR, before Phase 3 opens PR 1. |
| Schema-drift between Drizzle (TS) and Python ingest | Medium | High | `contract.snapshot.json` emitted from Drizzle, asserted by a Python contract test in CI (Phase 1–2). |
| Deleting `github.ts` breaks the 8 routes at once (Phase 7) | Medium | High | Land the fail-visible notice + version-signal per tier in earlier phases so Phase 7 only removes the last references; guard test for zero GitHub-host strings. |
| Raw `bytea` DB size / cost at N runs | Medium | Medium | Retention N=2; enforce Spec 51 size ceilings at ingest; object-storage escape hatch stays documented; cost confirmed pre-always-on. |
| Review data model diverges from Ben's intent | Medium | Medium | Phase 8 migration is gated on Ben's sign-off; #85 stays the tracking issue. |
| Magic-link email path collides with the `resend`-CLI rule | Medium | Medium | Transport decided with Ben/architect; default a dedicated transactional provider; never direct `api.resend.com`. |
| Reconciliation drifts once numbers are DB-served | Low | High | Ingest loads pre-aggregated exporter outputs only; keep the committed-vs-paper guard, run it against API data (Phase 3). |
| Always-on cost overrun | Medium | Medium | Pre-always-on cost gate against actuals with the architect; retention N as the lever. |

## Documentation Updates

- `apps/api/README.md` — new: service, schema, migration discipline (`drizzle-kit generate` → review →
  apply; never `db:push`), ingest contract, version endpoint.
- `results/README.md`, `results-raw/README.md` — update serving description (API-served; retire the
  dual-source/baked-bundle section) as those tiers cut over (Phases 3, 5).
- `traditions/README.md` — note the corpus is served from the DB (Phase 7); git stays authoring/source.
- `codev/resources/arch-critical.md` — new serving-layer fact; `lessons-critical.md` — **remove the two
  raw dual-source lessons** once Phase 5 lands (via MAINTAIN, respecting the hot-tier cap).
- `apps/multibrowser/.env.example` — `VITE_API_BASE` replaces the GitHub `VITE_*` knobs by Phase 7.
