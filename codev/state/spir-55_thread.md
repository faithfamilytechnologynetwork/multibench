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

## 2026-08-06 — Spec approved (gate cleared by Waleed). Plan phase.

Architect confirmed spec approval + coordinate-with-#51 reminder (scope to /results leaderboard
components + client aggregation, rebase at PR). Wrote plan: 4 phases —
1) pure client aggregation (computeLeaderboardRows/sortRows/subjectDrilldownRows; additive to
   leaderboard.ts; reconciliation + Δ-fixture + strip==Post all verified before any UI consumes it),
2) dense sortable table + URL state (resultsSelection gains sort+expanded, drops metric/framing;
   ResultsPage swap; pressure reframes whole table incl. rank),
3) multi-faith layer (heat strip from contributions + click-to-expand drill-down + judge selector
   Opus-badged-never-reranks + a11y: aria/title, keyboard expand, non-color empty, scroll wrapper),
4) docs + #49 supersession flag + live railway smoke.
Files confined: leaderboard.ts, resultsSelection.ts, ResultsPage.tsx, their tests, 2 READMEs. No
contact with #51 raw tier / #49 export. Committing, running plan consult.

## 2026-08-06 — Plan iter 1 consultation (codex + claude, both REQUEST_CHANGES, HIGH)

Central catch (both, verified): leaderboard.ts:66,88 use Pick<ResultsSelection,"framing"|"metric"|
"pressure"> → Phase 2 dropping those fields breaks it, and NOTHING typechecks in the gate (porch check
= vitest only; vite build = esbuild; check-types exists but unrun). Fixed: Phase 1 now decouples to a
`Slice` interface BEFORE Phase 2; check-types added to every phase's acceptance (per-phase DoD, not
the shared dispatcher — flagged dispatcher gap to architect as out-of-scope follow-up).
Other fixes: byFraming → id-keyed Record (Codex: sort by framing id); heat strip → manifest-aligned
`strip` field with value:null for uncovered traditions (Claude: contributions is sparse, can't yield
empty cells; mean over non-null still == post); subjectDrilldownRows → nullable per-slice fields +
inclusion=any-non-null + coverage-from-Post-slice (Opus sample path); test-plan corrected (no
"kept" additive-publish/403 tests — those live in results.data.test.ts; page reconciliation → display-
precision formatting test; API-budget call-log owned by Phase 2); Phase 2 removes opus-caption as
one clean unit + reframed as intermediate non-shipped state; Post==framings[0] visual-grouping note.
Rebuttal written. Committing iter-2, signaling done → plan-approval gate.

## 2026-08-06 — Plan iter 2 (Codex REQUEST_CHANGES, Claude COMMENT — iter-1 fixes verified). All incorporated.

Codex: (1) add run selector UI + two-run switch test (spec TS11 had no page affordance); (2) drill-down
coverage — nExpected always manifest-derived, nJudged from Post slice or null (—/N), inclusion any-non-null.
Claude (verified source, moved to COMMENT): (1) POSITIONAL-ZIP BUG — computeStandings returns per-column
sorted arrays; row builder must join by subject id (Map), not index (passes post-only test but misattaches
Initial/Δ/framing); added column-attribution test. (2) drop judgeModel from computeLeaderboardRows →
hardwire rankingJudgeModel (judge-never-reranks now structural). (3) byFraming all-keys for
noUncheckedIndexedAccess. (4) Phase 4 smoke → local pnpm build && preview (REF=main, identical runtime
path), prod railway up AFTER merge. Minor: retain #49 drill-down in Phase 2 via Slice literal (no dangling
opus-caption), Phase 3 upgrades it; strip pressure-reframe test. Rebuttal written. Committing iter-3,
signaling → plan-approval gate.

## 2026-08-06 — Plan approved (Waleed). Implement phase_1 DONE.

Phase 1 (pure client aggregation) implemented in leaderboard.ts:
- Slice interface + migrated the two Pick<ResultsSelection,...> sites (structural; all 153 pre-existing
  tests still green → decouple confirmed).
- computeLeaderboardRows (NO judgeModel param — ranking judge hardwired; by-subject-id column join,
  not positional zip), sortRows (numeric cols, nulls-last both dirs, ties by subject, rank untouched),
  isSortableColumn, subjectDrilldownRows (nullable per-slice, inclusion=any-non-null, coverage nExpected
  manifest-derived / nJudged from Post-slice-or-null), StripCell/LeaderboardRow/DrilldownRow types.
- Heat strip = Post contributions left-joined to manifest.traditions (null cell for uncovered).
Tests: +12 (positional-zip guard via crossing post/initial orderings; strip 1:1 + mean==post; Δ-distinct
fixture + Gemini-grid coincidence on committed data; sortRows nulls/ties/rank; drilldown Opus-sample path).
check-types green; full suite 165 passed. Only leaderboard.ts + leaderboard.test.ts touched.

## 2026-08-06 — Phase 1 impl consult (codex + claude, both RC — test completeness only)

Claude verified impl well-built + both gates green; RC items were TEST gaps, no behavior change:
- Column-attribution now covers delta + every framing (fixture where each column ordering differs).
- Added computeLeaderboardRows paper reconciliation on committed data (post==paper.unstated + strip
  len 7 + mean(non-null strip)==post) — Phase 2 defers exhaustive reconciliation here.
- sortRows now tests every numeric key both directions + null-among-non-nulls.
- Extracted loadCommitted() helper (dedup ~40 lines); comment at strip join re: tradition-id key match.
check-types green, 166 tests. Rebuttal written. Re-running porch done.

## 2026-08-06 — Phase 1 APPROVED (codex + claude, both APPROVE/HIGH).

Made the cheap non-blocking improvements both flagged: replaced brittle computeLeaderboardRows.length
proxy with a behavioral test (Opus data changes no row); asserted uncovered strip nJudged===0; added
drill-down inclusion via a non-first-framing slice (framings.some branch). 167 tests green.

⚠️ SCOPE-LEAK (PR-time, architect's call): d0fa576 "[Docs] paper drafts" is the branch base and is NOT
on origin/main → 27 docs/paper/* files would ride in my PR. This is the known branch-from-local-HEAD
leak. Plan: rebase spir-55 commits onto origin/main at PR prep (Phase 4) so the PR carries only my
changes. Flagged to architect. NOT rebasing mid-implement.

## 2026-08-06 — Phase 2 DONE: dense sortable table + URL state (presentation swap).

resultsSelection.ts: new shape {runId, judge, pressure, sort:{key,dir}|null, expanded[]} — dropped
framing/metric; parseSort (headline|framing-id validation, dir defaults desc, invalid→null; framing
ids accepted optimistically w/o manifest since page re-parses); parseExpanded (dedupe/trim); stale
?framing/?metric ignored. ResultsPage.tsx: dense board — computeLeaderboardRows→sortRows; columns
#|Subject|Initial|Post|Δ|<framings>|Traditions(k/N from non-null strip); sortable numeric headers
(aria-sort, desc→asc toggle) w/ persistent canonical rank; NEW run selector (when >1 run); pressure
reframes whole table; RETAINED #49 drill-down + judge selector + opus-caption via Slice literal
{framings[0],full,pressure} (no dangling caption); caption noting Post==first-framing column.
results.test.tsx: +geminiTurn1 so Initial-sort reorders; rewrote metric/framing-selector tests →
dense-columns, sort+persistent-rank, stale-param, run-switch (2 runs), API-budget call-log (1 tree,
0 results-via-api, shards via raw). resultsSelection.test.ts rewritten for new shape.
check-types green; 171 tests. Only the 4 intended files touched. expanded[] wired to URL in Phase 3.

## 2026-08-06 — Phase 2 impl consult (codex RC, claude COMMENT). All 3 incorporated.

Claude verified all deliverables present + 171 green; issues were 1 real bug + 2 refinements:
1. (real bug) SortHeader was defined inside Leaderboard render body → new component identity each
   render → <th>/button remount → keyboard focus lost after sort. HOISTED to module scope w/ props.
2. Vocabulary dedup: HEADLINE_SORT_KEYS (resultsSelection) vs HEADLINE_KEYS (leaderboard). Moved
   `type Metric` → resultsModel (breaks leaderboard→resultsSelection edge), resultsSelection now
   imports isSortableColumn+SortDir from leaderboard = single source of truth; re-exports for consumers.
3. (codex blocking) pressure-reframe test only checked Post; gemini had no secularize data so rank
   couldn't change → unobservable. Added false_authority fixture (sonnet 0.1/gemini 0.9 flips order) +
   test asserting headline reframe + RANK recompute (gemini→1, sonnet→2) + framing col reframe (stated→—).
check-types green, 172 tests. Touched resultsModel/leaderboard/resultsSelection/ResultsPage/results.test.

## 2026-08-06 — Phase 2 APPROVED (codex COMMENT, claude APPROVE).

Only non-blocking note: drill-down colSpan is one short — should be `5 + framingCols.length` (currently
4+F). Header = 6+F cols; drill row = <td/> (rank) + <td colSpan> over remaining 5+F. FOLDING INTO PHASE 3
(which rewrites the drill-down into the dense per-tradition sub-table — colSpan set correctly there).
Also Phase-3 TODO: wire sel.expanded to URL (currently useState, ?expanded inert). Phase-4 TODO: rebase
onto origin/main (docs/paper leak). Advancing to phase_3.

## 2026-08-06 — Phase 3 DONE: multi-faith layer (heat strip, dense drill-down, a11y).

ResultsPage.tsx: HeatStrip component (module scope) — one scoreColor square per row.strip cell, manifest
order; title+aria-label "<tradition>: <value>"/"no data" (color never sole encoding); null cell = dashed
border + data-empty. Strip lives in the Traditions column beside k/N; recomputes with pressure (part of
row). Drill-down UPGRADED: subjectDrilldownRows → dense sub-table (Init/Post/Δ + framings + Coverage),
—/N when Post numerator null, sample-badge for Opus. Expansion moved to sel.expanded (URL) via
onToggleExpand → update() — keyboard-operable (aria-expanded), deep-linkable. colSpan bug fixed: drill row
now single full-width <td colSpan={6+F}> (no off-by-one). Judge selector retained (headline/strip stay
Gemini). Table wrapped in overflow-x-auto (leaderboard-scroll).
Tests +5: heat strip labels+empty+pressure-reframe; dense drill columns; keyboard-expand+URL round-trip;
deep-linked ?expanded; —/N via non-Post slice; scroll-container. check-types green, 177 tests. Only
ResultsPage.tsx + results.test.tsx touched. Phase-2 colSpan note RESOLVED here.

## 2026-08-06 — Phase 3 impl consult (codex RC blocking, claude APPROVE). Fixed.

Codex blocking: ?expanded=bogus retained → parseExpanded now filters to manifest.subjects when present
(+ test: bogus dropped, no round-trip survival). Claude a11y (good): aria-label on role-less span is
ignored → added role="img" to strip cells. Claude minor: Traditions header title added. Deferred to
Phase 4: remove now-app-dead subjectTraditionValues export+test (replaced by subjectDrilldownRows).
check-types green, 178 tests. Touched resultsSelection(.test) + ResultsPage.

## 2026-08-06 — Phase 3 APPROVED (codex + claude, both APPROVE). Advancing to phase_4.

Phase-4 checklist (docs + cleanup + polish + verify):
- Remove app-dead subjectTraditionValues export + its test (replaced by subjectDrilldownRows).
- Claude minor polish: add test asserting heat strip unchanged on judge→Opus (structural, but pin it);
  test the collapse path of onToggleExpand; add aria-controls to expand button + unique strip-group
  aria-label per row.
- Docs: apps/multibrowser/README leaderboard section; results/README "Results explorer" bullets → v2.
- #49 supersession note (close #49 + retire its verify gate — architect action, flag it).
- Rebase spir-55 commits onto origin/main (drops docs/paper leak) at PR prep.
- Local `pnpm build && pnpm preview` smoke.

## 2026-08-06 — Phase 4: docs + cleanup + polish + smoke.

Cleanup: removed app-dead subjectTraditionValues (export + test); fixed the stale comment referencing it.
A11y polish (claude minors): unique strip-group aria-label per row (`Per-tradition scores for <subject>`);
aria-controls on expand button → sanitized drill row id; +2 tests (heat strip unchanged on judge→Opus;
collapse path removes drilldown + clears URL). Docs: apps/multibrowser/README leaderboard section →
dense-table v2 (headline/framing columns, heat strip, sort, canonical rank, pressure reframe, drill-down,
deep-link params) + fixed stale ?framing/?metric URL example; results/README "Results explorer" bullets → v2.
Smoke: `pnpm build` OK (bundle builds); `pnpm preview` serves /results SPA shell (200 + root div + JS) via
fallback; deploy.test REAL smoke green in suite. check-types green, 179 tests. PR prep TODO: rebase onto
origin/main (drops docs/paper base leak); #49 supersession note in PR/review.

## 2026-08-06 — Phase 4 iter-1 (codex RC, claude COMMENT): PR-prep items. Addressed.

Blockers were all PR-prep: (1) REBASED onto origin/main via `git rebase --onto origin/main d0fa576`
(backup ref backup-spir-55-prerebase; 40 commits clean, 0 conflicts — verified my commits touch 0
docs/paper|experiments files, 0 overlap with origin/main). Branch diff now = only my 9 files
(apps/multibrowser/* + results/README). docs/paper+experiments dropped. 179 tests still green, deps
unchanged, porch state intact. (2) #49 supersession note → written in codev/reviews/55-*.md. (3)
interactive smoke: honestly documented — 20 integration tests over byte-faithful GitHub stand-in +
build + shell-serve; live click-through is post-merge Railway (per plan). Minors: aria-controls gated
on open; README run-selector mention. Re-signaling for iter-2 consult.

## 2026-08-06 — Phase 4 iter-2 (codex RC on interactive smoke, claude APPROVE). Doc minors fixed + real-data-path verified.

Fixed 3 doc minors (review rebase→past tense; multibrowser README explorer heading → "#49 data tier;
#55 v2 presentation"; results/README run-selector mention). Verified the REAL GitHub runtime data path
live: main SHA 7f2c34c → recursive git-tree (non-truncated) lists all 8 results/20260803 files →
raw manifest parses (5 subj/7 trad) + sunni-islam shard parses (2 judges). This is the SPA's actual
runtime dependency, confirmed end-to-end.

BLOCKER (Codex): the plan's "manual local-preview browser click-through against real GitHub" is the ONE
thing a headless builder can't do (no real browser). Evidence assembled: 20 integration tests over
byte-faithful GitHub stand-in + build + shell-serve + real-data-path curl check. Escalating to architect
for the decision Codex itself offers ("obtain an explicit plan exception"): accept automated evidence +
defer live click-through to post-merge Railway (plan sequences prod railway up after merge), OR require a
human click-through pre-merge. NOT looping porch (would just re-block on the same unsatisfiable-headless item).

## 2026-08-06 — PLAN EXCEPTION GRANTED (architect). Proceeding to PR.

Architect accepted the automated evidence (20-test suite + build/preview + verified real data path @
7f2c34c); pre-merge live click-through deferred to post-merge Verify. Recorded in review doc: exception
+ evidence + rationale + ACCEPTANCE CRITERION = Waleed's approval of the LIVE leaderboard look-and-feel
after post-merge railway up; #55 AND parked #49 verify gate stay open until he confirms; his changes =
follow-up iterations, not scope creep. Flow: PR → architect integration review (expect high-risk CMAP,
it rewrites /results UX) → pr gate to Waleed. Committing exception, then opening PR.

## 2026-08-06 — Review-phase consult (codex RC, claude APPROVE). Fixed + PR pushed.

Codex real bug: malformed runs were selectable → picking one blanks the page (manifest null hides the
selector too) w/ no recovery. FIXED: knownRunIds + selector options now from selectableRuns (manifest
!= null); malformed ?run falls back to newest valid, notice still surfaces. +regression test (3-run
fixture: 2 valid + 1 malformed-newest). Codex #2: spec/plan Status draft→approved + approval boxes
checked (Success Criteria boxes stay unchecked — acceptance = Waleed's post-merge live approval per
exception). Claude latent nits documented (DEFAULTS.pressure hardcode / sort-key namespace / stale
run-switch params) — non-blocking, rationale in rebuttal. 180 tests green. Pushing to update PR #59.

## 2026-08-06 — Architect integration CMAP: gemini+claude APPROVE, codex RC OVERRULED. 3 items done.

Architect overruled codex's per-column-coverage RC (the #50 earned-full_grid invariant → whole-shard
exclusion uniform across columns → single k/N valid). Applied 3 required: (1) code comment at k/N
derivation documenting the full_grid dependency (revisit if invariant relaxes); (2) overrule rationale
recorded in review doc; (3) spec/plan Status draft→approved (done prior commit). Optional nits folded:
scope="col" on all table headers (main + drill sub-table); void rows (nContributing===0) muted
opacity-50 + data-void. 180 tests green. Pushing to PR #59, pinging architect → pr gate to Waleed.

## 2026-08-06 — Architect correction: void-rows nit was DEAD CODE. Fixed.

Misread "void rows" nit = dead `void rows;` no-op at results.test.tsx:255 (+ its unused `let rows`).
Removed (kept the await for render sync). My opacity-50/data-void addition: architect KEEPS it (honest
degradation) but wanted it tested + documented. Added test "mutes a zero-contribution subject row"
(Qwen data-void=true + opacity-50; sonnet not void). Noted in review doc as reviewed-and-kept deviation.
181 tests green. Pushing to PR #59, pinging architect → pr gate to Waleed.

## 2026-08-06 — Verify iteration 1 (Waleed live feedback): heat-strip tooltip. Follow-up PR.

Waleed wants a real hover+focus tooltip per strip square (not bare title): display name + Post/First/Δ
+ contributing n at current pressure, e.g. "Sunni Islam — Post +0.44 · First +0.62 · Δ −0.18 · 140
scenarios". Implemented on new branch builder/spir-55-strip-tooltip off origin/main:
- Enriched StripCell w/ initial+delta from the SAME computeStandings headline calls (no 2nd aggregation
  path — kept the full Standing[] for turn1/steadfastness, joined contributions per tradition).
- HeatStrip: each square focusable (tabIndex=0, role=img) w/ FULL summary in aria-label (SR gets it
  w/o interaction) + visual tooltip (role=tooltip) on hover OR keyboard focus. title-case display name.
  fmtSigned (+0.60/-0.18). "N scenarios" = nJudged (strip is Gemini full-grid).
- Chose a lightweight custom tooltip over HeroUI's (react-aria portal + focusable-trigger + hover-delay
  is heavy for a 7x5 tiny-square grid + harder to assert in jsdom) — FLAGGING the choice in the PR for
  architect review. Numbers consistent w/ drill-down (same source), tested.
Tests: rewrote heat-strip label test to rich format; +tooltip test (hover+focus+drill-down consistency);
+strip initial/delta unit assertion. 182 tests green, check-types + build OK. This is verify iter-1 on
OPEN #55 (not scope creep). PR against main → architect low-risk review → merge → redeploy → Waleed re-check.

## 2026-08-06 — Verify iter2 (Waleed live screenshot): 2 tooltip defects. Fixed.

(1) UNIT MISLABEL: "312 scenarios" was 52×6 judged CELLS. CHOSE to show true n_scenarios labeled
"scenarios" (reader-friendly, correct, pressure-stable; strip is Gemini full-grid so all covered) —
NOT "cells". Added StripCell.nScenarios (from manifest t.nScenarios); tooltip + aria-label use it
(singular/plural). Test now distinguishes: fixture "all" cell n_judged=12 (2 scenarios×6 pressures)
so "2 scenarios" proves nScenarios not nJudged (+ not.toContain "12 scenarios"); drill-coverage 2/12→12/12.
(2) EDGE CLIPPING: custom tooltip added edge-aware positioning — useLayoutEffect measures at neutral
translateX(-50%) and clamps within viewport (shift left/right); inert in jsdom (0-rects), verified by
inspection per architect. 182 tests green, check-types + build OK. Branched off origin/main (has #60).

## 2026-08-06 — Verify iter3 (Waleed screenshot tmp/tooltip-iter3.png): tooltip TRANSPARENT (text bled through header).

Root cause (from screenshot + reasoning): tooltip used `bg-default-900 text-default-50` classes, but
HeroUI v3 has NO `default-900` shade → the class generated no rule → transparent panel. Score cells /
badges render fine because they use INLINE style (scoreColor) — proven-working mechanism. Was always
broken; iter2's positioning shift put the tooltip over the header text, making the transparency glaring.
FIX: replaced bg-default-900/text-default-50 classes with inline concrete colors (bg #18181b, text
#fafafa, subtle border) + z-30. Same inline-style mechanism as the (visibly-working) score cells →
guaranteed opaque. +regression test (tip.style.backgroundColor/color not empty). Positioning (iter2)
untouched — screenshot showed it renders (not clipped), only the surface was missing. 251 tests green,
check-types + build OK. Branch off origin/main (has #51/#54/#61). NOTE: can't drive a real browser
headless; verifying via inline-style-parity-with-working-cells + tests + build. Deploy: architect asked
me to railway up — checking CLI availability; will report.

## 2026-08-06 — iter3: PR #65 open; railway BLOCKED (no linked project).

railway CLI installed + logged in (Waleed), but `railway status` = "No linked project found". Can't
`railway up` without `railway link` (needs project ID I don't have) — and it'd deploy an UNMERGED branch
to the single prod service (architect's domain for iter1/2). Reported to architect: fix+verify+PR done,
need them to link/authorize or redeploy. porch NOT advanced (architect said don't until Waleed confirms).
