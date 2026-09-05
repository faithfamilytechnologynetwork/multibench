# protestant-unified — the 8th cross-faith row (numbers for the paper)

Reference numbers for the cross-tradition results table and the derived-tradition appendix, after
scoring the **protestant-unified** tradition (Spec 119) and exporting it as the 8th row of the
cross-faith leaderboard (`results/20260905/`). protestant-unified is a **derived common-witness**
tradition: its 36 scenarios come from the 38 same-advice questions of the Protestant
guidance-divergence study (`docs/analysis/protestant-guidance-divergence-study.md`, D=0.16 →
Pathway B), i.e. the questions where the seven Protestant strands give the *same* pastoral answer;
Q17 (remarriage after divorce) and Q22 (IVF) were dropped at the spec gate as genuinely contested.

Every figure below is reproducible from the committed generator
`experiments/119_protestant_unified/analyze.py` (Typer CLI), which reuses the canonical aggregator
(`build_combined_runs` → `aggregate_tradition` → `compute_tradition_stats`) and the canonical figure
module (`analysis.figures.emit_figures`) over the five judging-run roots in load-bearing order, and
hard-fails unless its per-tradition means reconcile with the committed `results/20260905/` combined
block to ≤1e-9. Scores are the **combined two-judge mean** (Gemini 3.6 Flash + Claude Opus 4.8,
equal weight per cell; #120/#121 `rule: mean_of_judges`), on the −1…+1 scale (0 = neutral).

## The 8-row cross-faith leaderboard (combined two-judge mean-of-means)

Ranking score = the equal-weight mean over the five subjects × three framings of each tradition's
combined per-cell score (scope=full, pressure=all) — the same mean-of-means the `/results`
leaderboard ranks on, reconciled with the committed tier by construction. CIs are the 95%
scenario-cluster bootstrap (5000 resamples, seed 12345), reusing the canonical
`analysis.paper_bundle` method so they match the paper's `trad_pooled` convention.

| Rank | Tradition | Combined mean | 95% CI |
|---:|---|---:|:--|
| 1 | buddhism | +0.6695 | [+0.618, +0.716] |
| 2 | secular-sage | +0.6349 | [+0.556, +0.709] |
| 3 | taoism | +0.6308 | [+0.581, +0.679] |
| 4 | eastern-christianity | +0.5405 | [+0.489, +0.589] |
| **5** | **protestant-unified** | **+0.4863** | **[+0.368, +0.590]** |
| 6 | judaism | +0.4656 | [+0.383, +0.546] |
| 7 | roman-catholicism | +0.3635 | [+0.284, +0.436] |
| 8 | sunni-islam | +0.3597 | [+0.293, +0.421] |

protestant-unified lands **5th of 8**, between eastern-christianity (+0.541) and judaism (+0.466).
It sits in the lower half with the other normative, binding-claims traditions (roman-catholicism,
sunni-islam, judaism) rather than with the higher-scoring buddhism / secular-sage / taoism — the
placement the therapeutic-difficulty prior predicts for a tradition defined by its firm common
witness. The rank is not a sharp separation: protestant-unified's CI [+0.368, +0.590] overlaps
judaism (6th) and eastern-christianity (4th); the defensible claim is that it sits **in the lower,
normative-tradition band**, not that it is precisely 5th.

**Monolith sanity-check.** The retired 7-strand protestantism monolith (`results/20260813-protestantism`)
scores a combined mean-of-means of **+0.0286** — far below protestant-unified (+0.486). This is a
directional comparison only: the monolith is a different scenario set and a different construct (it
mixes all seven strands, including the divergent questions), where this tradition is the *same-advice
common witness*. The gap is consistent with the derivation's intent — restricting to the questions
where the strands agree yields a cleaner, higher-scoring target than the mixed monolith.

## Framing staircase (combined mean over subjects, per framing)

The universal three framings separate the traditions far more than the overall mean does. The
**unstated** framing — the subject is given no cue that a tradition is in view — is the sharpest
discriminator and the hardest condition; **guided** — the subject is handed the tradition's stance —
compresses everything toward the ceiling.

| Tradition | unstated | stated | guided |
|---|---:|---:|---:|
| buddhism | +0.4939 | +0.6691 | +0.8455 |
| secular-sage | +0.4828 | +0.5772 | +0.8446 |
| taoism | +0.3809 | +0.6438 | +0.8677 |
| judaism | +0.1705 | +0.4521 | +0.7743 |
| eastern-christianity | +0.0894 | +0.6175 | +0.9146 |
| **protestant-unified** | **+0.0539** | **+0.5808** | **+0.8241** |
| roman-catholicism | −0.0160 | +0.3616 | +0.7450 |
| sunni-islam | −0.0516 | +0.4476 | +0.6830 |

Under **unstated**, protestant-unified scores **+0.054** — near neutral, in the normative-tradition
cluster (roman-catholicism −0.016, sunni-islam −0.052, eastern-christianity +0.089) and far below
buddhism / secular-sage / taoism (+0.38…+0.49). The framing lift from unstated to guided is **+0.77**:
told the Protestant common witness explicitly, the subjects align with it; left to infer it, they
default close to neutral. This is the omissive-bias pattern the benchmark is built to surface.

The per-framing 95% CIs for protestant-unified (scenario-cluster bootstrap) are unstated **+0.054
[−0.105, +0.213]**, stated **+0.581 [+0.451, +0.694]**, guided **+0.824 [+0.716, +0.904]**. The
unstated CI straddles zero — under no cue, this tradition is not distinguishable from neutral; the
stated and guided intervals are firmly positive and non-overlapping with unstated.

## protestant-unified — per-subject unstated headline (point, 95% CI)

The unstated/full condition is the adversarial headline (scenario-cluster bootstrap, 5000 resamples,
seed 12345). Three of five subjects clear zero; two (Qwen3-235B, Gemini 3.6 Flash) sit below it.

| Subject | unstated headline | 95% CI |
|---|---:|---|
| gpt-5.6-terra | +0.2245 | [+0.0394, +0.4062] |
| claude-sonnet-5 | +0.1736 | [+0.0150, +0.3229] |
| thinkingmachines/Inkling | +0.1586 | [−0.0324, +0.3484] |
| gemini-3.6-flash | −0.1042 | [−0.2836, +0.0776] |
| Qwen/Qwen3-235B | −0.1829 | [−0.3530, −0.0093] |

Only gpt-5.6-terra and claude-sonnet-5 have CIs strictly above zero; Qwen3-235B is strictly below.
The bench is not ceilinged under unstated — the difficulty bar holds.

## Steadfastness under pressure (protestant-unified, unstated: full − turn1)

Steadfastness is the change from the first reply to the end of the pressured conversation; near zero
means the subject neither drifts nor recovers under pressure. All five subjects are within ±0.10 of
zero, and only Gemini 3.6 Flash drifts significantly.

| Subject | steadfastness | 95% CI |
|---|---:|---|
| claude-sonnet-5 | +0.0162 | [−0.0451, +0.0741] |
| gpt-5.6-terra | −0.0023 | [−0.0660, +0.0556] |
| thinkingmachines/Inkling | −0.0197 | [−0.0903, +0.0498] |
| Qwen/Qwen3-235B | −0.0394 | [−0.0926, +0.0150] |
| gemini-3.6-flash | −0.0984 | [−0.1667, −0.0336] |

## Opus-vs-Gemini agreement (protestant-unified, every double-judged cell)

| slice | n | Pearson r | bias (Opus − Gemini) | within ±0.5 | exact |
|---|---:|---:|---:|---:|---:|
| protestant-unified | 6480 | 0.810 | +0.045 | 92.1% | 67.7% |

The two judges agree on protestant-unified about as well as on the record grid overall (full-grid
r=0.833; #110/#120). Opus scores marginally higher (+0.045), and 92% of cells agree within half a
scale point — the combined mean is not resting on a judge disagreement.

## Figures

Rendered by `analyze.py`, written to `experiments/119_protestant_unified/data/output/figures/` as
PDF + PNG (all in the house style). The `scorecard` / `framing` / `steadfastness` / `distribution`
set comes from the canonical `analysis.figures.emit_figures`; `tradition_ranking` and
`judge_agreement` are local figures in `analyze.py` built with the same house-style helpers:

- `tradition_ranking` — the 8 traditions ranked by combined mean, with 95% CI error bars;
  protestant-unified marked.
- `judge_agreement` — a 5×5 Gemini × Opus score-count heatmap over protestant-unified's 6,480
  double-judged cells, with the equal-score diagonal and the r / bias / within-±0.5 annotation.
- `scorecard` — cross-tradition headline (unstated/full) per subject, 95% CIs.
- `framing` — the unstated/stated/guided staircase per subject.
- `steadfastness` — full − turn1 per subject, by pressure.
- `distribution` — combined-score distributions.

(PDF outputs carry matplotlib's build metadata, so a re-render produces a byte-different but
value-identical PDF; the PNGs are byte-stable.)

## Reproducibility and reconciliation

```bash
uv --project workflows/analysis run python experiments/119_protestant_unified/analyze.py
# from the main checkout after merge, pass the roots explicitly (they lose the ../../ prefix):
#   … analyze.py -r tmp/judging-runs/20260803-merged -r … --results-dir results/20260905
```

reads the five roots (`20260803-merged`, `20260803-unstated-opus`, `20260803-framings-opus-sample`,
`20260823-opus-fullgrid`, `20260904-protestant-unified`) — overridable via `--root`/`--results-dir`
Typer options for post-merge reproduction from the main checkout — and asserts, before writing
anything, that (1) `combined_subj_overall` equals the results-export combined mean-of-means for
every `subject|framing`; (2) every tradition's ranking mean-of-means equals the value in its
committed `results/20260905/<tradition>.json` combined block; and (3) each tradition's bootstrap
central estimate equals that same canonical mean-of-means — all to ≤1e-9. It writes
`data/output/{paper_numbers.json, combined_stats.json}` (the latter via the canonical
`build_combined_stats`, so the whole `data/output/` tree is reproducible from this one script) and
the figures. `workflows/analysis/tests/test_phase6_reconcile_119.py` guards the reconciliation and
the committed `paper_numbers.json` against staleness using committed JSON only (CI-runnable; skips if
`results/20260905/` is absent). Cost for the run is in
`experiments/119_protestant_unified/notes.md` (all-in $338.62 billed actual).
