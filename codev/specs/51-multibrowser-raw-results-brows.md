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
comments and the taqwabench design retrospective (`/Users/mwk/Development/fftn/taqwabench/tmp/jaleesbrowser-retro-multibench.md`)
constitute a complete brief. The questions those sources already answer, with their
resolved answers, are recorded here so the decisions are auditable:

- **Commit the raw tier, or host it elsewhere?** → Commit it, drop-in like `results/`
  (#49). SHA-pinning restores the atomic co-versioning that baking-in-repo bought
  jaleesbench, without redeploying the SPA on new data. (Architect + retro §2.)
- **Where do transcripts come from, given the Opus runs re-judge but don't re-run
  models?** → From the full-grid Gemini run (the only roots with `sittings.jsonl`);
  verdicts come from *all* roots, resolved through the #49 loaders. (Confirmed against
  the on-disk runs: the Opus roots carry `judgments.jsonl` only.)
- **Do we ship `context_prefix` (the stated/guided "what the model was told" text)?**
  → Yes, deduplicated. jaleesbench omitted it; MultiBench ships it because "browse the
  model's raw responses" is incomplete without the framing the model actually received.
  (Architect flagged this as a decision the spec must rule; ruled in *Desired State*.)
- **Band names?** → None, anywhere. Numeric −1…+1 + the #49 `scoreColor` ramp is
  MultiBench policy; jaleesbench's Burns/Perfume ladder does not port.
- **Score scale of the shipped verdicts?** → −1…+1 as stored (MultiBench judgment
  `score` is already one of {−1, −0.5, 0, 0.5, +1}); no −2…+2 → −1…+1 rescale (that was
  a jaleesbench-only step).

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
  export (manifest + per-tradition slice-table shards, single-digit MB). The SPA reads it
  at runtime over SHA-pinned GitHub `raw` fetches; `/results` renders the leaderboard.
  There are **no transcripts and no verdicts** in this tier by design.
- **Export pipeline (#49):** `workflows/analysis/analysis/export_results.py` reads the
  raw run roots, normalizes subject/judge id spellings, overlays `judgments_v2.jsonl`,
  deduplicates the Opus-alias collision (later-`ts` wins), and aggregates via the
  canonical `analysis.aggregate`. `analysis export` is the CLI entry point.
- **SPA seam (#49):** each scenario page renders an **inert** `ResultsRegion` fed by
  `results.ts::loadResults`, which *always returns `null`* today — a deliberately reserved
  hook, plus a subtle "results will appear here" placeholder. Nothing else in the SPA
  loads per-scenario results. `github.ts` is the single SHA-pinned fetch boundary;
  `scoreColor.ts` is the −1…+1 diverging colormap; `resultsModel.ts` is the fail-soft,
  version-checked parser pattern for remote dataset JSON.
- **Raw run data (source of truth, gitignored):** for each tradition,
  `tmp/judging-runs/20260803-merged/<tradition>/sittings.jsonl` (transcripts) +
  `judgments.jsonl`, plus the two Opus judge-layer roots (`…-unstated-opus`,
  `…-framings-opus-sample`) which carry `judgments.jsonl` (and `judgments_v2.jsonl`) but
  **no `sittings.jsonl`**. Scale: the Gemini grid is ~46,710 sittings / 93,420 judgments;
  the Opus layer adds ~40,114 judgments.
- **Reference to port:** jaleesbench `export_web.py` (catalog + per-probe gzip shard) and
  `apps/jaleesbrowser/src/` (generic, data-driven side-by-side viewer with client-side
  gunzip and URL-encoded deep links).

## Desired State

A reader lands on `/results`, drills from any scenario into a **raw-results view** and can:

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
5. **Deep-link any view** — the entire view state (scenario, A/B subjects, framing,
   pressure, scope) lives in the URL, so every view is shareable and every preset is
   just a URL.
6. **Jump to curated views** — export-computed **presets** ("Models split", "Judges
   differed") as capped, deterministic deep-link lists.

Delivered by two additive pieces that mirror the #49 architecture:

- **A new committed raw-data tier `results-raw/<run-id>/`** — a per-scenario, lazily
  loaded, gzip-compressed transcript+verdict export. Read at runtime exactly like
  `results/` and `traditions/` (SHA-pinned GitHub `raw`, no backend, no redeploy on new
  data). A new tradition or run appears in the browser with **no SPA code change**.
- **The `ResultsRegion` seam made live** — drill-in loads the per-scenario raw shard and
  renders transcripts + verdicts + A/B compare, with the same fail-soft `Notice`
  discipline used elsewhere.

**Contract stability & agreement (load-bearing):** the raw tier is produced by the *same*
loaders as the score tier (`read_run_root` / `resolve_judgments` / the alias maps), so the
verdicts a reader sees are byte-for-byte the same resolved judgments that produced the
`/results` means — the two tiers **cannot disagree by construction**, and a test guards it.

**`context_prefix` ruling (explicit):** the raw tier **ships** the stated/guided framing
text, **deduplicated** so an identical prefix is stored once per scenario rather than
repeated across that scenario's ~90 cells (guided prefixes are ~6.5 KB each). `unstated`
cells carry none. The exact pooling location (per-shard pool vs. catalog-level shared
section) is a plan-level mechanism; the *requirement* is: ship the text, never duplicate it
per cell, and keep each shard under its size ceiling.

## Stakeholders
- **Primary Users**: readers/reviewers of the MultiBench results (researchers,
  the paper's audience) who want to audit the raw evidence behind the scores.
- **Secondary Users**: the MultiBench team, who use the side-by-side and judges-differed
  views to spot-check judging quality and model behavior.
- **Technical Team**: this builder (spir-51); maintainers of `workflows/analysis` and
  `apps/multibrowser`.
- **Business Owners**: Waleed (requester, decision authority); the architect (baked the
  design decisions, coordinates the cross-workspace review).

## Success Criteria
- [ ] A new committed tier `results-raw/<run-id>/` exists, produced by a command in
      `workflows/analysis` that **reuses** the #49 loaders (`read_run_root`,
      `resolve_judgments`, subject/judge alias maps), so raw and score tiers share one
      normalization/overlay/dedup path.
- [ ] The tier carries, per scenario, every subject×framing×pressure cell with its
      transcript turns and its per-(judge, scope) verdicts (score −1…+1, direction
      summary, rationale where present), for **both** judges where present.
- [ ] Transcripts are sourced from the full-grid run; verdicts from all roots resolved.
- [ ] `context_prefix` is shipped, deduplicated, for stated/guided cells; absent for
      unstated.
- [ ] Export is **deterministic**: sorted keys, compact separators, `gzip(level 9,
      mtime=0)` → byte-identical re-runs; unchanged shards produce no-op commits.
- [ ] `schema_version` (or `contractVersion`) is stamped in **both** the catalog **and
      every shard**; the SPA refuses a mismatched version loudly (a `Notice`, no crash).
- [ ] Every shipped **exclusion** holds: no `usage`, `raw`, `attempts`, `ts`,
      `sitting_key` in the export.
- [ ] The `dataset` block carries an explicit **license** field.
- [ ] The SPA's `ResultsRegion` renders per-cell transcripts + verdicts on drill-in,
      lazy-loading only the one scenario's shard.
- [ ] **Side-by-side A/B** subject compare works on a cell.
- [ ] **Deep links** encode the full view state; **presets** (export-computed,
      deterministic, capped, deduped-per-scenario, stable keys) navigate via URL.
- [ ] Client gunzip carries the **magic-byte sniff** (0x1f 0x8b) verbatim; missing
      `DecompressionStream` is **feature-detected** and shown as a message (no polyfill).
- [ ] **No band names** anywhere; verdict scores use the #49 `scoreColor` ramp; a
      `null`/no-coverage cell reads as neutral, not zero.
- [ ] Fail-soft throughout: malformed/absent remote JSON, 404s, and rate-limits produce
      the existing `Notice`/banner UX, never a blank crash.
- [ ] A **baked dev fixture** (a `--limit`-style small export) lets the SPA's tests run
      without network access.
- [ ] A `results-raw/README.md` documents the contract, layout, exclusions, size
      ceilings, and the produce/refresh command.
- [ ] Both touched suites pass via `.codev/checks/test.sh` (`workflows/analysis` pytest +
      `apps/multibrowser` vitest); no coverage regression.

## Constraints

### Baked Decisions (from the architect — fixed, not to be relitigated)
1. **Version both files.** `schema_version`/`contractVersion` stamped in the catalog
   **and** every shard; viewer refuses loudly on mismatch (belt-and-braces atop SHA-pin).
2. **Judge axis in the score data.** Per-judge, per-scope verdicts are first-class (two
   judges + judge-split views); do not collapse to a cross-judge mean only.
3. **Magic-byte gunzip sniff** carried **verbatim** from `jaleesbrowser`
   `datasource.ts:70-84` (sniff 0x1f 0x8b; decompress only if still gzipped; never trust
   Content-Type; feature-detect `DecompressionStream`).
4. **Determinism** is load-bearing: sorted keys + compact separators + `gzip(level 9,
   mtime=0)` → byte-identical re-exports.
5. **Explicit exclusions:** judgment `usage`/`raw`; sitting `attempts`/`ts`/`usage`;
   `sitting_key`. Never leave the machine.
6. **`context_prefix` decision** ruled by this spec: ship it, deduplicated (see *Desired
   State*).
7. **License field** in the `dataset` block (corpus ≠ jaleesbench's public-domain proof
   texts).
8. **No band names anywhere** — numeric −1…+1 + the #49 `scoreColor` ramp (MultiBench
   policy).
9. **Build ON the #49 seams** — `results/` scores tier, the inert per-scenario
   `ResultsRegion`, and the `export_results.py` loaders (judgments_v2 overlay, alias
   maps, dedup). Raw and score tiers must never disagree.
10. **Both judges** where present (Gemini full-grid; Opus honest-sample, badged as #49).

### Technical Constraints
- **Runtime-fetch, committed tier** (like `results/`): SHA-pinned GitHub `raw`, no
  backend, no baked data in the SPA build, new data with no redeploy. `github.ts` is the
  only fetch boundary; the truncated-tree fallback already walks `results/` and must also
  reach `results-raw/`.
- **Client environment:** `DecompressionStream('gzip')` (evergreen; Safari ≥16.4).
  Unauthenticated GitHub budget (60/hr per IP, possibly NAT-shared): the catalog costs a
  tree walk; per-scenario `.gz` shards fetch via `raw` (off the API budget) and load only
  on drill-in.
- **Multi-language repo:** the exporter is Python (`uv`, in `workflows/analysis`); the
  viewer is the TS/React SPA. `.codev/checks/test.sh` already registers both.
- **Scale:** ~47k transcripts / ~133k judgments across 7 traditions / ~519 scenarios;
  estimated **30–80 MB gzipped** total for the raw tier.

### Business Constraints
- No time estimates (AI-age protocol rule).
- The corpus is **not** public-domain; the export must be licensable and must not leak
  cost/prompt internals (hence the exclusions + the `license` field).

## Assumptions
- The on-disk runs at `tmp/judging-runs/20260803-merged/` + the two Opus roots are the
  canonical inputs; the architect will symlink them read-only into the worktree `tmp/` if
  absent (they are present).
- Every judged scenario is within the Gemini full-grid universe (the #49 exporter already
  enforces this; the raw exporter inherits it).
- `context_prefix` for a given (scenario, framing) is constant across that scenario's
  cells, so per-scenario dedup is sound (the per-scenario shard makes this robust even if
  it varied by pressure).
- Transcript content is identical for the same cell across roots (Opus re-judged the same
  sittings), so taking transcripts from the full-grid run loses nothing.
- The judgment `score` is already on the −1…+1 scale; no rescale.

## Solution Approaches

### Approach 1 (chosen): New per-scenario committed `results-raw/` tier + live `ResultsRegion`
**Description**: Add a raw tier mirroring #49's shape — a catalog (`manifest.json`) plus
one gzip shard **per scenario** (`<tradition>/<scenario>.json.gz`), each shard carrying
that scenario's cells (transcript + verdicts). Produce it from a new `workflows/analysis`
command that reuses the #49 loaders. In the SPA, replace `loadResults`' `null` with a
lazy per-scenario fetch and light up `ResultsRegion` with transcripts, verdicts, and A/B
compare. The aggregate score matrix already lives in `results/` (#49) and answers
above-the-fold questions with zero shard loads; the raw tier is drill-in only.

**Pros**:
- Smallest lazy-load unit (one scenario ≈ 90 cells) → fast drill-in, small per-view bytes.
- Reuses #49 loaders end-to-end → raw/score agreement by construction.
- Additive: new traditions/runs/scenarios appear with no SPA change; the inert seam
  becomes live without a rewrite.
- Per-scenario granularity means a refresh rewrites only the shards whose scenarios
  changed (determinism → the rest are no-op commits) — the best fit for churny gz history.

**Cons**:
- ~519 shard files per run (manageable; `raw` fetch is per-file and off-budget).
- Committed tier grows repo history on each refresh (mitigated; see *Risks*).

**Estimated Complexity**: Medium
**Risk Level**: Medium

### Approach 2 (rejected): One shard per tradition
**Description**: One `.gz` per tradition (~74 cells/scenario × ~74 scenarios) instead of
per scenario.

**Pros**: Fewer files (7); fewer tree entries.
**Cons**: Each drill-in downloads a whole tradition's transcripts (many MB) to show one
scenario — defeats lazy loading; any single judgment change rewrites the whole
tradition shard (worse history churn than per-scenario). **Rejected.**

**Estimated Complexity**: Low
**Risk Level**: Medium

### Approach 3 (rejected): Bake the export into the SPA build (jaleesbench's model)
**Description**: Ship the raw export inside `apps/multibrowser/public/` like jaleesbench.

**Pros**: Atomic co-versioning for free; no runtime fetch.
**Cons**: Redeploy on every data refresh; breaks the #49/#1 "data is drop-in, SPA reads
GitHub at runtime" principle; the retro measured this as real pain (167 MiB pack over 4
generations). SHA-pinning already buys the co-versioning. **Rejected** (kept only as the
dev-fixture mechanism, which is legitimately baked and tiny).

## Open Questions

### Critical (Blocks Progress)
- [ ] None. The architect's brief + the on-disk data resolve every blocking decision.

### Important (Affects Design)
- [ ] **Extend `analysis export` vs. a sibling `export-raw` command?** Leaning a **sibling
      command** (`analysis export-raw`) so the fast, tiny score-tier export stays
      independent of the heavy transcript read; both reuse the same loaders. To confirm in
      Plan / cross-workspace review.
- [ ] **Where does the deduped `context_prefix` live** — a per-shard `contexts` pool, or a
      catalog-level shared-prompts section? Per-shard is simpler and keeps the shard
      self-contained; catalog-level dedupes across scenarios if guided text is
      tradition-constant. Resolve in Plan against measured sizes vs. the shard ceiling.

### Nice-to-Know (Optimization)
- [ ] **jsDelivr fronting** of `raw.githubusercontent.com` (real CDN, SHA-pinnable) — the
      retro's suggestion for a public viewer. Default to the existing `raw` path for #49
      consistency; note as a future optimization, not in scope.
- [ ] Whether presets should include a MultiBench-specific "steadfastness cliff" view
      (biggest full−turn1 drop) in addition to the ported "Models split" / "Judges
      differed".

## Performance Requirements
- **Per-view payload**: a scenario drill-in fetches one `.gz` shard (target well under a
  few hundred KB gzipped); above-the-fold `/results` uses only the #49 score tier.
- **API budget**: no per-scenario API calls — shards fetch via `raw` (off-budget); the
  catalog is discovered via the existing SHA-pinned tree walk.
- **Total tier size**: 30–80 MB gzipped per run; enforced by per-shard and per-run size
  ceilings that fail the export loudly rather than committing an oversized tier.
- **Determinism**: byte-identical re-exports (stable caching / no-op commits).

## Security Considerations
- **No secrets, no token** (client app; consistent with #49).
- **Exclusions** remove cost/usage internals and the judge's unparsed `raw` output
  (prompt-echo risk).
- **Path-injection**: manifest-declared shard paths and run/tradition/scenario ids are
  validated as safe single path segments before being spliced into a `raw` URL (reuse the
  #49 `_require_safe_segment` / `isSafePathSegment` guards).
- **Rationale content**: rationales are shipped (they are the product). If a rationale can
  quote sensitive scenario text, sanitize **at export**, not in the viewer (per retro §4).
- **License**: the `dataset.license` field makes the corpus's terms explicit on the public
  export.

## Test Scenarios
### Functional Tests
1. **Round-trip agreement (happy path):** for a sampled cell, the raw-tier verdict set for
   a judge equals the #49-resolved judgments for that cell (same `resolve_judgments`), and
   the mean of those verdict scores reconciles with the `results/` slice mean.
2. **Transcript sourcing:** a cell judged by Opus (whose root has no `sittings.jsonl`)
   still carries a transcript (sourced from the full-grid run).
3. **Determinism:** exporting twice over identical inputs yields byte-identical shards +
   catalog (only a timestamp field may differ).
4. **Exclusions:** no shard/catalog contains `usage`, `raw`, `attempts`, `ts`, or
   `sitting_key`.
5. **`context_prefix`:** stated/guided cells carry the framing text (deduped, not
   per-cell-repeated); unstated cells carry none.
6. **Version mismatch:** a shard/catalog stamped with an unsupported version yields a
   `Notice`, not a crash.
7. **Gunzip sniff:** a shard served already-decompressed (magic bytes absent) and one
   served raw-gzip both parse correctly.
8. **A/B compare + deep link:** selecting subjects A and B on a cell renders both; the URL
   encodes the full state and re-opening it restores the view.
9. **Preset navigation:** each preset entry is a valid deep link that opens the intended
   cell/compare.
10. **Fail-soft:** a 404 shard, a malformed shard, and a rate-limit each degrade to the
    existing `Notice`/banner UX.

### Non-Functional Tests
1. **Size ceilings:** an over-ceiling shard or total fails the export before writing
   anything (no partial tier).
2. **Feature-detect:** with `DecompressionStream` unavailable, the SPA shows a message
   rather than throwing.
3. **Network-free SPA tests:** the vitest suite runs against the baked dev fixture with no
   real fetch.

## Dependencies
- **External Services**: GitHub `raw` + git-trees API (unauthenticated), as #49.
- **Internal Systems**: `#49` scores tier + `export_results.py` loaders; the `#49` SPA
  seams (`ResultsRegion`, `results.ts`, `github.ts`, `resultsModel.ts`, `scoreColor.ts`,
  `searchParams.ts`); the raw run roots under `tmp/judging-runs/`.
- **Libraries/Frameworks**: Python `gzip`/`json` (stdlib), `typer` (existing CLI);
  SPA — React 19 / TanStack Query & Router / Zod / Tailwind / HeroUI (existing stack);
  browser `DecompressionStream`.

## References
- Issue #51 + the two architect comments (deep-read of jaleesbench + binding spec inputs).
- taqwabench retro: `/Users/mwk/Development/fftn/taqwabench/tmp/jaleesbrowser-retro-multibench.md`.
- Reference export: `/Users/mwk/Development/fftn/taqwabench/jaleesbench/jaleesbench/export_web.py`.
- Reference viewer: `/Users/mwk/Development/fftn/taqwabench/apps/jaleesbrowser/src/`
  (`datasource.ts:70-84` = the gunzip sniff to carry verbatim; `contract.ts` = the
  generic data model to adapt).
- #49 in this repo: `results/README.md`, `workflows/analysis/analysis/export_results.py`,
  `apps/multibrowser/src/{components/ResultsRegion.tsx,lib/results.ts,lib/resultsModel.ts,
  lib/github.ts,lib/scoreColor.ts}`.
- Contract to author: `results-raw/README.md`.

## Risks and Mitigation
| Risk | Probability | Impact | Mitigation Strategy |
|------|------------|--------|-------------------|
| Committed raw tier grows repo history on each refresh (gz doesn't delta) | High | Medium | Per-scenario granularity + determinism → only changed scenarios' shards rewrite, the rest are no-op commits; low refresh cadence; document the tradeoff in `results-raw/README.md`; git-LFS noted as a future lever if growth bites. |
| Raw tier and score tier drift apart | Low | High | Both tiers call the same `resolve_judgments`/alias maps; a parity test asserts raw verdicts == resolved judgments and the cell mean reconciles with the `results/` slice. |
| Double-gzip ambiguity corrupts shards on some hosts | Medium | High | Carry the magic-byte sniff (0x1f 0x8b) verbatim; never trust Content-Type. |
| `DecompressionStream` unsupported on an old browser | Low | Medium | Feature-detect and show a message (no polyfill), per retro. |
| Guided `context_prefix` (~6.5 KB) bloats shards if repeated per cell | Medium | Medium | Dedup at export; enforce per-shard size ceiling that fails loudly. |
| Rationale quotes sensitive scenario text in a public export | Low | Medium | Sanitize at export, not in the viewer; the `license` field states terms. |
| SPA tests coupled to the network | Medium | Medium | Baked `--limit` dev fixture; all viewer tests read the fixture. |

## Expert Consultation
**Date**: 2026-08-06
**Models Consulted**: Pending — porch will run the SPIR spec CMAP (Codex + Claude per this
repo's per-phase consult config). Additionally, the architect has arranged a
**cross-workspace pre-gate review by the taqwabench architect** (who authored the retro);
this spec will be shared before the `spec-approval` gate.
**Sections Updated**: (to be filled after consultation.)

## Approval
- [ ] Technical Lead Review
- [ ] Product Owner Review (Waleed)
- [ ] Cross-workspace review (taqwabench architect)
- [ ] Stakeholder Sign-off
- [ ] Expert AI Consultation Complete

## Notes
- This spec deliberately confines itself to WHAT/WHY. The exact shard document shape,
  the choice between extending `analysis export` vs. a sibling `export-raw` command, the
  `context_prefix` pool location, and the SPA component decomposition are Plan-phase
  decisions, seeded by the *Open Questions* above.
- The `context_prefix` and "sibling command" decisions are the two most likely to move in
  the cross-workspace review; they are flagged as Important open questions rather than
  frozen, per the architect's request to run that review pre-gate.
