# spir-49 — multibrowser: results explorer (judge & pressure selectors + leaderboard)

Builder for Spec 49. STRICT mode (porch-orchestrated). Started 2026-08-05.

## Phase: Specify (in progress)

Spec file did not exist at spawn — writing it fresh from issue #49 + reference data.

### Context gathered (pre-draft)

**Run data** (`tmp/judging-runs/` — READ-ONLY symlink to architect's data; never commit from it):
- Canonical launch set: `20260803-merged` (Gemini 3.6 Flash, full grid) + `20260803-unstated-opus`
  (Opus, unstated only, full grid) + `20260803-framings-opus-sample` (Opus, stated/guided SAMPLE).
- `framings-opus-sample` is a LIVE tail-fill (still appending) — counts are moving until architect
  seals it. It also carries the Opus alias split: `claude-opus-4-8` (batch) + `anthropic/claude-opus-4.8`
  (OpenRouter tail). Export MUST alias-normalize to one Opus judge.

**Data schema** (per tradition dir): `sittings.jsonl` (subject, tradition, scenario_id, pressure,
framing, turns[], usage) + `judgments.jsonl` (sitting_key, subject, tradition, scenario_id, pressure,
framing, judge, scope, score, direction, rationale, raw, usage). Also `report.json`/`report.md` per
tradition + `analysis-out/` (analysis_stats.json, figures, report-v2 html/pdf + stats_bundle.json).
- Grid: 5 subjects × 3 framings × 6 pressures × N scenarios (buddhism 52 … sunni-islam 140).
- `scope` ∈ {`turn1` (first-response), `full` (post-pressure)} — 2 judgments per sitting.
- Raw run = 583MB. Export target: single-digit MB, sharded per tradition, SCORES + METADATA ONLY
  (no transcript turns, likely drop rationale/raw to hit budget — open question in spec).

**Aggregation convention** (`workflows/analysis/analysis/aggregate.py` — CANONICAL, reuse it):
- cell = (subject, scenario_id, pressure, framing, scope); cell score = mean of present judges' scores.
- breakdown mean = unweighted mean of in-scope cell scores.
- headline = unstated framing, `full` scope; steadfastness = full − turn1.
- Leaderboard/standings = **mean of per-tradition means** (equal weight per tradition), per
  subject × framing × scope; matches paper Table `tab_standings`. Source: `stats_bundle.json.subj_overall`
  = subject|framing → [mean, ci_lo, ci_hi] (bootstrap CIs, seed 12345, n_boot 5000).

**SPA** (`apps/multibrowser/`, Vite6/React19/TS/Tailwind4/HeroUI v3/TanStack Router+Query):
- Already has a RESERVED inert results seam: `src/components/ResultsRegion.tsx` + `loadResults`
  in `src/lib/results.ts` (§4.1 seam for judging workflow #8). Additive slot exists.
- Data layer: `src/lib/github.ts` (SHA resolve + git-trees 1 call + raw fetch, SHA-pinned),
  `src/lib/queries.ts` (SHA-keyed), `useLatestSha` polls `VITE_SHA_POLL_MS` (5min) + focus/reconnect;
  403 → banner + cached. Unauthenticated 60/hr.
- Palette: `workflows/analysis/analysis/colors.py` — 7-stop diverging (deep red→grey-beige→deep green),
  `score_color` TwoSlopeNorm(−1,0,1) linear. Reuse for score cells.

### Explore agents (done)

**SPA map:** `/results` is a clean additive route — add one `createRoute` (+ `validateSearch`) in
`src/router.tsx` + nav link in `RootLayout`; mirror `src/lib/filtering.ts` + `searchParams.ts` for the
deep-linkable selection model; reuse `FilterBar` `Toggle`/native-`<select>` idiom for the four selectors;
fetch via existing SHA-pinned hooks (`queries.ts`, add a `loadResults`-style loader + `useResults` hook);
HeroUI v3 provider-less, semantic color tokens (no chart lib yet — leaderboard is first dataviz); test via
`fakeFetch` + `renderApp` (Vitest). Reserved seam: `results.ts`/`ScenarioResults`/`ResultsRegion`.

**JaleesBench parity:** the interactive-explorer specifics (judge/pressure selectors, `tab_standings`) are
NOT in this repo — they live in external `github.com/iaser-ai/jaleesbench`. BUT the repo gives the data
contract (Spec 8/26 §4.1), metric defs (headline=unstated/full; steadfastness=full−turn1; scope turn1/full;
numeric −1..+1, NO band names), and the reserved seam. I reconstructed + VERIFIED the standings convention
empirically (see below) — no external read needed.

### KEY VERIFIED FACT (backs the core acceptance criterion)
Leaderboard = equal-weight mean across the 7 traditions of each tradition's `by_framing[framing]` (full
scope) == paper `stats_bundle.subj_overall[subject|framing][0]`, matched to FULL precision for
unstated/stated/guided. So: export publishes per-tradition breakdown means (canonical aggregate.py); SPA's
only client math is a mean-of-per-tradition-means → guaranteed reconciliation + tiny size.

### Design chosen for spec (pre-aggregated, not per-cell)
Export = pre-aggregated per-tradition shards: subject × framing × scope × pressure(+all) × judge → {mean,
coverage(n_judged/n_expected)}, alias-normalized Opus, computed by canonical aggregate.py. + manifest
(subjects/judges/framings/pressures/scopes/counts/dates + per-cell coverage for honest Opus-sample degrade).
No transcripts, no rationale (size budget) — flagged as open Q. Per-scenario drill-down = SHOULD/limited
(size risk). Discovery: `results/*/manifest.json` via git-trees, latest by date, new run → no redeploy.

### Phase: Specify — draft committed (00a871a), 2-way consult done, revised for iter1 feedback.

Both reviewers (codex + claude) → REQUEST_CHANGES, HIGH confidence. All findings verified against real data
before incorporating. Load-bearing catches:
- **Subject-id split** (not just judge aliases): framings-opus-sample uses provider-prefixed lowercase ids;
  Qwen even drops `-Instruct` → naive merge = 10 subjects. Needs EXPLICIT subject alias map + test. (verified)
- **Tiny-non-zero Opus coverage**: secular-sage stated/full ≈ 2 cells vs sunni-islam ≈ 230 — equal 1/7 weight
  is dishonest. Added `min_coverage` rule (default 0.5) → exclude low-coverage tradition-means from
  mean-of-means, show k/7. (verified)
- **Truncation fallback** (`github.ts` walkTraditions) walks ONLY traditions/ → results/ would silently vanish
  on truncated tree. Must extend fallback + test. (verified)
- Plus: n_expected pinned to full grid; judge-vs-subject disambiguation for gemini-3.6-flash; Opus alias
  collision dedup (later-ts-wins overlay); asymmetric turn1/full → matched-cell steadfastness; exact size
  ceilings (≤8MB/run, ≤1MB/shard) for CI; runtime zod validation + schema_version; interim export permitted.

Design still Approach 1 (pre-aggregated per-tradition shards, canonical aggregate.py, SPA does mean-of-means).
Consultation Log filled. Re-committing, then porch next.

### GATE: spec-approval reached (2026-08-05) — STOPPED, waiting for human.

Wrote rebuttal (porch-tracked/gitignored, like consult outputs), ran `porch done` → `porch gate 49`.
Notified architect via `afx send`. Will NOT self-approve. Two Critical open questions surfaced to architect:
`min_coverage` threshold (default 0.5) and how Opus stated/guided ranks in the leaderboard.
Next action (after `porch approve 49 spec-approval` by human): `porch run`/`porch next` → Plan phase.

Commits so far: 00a871a (initial draft), 940d12c (with multi-agent review).

### Spec APPROVED (2026-08-06) + Plan phase.

Architect approved with simplifying decisions (folded into spec §"Approved Decisions", commit 525d843):
- **Leaderboard ranks GEMINI ONLY** (full grid). Opus never ranks; judge selector = inspection/validation
  layer only (drill-down/coverage badges where Opus data exists). Moots the Opus-ranking Critical Q.
- min_coverage no longer a ranking gate — display/badge only.
- pressure=all = cell-pooled mean (confirmed); run discovery = latest-by-manifest-date (selector optional);
  rationale = aggregates-only v1; CIs = optional SHOULD (pooled Gemini only); ResultsRegion seam = inert;
  one re-export at Opus tail-fill seal.

Gate flipped by architect (2ec8f5f). Now PLAN phase.

Dispatcher note: `.codev/checks/test.sh` ALREADY registers workflows/analysis (uv pytest) + apps/multibrowser
(pnpm test) — no dispatcher change needed. Export tool → `workflows/analysis` (Typer `export` cmd), reuses
aggregate.py.

**Plan drafted** (codev/plans/49-...md) — 6 phases: (1) export core normalization+aggregation+parity,
(2) export writer+manifest+CLI+committed dataset, (3) SPA data layer (discovery/loader/validation/truncation
fallback), (4) leaderboard route + framing/scope/pressure selectors (Gemini-ranked), (5) drill-down + judge
selector + Opus validation layer, (6) docs. Linear deps. Committing → porch done → 2-way plan consult.
