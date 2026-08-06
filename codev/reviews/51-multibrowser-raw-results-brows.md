# Review: multibrowser raw-results browser — per-scenario transcripts + judge verdicts

## Summary

Ported JaleesBench's raw-results experience to MultiBench: from any scenario a reader now
drills into a **raw-results view** showing every model's actual transcripts
(subject × framing × pressure) and our judging (per-(judge, scope) verdicts — score + direction
+ rationale), with A/B compare, curated presets, and fully deep-linkable view state.

Delivered as two additive pieces mirroring the #49 score tier:

1. **A committed `results-raw/<run-id>/` tier** — per-scenario gzip shards of
   transcripts + verdicts (519 shards, ~126 MB for run `20260803`), produced by a sibling
   `analysis export-raw` command that reuses the #49 judgment loaders. Both tiers stamp an
   equal **source fingerprint** so cross-tier agreement is a checkable invariant, not a hope.
2. **A catalog-generic raw viewer** in `apps/multibrowser` (`/results/$runId/$groupId/$itemId`)
   served **dual-source** (same-origin gz-baked bundle primary, SHA-pinned GitHub committed
   tier authoritative + fallback), with the `ResultsRegion` seam upgraded to a live drill-in.

The contract and viewer are **catalog-generic** (issue #54): score scale + ramp, subjects,
judges, condition axes, grouping axis, and items are all catalog-declared, so a non-MultiBench
0–4 catalog rides the same viewer with zero component changes (proven by a synthetic-catalog
render test and the static no-MB-vocab check).

All 8 implement phases were consult-approved (`[codex, claude]` per-phase); the final phase
carries both reviewers at **APPROVE**.

## Spec Compliance

Every Success Criterion in the spec is met. Highlights:

- **Sibling `export-raw` reusing #49 loaders** — `read_run_root`/`resolve_judgments`/alias maps
  reused for verdicts; transcripts via a **new** full-grid sitting reader (there is no #49
  sitting loader). ✔
- **Transcripts exclusively from the full-grid (report.json) run**; all other roots' sittings
  ignored; a resolved verdict with no matching full-grid transcript is a **loud export abort**. ✔
- **`context_prefix` via a per-shard `contexts` pool keyed by framing**; unstated cells carry
  none; a shard renders from one fetch. ✔
- **Determinism** — no wall-clock field anywhere; sorted keys, compact separators,
  `gzip(level 9, mtime=0)` → byte-identical re-exports (Test: full byte-identity). ✔
- **Source fingerprint** stamped in **both** tiers' manifests (additive #49 change) and asserted
  equal by the viewer + a committed-artifact test. ✔
- **`schema_version`** in catalog **and** every shard; SPA refuses a mismatch with a Notice. ✔
- **Shard enumeration manifest-declared** (never the trees API); catalog discovery may walk. ✔
- **Field allowlist** (positive list only) — no `usage`/`raw`/`attempts`/`ts`/`sitting_key`/
  `model` leak. ✔
- **`dataset.license = CC-BY-4.0`** (SPDX). ✔
- **Live `ResultsRegion`**, raw route, **A/B compare**, **deep links incl. run-id**,
  **presets** (Models split / Judges differed / Steadfastness cliff), **magic-byte gunzip sniff
  verbatim** + `DecompressionStream` feature-detect. ✔
- **No band names** anywhere; catalog-declared ramp (not a hardcoded viewer constant). ✔
- **Catalog-genericity (#54)** — static no-vocab check + synthetic off-domain render + a drift
  guard against the real committed `.gz`. ✔
- **Dual-source (Decision 14)** — baked-first, GitHub-fallback, fingerprint coherence, Notice on
  fallback; **served gz-baked** (see Deviations). ✔
- Fail-soft throughout; both suites green via `.codev/checks/test.sh`. ✔

## Deviations from Plan

1. **Baked bundle ships gz, not uncompressed (Decision 14 amendment, architect-approved).**
   Spec Decision 14 wrote "full **uncompressed** baked bundle." Measurement showed the
   uncompressed tier is ~3.7× the gz size, ballooning the Railway image to ~1 GB (public/ +
   dist/ copy). The architect ruled **gz-baked**: the baked bundle ships the *same* gz shards as
   the committed tier (~126 MB), so the client's magic-byte sniff still exercises the
   `DecompressionStream` path on both sources. Identical content + fingerprint; only the image
   size changes.
2. **`ResultsRegion` is a live link, not an eager cell-score grid (architect-approved,
   perf-driven).** A per-scenario summary grid on the scenario page would fetch that scenario's
   ~220 KB raw shard on **every** scenario load, and the score tier carries no per-scenario cell
   scores to build one without it. The region is instead a **contentful link** ("N models × M
   conditions" from the already-loaded score manifest — no raw fetch); the full grid + transcripts
   live one tap away in the raw view.
3. **Cell-score grid moved into the raw view (architect ruling b).** The grid overview
   (subjects × condition-tuples, chips colored by the catalog ramp, judge-selectable, click =
   navigate; A/B pins two subjects) lives in the **raw view**, where the shard is already
   fetched — not on the scenario page. The grid *is* the navigation; selectors remain the URL-state
   backbone.
4. **Presets round-robin across the grouping axis (architect-approved, CMAP-required).** A
   straight magnitude + lexicographic cut filled all 12 slots from the alphabetically-first
   tradition (verified: all 36 launch entries landed in `buddhism`), defeating the "curated
   navigation" intent. Selection now round-robins one entry per group per round in sorted order;
   with a single group it degenerates to plain magnitude order.
5. **Hot-tier lessons consolidated (deviation from the plan's "4 lessons in `lessons-critical.md`").**
   The plan asked for the genericity / gunzip-sniff / fingerprint / Railway-`.gitignore` lessons in
   the hot tier "displacing weaker entries if capped." The hot tier is at its hard cap of 10 with
   one-for-one displacement discipline; promoting all four would gut it. The one lesson a reviewer
   flagged as truly hot-worthy — the Railway `.gitignore` "silently never ships" deploy trap (plus
   the companion `serve -s` HTML-fallback trap) — is **folded into the existing SPA-data-layer hot
   entry** (same domain), adding no net slot. The other three stay in the cold archive.
6. **Per-phase consult is `[codex, claude]`, not the full 3-way.** Gemini's per-phase sandbox
   can't see the worktree (empty → no verdict → parsed REQUEST_CHANGES), so it is dropped from
   per-phase review; the full 3-way CMAP runs at the PR gate where the diff is fed inline. (Repo
   convention, not new to #51.)

## Lessons Learned

### What Went Well
- **Fingerprint-as-invariant.** Stamping one hash over the resolved-judgments stream in both
  tiers turned "same loaders" into a checkable equality — and the client uses the same hash to
  decide baked-vs-GitHub coherence, so one mechanism serves provenance *and* source resolution.
- **Catalog-genericity paid off cheaply.** Pushing scale/ramp/subjects/judges/axes/items into
  catalog data (guarded by a static no-vocab check + a synthetic off-domain render) means #54's
  0–4 AFB catalog rides the viewer unchanged.
- **Real-data sizing early** (phase 2) caught the ~126 MB reality vs. the 30–80 MB estimate before
  it became a deploy surprise, and drove the gz-baked ruling.

### Challenges Encountered
- **The `serve -s dist` SPA-fallback trap.** A missing baked file returns `200 + index.html`, not
  404, so the baked→GitHub fallback fired via the *parse-failure* branch and showed a misleading
  "baked data unreadable" notice on every load until the first bake. Fixed by treating a
  `text/html` content-type as "absent."
- **`railway up` respects `.gitignore` by default**, which would have made the "primary" baked
  source silently never ship. `--no-gitignore` + a `.railwayignore` mirror closes it.
- **Preset degeneracy on real data** — the magnitude+lexicographic tie-break wasn't visible on
  fixtures; only the real launch run exposed the all-one-tradition collapse.

### What Would Be Done Differently
- Confirm the porch review loop's exact command surface up front (the consult is a manual
  `consult` CLI step; `porch done`↔`porch next` is only the build↔review handshake).

### Methodology Improvements
- Keep deriving formats and sizes from the **real reference data**, not the issue estimate.

## Technical Debt / Follow-up Items
- **Dead seam cleanup:** `loadResults()` / `Scenario.results` (#8) is now deprecated (always
  `null`, unread) — left in place to keep this phase's scope tight; slated for removal in a
  follow-up.
- **Bake-retry cost:** the `bake-and-deploy.sh` EXIT trap discards the baked dir on a failed
  `railway up`, forcing a full re-export to retry. Acceptable default (guarantees `deploy.test`
  stays clean); revisit if deploy failures become common.
- **Service pinning:** the bake script relies on the already-linked Railway service; it does not
  pin the target service/environment explicitly.
- **Post-merge, architect-driven:** the actual production `railway up --no-gitignore` and the
  ~126 MB upload / image-size confirmation happen through the architect after merge (phase 8 is
  wiring + docs only).
- **⚠ OPEN — baked-primary upload times out at ~126 MB (2026-08-06 deploy).** The post-merge
  production deploy reproducibly failed the baked-bundle upload (2× `operation timed out` at
  `backboard.railway.com`) — the ~126 MB gz bundle exceeds the `railway up` CLI's tolerance.
  **Production therefore runs WITHOUT the baked primary, serving the raw tier from the committed
  GitHub fallback — the dual-source design's exact graceful path** (verified live: the app treats
  the absent baked path's `200 + index.html` as "absent" and serves GitHub with the "no baked
  bundle — serving the live GitHub copy" notice; deep links, catalog, and gz shards all resolve at
  the pinned `main` SHA). The wiring is correct; only the baked *primary* is not yet live.
  **Follow-up options for enabling baked-primary:** a newer `railway` CLI, an off-peak retry, a
  chunked/asset-based upload, or a Railway support ticket for the source-upload size limit. Until
  then the GitHub fallback carries production (correct, just without the same-origin speed / full
  rate-limit immunity).

## Verification (post-merge, live — 2026-08-06)

Client-side data-path verification against `https://multibrowser-production.up.railway.app`:

- **App shell + deployed bundle** — served (HTTP 200); the deployed JS (`index-*.js`, ~685 KB)
  contains the raw-browser + dual-source code, including the literal `no baked bundle — serving the
  live GitHub copy` notice and `content_fingerprint`.
- **Baked absent → graceful GitHub fallback** — `/data-raw/20260803/manifest.json` returns
  `200 + text/html` (the `serve -s` SPA history fallback), which the client's `isHtmlResponse` guard
  treats as "absent" → the clean GitHub fallback path (exactly the deploy deviation above).
- **GitHub fallback tier** — reachable at the pinned `main` SHA `6e5bba3`: manifest (519 items, both
  `fingerprint` and `content_fingerprint`) + gz shards with valid `1f 8b` magic bytes.
- **Deep-link route** — `/results/20260803/sunni-islam/JLS-001` resolves to the app (SPA fallback).

The rendered interaction layer (raw view render, A/B, presets, cell-score grid, fallback-notice
display, deep-link restore) is covered by the **251 vitest tests** against the real committed
catalog/shards + fixtures; the interactive human walkthrough is Waleed's live look at the gate.

## Consultation Feedback (per-phase `[codex, claude]`)
- **Phase 1** (export core) — 3 rounds → APPROVE/APPROVE.
- **Phase 2** (fingerprint plumbing + writer + CLI + sizing) — 3 rounds → APPROVE/APPROVE.
- **Phase 3** (presets) — 2 rounds → APPROVE/APPROVE (round-robin refinement landed here).
- **Phase 4** (committed dataset + README) — 2 rounds → APPROVE/APPROVE.
- **Phase 5** (SPA raw data layer) — 7 rounds (deepest; dual-source + persistence + coherence) →
  APPROVE/APPROVE.
- **Phase 6** (raw view + live ResultsRegion) — 4 rounds → APPROVE/APPROVE.
- **Phase 7** (A/B + deep links + presets nav) — 2 rounds → APPROVE/APPROVE.
- **Phase 8** (deploy wiring + docs) — **iter 1**: Codex REQUEST_CHANGES (unsafe `rm -rf`,
  leftover bake dir, doc drift), Claude COMMENT (serve-s fallback notice, narrow `.railwayignore`,
  hot-tier placement, nits); **iter 2**: **Codex APPROVE, Claude APPROVE** — all items fixed.

## Architecture Updates
Applied via the `update-arch-docs` skill:
- **`arch-critical.md`** (HOT) — added the raw-tier fact: `results-raw/<run-id>/` per-scenario gz
  shards (~126 MB/run) via `analysis export-raw`, equal source fingerprint across tiers,
  dual-source serving, catalog-generic viewer (AFB #54 rides it), numeric scores + catalog ramp,
  no band names. (At the 10-fact cap.)
- **`arch.md`** (COLD) — extended "The analysis workflow" with the two committed SPA-browsable
  tiers (score + raw), the shared fingerprint, catalog-genericity, and dual-source serving; points
  to `results-raw/README.md`.

## Lessons Learned Updates
Applied via the `update-arch-docs` skill:
- **`lessons-critical.md`** (HOT) — folded the two deploy traps into the existing SPA-data-layer
  entry (no net slot): `railway up` respects `.gitignore` (force with `--no-gitignore` +
  `.railwayignore` or the primary silently never ships); a `serve -s dist` host answers a MISSING
  baked file with `200 + index.html`, so treat an HTML content-type as "absent" or the fallback
  never fires cleanly.
- **`lessons-learned.md`** (COLD) — added: keep a browsable data contract catalog-generic when a
  second dataset type reuses the viewer; stamp a shared source fingerprint across two tiers that
  must agree; client gzip magic-byte sniff before `DecompressionStream`; size a browsable tier from
  the real data (not the issue estimate); the localStorage-persisted TanStack cache must exclude
  big/volatile queries and never cache class instances.

## Flaky Tests
None.
