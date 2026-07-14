# JaleesBench upstream audit — Lens: paper methodologist / referee

Read of `docs/paper/jaleesbench-paper.tex` (1102 lines) against `probes.json`,
`score.py`, `citation.py`, `commentary.json`, the design doc, and the chapter map.
No edits made to the upstream repo. All findings are proposals for the authors.

## Headline

The **paper is largely internally consistent** — Table 1 (scorecard) and the
framing-staircase table agree exactly on their shared Unstated/Guided columns,
the abstract matches the tables, the polarizing breakdown sums correctly, the
guided-wash cell accounting sums to 840, and the scale/cost arithmetic checks.
The problems are (a) one genuine **internal arithmetic contradiction** in the
clustering sentence, and (b) a **released-artifact-vs-paper mismatch**: the
shipped results narrative `commentary.json` disagrees with the paper's numbers,
most starkly on the number of polarizing cells (320 vs 691) and the Ansari-layer
value (+0.75 vs +0.74). For a paper that headlines "we release the probe bank,
judging rubric, and harness," the released narrative not matching the tables is
the most serious issue.

---

## Defects

### D1 (revise) — Clustering arithmetic is internally contradictory: 143 − 4 = 139 ≠ 140
`sec:clustering` (line 254-255): *"this yields **140 probes** from 369 mapped
chapters / 143 clusters (four etiquette-only clusters excluded)."*
143 − 4 = **139**, not 140. Verified:
- The chapter map (`docs/jaleesbench-chapter-map.md`) marks exactly **4** clusters
  `*(etiquette-leaning)*` (lines 14, 15, 113, 139), totalling 15 chapters — the
  intro line 5 is the definition, not a fifth cluster.
- The design doc (line 155-156) is self-consistent: *"**139 probes**: 369 mapped
  chapters form 143 clusters, of which 4 (15 chapters …) … are excluded."*
- But `probes.json` actually contains **140** probes (JLS-001…JLS-140, contiguous).

So the bank grew to 140 while the paper reused the design doc's `143 − 4 = 139`
scaffolding and pasted the newer 140 count on top, producing a contradiction. Fix
one of the two operands: if 140 is right, either 3 clusters were excluded
(143 − 3) or the cluster/mapped-chapter counts changed — the sentence must be
re-derived from the current map, not the v0.3 design doc.
**fix_type: doc/statistics.**

### D2 (revise) — Released `commentary.json` does not match the paper's numbers (different run)
The shipped results narrative disagrees with the paper's tables in ways that are
too large and too patterned to be rounding:
- **Polarizing cells: 691 (paper `app:polarizing`, line 798) vs 320 (`commentary.json` "exhibits").** Both state "of 2,520." The per-pressure ranking also flips: paper says *personal appeal 146* is highest (breakdown sums to 691); commentary says *"flattery and false authority most."* This is a 2× discrepancy on the appendix's headline statistic.
- **Ansari layer: +0.74 (paper, lines 85/428/455/464) vs +0.75 (commentary, ×3).** The paper's +0.74 is the correct arithmetic (0.48 − (−0.26) = 0.74); commentary's +0.75 is wrong.
- **Scorecard point estimates:** GPT-5.5 +0.28 (paper) vs +0.27 (commentary); Claude Sonnet 4.6 +0.23 vs +0.22.
- **Ansari steadfastness** −0.29 (paper Table 1) vs −0.30 (commentary); Ansari insistence −0.60 vs −0.61; Claude false-authority +0.13 vs +0.12.
- **Dual-judged cells:** paper "40,320" (line 617) vs commentary "40,311."

The uniform ~0.01 drift plus the polarizing gap indicate `commentary.json` was
generated from a **different (earlier) run/snapshot** than the paper's tables.
Since the harness + results are a release deliverable, regenerate the narrative
from the same run the paper reports, or the reproducibility claim fails at the
first artifact a reader opens. **fix_type: statistics/doc.**

### D3 (revise) — Paper's citation method (LLM, turn-1) is not what the released report code runs (regex, both turns)
`sec:citation` (line 550-557): citation is *"detected by a temperature-0 LLM
grader over the agent's **first (pre-pressure) response**."* That method exists
in `citation.py` (`detect_all(turn1=True)`, `gemini-3.1-flash-lite`, temp 0.0,
`asst[0]` only) — so the paper's *description* is faithful to that module.
**But the released report pipeline `score.py::build_report()` uses a different
detector:** a regex (`cites()`, `QURAN_RE`/`HADITH_RE`, comment line 27
"Transparent regex heuristics over assistant turns") applied over **all**
assistant turns (loop line 194-195), not the LLM and not turn-1-only. A reader
who runs the released report to reproduce Table 2 gets regex/both-turn numbers,
not the paper's LLM/turn-1 numbers. State which detector produced Table 2 and
either route `build_report` through `citation.py` or document the two-detector
split. **fix_type: code/doc.**

### D4 (minor) — README band labels contradict paper/rubric
`README.md` line 53 band strip: *"Burns (−1) · **Smoke (−0.5)** · **Neutral (0)**
· Scent (+0.5) · Perfume (+1)."* The paper (`tab:bands`, line 944-949), design
doc, and judge prompt use **Sparks** (−0.5) and **Inert** (0). Public-facing
label drift; align the README to the canonical band names. **fix_type: doc.**

### D5 (minor) — "etiquette-only" overstates; the excluded clusters are *majority*-etiquette
`sec:clustering` line 255 calls the excluded clusters "etiquette-**only**," but
the chapter map defines them as clusters "where such [non-probe-able] chapters
form the **majority**" and marks them `*(etiquette-leaning)*` — they contain some
non-etiquette chapters (e.g. the 7-chapter "Trivial manners proportionality"
cluster). "Etiquette-only" is a stronger, inaccurate claim. Use
"etiquette-leaning" / "majority-etiquette." **fix_type: framing.**

### D6 (minor) — Agreement denominator ignores the 9 single-judge cells the release documents
Paper line 617: *"Across 40,320 dual-judged cells, exact band agreement is 66%."*
`commentary.json` ("caveats") documents that **9 of 40,320 cells are
single-judge** (8 refused by the Gemini judge's safety filter *even with
thresholds disabled* — relevant to `judge.py`'s `safety_off=True` — plus 1 Opus
rationale omission), so only **40,311** are actually dual-judged. The paper both
rounds the denominator and **omits the Gemini safety-refusal caveat entirely**
from Limitations. Add the single-judge-cell note and use 40,311 for the agreement
base. **fix_type: doc/statistics.**

### D7 (note) — Framing-table derived-gap columns differ from the displayed subtraction by 0.01
In `tab:framing`, several Recognition (S−U) / Instruction (G−S) cells don't equal
the difference of the two displayed rounded scores: e.g. GPT-5.5 0.73 − 0.28 =
0.45 but the table prints +0.46; Claude 0.65 − 0.23 = 0.42 vs +0.43; Gemini
0.28 − (−0.26) = 0.54 vs +0.55. This is **correct behaviour** (gaps computed on
unrounded per-probe means, then rounded independently — rounding-of-a-difference
≠ difference-of-roundings), not an error, but a referee will flag it. A one-line
table footnote ("gaps computed pre-rounding") preempts the confusion.
**fix_type: doc.**

### D8 (note, needs web grounding) — Related-work citations are unverifiable at cutoff
The related-work section leans on IslamicMMLU, IslamicLegalBench, IslamTrust
(66.5%), VirtueBench, EdifyBench, CEFE-AI/AllFaith, `omissivebias2026`,
`moraljustification2023`. Several are dated 2025-2026 and could not be verified
here; the framing (complementary, not competitive) is fair *if* the works exist
as described. Flagged for the verify phase to confirm each `references.bib` entry
resolves. **fix_type: citation.**

---

## Confirmed strengths (methodology)

- **S1** — Table 1 and the framing-staircase table agree exactly on shared
  Unstated (Jalees Score) and Guided-ceiling columns for all 8 subjects; the
  abstract's +0.28/+0.23 → +0.84/+0.87 matches the tables. Internally coherent.
- **S2** — Polarizing per-pressure breakdown sums exactly: 146+133+120+101+101+90
  = 691 (paper). Guided-wash cell accounting sums exactly: 594+144+102 = 840.
- **S3** — Case-study arithmetic is coherent and honest: held-out +0.44,
  full-bank +0.41 improvement, non-overlapping bootstrap CIs, and an explicit
  no-regression check on the 3 untargeted pressures.
- **S4** — Scale arithmetic correct: 140×6×3×8 = 20,160 sittings; ×2 turns ×2
  judges = 80,640 judgments; 40,320 turn-level dual-judged cells. Cost table
  reconciles with the released $1,316 (collection ~$380 + batch judging ~$936).
- **S5** — Genuinely well-scoped Limitations: single response per cell (no
  run-to-run variance), scholar review explicitly gating any normative claim,
  source-in-training-data risk acknowledged, and the judge/family-tie conflict
  reported as a *directional observation, not a confirmed bias* (with Qwen3-235B
  offered as the confound). This is careful, non-overclaiming referee-grade work.
- **S6** — Citation is reported **beside** the Jalees Score, not folded into it,
  with an explicit rationale (pressing verses on a user who asked for none is a
  register failure the bands already penalize) — a clean methodological choice.
