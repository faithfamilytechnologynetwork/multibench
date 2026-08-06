# Specification: multibrowser raw-results browser — per-scenario transcripts + judge verdicts

<!--
SPEC vs PLAN BOUNDARY:
This spec defines WHAT and WHY. The plan defines HOW and WHEN.
Implementation phases, file paths, and code live in codev/plans/51-*.md.
-->

## Metadata
- **ID**: spec-2026-08-06-multibrowser-raw-results-brows
- **Status**: draft
- **Created**: 2026-08-06

## Clarifying Questions Asked

No clarifying questions were put to the user: issue #51 plus the two architect
comments and the taqwabench design retrospective (`…/taqwabench/tmp/jaleesbrowser-retro-multibench.md`)
constitute a complete brief. The questions those sources — and the three iter-1 reviews
(taqwabench cross-workspace, Codex, Claude) — resolved, with answers, are recorded here so
the decisions are auditable:

- **Commit the raw tier, or host it elsewhere?** → Commit it, drop-in like `results/`
  (#49). SHA-pinning restores the atomic co-versioning that baking-in-repo bought
  jaleesbench, without redeploying the SPA on new data. (Architect + retro §2.) **But the
  committed weight is ~110–150 MB gz/run — 2–4× the issue's 30–80 MB estimate (measured,
  see *Performance Requirements*); this is surfaced to Waleed as a gate decision.**
- **Where do transcripts come from?** → **Exclusively from the full-grid run** (the merged
  Gemini run — the only root bearing `report.json` that pins the scenario universe).
  *Correction from iter 1:* the `…-framings-opus-sample` root **does** carry
  `sittings.jsonl`/`sittings_tail.jsonl` (verified); only `…-unstated-opus` lacks them.
  The export **ignores every non-full-grid root's sittings** and reads transcripts only
  from the full-grid run — one unambiguous source. Verdicts still come from **all** roots,
  resolved through the #49 judgment loaders.
- **Is the transcript read a reuse of the #49 loaders?** → *Half.* `read_run_root`/
  `resolve_judgments`/the alias maps are reused for **judgments**; there is **no** sitting
  loader in #49 (verified: `read_run_root` reads `judgments*.jsonl`/`report.json` only), so
  the transcript reader is **new code that applies the same normalization** (the subject
  alias map), because subject spellings differ across roots (e.g. `Qwen/Qwen3-235B-A22B-Instruct-2507`
  vs `qwen/qwen3-235b-a22b-2507`, verified).
- **Do we ship `context_prefix` (the stated/guided "what the model was told" text)?**
  → Yes, via a **per-shard `contexts` pool keyed by framing** (taqwabench ruling b).
- **Band names?** → None, anywhere. Numeric −1…+1 + the #49 `scoreColor` ramp is
  MultiBench policy; jaleesbench's Burns/Perfume ladder does not port. (Includes editing
  the existing `ResultsRegion` placeholder string, which literally reads "bands" today.)
- **Verdict score scale/type?** → The judgment `score` is one of {−1, −0.5, 0, 0.5, +1}
  (validated by the #49 `is_valid_score` contract); it ships as a **number** on −1…+1 with
  **no rescale** (the −2…+2 rescale was jaleesbench-only).
- **`analysis export` extended, or a sibling command?** → **Sibling `export-raw`**
  (taqwabench ruling a); both reuse the same judgment loaders and stamp the same fingerprint.
- **How is "cannot disagree" made real across two separately-run exporters?** → A
  deterministic **source fingerprint** (a hash over the resolved-judgments stream) is
  stamped in **both** tiers' manifests and asserted equal per run-id by the viewer/CI.

## Problem Statement

The `/results` explorer shipped in #49 shows **aggregate scores only** — per-tradition
slice means, a Gemini-ranked leaderboard, an Opus validation badge. It answers "how did
model X score" but never "**what did model X actually say, and why did the judge score it
that way?**". The evidence behind every number — the raw transcript per
subject×framing×pressure, and the judge's per-scope verdict (score + rationale) — is
invisible in the browser. It exists only in gitignored multi-hundred-MB run artifacts on
one machine (`tmp/judging-runs/…`), unreadable by anyone without shell access to that box.

Waleed's ask, verbatim: *"the results browser that shows the different models' raw
responses and our judging."* JaleesBench already built exactly this experience
(`jaleesbrowser`); #51 is the port to MultiBench's corpus, scale, and conventions.

Without it, the benchmark's central claims are unauditable by a reader: they can see the
leaderboard but cannot inspect a single response that produced it, cannot compare two
models side-by-side on the same prompt, and cannot see where the two judges disagreed.

## Current State

- **Scores tier (#49):** `results/<run-id>/` is a committed, scores-and-metadata-only
  export (manifest + per-tradition slice-table shards, **~184 KB** for the launch run).
  The SPA reads it at runtime over SHA-pinned GitHub `raw` fetches; `/results` renders a
  Gemini-ranked leaderboard (Opus badged, never re-ranking). The tier is **run-scoped**:
  `loadResultsRuns`/`defaultRunId` pick a default and `?run=<run-id>` pins one. There are
  **no transcripts and no verdicts** in this tier by design.
- **Export pipeline (#49):** `workflows/analysis/analysis/export_results.py` reads the raw
  run roots, normalizes subject/judge id spellings (`_SUBJECT_ALIAS`/`_JUDGE_ALIAS`),
  overlays `judgments_v2.jsonl`, deduplicates the Opus-alias collision (later-`ts` wins in
  `resolve_judgments`), pins the full-grid universe from `report.json` (`_scenario_universe`),
  and aggregates via canonical `analysis.aggregate`. `read_run_root` reads
  `judgments*.jsonl`/`report.json` **only — there is no sitting loader.** `analysis export`
  is the CLI entry point; its manifest currently carries a wall-clock `generated_at`.
- **SPA seam (#49):** each scenario page renders an **inert** one-line `ResultsRegion`
  (`ScenarioPage.tsx:127`) fed by `results.ts::loadResults`, which *always returns `null`*
  today — a reserved hook plus a placeholder string that literally reads "model scores,
  **bands**, and verdicts will appear here". Nothing else in the SPA loads per-scenario
  results. `github.ts` is the single SHA-pinned fetch boundary; its truncated-tree fallback
  walks `traditions/` and `results/` (`WALK_DIRS`). `scoreColor.ts` is the −1…+1 diverging
  colormap; `resultsModel.ts` is the fail-soft, version-checked (`SUPPORTED_SCHEMA_VERSION`),
  `isSafePathSegment`-guarded parser pattern for remote dataset JSON.
- **Raw run data (source of truth, gitignored):** for each tradition,
  `tmp/judging-runs/20260803-merged/<tradition>/` has `sittings.jsonl` (transcripts),
  `judgments.jsonl`, and `report.json` (the **full-grid Gemini run**). Two Opus judge-layer
  roots add verdicts: `…-unstated-opus/<tradition>/` (judgments only, **no** sittings) and
  `…-framings-opus-sample/<tradition>/` (judgments **and** `sittings.jsonl`/`sittings_tail.jsonl`
  — which the export ignores). Scale (measured): the Gemini grid is **46,710 sittings /
  93,420 judgments**; the Opus layer adds **42,711 judgments** (31,114 unstated + 11,597
  framings-sample). 519 scenarios × 90 cells (5 subjects × 3 framings × 6 pressures).
- **Reference to port:** jaleesbench `export_web.py` (catalog + per-probe gzip shard) and
  `apps/jaleesbrowser/src/` (generic, data-driven side-by-side viewer with client-side
  gunzip and URL-encoded deep links).

## Desired State

A reader on `/results` drills from any scenario into a **raw-results view** (a new
run+scenario-scoped route; see *entry-point ruling* below) and can:

1. **Read the actual transcripts** — the full multi-turn conversation for any
   subject×framing×pressure cell of that scenario.
2. **See the framing the model received** — the stated/guided `context_prefix` ("what the
   model was told"), rendered where present.
3. **See our judging** — per (judge, scope) verdicts on each cell: the numeric score on
   the −1…+1 scale (colored by the #49 ramp), the direction summary, and the rationale
   where recorded. **Both judges** appear where present — Gemini (full grid) and Opus
   (honest-sample, **badged** exactly as #49 badges it), never re-ranking.
4. **Compare two subjects side-by-side (A vs B)** on the same cell — the jaleesbrowser
   parity feature.
5. **Deep-link any view** — the entire view state (**run-id**, tradition, scenario, A/B
   subjects, framing, pressure, scope) lives in the URL, so every view is shareable and
   every preset is just a URL.
6. **Jump to curated views** — export-computed **presets** (see *Presets* under Constraints)
   as capped, deterministic deep-link lists.

Delivered by two additive pieces that mirror the #49 architecture:

- **A new committed raw-data tier `results-raw/<run-id>/`** — a per-scenario, lazily
  loaded, gzip-compressed transcript+verdict export, read at runtime exactly like
  `results/` and `traditions/` (SHA-pinned GitHub `raw`, no backend, no redeploy on new
  data). A new tradition/run/scenario appears with **no SPA code change**.
- **The `ResultsRegion` seam made live** — see *entry-point ruling*.

**Entry-point ruling (resolves the iter-1 ambiguity):** the full raw view — transcripts,
per-cell verdicts, A/B compare, presets — lives on a **new run+scenario-scoped route**
(a dedicated view, not the one-line inline region). The existing `ResultsRegion` on
`ScenarioPage` is **upgraded to a live in-page entry**: a compact per-scenario summary
(e.g. the cell score grid) that links into the raw view. `/results` gains a drill-down
into the same route. Exact route path and component decomposition are Plan-level; the
*shape* (dedicated view + live entry, run-scoped) is fixed here.

**Agreement, made checkable (not just "same loaders"):** both exporters stamp a
deterministic **source fingerprint** — a hash over the resolved-judgments stream (the
sorted list of `(normalized subject, scenario, pressure, framing, judge, scope, score,
direction, rationale)`) — into their manifests. The viewer (and a CI check) assert the
raw tier's fingerprint equals the score tier's for the same run-id, and show a `Notice` on
mismatch. This upgrades "produced by the same loaders" from a convention to a checkable
invariant that holds even though the two are separate commands run at separate times.

**`context_prefix` ruling:** shipped via a **per-shard `contexts` pool keyed by framing**
— the prefix text is stored once per shard per framing, and cells reference it by their
framing key. `unstated` cells have no prefix. The shard renders completely from **one
fetch** (self-containment preserved; no catalog coupling). Tradition-level constancy of
guided text, if it holds, is a compression fact, **not** part of the schema.

## Stakeholders
- **Primary Users**: readers/reviewers of the MultiBench results (researchers, the paper's
  audience) who want to audit the raw evidence behind the scores.
- **Secondary Users**: the MultiBench team, who use side-by-side and judges-differed views
  to spot-check judging quality and model behavior.
- **Technical Team**: this builder (spir-51); maintainers of `workflows/analysis` and
  `apps/multibrowser`.
- **Business Owners**: Waleed (requester, decision authority — incl. the repo-weight and
  license calls at the gate); the architect (baked the design decisions, ran the
  cross-workspace review).

## Success Criteria
- [ ] A new committed tier `results-raw/<run-id>/` exists, produced by a **sibling
      `analysis export-raw`** command that **reuses the #49 judgment loaders**
      (`read_run_root`, `resolve_judgments`, `_SUBJECT_ALIAS`/`_JUDGE_ALIAS`) for verdict
      resolution.
- [ ] The tier carries, per scenario, every subject×framing×pressure cell with its
      transcript turns and its per-(judge, scope) verdicts (score −1…+1, direction
      summary, rationale where present), for **both** judges where present.
- [ ] **Transcripts are read exclusively from the full-grid (report.json) run**; every
      other root's sitting files are ignored.
- [ ] **Transcripts are keyed by normalized subject** (same alias map); a resolved verdict
      whose cell has **no matching full-grid transcript is a loud export failure** (abort,
      never a verdict shipped without a transcript).
- [ ] `context_prefix` is shipped via a **per-shard `contexts` pool keyed by framing**;
      unstated cells carry none; a shard renders from one fetch.
- [ ] The export is **fully deterministic**: **no wall-clock field anywhere** in the raw
      tier; sorted keys, compact separators, `gzip(level 9, mtime=0)` → **byte-identical**
      re-runs; unchanged shards produce no-op commits.
- [ ] Run identity/provenance is a **deterministic source fingerprint** stamped in the raw
      manifest; the **same fingerprint is also stamped in the `results/` manifest**
      (additive #49 change), and the viewer/CI asserts equality per run-id (`Notice` on
      mismatch).
- [ ] `schema_version` is stamped in **both** the catalog **and every shard**; the SPA
      refuses a mismatched version loudly (a `Notice`, no crash).
- [ ] **Shard enumeration is manifest-declared** — the viewer never uses the trees API to
      list per-scenario shards (only catalog discovery may walk the tree).
- [ ] The export ships **only an explicit field allowlist** (below); no `usage`, `raw`,
      `attempts`, `ts`, `sitting_key`, `model`, or `context_prefix`-internals leak.
- [ ] The `dataset` block carries an explicit **license** field with a concrete SPDX
      identifier confirmed by Waleed at the gate.
- [ ] The **`ResultsRegion` seam is live** as an in-page entry; the **raw view route**
      renders per-cell transcripts + verdicts on drill-in, lazy-loading only the one
      scenario's shard.
- [ ] **Side-by-side A/B** subject compare works on a cell.
- [ ] **Deep links** encode the full view state **including run-id**; opening a raw view
      whose `results-raw/<run-id>/` counterpart is absent degrades to a `Notice`.
- [ ] **Presets** ("Models split", "Judges differed", "Steadfastness cliff") are
      export-computed to the definitions in *Constraints → Presets*: deterministic,
      thresholded, capped, deduped-per-scenario, stable-keyed, sparse-Opus-safe.
- [ ] Client gunzip carries the **magic-byte sniff** (0x1f 0x8b) **verbatim** from
      `datasource.ts:70-84`; missing `DecompressionStream` is **feature-detected** and
      shown as a message (no polyfill).
- [ ] **No band names** anywhere; verdict scores use the #49 `scoreColor` ramp; a
      `null`/no-coverage cell reads as neutral, not zero; the `ResultsRegion` placeholder
      string is edited to drop "bands".
- [ ] Fail-soft throughout: malformed/absent remote JSON, 404s, and rate-limits produce
      the existing `Notice`/banner UX, never a blank crash.
- [ ] A **baked dev fixture** (a `--limit`-style small export) lets the SPA's tests run
      without network access.
- [ ] A `results-raw/README.md` documents the contract, layout, allowlist, size ceilings,
      fingerprint, and the produce/refresh command.
- [ ] Both touched suites pass via `.codev/checks/test.sh` (`workflows/analysis` pytest +
      `apps/multibrowser` vitest); no coverage regression.

## Constraints

### Baked Decisions (from the architect / cross-workspace review — fixed, not to relitigate)
1. **Version both files.** `schema_version` stamped in the catalog **and** every shard;
   viewer refuses loudly on mismatch (belt-and-braces atop SHA-pin).
2. **Determinism, no wall-clock.** No timestamp anywhere in the raw tier. Sorted keys +
   compact separators + `gzip(level 9, mtime=0)` → byte-identical re-exports. Identity =
   run-id + **source fingerprint** (hash over the resolved-judgments stream), stamped in
   **both** tiers' manifests and checked equal per run-id.
3. **Judge axis is first-class.** Per-judge, per-scope verdicts (two judges + judge-split
   views); never collapse to a cross-judge mean.
4. **Magic-byte gunzip sniff** carried **verbatim** from `datasource.ts:70-84` (sniff
   0x1f 0x8b; decompress only if still gzipped; never trust Content-Type; feature-detect
   `DecompressionStream`).
5. **Export field allowlist (positive list — the only fields that ship):**
   *per cell* → `subject` (normalized), `framing`, `pressure`, `transcript` (turns of
   `{role, content}` only), a framing reference into the shard `contexts` pool, and
   `verdicts`; *per verdict* → `judge` (UI key), `scope`, `score` (number −1…+1),
   `summary` (= `direction`), and `rationale` when present. Everything else is **excluded**
   (notably judgment `usage`/`raw`/`ts`/`sitting_key`; sitting `attempts`/`usage`/`ts`/
   `model`). This replaces "sanitize if sensitive" — see *Security*.
6. **`context_prefix`** → per-shard `contexts` pool keyed by framing (ruling b).
7. **License field** in the `dataset` block (concrete SPDX id, confirmed by Waleed).
8. **No band names anywhere** — numeric −1…+1 + the #49 `scoreColor` ramp (MultiBench
   policy).
9. **Build ON the #49 seams** — `results/` scores tier, the inert per-scenario
   `ResultsRegion`, and the `export_results.py` judgment loaders. Agreement is enforced by
   the shared fingerprint (item 2), not by hope.
10. **Both judges** where present (Gemini full-grid; Opus honest-sample, badged as #49).
11. **Transcript source = the full-grid (report.json) run only**; other roots' sittings
    ignored (ruling on the iter-1 factual correction).
12. **Sibling `export-raw`** command (ruling a).

### Presets (export-computed; user-visible, hence specified here)
Each preset is a capped, deterministic list of deep-link entries with stable keys, deduped
to **one entry per scenario**, sorted by magnitude with `(scenario, pressure, framing)`
tie-breaks, **cap = 12**, computed only from cells that have the required judge/scope
(sparse-Opus cells are simply skipped, never zero-filled):
- **Models split** — for each `(scenario, pressure, framing)` at **scope = turn1**, the
  widest cross-subject spread of the **Gemini** cell score; entry links the max-score vs
  min-score subjects (A/B). Skip zero-spread and <2-subject cells.
- **Judges differed** — for each cell at **scope = full**, where the two judges' scores
  differ by **≥ 1.0** (on the −1…+1 scale); entry links that cell (and, for A/B, the
  split subject vs the top subject in that `(scenario, pressure, framing)`).
- **Steadfastness cliff** (promoted from nice-to-know, endorsed) — for each
  `(scenario, subject, pressure, framing)`, the largest **negative** `mean(full) −
  mean(turn1)` (Gemini), i.e. the biggest post-pressure drop; entry links that cell.

### Technical Constraints
- **Runtime-fetch, committed tier** (like `results/`): SHA-pinned GitHub `raw`, no backend,
  no baked data in the SPA build, new data with no redeploy. `github.ts` is the only fetch
  boundary; its truncated-tree fallback (`WALK_DIRS`) must also reach `results-raw/` for
  **catalog** discovery (per-scenario shards are manifest-declared, never enumerated via
  the API).
- **Client environment:** `DecompressionStream('gzip')` (evergreen; Safari ≥16.4).
  Unauthenticated GitHub budget (60/hr per IP, possibly NAT-shared): the catalog costs a
  tree walk; per-scenario `.gz` shards fetch via `raw` (off the API budget) and load only
  on drill-in.
- **Multi-language repo:** the exporter is Python (`uv`, `workflows/analysis`); the viewer
  is the TS/React SPA. `.codev/checks/test.sh` already registers both.

### Business Constraints
- No time estimates (AI-age protocol rule).
- The corpus is already public in `traditions/`, but transcripts + judge rationales are new
  published artifacts; they require an explicit `dataset.license` (below) and the field
  allowlist to avoid leaking cost/prompt internals.

## Assumptions
- The on-disk runs at `tmp/judging-runs/20260803-merged/` + the two Opus roots are the
  canonical inputs (present in the worktree; architect will re-symlink read-only if absent).
- Every judged scenario is within the Gemini full-grid universe (#49 `_scenario_universe`
  enforces this; the raw exporter inherits it — and the transcript-join guard makes any
  violation a loud failure rather than a silent drop).
- Transcript content for a cell is identical wherever it appears; taking it from the
  full-grid run loses nothing (and is the single authoritative source regardless).
- The judgment `score` validates against the #49 `is_valid_score` contract and ships as a
  number on −1…+1 (no rescale).
- The `results/` manifest can gain a `fingerprint` field additively; the SPA's zod parser
  can be made to tolerate both old (no fingerprint) and new datasets.

## Solution Approaches

### Approach 1 (chosen): Per-scenario committed `results-raw/` tier + live raw view
**Description**: Add a raw tier mirroring #49's shape — a catalog (`manifest.json`, no
timestamp, with `schema_version` + `fingerprint` + manifest-declared shard paths) plus one
gzip shard **per scenario** (`<tradition>/<scenario>.json.gz`), each shard self-contained
(cells + a framing-keyed `contexts` pool + `schema_version`). Produce it from a new
`analysis export-raw` command that reuses the #49 judgment loaders and adds a normalized
sitting reader. In the SPA, replace `loadResults`' `null` with a lazy per-scenario fetch,
light up `ResultsRegion` as an entry, and add a run+scenario-scoped raw view with A/B
compare and presets. The #49 score matrix answers above-the-fold questions with zero shard
loads; the raw tier is drill-in only.

**Pros**: smallest lazy-load unit; fingerprint makes agreement checkable; additive (new
data → no SPA change); per-scenario granularity → a refresh rewrites only changed shards
(determinism → the rest are no-op commits).
**Cons**: ~519 shard files/run; the committed tier is large (~110–150 MB gz/run, see
*Performance*) and grows history per refresh (mitigated; a gate decision for Waleed).
**Estimated Complexity**: Medium–High **Risk Level**: Medium

### Approach 2 (rejected): One shard per tradition
Fewer files (7), but each drill-in downloads a whole tradition (many MB) to show one
scenario — defeats lazy loading — and any single judgment change rewrites the whole
tradition shard (worse history churn). **Rejected.**

### Approach 3 (rejected): Bake the export into the SPA build (jaleesbench's model)
Atomic co-versioning for free, but redeploy on every refresh; breaks the #49/#1
runtime-fetch principle; the retro measured this as real pain (167 MiB pack over 4
generations). SHA-pinning already buys co-versioning. **Rejected** (kept only as the tiny
baked dev-fixture).

## Open Questions

### Critical (Blocks Progress)
- [ ] **Repo-weight acceptance (Waleed, at the gate):** the raw tier is **~110–150 MB gz
      per run** (measured extrapolation, not the issue's 30–80 MB) and grows history per
      refresh. Confirm committing at this magnitude is acceptable, or choose a lever
      (git-LFS; a subject/tradition subset; a retention policy of one run at a time). The
      rest of the spec assumes plain commit with per-scenario determinism as the mitigation.

### Important (Affects Design)
- [ ] **License identifier:** the concrete SPDX id / text and its approval source for
      `dataset.license` (Waleed). Placeholder until then.
- [ ] **Dropping `results/` `generated_at`:** the reviewer recommends removing it so the
      score tier is byte-identical too (backward-compat via a tolerant zod parser), and
      replacing the "newest by timestamp" default-run signal with run-id ordering or an
      explicit marker. Not required for the raw tier's determinism (the raw tier is always
      addressed by run-id from the score-tier context); folded in as an additive #49
      improvement if cheap. **Resolve in Plan.**

### Nice-to-Know (Optimization)
- [ ] **jsDelivr fronting** of `raw.githubusercontent.com` (CDN, SHA-pinnable) — retro
      suggestion; default to the existing `raw` path for #49 consistency; future work.

## Performance Requirements
- **Measured sizes (this worktree, level-9 gzip, allowlist applied):** per-scenario shard
  **161–300 KB gz (median ~221 KB)**; one mid-small tradition (taoism) **~10.6 MB gz**;
  Gemini grid extrapolates to **~110–130 MB gz**, **~110–150 MB gz** including the ~42.7k
  Opus verdicts. These supersede the issue's 30–80 MB estimate.
- **Size ceilings (guardrails, calibrated above observed):** per-shard **≤ 512 KB gz**;
  per-run total **≤ 200 MB gz**. The export validates **all** sizes before writing
  anything (no partial tier) and fails loudly on breach. Final values may be tuned in Plan
  from the measured p99, but must sit above real data, not on it.
- **Per-view payload**: a drill-in fetches **one** `.gz` shard (~a few hundred KB);
  above-the-fold `/results` uses only the #49 score tier.
- **API budget**: no per-scenario API calls — shards fetch via `raw` (off-budget); the
  catalog is discovered via the existing SHA-pinned tree walk.
- **Determinism**: byte-identical re-exports (stable caching / no-op commits).

## Security Considerations
- **No secrets, no token** (client app; consistent with #49).
- **Field allowlist (not blocklist):** the export emits only the positive list in
  *Constraints → Baked Decision 5*; cost/usage internals and the judge's unparsed `raw`
  output never leave the machine. This is testable (assert no disallowed key appears),
  unlike "sanitize if sensitive".
- **Rationale content:** shipped (it is the product). The iter-1 "sanitize scenario text"
  clause is **dropped as vestigial** — the scenario corpus is already public in
  `traditions/`, so quoting it in a rationale exposes nothing new. (If a future tradition
  is private, that tradition's raw export is simply not produced.)
- **Path-injection**: manifest-declared shard paths and run/tradition/scenario ids are
  validated as safe single path segments before being spliced into a `raw` URL (reuse
  `_require_safe_segment` / `isSafePathSegment`).
- **License**: `dataset.license` states the corpus's terms on the public export.

## Test Scenarios
### Functional Tests
1. **Field-level parity (happy path):** for a sampled cell/judge/scope, the raw-tier
   verdict's preserved fields — normalized `(subject, scenario, pressure, framing, judge,
   scope)`, `score`, `summary`(=direction), `rationale` — equal the #49-resolved judgment
   for that identity.
2. **Aggregate reconciliation:** independently recompute a `results/` slice mean from **all
   included raw-tier verdicts** (not one cell) and assert it equals the score-tier slice —
   the mathematically correct form of "cannot disagree".
3. **Fingerprint equality:** the raw manifest's `fingerprint` equals the `results/`
   manifest's `fingerprint` for the same run-id; a deliberately mutated input changes both.
4. **Transcript sourcing:** a cell judged only by Opus still carries a transcript (from the
   full-grid run); a non-full-grid root's differing sitting file does **not** change the
   shipped transcript.
5. **Orphan-judgment guard (inverse):** a resolved verdict whose cell has no full-grid
   transcript **aborts the export loudly** (simulates a half-copied run root).
6. **Normalized join:** transcripts and verdicts join by **normalized** subject across
   roots with divergent spellings (no silent cell drop).
7. **Determinism:** exporting twice over identical inputs yields **byte-identical** shards
   **and** catalog — no exceptions.
8. **Allowlist:** no shard/catalog contains `usage`, `raw`, `attempts`, `ts`,
   `sitting_key`, or `model`.
9. **`context_prefix` pool:** stated/guided cells resolve their framing text from the
   per-shard `contexts` pool (stored once per framing); unstated cells carry none.
10. **Version mismatch:** a shard/catalog with an unsupported `schema_version` yields a
    `Notice`, not a crash.
11. **Gunzip sniff:** a shard served already-decompressed (no magic bytes) and one served
    raw-gzip both parse.
12. **A/B + deep link (incl. run-id):** selecting A and B renders both; the URL encodes
    run-id + full state and re-opening restores the view; a missing `results-raw/<run-id>/`
    degrades to a `Notice`.
13. **Preset navigation:** each preset entry (per the *Presets* definitions) is a valid
    deep link opening the intended cell/compare; presets are ≤12, deduped-per-scenario,
    deterministic.
14. **Fail-soft:** a 404 shard, a malformed shard, and a rate-limit each degrade to the
    existing `Notice`/banner UX.

### Non-Functional Tests
1. **Size ceilings:** an over-ceiling shard or total fails the export before any write.
2. **Feature-detect:** with `DecompressionStream` unavailable, the SPA shows a message.
3. **Network-free SPA tests:** the vitest suite runs against the baked dev fixture.

## Dependencies
- **External Services**: GitHub `raw` + git-trees API (unauthenticated), as #49.
- **Internal Systems**: #49 scores tier + `export_results.py` judgment loaders (+ a new
  normalized sitting reader); the #49 SPA seams (`ResultsRegion`, `results.ts`, `github.ts`,
  `resultsModel.ts`, `scoreColor.ts`, `searchParams.ts`); the full-grid run root under
  `tmp/judging-runs/`.
- **Libraries/Frameworks**: Python `gzip`/`json`/`hashlib` (stdlib), `typer` (existing);
  SPA — React 19 / TanStack Query & Router / Zod / Tailwind / HeroUI; browser
  `DecompressionStream`.

## References
- Issue #51 + the two architect comments (deep-read of jaleesbench + binding spec inputs).
- taqwabench retro: `…/taqwabench/tmp/jaleesbrowser-retro-multibench.md`.
- taqwabench cross-workspace spec review: `…/taqwabench/tmp/multibench-51-spec-review.md`.
- Reference export: `…/taqwabench/jaleesbench/jaleesbench/export_web.py`.
- Reference viewer: `…/taqwabench/apps/jaleesbrowser/src/` (`datasource.ts:70-84` = the
  gunzip sniff to carry verbatim; `contract.ts` = the generic data model to adapt).
- #49 in this repo: `results/README.md`, `workflows/analysis/analysis/export_results.py`,
  `apps/multibrowser/src/{components/ResultsRegion.tsx,lib/results.ts,lib/resultsModel.ts,
  lib/github.ts,lib/scoreColor.ts}`.
- Contract to author: `results-raw/README.md`.

## Risks and Mitigation
| Risk | Probability | Impact | Mitigation Strategy |
|------|------------|--------|-------------------|
| Committed raw tier is ~110–150 MB gz/run and grows history per refresh (gz doesn't delta) | High | High | Surfaced to Waleed as a gate decision (Critical open question); per-scenario granularity + determinism → only changed shards rewrite; git-LFS / subset / one-run-retention as levers; documented in `results-raw/README.md`. |
| Raw and score tiers drift (separate commands, separate times) | Low | High | Shared **fingerprint** stamped in both manifests + viewer/CI equality check; field-parity + aggregate-reconciliation tests. |
| Transcript↔verdict join silently drops cells (divergent subject spellings; no #49 sitting loader) | Medium | High | New sitting reader keys by **normalized** subject; orphan verdict = loud export abort; explicit tests (6, 5). |
| Wrong-root sittings shadow the authoritative transcript | Medium | Medium | Transcripts read **only** from the full-grid run; all other roots' sittings ignored (test 4). |
| Double-gzip ambiguity corrupts shards on some hosts | Medium | High | Magic-byte sniff (0x1f 0x8b) verbatim; never trust Content-Type. |
| `DecompressionStream` unsupported on an old browser | Low | Medium | Feature-detect + message (no polyfill). |
| Guided `context_prefix` (~6.5 KB) bloats shards | Low | Medium | Per-shard framing-keyed pool (once per framing) + per-shard ceiling. |
| SPA tests coupled to the network | Medium | Medium | Baked `--limit` dev fixture. |

## Expert Consultation
**Date**: 2026-08-06
**Models Consulted**: taqwabench main architect (cross-workspace, arranged by our
architect); Codex and Claude (SPIR spec CMAP, per this repo's per-phase consult config).
**Sections Updated (iter-1 → iter-2):**
- *Determinism/identity*: banned all wall-clock from the raw tier; introduced the shared
  **source fingerprint** in both tiers' manifests (taqwabench defect; Codex).
- *Transcript sourcing*: corrected the factual error that Opus roots lack sittings
  (`…-framings-opus-sample` has them, verified); ruled the full-grid run the sole
  transcript source (Claude).
- *Transcript join*: added the normalized-subject key + orphan-verdict loud-fail; corrected
  "reuses #49 loaders" (no sitting loader exists — new code) (Claude; taqwabench add).
- *Sizes/ceilings*: replaced 30–80 MB with the measured ~110–150 MB gz/run; concrete
  guardrail ceilings; raised the repo-weight decision to Waleed (Claude).
- *`context_prefix`*: ruled per-shard framing-keyed pool (taqwabench b).
- *Command*: ruled sibling `export-raw` (taqwabench a).
- *Deep-link state*: added run-id; missing-run fail-soft (Codex; Claude).
- *Entry point*: ruled a dedicated raw view route + live `ResultsRegion` entry (Claude).
- *Presets*: fully specified (score/scope, threshold, cap, sort, tie-break, sparse-Opus);
  promoted "Steadfastness cliff" (Codex; taqwabench).
- *Agreement test*: fixed the math (field-level parity + independent aggregate recompute +
  fingerprint) (Codex).
- *Licensing/safety*: field allowlist + concrete license id; dropped vestigial rationale
  sanitization (Codex; Claude).
- *Minor*: #49 tier = 184 KB; Opus judgments = 42,711; score numeric via `is_valid_score`;
  edit the "bands" placeholder string (Claude).

## Approval
- [ ] Repo-weight decision (Waleed) — Critical open question
- [ ] License identifier (Waleed)
- [ ] Technical Lead / Architect Review
- [ ] Product Owner Review (Waleed)
- [x] Cross-workspace review (taqwabench architect) — approve-with-defect, folded in
- [x] Expert AI Consultation Complete (Codex + Claude, iter 1 → iter 2)
- [ ] `spec-approval` gate

## Notes
- This spec confines itself to WHAT/WHY. Route path, component decomposition, the
  `contexts`-pool wire shape, the fingerprint's exact hash construction, size-ceiling
  final values, and the `results/` `generated_at` change are Plan-phase decisions, seeded
  by the *Open Questions* and *Constraints* above.
- Two decisions await Waleed at the gate: the **repo-weight** acceptance (the corrected
  ~110–150 MB/run) and the **license** identifier. Both are flagged rather than assumed.
