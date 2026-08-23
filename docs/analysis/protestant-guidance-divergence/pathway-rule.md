# The pathway decision rule (pre-registered)

Committed **before any answers were generated**, so the recommendation follows from the rule and
the data rather than from taste after seeing results. This operationalises the maintainers'
direction: *start simple; add architecture only when the evidence demands it* — and it replaces
the presumed 7+1 endpoint of `protestantbench-refactor.md` §1 with a conditional decision.

**D** = the substantive-divergence share (codebook): the fraction of the 50 questions whose
adjudicated severity is `substance`.

**Concentration**: divergence is *concentrated* when ≥70% of `substance` questions fall in at
most three of the nine frame domains, or are attributable to at most two strands as recurring
outliers.

| Evidence | Pathway |
|---|---|
| **D < 15% and concentrated** | **A — unified bench only.** Build `protestant-unified` from the consensus worksheets with receipts. The `substance` questions carry family-conditional notes inside their `judge-guidance.md`. No strand benches. |
| **15% ≤ D ≤ 35%, or D < 15% but not concentrated** | **B — unified bench + a conditional tier, strand benches only where earned.** Unified bench as in A; a first-class conditional-guidance treatment for the divergent set; a separate strand bench **only** for a strand that is the outlier on ≥20% of all questions (a strand whose counsel is systematically its own — expected candidate: `anabaptist`). |
| **D > 35%** | **C — the per-strand suite** of `protestantbench-refactor.md` is warranted as specified (§2–§7), with the study's worksheets as the seed ground truth. |

Secondary rule, applied within any pathway: if a single strand accounts for more than half of all
outlier appearances, that is evidence for **that strand's own bench or column**, never for
suite-wide complexity.

Whatever the pathway, two things are unconditional: the unified source is **derived with
receipts** from these columns (never composed freehand — the freehand pan-Protestant guide is the
measured failure that motivated this study), and the worksheets are published as a dataset in
their own right.
