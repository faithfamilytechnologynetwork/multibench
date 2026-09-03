# Review: Extend the 20260803 Opus validation layer to the full grid (stated+guided) and re-export

**Spec**: [codev/specs/110-extend-the-20260803-opus-valid.md](../specs/110-extend-the-20260803-opus-valid.md) ·
**Plan**: [codev/plans/110-extend-the-20260803-opus-valid.md](../plans/110-extend-the-20260803-opus-valid.md) ·
**Closes**: #110 (and #96, earn `full_grid` from coverage)

## What was built

Four phases in one PR:

1. **Exporter refactor (`workflows/analysis`, #96).** `full_grid` is now **earned from coverage**
   (tolerant: all three framings ≥ `FULL_GRID_MIN_COVERAGE = 0.95`) instead of a static
   `JUDGE_UI` flag; ranking eligibility became a separate static **`rankable`** (Gemini only); a
   per-judge **`coverage`** fraction is emitted. Both the score exporter (`export_results.py`) and
   the streaming raw exporter (`export_raw.py`) share the coverage contract (pinned to
   `_coverage_summary`'s scope=full/pressure=all slicing) and both enforce **exactly one
   strictly-complete rankable judge**. `resolve_judgments` gained deterministic `(priority, ts)`
   source precedence (base **and** v2), so a full-grid layer wins any same-judge overlap. Coverage
   denominators use the report-**declared** subject universe. 34 new/updated tests.

2. **SPA rewire (`apps/multibrowser`).** `rankingJudgeModel` and every default/label/prose
   ranking-proxy site key off `rankable` (with a `?? fullGrid ?? gemini` fallback so pre-#110 and
   the untouched `20260813-protestantism` manifests still rank Gemini); `fullGrid` keeps
   coverage/sample-caption semantics. `loadCommitted()` carries `rankable`/`coverage` through
   (else the sealed parity test would flip to Opus after re-export). New `isRankingJudge` /
   `classifyJudgeRoles` helpers + tests, incl. a real full-grid-Opus UI test.

3. **In-place re-export.** `results/20260803` + `results-raw/20260803` regenerated from the four
   roots. Opus earns `full_grid:true`, `rankable:false`, `coverage:0.999422`; Gemini
   byte-identical.

4. **Paper artifacts + numbers summary.** Committed
   `docs/analysis/110-dual-judge-fullgrid-summary.md` and the reproducible generator
   `docs/analysis/110-dualjudge-fullgrid-figs.py`; regenerated `fig_dual_judge.pdf` +
   `tab_dualjudge_{tier,agree}.tex` into `../multibench-papers/` (uncommitted).

## Verification evidence (against the spec's Success Criteria)

- **SC1** — `results/20260803` manifest: Opus `{full_grid:true, rankable:false, coverage:0.999422}`,
  Gemini `{full_grid:true, rankable:true, coverage:1.0}`. ✓
- **SC2** — Gemini `means`/`steadfastness` sub-trees **byte-identical** across all 7 shards (git
  HEAD vs re-export); manifest diff confined to `judges`/`counts`/`fingerprint`/`generated_at`. ✓
- **SC3** — score & raw manifests stamp the same `fingerprint` (`sha256:4143f4a4…`). ✓
- **SC4** — `test_committed_dataset_reconciles_with_paper` + sealed parity green against the
  re-exported data (250/254 with launch data reachable; skips only in the bare worktree). ✓
- **SC5–7** — export + SPA tests (both-sides threshold, static rankable, strict/one-rankable
  fail-fast, `(priority, ts)` incl. v2, cross-tier agreement, declared-subject denominator; SPA
  ranking-by-rankable, legacy fallback, full-grid-Opus UI). Dispatcher green: `workflows/analysis`
  pytest + `apps/multibrowser` vitest (394). ✓
- **Dedup** — all **8,996** sample↔full-grid overlaps (772 genuinely disagreeing) resolve to the
  full-grid verdict. ✓
- **SC8–9** — dual-judge agreement (93,385 matched cells): overall r=0.833, bias −0.031, 94.0%
  within ±0.5; unstated 0.854 / stated 0.825 / guided 0.683 (ceiling compression); identical
  5-model order under both judges in all framings — reproduces the pre-registered expectations.
  New full-grid Opus spend **$1,313.29** usage-computed. ✓

## Deviations from the issue's pre-run estimates (computed exact from data)

The architect's instruction was to compute exact figures, not assert the estimates:

- **Residual 35**, not 79 or 39: 26 unstated + 9 stated/guided (39 = the full-grid **run alone**;
  the retained sample back-fills 4). Judge-side (empty response → `json.loads('')`), cause per #116.
- **Matched cells 93,385**, not 93,341 (issue estimate).
- **Opus committed 40,114 → 93,385**; the paper's published **42,711** is 40,114 + the 2,597 route
  bridge (not an estimate).
- **Programme total 137,931 → 191,202** (paper convention: 93,420 + 95,982 Opus + 1,800 pilot).
- **Spend $1,313.29** new full-grid / **$2,381.98** total Opus, vs the ~$1,220 estimate.

## Consultation Feedback

3-way per-phase consult was `[codex, claude]` (Gemini can't see the worktree here). Every phase
reached unanimous APPROVE; dispositions:

- **Spec/Plan** — both REQUEST_CHANGES; addressed (rebuttals in `codev/projects/110-*/`). Surfaced
  and the architect **resolved** the load-bearing contradiction: strict `full_grid` is unachievable
  for Opus (unstated already 15,551/15,570), so `full_grid` is tolerant-earned + `rankable` is the
  separate ranking gate, plus a per-judge `coverage` fraction and both-sides-of-threshold tests.
- **phase_1** (3 iters) — fixed a real **v2-priority bug** (sample's 20 `judgments_v2` rows could
  override full-grid), `--limit` coverage truncation, and the observed-vs-declared subject
  denominator; **conceded** the raw tier should enforce exactly-one strictly-complete rankable
  (my genericity objection was wrong — AFB bypasses `_catalog_doc`).
- **phase_2** (3 iters) — replaced a tautological #50 test with a real full-grid-Opus UI test;
  fixed the drill role word + a prose site that goes false post-#110; role-accurate review prose.
- **phase_3** (2 iters) — data verified correct on every SC by both; fixed the README schema
  tables (earned/rankable/coverage split; ranks on rankable not full-grid; full-scope coverage).
- **phase_4** (3 iters) — agreement stats + spend verified exact by both; fixed the `tab:djtier`
  shape (I'd wrongly reshaped the paper's 6-col tier×framing table), the route-bridge count
  (2,597) + programme total (191,202), the spend (include the sample's v2 re-judges → $2,381.98),
  `.tex` conventions (signed, U+2212, full tier labels), and persisted the generator; added the
  full paper-edit handoff. Residual minors (`.bak` snapshot wording, an inline cost-model pointer)
  applied at review.

## Architecture Updates

- **HOT** (`codev/resources/arch-critical.md`) — refined the Results-datasets fact: the leaderboard
  ranks on the single **`rankable`** judge; **`full_grid` is a separate earned coverage badge**
  (#96) that never confers ranking; per-judge `coverage` is emitted; both exporters enforce
  exactly-one strictly-complete rankable. (Refinement of an existing fact — no net growth.)
- **COLD** (`codev/resources/arch.md`) — nothing new; the Spec 49/51 sections already describe the
  tier shape, which is unchanged apart from the additive `rankable`/`coverage` fields.

## Lessons Learned Updates

- Routed to **COLD** `codev/resources/lessons-learned.md` (the hot lessons file is at its cap):
  (1) a tier that *publishes* a metadata flag should validate it to the same bar as the authority
  that consumes it (the raw catalog now enforces the ranking invariant, not just the score
  manifest); (2) paper-figure deliverables must match the paper's LaTeX **shape and conventions**
  (column count, signs, U+2212, labels), not merely carry correct numbers, and their generators
  must be **persisted/committed** for reproducibility; (3) verify a reviewer's premise against the
  code before rebutting — my "genericity" objection was weaker than claimed and cost an iteration.
- The existing hot lessons already cover "compute exact actuals, never estimates" and "reconcile
  derived numbers in the canonical code" — both load-bearing here (matched cells, residual, spend,
  programme total).

## Handoff to the architect (post-merge)

- **Railway re-bake (yours):** `railway up --no-gitignore` from `apps/multibrowser` after merge, so
  the baked raw bundle is built from `main`. `results-raw/20260803` rewrote all 519 gz shards
  (~132 MB); until the re-bake the baked bundle is fingerprint-stale and `resolveRawSource` fails
  safe to the committed GitHub tier.
- **Paper wiring:** the dual-judge figure/tables are regenerated into `../multibench-papers/`
  (uncommitted). The summary's "Paper edits" section lists every prose/caption/count/cost site to
  update, and flags that `tmp/paper_figs_multibench.py` still emits the sample-era dual-judge
  artifacts (a standard re-run reverts them) — its dual-judge section should defer to
  `docs/analysis/110-dualjudge-fullgrid-figs.py`.

## Flaky tests

None. (The six real-data reconciliation tests `skipif` when `tmp/judging-runs/` is absent — a
worktree gap, not flakiness; verified out-of-band via a `tmp -> ../../tmp` symlink: 254 pass, 0
skipped.)
