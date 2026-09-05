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
leaderboard ranks on, reconciled with the committed tier by construction.

| Rank | Tradition | Combined mean |
|---:|---|---:|
| 1 | buddhism | +0.6695 |
| 2 | secular-sage | +0.6349 |
| 3 | taoism | +0.6308 |
| 4 | eastern-christianity | +0.5405 |
| **5** | **protestant-unified** | **+0.4863** |
| 6 | judaism | +0.4656 |
| 7 | roman-catholicism | +0.3635 |
| 8 | sunni-islam | +0.3597 |

protestant-unified lands **5th of 8**, between eastern-christianity (+0.541) and judaism (+0.466).
It sits in the lower half with the other normative, binding-claims traditions (roman-catholicism,
sunni-islam, judaism) rather than with the higher-scoring buddhism / secular-sage / taoism — the
placement the therapeutic-difficulty prior predicts for a tradition defined by its firm common
witness.

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

Rendered by `analyze.py` via the canonical `emit_figures` (house style, 95% CIs), written to
`experiments/119_protestant_unified/data/output/figures/` as PDF + PNG:

- `scorecard` — cross-tradition headline (unstated/full) per subject, 95% CIs.
- `framing` — the unstated/stated/guided staircase per subject.
- `steadfastness` — full − turn1 per subject, by pressure.
- `distribution` — combined-score distributions.

## Reproducibility and reconciliation

```bash
uv --project workflows/analysis run python experiments/119_protestant_unified/analyze.py
```

reads the five roots (`20260803-merged`, `20260803-unstated-opus`, `20260803-framings-opus-sample`,
`20260823-opus-fullgrid`, `20260904-protestant-unified`) from the main checkout's
`tmp/judging-runs/`, and asserts, before writing anything, that (1) `combined_subj_overall` equals
the results-export combined mean-of-means for every `subject|framing`, and (2) every tradition's
ranking mean-of-means equals the value in its committed `results/20260905/<tradition>.json` combined
block — both to ≤1e-9. `workflows/analysis/tests/test_phase6_reconcile_119.py` guards the same
reconciliation against committed JSON only (CI-runnable; skips if `results/20260905/` is absent).
Cost for the run is in `experiments/119_protestant_unified/notes.md` (all-in $338.62 billed actual).
