# Lens: Measurement-Coverage Analyst

Scope: distribution of `pillars`, `hearts`, `identity_signal`, pressures-per-probe across
the 140 probes; whether coverage is disclosed; cross-check of the paper's *by virtue / by
heart state* section (sec:by-theme) against real tag counts. Sources read:
`jaleesbench/jaleesbench/data/probes.json`, `mapping.py`, `score.py:137-270` (build_report),
`docs/paper/jaleesbench-paper.tex:385-546`. No edits made (read-only audit).

## Exact counts (computed from probes.json, N=140)

**Pillars** (multi-label; total 302 tags, avg 2.16/probe; 0 probes untagged):

| pillar | n | % of probes |
|---|---|---|
| restraint | 107 | 76.4 |
| cross_cutting | 67 | 47.9 |
| justice | 66 | 47.1 |
| patience | 36 | 25.7 |
| **courage** | **26** | **18.6** |

pillars-per-probe: 1→11, 2→96, 3→33.

**Heart states** (multi-label; total 419 tags, avg 2.99/probe; 0 probes untagged):

| heart | n | % |
|---|---|---|
| love_contentment | 81 | 57.9 |
| self_accounting | 79 | 56.4 |
| intention_sincerity | 59 | 42.1 |
| vigilance | 45 | 32.1 |
| fear_hope | 40 | 28.6 |
| reliance_on_god | 36 | 25.7 |
| truthfulness | 34 | 24.3 |
| patience_gratitude | 16 | 11.4 |
| **repentance** | **15** | **10.7** |
| **patience** | **14** | **10.0** |

hearts-per-probe: 2→32, 3→79, 4→27, 5→2.

**identity_signal:** clean 58 / leaky 40 / intrinsic 42 (matches recon; universal 98 / intrinsic 42).

**Pressures-per-probe:** all 140 probes carry exactly all 6 pressures (secularize, insistence,
false_authority, good_cause, flattery, personal_appeal); 0 empty pressure turns.

## Strengths confirmed

- **Pressure coverage is perfectly balanced and complete** — every probe has all six pressure
  turns populated, no empties. The 6-pressure axis is a clean, fully-crossed factor.
- **No degenerate taxonomy cells** — every pillar and every heart state has ≥14 probes; no empty
  or singleton category. The multi-label bank is densely populated.
- **identity_signal is reasonably spread** (58/40/42), supporting the intended universal/intrinsic
  contrast without a starved cell.

## Defects found

### D1 (revise, statistics) — by-theme "best" claims rest on the least-covered cells; asymmetric power
paper.tex:509-517 singles out **repentance** (n=15, the 2nd-smallest heart cell) as the single best
heart state (+0.17) and **patience** as "the one pillar" models handle (pillar n=36, 2nd-smallest
pillar). The **worst** cells it names — love_contentment (n=81), justice (66), cross_cutting (67) —
are all well-powered. So the paper's interpretive narrative ("models are good company where counsel
coincides with comfort") leans hardest on the thinnest cells, exactly in the direction of the claim.
Prose reports point-estimate rankings with no inline n or CI. Fix: report per-cell n and CI
half-width in the by-theme prose/figures; soften the repentance/patience "best" claims to reflect
the low-n cells. Figures do carry error bars (paper.tex:391-393), which mitigates but does not
disclose n.

### D2 (revise, statistics/doc) — per-cell coverage (n) disclosed nowhere
No per-category probe count appears in the paper prose, README, or the generated report. score.py's
`build_report()` (lines 241-270) emits the by-pillar and by-heart tables as pooled means with **no n
column and no CI** — the heart "patience" cell (n=14) sits beside love_contentment (n=81) with
identical visual weight. A reader cannot tell which cells are thin. Fix (code+doc): add an n column
and CI half-width to the build_report tables, and a coverage table to the paper appendix.

### D3 (revise, taxonomy-coverage / new-scenario) — courage under-covered; thin cells cluster
**courage** is the least-covered named conduct pillar (n=26, ~4x below restraint's 107). The three
smallest heart cells — patience(14), repentance(15), patience_gratitude(16) — are all sub-20. The
by-virtue prose (paper.tex:509-512) names patience/justice/cross_cutting but **never mentions courage
or restraint** — i.e. the two extreme-coverage pillars (26 and 107) are precisely the two omitted
from discussion. This motivates an authoring pass to lift courage and the sub-20 heart cells (fix:
new-scenario), plus disclosure (fix: doc). This is a *coverage-imbalance* observation for an
authoring proposal, NOT a re-tag-to-fix-balance recommendation (which is forbidden).

## Interpretive caveats (notes)

### D4 (note, statistics) — multi-label overlap not disclosed
Pillars avg 2.16/probe, hearts 2.99/probe; the by-virtue and by-heart breakdowns overlap heavily and
are **not partitions** of the 140 probes. A reader may misread the cells as disjoint subsets. Worth a
one-line note in sec:by-theme.

### D5 (note, taxonomy) — cross_cutting is a near-half-of-bank catch-all treated as a virtue
cross_cutting is the 2nd-largest pillar (67, 47.9%) but is a residual bucket, not a conduct virtue.
paper.tex:511-512 reports "cross-cutting virtues ... field mean −0.10" as if a coherent virtue cell.
A ~half-of-bank vague bucket weakens the "by virtue" axis's interpretability.

### D6 (note, taxonomy) — the "patience" station is fragmented into the two smallest heart cells
heart "patience"(14) + "patience_gratitude"(16) split one al-Ghazali station across the two lowest-n
cells, and bare "patience" also duplicates the pillar name. The fragmentation lands exactly in the
coverage nadir, so any per-heart claim about patience is the least statistically reliable of all.
(Complements the taxonomy-fidelity lens's duplicate-label finding from the coverage angle.)
