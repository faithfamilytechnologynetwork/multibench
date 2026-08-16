# Specification: Multibrowser data platform — Postgres serving layer for corpus, results, raw, and review tiers

<!--
SPEC vs PLAN BOUNDARY:
This spec defines WHAT and WHY. The plan defines HOW and WHEN.
Keep implementation phases, file paths, code, and "first we will… then we will…"
out of the spec — those belong in codev/plans/92-*.md.
-->

> **Amendment — 2026-08-15 (Waleed, final; supersedes the text below where they conflict).** After
> this spec was approved, Waleed re-cut the review slice. Two decisions in the body are **superseded**;
> the as-built follows this amendment, not the original wording:
> 1. **Auth is email + password (argon2id) — NOT magic-link, and there is no email transport or OAuth.**
>    Every "magic-link"/"OAuth"/"email provider" reference below (Success Criteria, Constraints,
>    Solution Approaches, Test Scenarios) is superseded by: email + password, an invite-code signup
>    gate (`REVIEW_INVITE_CODE`, fail-closed), server-side revocable sessions, httpOnly `Secure`
>    `SameSite=None` cookies, and double-submit CSRF. Scale is a ~5-user internal test tool, so
>    enumeration/rate-limit hardening and custom backup tooling are intentionally out of scope.
> 2. **Delivery is REVIEW-FIRST — not results-first.** The tier order `results → raw → corpus → review`
>    below is superseded: the **review backend ships first** (PR 1–2), the serving tiers
>    (results → raw → corpus) follow (PR 3–5), and review coordination is PR 6. See the plan for the
>    phase→PR mapping.
>
> The Problem Statement, the invariants (git as source of truth, aggregation stays in Python, explicit
> reviewed migrations / never `db:push`), and the serving-tier design are **unchanged**.

> **Amendment — 2026-08-16 (Waleed, final; scope).** Spec 92 is the **review system only**. The
> **serving-tier migration is OUT OF SCOPE and removed**: the corpus, score-results, and raw-transcript
> tiers keep reading git/GitHub at runtime (no Postgres serving layer, no ingest/drift/version/
> fingerprint-URL work, no `github.ts` deletion). Everything review-related is in scope — the shipped
> auth + draft-persistence + immutable-submission slice, the **one-origin / same-origin-proxy / private-API
> topology consolidation**, and the **parked** review-coordination tail (assignment + coordinator
> dashboards), which stays specified but dormant until Waleed calls for it. The removed serving-tier
> design is preserved as an appendix in the plan and tracked in
> **[GitHub issue #100](https://github.com/faithfamilytechnologynetwork/multibench/issues/100)** for
> possible future re-derivation. Where the title and body below say "corpus, results, raw" serving
> tiers, treat that as future/out-of-scope material (see #100).

## Problem Statement

`apps/multibrowser` serves every data tier — corpus, score results, raw transcripts — by reading
git/GitHub at runtime. That was the right minimal choice for browsing a small corpus with no
backend, but the model has accumulated real, load-bearing operational cost:

1. **Rate limits.** The unauthenticated GitHub data layer is 60 requests/hour per IP (often
   NAT-shared, with no safe way to hold a token in a static SPA). Compensating for the *absence of
   a server* forced SHA-pinned trees, `raw.githubusercontent.com` content fetches off the API
   budget, gentle commit-SHA polling, and serve-stale-plus-banner fallback logic.
2. **The raw tier broke the "just read the repo" model.** At ~126 MB/run, the raw transcripts do
   not fit runtime GitHub reads, so Spec 51 introduced a dual-source workaround: a baked bundle
   deployed with `railway up --no-gitignore`, HTML-content-type sniffing to detect a missing baked
   file behind the SPA history fallback, and a baked-first/GitHub-fallback resolver. Two standing
   `lessons-critical.md` entries exist *only* to keep that workaround working.
3. **New runs require a redeploy dance.** Publishing a run means commit + (for raw) a separate
   baked-bundle upload, instead of the data simply appearing once it lands.
4. **The review workspace cannot grow without a backend.** Spec 83's reviewer workspace deliberately
   uses `localStorage` + prefilled public GitHub issues. Issue #85 documents the three structural
   limits that stops at: reviewer PII in public issues (privacy), single-device unverified state
   (durability/identity), and no assignment/aggregation once reviewer count grows (coordination).

Who is affected: the whole team browsing the corpus and runs (rate-limit friction, redeploy
overhead), whoever publishes runs (the bake/deploy ceremony), and — most sharply — scholar
reviewers of religious-content judgments, who currently have no private, durable, coordinated place
to work.

**Direction (Waleed, 2026-08-13): multibrowser should serve almost everything from a database.**
The database is not the source of truth — git remains that. The DB is *how we serve* the corpus,
runs, and review layer: a rebuildable serving cache/index that retires the rate-limit and
dual-source complexity and unlocks the read-write review slice.

## Current State

`apps/multibrowser` is a pure client-side SPA (Vite + React 19 + TanStack Query/Router, Tailwind 4
+ HeroUI 3) deployed on Railway as a static site (`railway.json` NIXPACKS → `pnpm build` →
`serve -s dist`). There is **no backend service** anywhere under `apps/` today (only `multibrowser`
and the `tradition_validator` Python CLI). All runtime data is read live from GitHub, SHA-pinned,
through a clean three-layer data seam:

- **`lib/github.ts`** — the single GitHub fetch boundary. Four functions, each with an injectable
  `fetchImpl`: `latestSha()` (`GET /repos/{repo}/commits/{ref}`, on the API budget), `tree()`
  (`GET /git/trees/{sha}?recursive=1`, on budget, with a per-directory walk fallback on
  `truncated`), `raw()` and `rawBytes()` (`raw.githubusercontent.com/{repo}/{sha}/{path}`, off the
  API budget). Typed `RateLimitError` / `GitHubError` drive a fail-soft banner.
- **`lib/rawSource.ts`** — the raw-tier dual-source seam (Spec 51): a `RawDataSource` interface with
  `BakedRawSource` (same-origin `public/data-raw/`) and `GitHubRawSource`, a baked-first/
  GitHub-fallback `resolveRawSource()`, HTML-content-type sniffing, and gzip magic-byte decode. The
  deploy path is `scripts/bake-and-deploy.sh` + `.railwayignore` + `railway up --no-gitignore`.
- **`lib/queries.ts`** — the TanStack Query hooks the UI actually depends on (`useTraditions`,
  `useTradition`, `useScenario*`, `useResultsRuns/Run/Shard`, `useRawScenario`, `useRawCatalog`,
  `useScenarioRaw`, `useCorpusGuidance`, `useLatestSha`). **No component or route calls `fetch` or
  imports a *fetcher* from `github.ts`/`rawSource.ts`** — the UI consumes only these hooks for data.
  Two GitHub couplings do reach the UI, and matter for the cutover: all 8 route pages call
  `useLatestSha` (the commit-SHA poll) and render `<RateLimitBanner>`, and `components/RateLimitBanner.tsx`
  imports the `RateLimitError` *type* from `lib/github.ts`. Everything is keyed by the polled head SHA
  (`staleTime: Infinity`); a new SHA yields new keys and an automatic refetch.

The data these tiers read is produced by the canonical Python exporters in `workflows/analysis`
(Typer CLI, `python -m analysis`): `export` (Spec 49 score tier → `results/<run-id>/manifest.json`
+ `<tradition>.json`), `export-raw` (Spec 51 raw tier → `results-raw/<run-id>/manifest.json` +
`<tradition>/<scenario>.json.gz`), and `export-afb` (Spec 54 non-MultiBench catalog). Both score
and raw tiers stamp a shared **source fingerprint** (`analysis/fingerprint.py`: `sha256:` over the
sorted resolved-judgment lines); the raw tier additionally stamps a **content fingerprint** over the
shard byte stream. The corpus itself is not "exported" — it is the `traditions/*/` files, read by
`analysis/loaders.py::load_corpus`.

Limitations this produces, concretely: a lab full of reviewers behind one NAT can exhaust 60/hr in
minutes; a new raw run is invisible until someone re-runs `bake-and-deploy.sh`; the review workspace
can attribute nothing privately and aggregate nothing across reviewers.

## Desired State

Multibrowser serves the corpus, score results, and raw tiers — and a new read-write review layer —
from **Postgres on Railway behind a thin API service** (a new `apps/` member alongside
`multibrowser`). Git stays the source of truth; the DB is a rebuildable serving cache.

- **Read tiers move behind the existing hook seam.** The `lib/queries.ts` fetchers repoint from
  GitHub URLs to API endpoints; the `RawDataSource` gains an API-backed implementation. **There is no
  UI *redesign*** — components keep their layout and behavior — but the cutover does require bounded,
  mechanical route/component edits: `useLatestSha` is replaced by the API version signal, and
  `<RateLimitBanner>` (which depends on `lib/github.ts`) is replaced by the API fail-visible notice.
  The unauthenticated-GitHub machinery (rate-limit banner, SHA-pinned trees, `raw` fetches) is
  retired — the API has no per-IP budget.
- **The raw tier is served by the API** from the DB (or object storage), so the Spec 51
  baked-bundle / dual-source workaround — `.railwayignore`, `railway up --no-gitignore`,
  HTML-content-type sniffing, the baked-first resolver — is deleted, and its two `lessons-critical`
  entries with it.
- **An ingest command loads the tiers into Postgres**, fingerprint- and commit-SHA-stamped, and
  idempotent. Publishing a new run becomes: land the exporter output in git, run ingest — and it
  appears in the browser. No redeploy, no bake.
- **Two data classes with different guarantees.** (1) The **serving-cache tiers** (corpus, score,
  raw) are rebuildable from the repo at any time: dropping and re-ingesting from a commit reproduces
  byte-equal served payloads (same fingerprints). (2) The **operational review store** (reviewer
  identities, drafts, assignments, submissions) is *authoritative, not reconstructable from git* — it
  is the one place data is authored in the DB, so it needs backup/restore, retention, and deletion of
  its own (below). "Git stays the source of truth" applies to the serving tiers and to review
  *outcomes* that land in git (accepted revisions → PRs; `scholar_review` → `tradition.yaml`), **not**
  to in-flight operational review data.
- **The serving DB is rebuildable from the repo.** Aggregation stays in the canonical Python; ingest
  loads the *outputs* of the exporters (and, for corpus, reuses `load_corpus`) — the DB never
  becomes a second implementation of scoring conventions, so the leaderboard still reconciles with
  the paper by construction.
- **Every served payload carries its provenance** — the ingest's commit SHA + source fingerprint —
  and the SPA displays what it serves (the same discipline the results tiers already use).
- **The review slice becomes the first read-write layer** (folding in Issue #85): reviewer accounts
  (magic-link email, optionally GitHub OAuth), private-by-default intake, in-progress review state
  resumable across devices, and assignment + aggregation/dashboard views. Persistence swaps
  `localStorage` → API behind Spec 83's existing zod-tolerant loader; the review UI is otherwise
  unchanged. Reviewer identity/contact never lands in a public artifact unless explicitly published.

What stays the same: authoring, provenance, forkability, and the record of outcome all remain in
git. Accepted revisions still arrive as PRs; `scholar_review` status still lives in `tradition.yaml`.
No re-ranking, no new scoring semantics — this is a serving change.

## Success Criteria

- [ ] A Postgres instance and a thin API service run on Railway; in production the SPA reads the
      corpus, score, and raw tiers from the API. **End state: ZERO runtime GitHub reads** — no
      requests to `api.github.com` or `raw.githubusercontent.com` for any tier, and `lib/github.ts`
      plus the commit-SHA poll are removed (the SPA's freshness signal comes from an API version
      endpoint).
- [ ] Ingest loads the corpus, score, and raw tiers into Postgres, each run stamped with the ingest
      commit SHA + source fingerprint, and is **idempotent**: re-running unchanged inputs is a no-op
      and the stamped fingerprint equals the committed manifest's.
- [ ] **Each tier ingests independently.** A **raw-only run** with no `results/` score tier (e.g. the
      Spec 54 AFB dataset `results-raw/afb-20260808`) ingests and serves correctly, landing at
      `/raw/<runId>` — ingest never assumes score and raw arrive together. The **corpus** tier, which
      has no exporter manifest or judgment fingerprint, gets its own provenance (a content hash over
      the `traditions/` tree at the ingest commit). The cross-tier fingerprint-equality check applies
      **only when both score and raw tiers exist** for a run-id.
- [ ] Ingest **publishes a run transactionally** — a run becomes visible all-or-nothing, never as a
      half-ingested state the SPA can read.
- [ ] **Serving tiers are rebuildable from the repo**: dropping the serving DB and re-ingesting from a
      given commit reproduces byte-equal served payloads (fingerprints unchanged) — proven by a
      round-trip test. (This guarantee is scoped to the serving-cache tiers, **not** the operational
      review store.)
- [ ] The results leaderboard served from the API **reconciles with the paper** (the same
      mean-of-means guard as Spec 49/55), and an ingest round-trip test proves DB-served score values
      equal the exporter shard values.
- [ ] The raw tier is served by the API; the Spec 51 baked-bundle path is **removed**:
      `scripts/bake-and-deploy.sh`, `.railwayignore`, `railway up --no-gitignore`, the
      HTML-content-type sniffing, and the dual-source resolver no longer exist, and the raw viewer
      still renders transcripts + verdicts correctly.
- [ ] A newly landed run appears in the browser after **ingest alone** — no redeploy, no
      baked-bundle upload.
<!-- Amended 2026-08-15: auth is email+password (no magic-link/OAuth) — see the Amendment note at the top. -->
- [ ] **Review slice — function**: a reviewer authenticates (~~magic-link email; optionally GitHub
      OAuth~~ → **email + password**, per the 2026-08-15 amendment), resumes in-progress review state
      on a second device, and submits privately (not to a
      public issue by default); assignment and aggregation views exist with defined status
      transitions (assigned → in-progress → submitted) and an explicit definition of "complete."
- [ ] **Review slice — isolation & privacy**: server-side authorization enforces that a reviewer can
      read/write only their own drafts, assignments, and submissions (a coordinator/admin role may
      read aggregates); reviewer identity/contact never appears in a public artifact unless explicitly
      published; magic-link tokens are single-use and expire; sessions are revocable; the auth surface
      resists email-enumeration and open-redirect. PII has a stated retention + deletion path.
- [ ] **Operational review store durability**: the review store has backup/restore and its retention
      is defined; a submitted review is an immutable snapshot (drafts are mutable, submissions are
      not).
- [ ] **Read endpoints have a stated access posture** (public read is acceptable for the corpus/
      score/raw tiers) with abuse bounds and a caching strategy (e.g. ETag/immutable cache keyed by
      fingerprint) so the ~121 MB/run raw blobs don't become an unbounded egress/DoS surface.
- [ ] **Migrations are explicit**: schema changes are `drizzle-kit generate`-d SQL, reviewed, and
      applied deliberately; **no `db:push` against live data**. Drift between the Drizzle-owned
      schema and the ingest writer is caught by a contract test.
- [ ] Every served payload carries the ingest commit SHA + fingerprint, and the SPA displays it.
- [ ] **Git remains the source of truth**: authoring, provenance, the review trail, and forkability
      are unchanged; accepted revisions still arrive as PRs; `scholar_review` stays in
      `tradition.yaml`.
- [ ] Each read tier **fails visibly** when the API is unavailable — a notice, not a crash, and
      **not** a GitHub fallback (no dual-source paradigm is reintroduced).
- [ ] The corpus tier is served from the DB; each tier lands as its **own PR** (`results → raw →
      corpus → review`), each a shippable integration.

## Constraints

### Baked decisions (architect — from Issue #92, not relitigated)

These are the architect's fixed decisions. They are copied here as settled; a genuine problem with
one is raised via `afx send architect`, not overridden in Solution Approaches.

- **Git stays the source of truth.** The DB is a serving cache/index, rebuildable from the repo at
  any time. Every ingest stamps commit SHA + source fingerprint; the SPA displays what it serves.
- **Aggregation stays in the canonical Python** (`workflows/analysis`). Ingest loads the *outputs*
  of the canonical exporters. The DB never becomes a second implementation of scoring conventions —
  reconciliation with the paper holds by construction.
- **Migrations are explicit**: `drizzle-kit generate` → review SQL → apply. **Never `db:push`
  against live data.** (This also matches the standing global rule against `db:push`/`drizzle-kit
  push` on live tables.)
- **Shape**: Postgres on Railway + a thin API service as a new `apps/` member alongside
  `multibrowser`; an ingest command in the Python workflows (e.g. `analysis ingest <run-id>`)
  loading corpus, score, and raw tiers, fingerprint-stamped and idempotent; the SPA swap happens
  **behind the existing TanStack loaders** (fetchers move from GitHub URLs to API endpoints, UI
  unchanged); the raw tier is served by the API (DB or object storage) and the Spec 51 baked-bundle
  workaround retires.
- **The review slice rides this same service** as the first read-write layer: reviewer identity via
  magic-link/OAuth, private intake, resumable review state, assignment + aggregation views. Issue
  #85 stays the tracking issue; its design content is folded into this spec.
- **Out of scope**: moving authoring or the record-of-outcome off git (revisions still arrive as
  PRs; `scholar_review` stays in `tradition.yaml`); re-ranking or new scoring semantics (serving
  only).

### Architect resolutions (2026-08-14 — the four critical questions, now settled)

- **Raw-tier storage: Approach A — gz shards as `bytea` in Postgres.** Object storage is documented
  as the escape hatch to invoke only if retention growth demands it; it is not built now.
- **Ingest: Approach A — Python `analysis ingest`** writing parameterized SQL into the Drizzle-owned
  schema, guarded by a **schema-drift contract test in CI**.
- **Auth: magic-link primary + optional GitHub OAuth.** Whether OAuth ships in the *first* review
  slice is a plan-time call based on cost (the spec keeps both in scope).
  > **Superseded 2026-08-15 (Waleed, final):** auth is **email + password (argon2id), no magic-link,
  > no email transport, no OAuth**, with an invite-code signup gate. See the Amendment note at the top.
- **Corpus moves to the DB too.** Waleed's explicit direction is to serve almost everything from the
  DB; the **end state has ZERO runtime GitHub reads** — `lib/github.ts` and the commit-SHA poll are
  retired, not just the raw dual-source.
- **Cutover: a PR *per tier*, not one mega-PR.** Order is `results → raw → corpus → review`; each
  tier is a shippable integration (its own branch off the integration branch, its own PR). This
  overrides the default "plan phases = commits in one PR" for this project.
  > **Superseded 2026-08-15 (Waleed, final):** delivery is **review-first** — the review backend ships
  > first (PR 1–2), then the serving tiers `results → raw → corpus` (PR 3–5), then review coordination
  > (PR 6). PR-per-tier is retained; only the *order* changed. See the Amendment note at the top and the plan.
- **Fail-soft (end state): fail visibly with a notice if the API is down — no GitHub read
  fallback.** Do **not** rebuild a dual-source paradigm; a resilient fallback is exactly the scar
  this project retires.

### Technical constraints

- **Drizzle owns the schema and migrations** (the explicit-migration decision names `drizzle-kit`),
  which makes the API service TypeScript-native and aligned with the team frontend stack. Whatever
  writes ingest rows must target that Drizzle-owned schema without becoming a second schema
  authority.
- The SPA's isolation seam is real and must be respected: data fetching swaps at `lib/github.ts` /
  `lib/rawSource.ts` / the `lib/queries.ts` hooks. **No UI redesign**, but bounded route/component
  edits *are* required by the zero-GitHub-reads end state: all 8 route pages drop `useLatestSha` (→ the
  API version signal) and `<RateLimitBanner>` is replaced by the API fail-visible notice
  (`RateLimitBanner.tsx` type-imports from `github.ts`, which is being deleted). Tests inject
  `fetchImpl`, so an API mock rides the same harness.
- **Review-slice security posture** (stated at spec altitude; mechanics are plan detail): server-side
  authorization isolates each reviewer's records; magic-link tokens are single-use + expiring; sessions
  use secure httpOnly cookies and are revocable; the auth flow has CSRF protection, email-enumeration
  and rate-limit bounds, and validated redirects; PII is minimized, private-by-default, with a stated
  retention/deletion path. Publish-to-issue is explicit opt-in.
- **Email provider for magic-link must be chosen deliberately.** The standing global rule routes all
  Resend operations through the `resend` CLI wrapper (with an explicit-permission flag) — a
  transactional magic-link path sending directly from a Node service would collide with that. The
  provider/transport decision is made at plan time so it does not bypass that rule.
- **Read-endpoint access posture**: the corpus/score/raw read endpoints may be public (no per-IP
  budget is the whole point), but must carry abuse bounds and a fingerprint-keyed caching strategy
  (ETag / immutable cache) so the ~121 MB/run raw blobs are not an unbounded egress/DoS surface.
- **Per-tier rollback**: because there is no GitHub fallback, each tier's PR must be revertable on its
  own — reverting the SPA swap restores the prior tier's serving path, and a failed tier does not
  strand the others. Tiers ship in the approved order so a later tier never hard-depends on an
  un-shipped one.
- **Provenance discipline is preserved**: the shared source fingerprint (`analysis/fingerprint.py`)
  and, for raw, the content fingerprint remain the coherence keys; the API serves them and the SPA
  displays them. The SPA's freshness signal (today: polling the GitHub commit SHA) must be replaced
  by an API-provided snapshot/version signal.
- **Reconciliation guard stays**: the committed-artifact-vs-paper test (Spec 49/55) must continue to
  pass against API-served numbers.
- **Multi-language repo + per-builder test dispatcher**: the new API app registers its suite in
  `.codev/checks/test.sh` (one line per app); per-phase consult is `["codex","claude"]`.
- **Deployment is Railway**; the standing Tailwind-4/Nixpacks Node-20 constraint applies to any
  Node service. Railway Postgres is a managed instance; secrets live in Railway env, never in the
  static SPA (the SPA remains secret-free — the API holds any credentials).
- **Cost has a ceiling.** A new always-on API + managed Postgres + raw-blob egress is recurring
  spend; given this project's budget-overshoot history, the monthly cost envelope (compute + DB
  storage-at-retention + egress) is confirmed with the architect against actuals — not rolling
  estimates — before the service goes always-on. Raw retention N is the main sizing lever.
- **Privacy**: reviewer PII (name, contact, standing) is stored private-by-default; publish-to-issue
  is an explicit opt-in, not the default path.

## Assumptions

- Railway can host a small always-on Node API service + a managed Postgres alongside the existing
  static SPA within acceptable cost; a thin service (no heavy compute — aggregation stays in the
  offline Python) keeps this modest.
- The exporter outputs (`results/`, `results-raw/`) remain the ingest inputs and keep their current
  file layout and fingerprints; corpus ingest reads `traditions/*/` via `load_corpus`.
- 126 MB/run of gz raw shards × a small retention window fits comfortably in Postgres (`bytea`/TOAST)
  or a Railway volume; the raw tier is served pre-gzipped with `content-encoding: gzip`.
- Ben (@benolio) owns the review seam; the review data model is settled in coordination with him.
  #85's sketch (reviewers / assignments / reviews / submissions, versioned, immutable submission
  snapshots) is the starting point.
- The CHI timing note in #85 (target the Nov 5 – Dec 3 revise-and-resubmit window for the review
  slice) is a scheduling preference for that slice; the serving-layer tiers (corpus/results/raw) run
  in this project's parallel lane now.

## Solution Approaches

### Overall serving architecture

**Approach 1 — Postgres serving layer + thin API behind the existing seam (recommended; the
architect's direction).** Stand up Railway Postgres + a TypeScript API. Ingest (Python) loads
exporter outputs + corpus into the DB, fingerprint-stamped. The SPA's `lib/queries.ts` fetchers and
a new `ApiRawSource` repoint to API endpoints; the UI is not redesigned (only the bounded
`useLatestSha`→version-signal and `RateLimitBanner`→notice swaps). The raw dual-source workaround
is deleted.
*Pros*: retires rate limits, the bake/deploy dance, and the dual-source complexity in one move;
unlocks the read-write review slice on the same service; DB rebuildable from git preserves the
source-of-truth invariant. *Cons*: introduces an always-on service + DB to operate and secure; two
languages touch one schema (mitigated below). *Risk*: medium, bounded by tier-by-tier cutover behind
a proven seam.

**Approach 2 — keep git-serving for read tiers, add a backend only for review (rejected baseline).**
Leave corpus/results/raw reading GitHub; build Postgres+API only for #85.
*Pros*: smallest change; read tiers keep zero-backend simplicity. *Cons*: every operational scar in
the Problem Statement survives (rate limits, the raw dual-source, the redeploy dance); the SPA now
has *two* data paradigms; the "almost everything from a database" direction is not met. *Rejected*:
it fixes only the review limit and leaves the standing complexity that motivated this work.

### Raw-tier storage — **Decided: Approach A**

**Approach A — gz shards as `bytea` in Postgres (recommended).** One row per (run, tradition,
scenario) holding the exact gz bytes + the content fingerprint; the API serves them with
`content-encoding: gzip`. *Pros*: one backend, transactional with everything else, trivially
rebuildable, retires the baked bundle outright; ~126 MB/run × small retention is well within
Postgres/TOAST. *Cons*: large blobs bloat DB backups; retention must be tended. *Risk*: low.

**Approach B — object storage (Railway volume or S3-compatible), DB holds only the shard index +
fingerprints.** *Pros*: keeps the DB lean; scales to many large runs. *Cons*: a second store to keep
coherent, another credential, more failure modes; coherence between index and blobs must be
policed. *Risk*: medium. *Recommended as the escape hatch* if raw volume grows beyond a couple of
retained runs; start with A.

### Ingest ownership & schema authority — **Decided: Approach A**

**Approach A — Python `analysis ingest`, writing to the Drizzle-owned schema via parameterized SQL,
guarded by a schema-drift contract test (recommended).** Ingest lives next to the canonical
exporters and reuses `load_corpus` and the exporter output loaders; it writes rows with plain
`psycopg`, no Python ORM. A shared schema-contract fixture (columns/types the ingest depends on) is
asserted against the live Drizzle schema in CI, so a migration that moves a column fails loudly.
*Pros*: honors the issue's "ingest in the Python workflows"; single schema authority (Drizzle);
corpus ingest reuses existing Python loaders. *Cons*: Python must track schema shape out-of-band
(the contract test closes this).

**Approach B — TypeScript ingest reusing Drizzle types.** Ingest reads the exporter output files
(language-neutral) from Node and inserts via Drizzle. *Pros*: one language owns schema + writes.
*Cons*: splits ingest from the canonical Python exporters and from `load_corpus` (corpus has no file
"export" — it is the traditions tree); fights the issue's stated placement. *Considered, not
recommended.*

### Auth for the review slice — **Decided: Approach A** (OAuth-in-first-slice deferred to plan)

**Approach A — magic-link email primary, optional GitHub OAuth (recommended, matches #85).** Scholar
reviewers need private intake without GitHub-account friction; magic-link (signed, expiring token →
httpOnly session cookie) serves them, with OAuth as a convenience for GitHub-native reviewers.
*Pros*: inclusive of non-GitHub scholars; private by default. *Cons*: email delivery is a dependency
to operate. **Approach B — GitHub OAuth only.** Simpler, but re-imposes the account friction #85
exists to remove. *Recommended: A, with OAuth optional; confirm whether OAuth is in the first slice
or deferred.*

### Cutover order (the SPA's tiers)

Recommended sequence, lowest-risk-first, each a shippable slice behind the hook seam:

1. **Score results tier** — smallest dataset, already reconciled by construction, carries the
   paper-reconciliation guard; proves ingest + API + fingerprint-display end-to-end at low risk.
2. **Raw tier** — retires the Spec 51 baked-bundle/dual-source workaround (the biggest complexity
   win) and proves blob serving.
3. **Corpus tier** — the largest schema surface and primary browse path; reuses `load_corpus`.
4. **Review backend** — the read-write + auth slice (#85), riding the now-proven service.

Rationale: prove the ingest/serve/reconcile machinery on the tier that already has a correctness
guard, then spend the proven pattern on the highest-pain tier (raw), then the highest-traffic tier
(corpus), then the net-new read-write layer.

**Decided (architect, 2026-08-14):** this order is approved, and **each tier ships as its own PR** —
a separate branch off the integration branch, a shippable integration per tier — rather than
phase-commits in one PR. (Recorded in Constraints → Architect resolutions.)

## Open Questions

> The four originally-Critical questions (raw storage, ingest/schema authority, auth, corpus-in-DB)
> and two Important ones (cutover granularity, fail-soft posture) were **resolved by the architect
> on 2026-08-14** — see Constraints → *Architect resolutions*. What remains open:

**Important (shapes design):**

1. **Freshness/version signal**: with GitHub commit-SHA polling gone, how does the SPA learn a new
   run/ingest is available — poll an API `/version` (or per-tier snapshot) endpoint? What cadence?
   (Design in the plan.)
2. **API framework** (TypeScript is fixed by the Drizzle decision): Hono / Fastify / Express?
3. **Review data model + authz model** (reviewers / assignments / reviews / submissions; role model
   reviewer-vs-coordinator; versioning; immutable submission snapshots; status transitions;
   concurrent-edit/conflict handling) — **settled in coordination with Ben (@benolio), his seam,
   before the review-tier PR.** The security *posture* is fixed (Constraints); the schema is not.
4. **Raw retention N** in the DB — a sizing/cost lever (Spec 51 keeps last 2 committed run-ids;
   mirror that, or larger?). Sets DB size, backup time, and Railway spend; **promoted from
   nice-to-know** because it feeds the cost ceiling.
5. **Monthly cost ceiling** for the always-on API + Postgres + raw egress — a number confirmed with
   the architect against actuals before the service is always-on.
6. **Does OAuth ship in the first review slice, or magic-link only first?** Architect deferred this
   to plan time, decided on cost.
7. **Read-endpoint caching/egress strategy** for the raw blobs (ETag/immutable keyed by fingerprint;
   any CDN in front) — posture is fixed (Constraints), the mechanism is a plan choice.

**Nice-to-know (optimization):**

8. **Object-storage escape-hatch provider** if raw growth ever forces Approach B (Railway volume vs
   external S3).
9. Whether the exporters should *also* gain a direct-to-DB path later, or ingest of committed
   outputs stays the only ingress (keeps git-as-source-of-truth crisp — likely yes).

## Test Scenarios

- **Ingest idempotency**: ingesting a run twice with unchanged inputs produces no row changes and
  the stamped fingerprint equals the committed manifest's; changing an input replaces the run's rows
  transactionally and re-stamps.
- **Rebuild-from-scratch**: drop the serving DB, re-ingest at a fixed commit, and every API-served
  payload is byte-equal to before (fingerprints unchanged).
- **Reconciliation**: the API-served leaderboard's mean-of-means equals the paper figure (existing
  guard), and DB-served per-slice scores equal the exporter shard values (round-trip).
- **Raw round-trip**: gz shard bytes served by the API decode to the same transcripts + verdicts as
  the exporter produced; `content-encoding: gzip` is set; a size-ceiling breach is refused at ingest.
- **Raw-only run**: ingesting the Spec 54 AFB dataset (`results-raw/afb-20260808`, no score tier)
  succeeds, `/raw/afb-20260808` renders it, and the absence of a `results/` tier triggers **no**
  cross-tier mismatch error.
- **Corpus provenance**: corpus ingest computes and stamps a `traditions/`-tree content hash at the
  commit; re-ingest at the same commit is a no-op; a changed tradition file changes the hash.
- **Transactional publish**: a run interrupted mid-ingest is never visible to the SPA (all-or-nothing).
- **Read-endpoint caching**: a raw-blob response carries a fingerprint-keyed ETag/immutable cache
  header; a conditional re-request is served from cache, not re-egressed.
- **SPA seam swap**: with the API mock injected via `fetchImpl`, existing corpus/results/raw route
  tests pass unchanged; the only UI edits are the `useLatestSha`→version-signal and
  `RateLimitBanner`→fail-visible-notice swaps.
- **Auth**: magic-link happy path (request → email token → session); expired/invalid/reused token is
  rejected (single-use); optional OAuth path (if in scope); an unauthenticated request to a private
  review endpoint is refused; the flow resists email-enumeration and open-redirect.
- **Reviewer isolation**: reviewer B cannot read or write reviewer A's drafts/assignments/
  submissions; a coordinator role can read aggregates but not author another's review.
- **Immutable submissions**: a submitted review cannot be mutated; drafts can; the operational store
  restores cleanly from backup.
- **Private intake**: reviewer identity/contact is never present in any public artifact; publish-to-
  issue happens only on explicit opt-in.
- **Resumable state**: in-progress review saved on device A is resumed on device B for the same
  authenticated reviewer; the zod-tolerant loader still degrades a corrupt subfield to a default.
- **Assignment + aggregation**: per-tradition assignment and completion/aggregation views reflect
  submitted reviews.
- **Migration discipline**: a schema change produces reviewable generated SQL; the schema-drift
  contract test fails when ingest and schema disagree; no code path calls `db:push`.
- **Fail-visible**: with the API down, each read tier shows a notice (not a crash / blank) and does
  **not** silently fall back to GitHub — no dual-source path exists to engage.
- **Provenance display**: every served tier surfaces its ingest commit SHA + fingerprint in the UI;
  a fingerprint mismatch between tiers is surfaced.
- **Deploy hygiene**: a normal SPA build bundles no baked raw tier (the Spec 51 bake path is gone);
  the SPA build ships no server secret.

## Risks and Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Two writers, one schema (Python ingest vs Drizzle) drift silently | Medium | High | Single schema authority (Drizzle); a schema-drift contract test in CI; ingest via plain SQL against asserted columns. |
| Raw `bytea` bloats DB size/backups | Medium | Medium | Retention (keep last N runs); enforce Spec 51 size ceilings at ingest; object-storage escape hatch (Approach B) if growth demands. |
| Reviewer PII mishandled / leaks to public repo | Low | High | Private-by-default storage; publish-to-issue is explicit opt-in; minimal PII; managed-PG encryption at rest; magic-link token expiry; stated retention/deletion path. |
| Broken authz lets one reviewer read another's records | Low | High | Server-side per-reviewer isolation as a success criterion + test; roles (reviewer vs coordinator); reviewer-isolation test in the review-tier PR. |
| Operational review data lost (not rebuildable from git) | Low | High | Treated as a distinct authoritative data class with its own backup/restore + retention; immutable submission snapshots; only serving tiers are "rebuildable." |
| Loss/misuse of the magic-link email path (collides with the Resend-CLI rule) | Medium | Medium | Provider/transport decided deliberately at plan time so the transactional path does not bypass the `resend` CLI's explicit-permission rule. |
| Raw-blob read endpoint becomes an egress/DoS surface | Medium | Medium | Fingerprint-keyed ETag/immutable caching; abuse bounds on read endpoints; retention caps per-run size. |
| Cutover regresses SPA behavior | Medium | Medium | Tier-by-tier slices behind the hook seam; reuse `fetchImpl`-injected test harness with an API mock; per-tier revertable PRs; fail-visible notices. |
| Leaderboard numbers drift from the paper | Low | High | Ingest loads pre-aggregated exporter outputs only (no re-aggregation); keep the committed-vs-paper guard against API-served numbers. |
| New always-on service + DB cost/ops burden | Medium | Medium | Thin service (no heavy compute); single small managed Postgres; aggregation stays offline in Python; monthly cost ceiling confirmed with the architect against actuals before always-on (retention N is the sizing lever). |
| Losing the git source-of-truth invariant | Low | High | Ingest is one-way from committed artifacts; provide a full rebuild path; every payload stamped with commit SHA + fingerprint; DB never authors. |
| Review-seam design diverges from Ben's intent | Medium | Medium | Coordinate the data model with Ben (@benolio) before building; #85 stays the tracking issue. |
| API outage takes down all browsing at once (vs today's per-IP degradation) | Medium | Medium | Accepted trade-off (architect: fail visibly, no fallback — a resilient fallback is the scar this project retires); mitigate with a fail-visible notice, health checks, and Railway restart policy rather than a second data path. |

## References

- **Issue #92** (this project) and **Issue #85** (review backend — folded in here; stays the review
  tracking issue).
- **Spec 83 / Plan 83** — the reviewer workspace whose `localStorage`/GitHub-issue seam this
  replaces ("the submit panel is the only seam to replace").
- **Spec 49 / `results/README.md`** — the score tier contract and paper-reconciliation guard.
- **Spec 51 / `results-raw/README.md`** — the raw tier, its fingerprints, and the dual-source
  baked-bundle workaround being retired.
- **Spec 54 / `export-afb`** — the catalog-generic raw viewer (a non-MB catalog that must keep
  riding the served raw tier unchanged).
- **Spec 55** — the results leaderboard (Gemini-only ranking; Opus badged, never re-ranks).
- **`traditions/README.md` / Spec 1** — the corpus contract the corpus tier ingests.
- **`workflows/analysis`** — the canonical exporters (`export`, `export-raw`, `export-afb`),
  `aggregate.py`, `loaders.py::load_corpus`, and `fingerprint.py` (the ingest inputs and provenance
  keys).
- **`apps/multibrowser/src/lib/`** — the seam: `github.ts`, `rawSource.ts`, `queries.ts`.
