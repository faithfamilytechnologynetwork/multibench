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

### Phase: drafting spec now.
