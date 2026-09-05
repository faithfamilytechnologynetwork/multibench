# Review: Two-judge mean scoring — analysis bundle, results tier, leaderboard ranking, and docs

## Summary

Rescored the benchmark of record (`20260803`) on the **equal-weight mean of both judges** (Gemini
3.6 Flash + Claude Opus 4.8) per cell — the analysis stats bundle, the committed `results/20260803/`
tier, and the `/results` leaderboard — after **completing the grid** (re-judging the Opus
empty-response cells). Six phases; PR #121 (+2 review rounds); all suites green (analysis 268,
multibrowser 411, governance 9/9, typecheck clean); reconciliation to 2.2e-16.

## Spec Compliance

- [x] AC1 — Grid completed before rescoring: 33/35 missing Opus cells re-judged; 2 residual reported, not imputed (Phase 1).
- [x] AC2 — Re-judging within budget (≤$20): measured $11.02 + est. ≤~$6 overhead; actuals recorded (Phase 1).
- [x] AC3 — Combined cell rule via `cell_scores` over all judges; single-judge cells use their lone verdict (Phase 2).
- [x] AC4 — Equivalence test: combined == mean-of-per-judge-means on double-judged sets, diverges only on single-judge cells (Phase 2).
- [x] AC5 — Documented combined-stats capability (`analysis combined-stats`) + v3 bundle produced (Phase 3).
- [x] AC6 — Additive `results/20260803` re-export: Gemini byte-identical, Opus delta bounded to the 33 recovered cells (Phase 4).
- [x] AC7 — Manifest `ranking = {rule, score_key, judges, single_judge_cells}`; `single_judge_cells` count 2, ids + attempts recorded (Phase 2/4).
- [x] AC8 — Full-grid gate re-shaped to "≥1 real judge strictly complete" in **both** exporters (Phase 2).
- [x] AC9 — Combined headline reconciliation guard (combined mean-of-means == v3 `subj_overall` ≤1e-9) (Phase 3/4).
- [x] AC10 — SPA leaderboard ranks on the combined block; Gemini/Opus selector kept; legacy fallback + malformed notices; `leaderboard.test.ts` updated; no invented combined pin (Phase 5).
- [x] AC11 — Docs + HOT mirrors updated (README ×all assertions + `ranking` row, arch-critical fact, mirrors, 110 summary) (Phase 6).
- [x] AC12 — Scope respected: no prompt/config change; only authorized spend; nothing under `traditions/protestant-unified` or #119's files.
- [x] AC13 — Per-builder suites green.

## Deviations from Plan

- **Baked #2 vs #7** (Opus block byte-identical vs re-judge adds Opus verdicts) — not resolved
  autonomously; the architect confirmed #7 governs (Gemini byte-identical; Opus changes only in the
  grid-completion cells). Phase 4 bounds the Opus diff accordingly.
- **`dual_judge` recompute** — initially planned to reuse v2's `dual_judge` verbatim; the architect
  directed a **recompute on the completed grid** (guided r 0.683→0.684 at n=93,418), with v2's
  partial-Opus block kept under `full_grid_v2_partial`.
- **Raw tier re-export added to Phase 4** — the score-tier re-export changed the shared fingerprint,
  so `results-raw/20260803` had to be re-exported too (Spec 51 cross-tier invariant).
- Otherwise the plan held.

## Consultation Feedback

Per-phase 2-way consults (`codex`, `claude`); every phase reached APPROVE (phase_1/phase_3
force-advanced on codex APPROVE once the flagged item was addressed + architect-resolved).

### Phase 1 — Complete the grid (Rounds 1–3)
- **Claude**: `judge` has no cell targeting → ~1000× overspend risk; 26 unstated gaps unreachable as planned → **Addressed** (filtered sittings + pre-spend work-count assertion; per-cell routing).
- **Codex**: runbook not reproducible (placeholder script); spend not authoritative; work-count guard not config-driven → **Addressed** (committed `results/rejudge_20260803.py` with a config-derived work-count guard; measured+bounded spend). Authoritative console delta → **N/A** (architect-accepted "not checked").
- **Both**: "strictly complete" wording vs 2 residual; stale "35"→"33"; test-in-CI gap → **Addressed**.

### Phase 2 — Combined block + ranking (Rounds 1–2)
- **Codex**: `judge_present` missing; raw exporter ranking shape; empty-`all_judges` IndexError → **Addressed** (judge_present; reduced raw ranking reconciled + plan-amended; fail-fast guard).
- **Claude**: combined key would break shard guards if inside `means`; unbounded `single_judge_cells`; stale comments → **Addressed** (combined is a separate top-level field; `SINGLE_JUDGE_CELLS_CAP`; comments fixed).

### Phase 3 — Combined stats + v3 bundle (Rounds 1–3)
- **Both**: v3 `dual_judge` built its Gemini lut from the combined `merged` → inflated agreement (r 0.854→0.956) → **Addressed** (recompute on the completed grid; `rank` subsection ported; fail-fast judge dispatch).
- **Codex**: report-flag not viable (`load_corpus`) → **Addressed** (`analysis combined-stats` over the resolve seam).

### Phase 4 — Additive re-export (Rounds 1–2)
- **Claude (blocking)**: cross-tier fingerprint drift (raw tier stale) → **Addressed** (re-exported the raw tier; fingerprints equal; `rawData.test.ts` 35/35).
- **Both**: Opus-delta test too weak; no committed↔v3 reconciliation → **Addressed** (n_judged-unchanged⇒byte-identical + total==33; committed combined reconciliation test).

### Phase 5 — SPA leaderboard (Rounds 1–2)
- **Both**: a non-"combined" `score_key` blanked the board with no notice; header claimed the mean for legacy runs → **Addressed** (validate `score_key`; header gated on `manifest.ranking`; committed drift guard; `drillJudge` fallback hardened).

### Phase 6 — Docs + HOT mirrors (Round 1)
- **Codex** (COMMENT): stale Opus coverage number; retain-history labeling → **Addressed**.
- **Claude** (APPROVE): raw-README `ranking` row; record deferred test-robustness → **Addressed** (added the row + a Deferred note).

### Review Phase — PR-level (Round 1)
- **Codex** (COMMENT): stale `leaderboard.ts` comments ("always ranks on Gemini", "RANKING
  (Gemini)", Opus-as-validation) contradict the combined ranking → **Addressed** (comments updated
  to the `rankingJudgeModel`/combined behavior).
- **Claude** (APPROVE): `single_judge_cell_dict` docstring claimed both tiers share it → **Addressed**
  (score-tier only); header hardcoded "(Gemini + Opus)" → **Addressed** (derived from
  `ranking.judges`); `singleJudgeCells` parsed but not rendered → **N/A** (parsed for schema
  completeness; disclosure is manifest-only, by design); combined-steadfastness pairing on the 2
  residual cells → **N/A** (numerically immaterial; the 2 cells are disclosed).

No `CONSULT_ERROR`s.

### Review Phase — PR-level (Round 2, architect-relayed 3-way, 5 items)
Changes requested, all small; all addressed:
1. **v3 bundle generator reproducibility** → the gitignored throwaway figs script is committed as
   `analysis paper-bundle` (`paper_bundle.py`, Typer CLI, deterministic seed) with a CI fixture test
   (`test_paper_bundle.py`) whose `subj_overall` reconciles with the export combined mean-of-means
   (non-skipping); `test_v3_bundle_schema` switched to ABSOLUTE assertions (v2 bundle is gitignored
   and may be re-patched). `COMBINED-STATS.md` updated to point at the committed command.
2. **ResultsPage judge copy derived from data** → header/caption derive the judge count and names
   from `manifest.ranking.judges`; a one-judge manifest SPA test added (`results.test.tsx`).
3. **False "Gemini ranks the leaderboard" line** (`ReviewScenarioPage.tsx`) → the ranking judge no
   longer claims to "rank the leaderboard"; copy now states the `/results` board ranks on the
   per-cell mean of the judges.
4. **Stale `leaderboard.ts` comments** → verified consistent with the combined `rankingJudgeModel`
   behavior (fixed in Round 1; no residual drift).
5. **Raw catalog `ranking` block shape** → DROPPED from `export_raw._catalog_doc` (the raw viewer is
   catalog-generic and never read it; the ranking rule lives on the score manifest). Kept the
   completeness guard as a real invariant; raw tier manifest re-exported (only `manifest.json`
   changes, shards byte-stable, cross-tier fingerprint parity preserved); raw README + golden-freeze
   fixture + raw tests updated.

All suites green after Round 2 (analysis 268, multibrowser 411, typecheck clean, governance 9/9).

## Lessons Learned

### What Went Well
- Reviewers were code-verified and caught real, load-bearing issues early (the overspend path, the
  shard-guard collision, the cross-tier fingerprint drift, the stale `dual_judge.unstated` n). Each
  became a committed guard.
- Single-sourcing the combined convention (`cell_scores` over all judges) meant the committed
  primitive, the export, and the v3 bundle reconcile by construction (2.2e-16).

### Challenges Encountered
- The paper stats bundle is produced by gitignored `tmp/` figs scripts split across three
  generators (v2 figs, `refresh_dualjudge_stats`, `110-dualjudge-fullgrid-figs`); getting the v3
  `dual_judge` right meant matching `paper_figs_multibench.py`'s exact `load_opus` so the bundle n
  values pass its live asserts.
- Baked #2 vs #7 was a genuine contradiction — surfaced and left to the architect rather than
  guessed.

### What Would Be Done Differently
- Anticipate the cross-tier raw re-export in the plan's Phase 4, not discover it in review.
- Avoid bare-word backticks in `git commit -m` under zsh (they command-substitute — one commit
  message dropped two words).

### Methodology Improvements
- The per-phase force-advance on a split APPROVE/REQUEST_CHANGES let a real (later-fixed) Claude
  catch slip past the phase boundary; the fix rode the next phase's consult. A "both must APPROVE or
  builder must explicitly override" gate would be safer for correctness-critical phases.

## Architecture Updates

- Routed: **hot** — `codev/resources/arch-critical.md` — the `/results` leaderboard fact updated in
  place to the **two-judge mean** (combined block + manifest `ranking`; gate now guards a
  *component*; legacy → Gemini fallback; Spec 49/110/120). One line edited, no new fact, **no
  demotion needed** (line/fact caps still satisfied). CLAUDE.md/AGENTS.md HOT mirrors regenerated
  verbatim (governance 9/9).

## Lessons Learned Updates

- Routed: **cold** — `codev/resources/lessons-learned.md` (§Metadata contracts & paper deliverables)
  — two #120 lessons: (1) when two committed tiers share a source fingerprint, re-export **both**
  (score + raw) or the Spec 51 invariant breaks (+ the raw baked bundle goes stale); (2) a re-judge
  is a spend — filtered sittings + a pre-spend work-count assertion make overspend impossible, and
  never reuse a coverage-dependent stat (v2's `dual_judge.unstated` n) after the grid grows.
  Routed to **cold** because HOT `lessons-critical.md` is at its 10-lesson cap and these are
  run/pipeline-specific, not cross-cutting enough to justify displacing a capped hot lesson.
- Also fixed a **pre-existing #110 governance drift** encountered here: the "Metadata contracts &
  paper deliverables (#110)" section of `lessons-learned.md` was missing from the `lessons-critical.md`
  map — added the map topic so `test_governance_docs.py` is fully green.

## Flaky Tests

No flaky tests encountered.

## Follow-up Items

- **Architect:** regenerate the paper from the v3 combined stats bundle (`results/COMBINED-STATS.md`);
  add the combined `/results` leaderboard pin once the paper numbers are accepted; redeploy the raw
  tier (`railway up --no-gitignore`) so the baked bundle matches the new `content_fingerprint`; carry
  the updated `docs/analysis/110-dual-judge-fullgrid-summary.md` numbers into the paper.
- **#119:** its superset export + leaderboard pin should adopt this rule (architect amends the plan;
  the builder rebases).
- **Deferred (non-blocking):** extend the Opus-delta guard to the `steadfastness` block + new-key
  detection (phase_4 comment).
