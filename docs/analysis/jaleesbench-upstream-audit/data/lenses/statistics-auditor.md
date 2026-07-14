# JaleesBench upstream audit — Statistics / inference lens

Auditor lens: applied statistician scrutinizing the inference. Read: paper
`sec:eval`, `sec:scorecard`, `sec:judge-agreement`, `sec:limitations`; `score.py`,
`judge.py`, `html_report.py`, `results/commentary.json`. NO-EDITS audit — every item
below is a proposal for the upstream authors.

## Verdict
The inference is, in its honest moments, unusually careful: the bootstrap clusters on
the right unit, the single-run limitation is disclosed, and overlapping CIs are called
out rather than hidden. But three things undercut the headline reliability claims —
(1) the reported inter-judge agreement is computed **after** a one-directional re-judge
overlay that can only move it up, undisclosed; (2) the conflict-of-interest paragraph
omits the single most consequential case (the #1 system Ansari is Gemini-family); and
(3) the paper's central inferential object — the probe-cluster bootstrap CI — has **no
implementation anywhere in the released harness**, and the shipped report code says the
opposite ("no confidence intervals yet").

---

## Strengths confirmed (preserve)

- **S1 — Correct bootstrap clustering unit.** The paper resamples "the 140 probes"
  (`sec:scorecard`, l.346, l.385). Because the bank is one-probe-per-cluster, the probe
  *is* the cluster, and each probe's 6 pressures × framings × 2 judges are the correlated
  cells that must move together under resampling. Clustering on the probe correctly
  propagates between-probe variance and does not pretend the ~40k cells are independent.
  This is the right design, not a shortcut.
- **S2 — Single-response-per-cell limitation disclosed.** `sec:limitations` (l.726–728)
  states plainly that CIs capture probe-sampling variance only and "run-to-run
  stochasticity is not captured." Correct interpretation, honestly flagged.
- **S3 — Overlapping-CI honesty.** `sec:scorecard` (l.386–389) explicitly reports that
  GPT-5.5 vs Sonnet 4.6 and Nemotron vs GLM "have overlapping intervals, not separable
  at 95%." Many benchmark papers would have ranked these silently.
- **S4 — COI is raised and hedged.** `sec:judge-agreement` (l.624–639) raises the
  family-tie question at all, gives the confound (Qwen3, no tie, has the largest gap),
  and labels it "a directional observation, not a confirmed bias." Good scientific register.

---

## Defects

### D1 (SERIOUS) — v2 re-judge overlay inflates the reported agreement; undisclosed
`score.py:load_judgments()` (l.106–125) loads base judgments then **overlays**
`judgments_v2.jsonl` by identity key ("v2 wins"). `judgments_v2.jsonl` is produced by
`judge.py:rejudge_disagreements()` (l.170–232), which targets **only** cells where the
two judges disagreed by ≥2 bands and re-scores them with a "v2 boundary-rules prompt."
`build_report()`'s judge-agreement block (`score.py` l.213–235) then computes exact /
within-one agreement over the **overlaid** `judgments` list.

Because the selection is one-directional — only the worst-disagreeing cells are re-drawn,
agreeing cells are frozen — the overlay can only **raise** measured agreement in
expectation (a disagreement can stay a disagreement or resolve; an agreement cannot
become a disagreement). With within-one at 85%, the ≥2-band cells are ~15% (~6,000 of
40,311), so the adjustable mass is large. The 66/85 figure is the benchmark's declared
"calibration instrument" (`sec:protocol`, l.324), yet neither the paper
(`sec:judge-agreement`, `sec:limitations`) nor `commentary.json` ("judges"/"caveats")
mentions that a re-judge overlay feeds it. Reporting post-adjudication agreement as the
raw inter-judge agreement overstates reliability.
- **Fix (statistics/doc):** disclose the two-pass adjudication; report **first-pass**
  exact/within-one agreement as the calibration number, and present the post-adjudication
  figure separately as a resolved-disagreement diagnostic. (Note the same overlay also
  silently replaces the ≥2-band bands in the *scorecard* means — worth disclosing too.)

### D2 (REVISE) — COI paragraph omits the headline system, the most consequential case
`sec:judge-agreement` (l.627–629) says "**two** subjects share a model family with a
judge — Claude Sonnet 4.6 with the Opus judge, Gemini 3.5 Flash with the Gemini judge."
But `sec:eval` (l.331) states Ansari's base model **is** Gemini 3.5 Flash. Ansari is
therefore also Gemini-family with the Gemini judge — and it is the #1 system (+0.48
headline) and the entire case study. The single most consequential family tie is left
out of the family-tie discussion.
Concretely: `commentary.json` "judges" (l.17) reports the Opus–Gemini gap is **tightest
on Ansari (+0.04)** — i.e. the stricter Gemini judge is least strict, relative to Opus,
exactly on the Gemini-based headline system, which inflates its two-judge-average score.
This also contradicts the paper's own claim (l.634–635) that the gap is narrowed "more
for Gemini 3.5 Flash than for any other subject" — by the commentary's numbers Ansari is
the most-narrowed, not Gemini 3.5 Flash.
- **Fix (framing/doc):** add Ansari to the COI paragraph as the primary case, reconcile
  the "narrows more than any other subject" sentence with the +0.04-on-Ansari figure, and
  note that the family-favorability direction, if real, inflates the headline result.

### D3 (REVISE) — Bootstrap CIs are not reproducible from the released code
The paper's central inferential object is the "probe-cluster bootstrap 95% CI (5,000
resamples)," reported "for every reported quantity" and claimed to "ship with the
reproducibility artifact" (`sec:scorecard` l.392–394; `sec:limitations` l.726–727).
A repo-wide search finds **no** bootstrap/resample/percentile/`random.choice` code in any
`.py` file — `score.py` emits point estimates only, and the figure-generation scripts
(`figures/fig_scorecard`, etc.) are not in the tree. Worse, the shipped `html_report.py`
(l.500) prints "Single run per cell — no confidence intervals **yet**," directly
contradicting the paper. The CIs, the agreement CI (64–68% / 84–86%), and the
"non-overlapping intervals" separation claims (e.g. case study l.693) cannot be
regenerated from what is released.
- **Fix (code-repro):** release the bootstrap + figure code, or soften the "every reported
  quantity / ships with the artifact" language to match what is actually shipped.

### D4 (MINOR) — Multiplicity across many reported cells
The paper computes per-comparison 95% CIs for "every table cell" and draws separation
conclusions at several points ("non-overlapping intervals," `sec:casestudy` l.693;
citation `sec:citation`). Across 8 systems × {scorecard, 6 pressures, 3 framings, pillars,
hearts, citation classes} the implicit comparison count is large and no family-wise or FDR
adjustment is mentioned, so 95% per-comparison intervals overstate simultaneous
confidence. Mitigated by the overlap honesty (S3), so this is a disclosure item, not a
headline threat.
- **Fix (statistics):** add one sentence that intervals are per-comparison (not
  multiplicity-adjusted), and lean on effect size + overlap (as already done) rather than
  treating each non-overlap as an independent significance test.

### D5 (MINOR) — "dual-judged" cell count and "every cell scored by both judges" overstate
`sec:eval` (l.335) says "every cell scored by both judges" and `sec:judge-agreement`
(l.617) says "Across **40,320** dual-judged cells." But `commentary.json` "caveats" (l.19)
discloses 9 of 40,320 cells are single-judge (Gemini refused 8, Opus dropped 1 rationale),
and "judges" (l.17) correctly uses **40,311** dual-judged cells. The paper's 40,320 double-
counts the 9 single-judge cells and the blanket "every cell scored by both judges" is
false for those 9.
- **Fix (doc):** use 40,311 as the dual-judged denominator and footnote the 9 single-judge
  cells as the commentary already does.

---

## Not-a-defect notes
- The CI interpretation "would another sample of 140 probes rank these the same" (not
  "would a re-run") is the correct reading of a probe-cluster bootstrap and is disclosed —
  keep it.
- The scale/grid arithmetic is otherwise consistent: 140×6×3×8 = 20,160 sittings;
  ×2 turns ×2 judges = 80,640 nominal judgments; 40,320 (subject,probe,pressure,framing,
  scope) cells. Only the "dual-judged" labeling (D5) is off.
