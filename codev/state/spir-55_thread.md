# spir-55 thread — /results leaderboard v2 (jaleesbrowser-style dense table, multi-faith)

## 2026-08-06 — Specify phase, orientation

**Task:** Replace #49's `/results` leaderboard *presentation* (selector-driven, one metric at a
time) with the jaleesbrowser dense-table model (whole picture at a glance), extended with
MultiBench's tradition dimension. #49's DATA tier + export stay — this is **UI + client
aggregation only**.

**Reference read (taqwabench/apps/jaleesbrowser):**
- `leaderboard.ts` — one row per subject; headline Initial/Post/Δ computed on the FIRST
  breakdown-axis value only (unstated), NEVER pooled across framings (their issue #19 lesson);
  per-framing breakdown columns; canonical order = first-framing post desc.
- `components/Leaderboard.tsx` — click-to-sort every column; Rank column always shows CANONICAL
  rank (re-sort never re-numbers); nulls last; click model → detail.

**MultiBench data (already committed, #49):** `results/20260803/` — manifest + 7 per-tradition
shards. 7 traditions, 5 subjects. Shard `means[judge][subj][framing][turn1|full][pressure]` and
`steadfastness[judge][subj][framing][pressure]` — EVERY slice the jaleesbrowser headline needs is
already present. Confirmed: **no export change needed.**

**Reusable #49 code:** `lib/leaderboard.ts` (`computeStandings`, `subjectTraditionValues`,
`traditionValue`, `rankingJudgeModel`, `judgeModelForKey`) + `lib/resultsSelection.ts` (URL
machinery) + `scoreColor`. The rewrite is `ResultsPage.tsx` presentation + extending the
selection model with sort/expansion; the pure compute stays.

**Key correctness decision to bake:** Δ headline column = mean of per-tradition **steadfastness**
(matched-cell, from shard), NOT (Post − Initial) — the two differ because post/turn1 means cover
possibly-different matched cells. Issue says so explicitly.

**Coordination:** #51 (raw-results browser) is a SEPARATE route family + its own contract; #49
score/leaderboard tier stays MB-specific. Shared app → rebase discipline, no touching #51's raw
tier. #49 verify gate parked; close #49 when this lands.

Writing the spec now.

## 2026-08-06 — Specify iter 1 consultation (codex + claude, both REQUEST_CHANGES, HIGH)

Both high-quality, converging. Claude verified data/reuse claims against actual shards + code.
Incorporated all: pressure now reframes WHOLE table (headline+framing+strip+rank) at selected
pressure (default all); canonical rank recomputed at selected pressure; **Δ-distinctness test
re-scoped to a synthetic fixture** (Claude's catch: all 34 shard-steadfastness≠full−turn1 cells are
Opus; Gemini identical in all 1470 — grid complete); heat strip built from computeStandings'
returned `contributions` (by-construction mean==Post, not a 2nd aggregation); drill-down columns
defined (per-tradition Initial/Post/Δ + framings); sortable = numeric cols only + tie-break; heat-strip
accessibility (title/aria-label, keyboard expand, non-color empty, narrow-viewport scroll); k/N
coverage visibility; Δ reuses −1…+1 ramp which CLAMPS (verified scoreColor.ts); dropped
coverage-% gate (no provider) → suite-green + new tests; stale ?metric/?framing ignored.
Committing iter-2, re-running consult.
