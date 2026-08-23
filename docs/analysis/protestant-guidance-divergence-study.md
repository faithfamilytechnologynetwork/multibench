# Seven strands, one counsel? — the Protestant guidance-divergence study (v1)

**The question**: when the major Protestant strands' own authoritative texts are asked the same
ordinary-life pastoral questions, does the *guidance* (concrete counsel) differ, even where the
*theology* (grounding) differs?

**The answer, measured**: **on 78% of questions the concrete advice is the same across all seven
strands; on 6% it differs only in emphasis; on 16% it substantively diverges — and the divergence
is not spread thin but stacked in nameable terrain** (the sword and the oath; rule-versus-liberty
practices; the tithe; household order). Where advice diverges, the divergence is doctrinally
driven (seven of the eight cases have divergent grounding). And in nine further cases the strands
give the **same advice from different theology** — including on assurance, healing, and private
revelation, exactly the loci where Protestant theology famously divides.

Under the pre-registered decision rule, this yields **Pathway B in its minimal form: build one
unified Protestant bench with family-conditional guidance on the divergent minority; no strand
earns a separate bench on this evidence** (§8).

This is the v1 study specified by [`protestantbench-refactor.md`](./protestantbench-refactor.md)
§5, run at the maintainers' direction as the *first* step — measure guidance divergence before
committing to any architecture. **Pre-registration**: the instrument
([`questions.md`](./protestant-guidance-divergence/questions.md)), the answering protocol
([`method.md`](./protestant-guidance-divergence/method.md)), the coding rules
([`codebook.md`](./protestant-guidance-divergence/codebook.md)), and the pathway thresholds
([`pathway-rule.md`](./protestant-guidance-divergence/pathway-rule.md)) were committed at
`6f3ad58`, before any strand answer existed; the git history is the timestamp.

---

## 1. Design in one paragraph

Fifty concrete pastoral situations (a person, a trouble, statable with no church noun), sampled
from a domain frame of ordinary life — work, money, marriage and family, body and mind,
friendship, civic life, digital life, the interior life, death and grief. Seven columns —
**Lutheran** (Book of Concord), **Reformed/Presbyterian** (Westminster Standards + Three Forms),
**Anglican** (Thirty-Nine Articles + 1662 Prayer Book + Homilies), **Baptist** (BF&M 2000, 1689,
covenant tradition), **Methodist/Wesleyan-Holiness** (Articles of Religion, Wesley's Standard
Sermons, General Rules, Discipline/Manual), **Pentecostal** (AG Fundamental Truths + position
papers, CoG, COGIC), **Anabaptist** (Schleitheim, Dordrecht, the 1995 Mennonite Confession) —
each answered every question **independently, from its own corpus only**, in a fixed worksheet
separating *Counsel* (concrete advice) from *Grounding* (cited loci with confidence flags), with
**silence** as an allowed answer. A fixed five-question sample per column was then adversarially
citation-audited; the counsel fields were pseudonymised, shuffled, and **blind double-coded**
into advice clusters with a third-coder adjudication; grounding similarity was coded separately.
Everything — 350 worksheets, audit logs, codings, scripts — is committed under
[`protestant-guidance-divergence/`](./protestant-guidance-divergence/).

## 2. Headline result

| Advice similarity (adjudicated) | n | share |
|---|---|---|
| **same** — one cluster, counsel practically interchangeable | 39 | **78%** |
| **emphasis** — real differences, but no counsel forbids what another permits | 3 | 6% |
| **substance** — at least one strand forbids/commands what another permits | 8 | **16%** |

**D (substantive-divergence share) = 0.16.** Inter-coder agreement: 92% on severity, 88% on the
exact cluster partition (46 and 44 of 50; six questions adjudicated). One "same" is vacuous —
Q50 (cremation), where **all seven** strands' standards are silent; counting only non-vacuous
questions, same-advice is 38/49 (77.6%).

The prediction this study was built to test — *"in ~80% of cases it's exactly the same, and in
~20% it's different, and those cases come from nameable areas"* — is, on this instrument,
**almost exactly right**: 78% exactly-same, 22% not, with the divergence concentrated (§4).

## 3. The advice × grounding grid — same counsel, different theology

| | grounding **shared** | **parallel** | **divergent** |
|---|---|---|---|
| advice **same** | 30 | 5 | **4** |
| **emphasis** | 2 | 1 | 0 |
| **substance** | 1 | 0 | **7** |

Two cells carry the paper's story:

- **Same advice from different theology (9 questions — same/emphasis × parallel/divergent).**
  The strands reach identical counsel down visibly different doctrinal roads: on the returning
  prodigal terrified of the unforgivable sin (Q47), the Reformed and Baptist columns ground his
  comfort in **perseverance** (Dort; BF&M V) while the Wesleyan and Anglican columns hold real
  **falling from grace with real return** — and both counsel the same thing: *your terror is
  itself evidence you are not beyond grace; come back.* On the "God told me to quit my job"
  claim (Q46), a cessationist grounding and a continuationist one both issue the same
  instruction: test it against Scripture, take counsel, do not bet the family on an impression.
  On unanswered healing (Q27), healing-in-the-atonement and providence-through-means both say:
  take the new drug, keep praying, the friend's faith-metering is cruel and false. **This is the
  study's sharpest finding: the loci where Protestant *theology* famously divides produced
  convergent *pastoral instruction*.**
- **Where advice diverges, doctrine is doing it (7 of 8 substance cases have divergent
  grounding).** The one exception (Q28, fasting under a suspected eating disorder) is a
  practice-rule difference on shared texts. Divergent advice is not noise in this dataset; it is
  confession.

## 4. Where the strands actually differ — the areas

Per-domain substance rates: civic 3/5 · body & mind 2/7 · work 1/7 · money 1/7 · family 1/10 ·
social, digital, interior, grief 0/19. Three areas, per the pre-registered concentration
measure (75% of substance cases in the top three domains):

**(a) The sword and the oath** — Q37 (a son enlisting), Q38 (the courtroom oath), Q39 (the
jury). Six strands bless or permit what the **Anabaptist** column, alone each time, refuses from
its confessions: no rifle (alternative service instead), no sworn oath (affirm instead), scruples
declared to the judge. These are the purest doctrine-to-advice divergences in the dataset — and
the Pentecostal corpus is silent on two of the three, its bodies having settled conscience-liberty
positions rather than binding rules.

**(b) Rule versus liberty in bodily and calendar practice** — Q02 (a promotion working most
Sundays: a sabbatarian camp — Reformed, Anglican, Baptist, Methodist — counsels declining if the
Lord's Day cannot be protected, while Lutheran, Pentecostal, and Anabaptist counsel a conditional
yes with worship and body-life concretely secured); Q26 (nightly drinking: a five-strand
abstinence-season test, an Anglican moderation-reduction, a Pentecostal permanent stop); Q28 (the
fasting regimen: all direct a medical screen, but two strands suspend fasting entirely —
"suspended, not negotiated" — while the Anglican column keeps the Church's appointed fasts
through the same season).

**(c) Money-rule and household order** — Q08 (the tithe under $40k debt: six strands set a
freely chosen sustainable proportion and forbid stretching the payoff for a fixed ten percent;
the **Pentecostal** column alone counsels keeping the full tithe); Q24 (the relocation deadlock:
all seven reject the father's "husband decides" trump, and then split three mutually exclusive
ways at true deadlock — freely-given yielding with the husband first to offer his loss
(Lutheran, Anabaptist, Methodist), the husband deciding *toward her good*, likely her city
(Reformed, Pentecostal), and no move over an unpersuaded spouse (Anglican, Baptist)).

**Who diverges**: outlier appearances — Pentecostal 5, Anabaptist 4, Anglican 4, Lutheran 2,
Baptist 1, Reformed/Presbyterian 1, Methodist 0. **No strand is an outlier on even 10% of the 50
questions** (the pre-registered own-bench threshold was 20%). The Anabaptist appearances are the
most doctrinally load-bearing (the civic trio); the Pentecostal ones split between real rules
(tithe, abstinence) and one added-practice emphasis (Q45).

**Pairwise agreement** (share of co-answered questions in the same advice cluster) runs 0.81 to
0.98 across all twenty-one pairs. The magisterial-and-Baptist core — Lutheran, Reformed,
Baptist, Methodist — agree pairwise at 0.93–0.98; the lowest agreements are Anglican–Anabaptist
(0.81) and Anglican–Pentecostal (0.83). Full matrix:
[`output/pairwise_agreement.csv`](./protestant-guidance-divergence/output/pairwise_agreement.csv).

## 5. Silence — who doesn't answer

34 of 350 worksheets (10%) honestly declared their standards do not reach the case:
Pentecostal 11, Anglican 6, Anabaptist 5, Reformed 4, Methodist 3, Lutheran 3, Baptist 2. The
Pentecostal number is structural: its corpus is topical position papers, dense exactly where its
divergences are (healing, abstinence, tithe) and silent on civic and digital questions. Q50
(cremation) is the one all-silent question in the set — no strand's standards legislate the
disposition of a body — which is itself a finding about where Protestant standards run out.
Silence matters for the merge: a consensus computed over non-silent columns rests on fewer
witnesses exactly where corpora are thin, and the unified source must say so per claim.

## 6. Verification

- **Citation audit** (fixed sample Q05/Q15/Q24/Q37/Q47 × 7 columns, guilty-until-confirmed,
  web-anchored against standard editions through search snippets where the egress proxy blocked
  direct fetches): **222 citations checked, zero fabricated loci**, 11 corrections and 6
  confidence-flag downgrades applied in place — an ~8% finding rate, none touching a Counsel
  field. The worst catches: an Anabaptist worksheet's gloss of Matt 5:39 that had flipped the
  strand's own nonresistance proof-text; a Lutheran attribution drift (Table of Duties → AC
  XVI); an Anglican claim of cross-province uniformity for Article XXXVII that TEC's 1801
  revision falsifies. Logs: [`audit/`](./protestant-guidance-divergence/audit/).
- **Blinding**: coders saw only pseudonymised, per-question-shuffled Counsel fields (seeded
  shuffle, regenerable byte-identically). Severity agreement 92%, partition agreement 88%,
  adjudication blind as well.
- **Reproducibility**: `prepare_packets.py` (blinding), `merge_codings.py` (adjudication merge),
  `analyze.py` (all aggregates) — every number above recomputes from the committed codings.

## 7. Limits

Declared before the run in [`method.md`](./protestant-guidance-divergence/method.md), now with
observed values:

1. **v1 scale.** Eight substance cases is enough to name areas, not to found a taxonomy. The
   dataset extends under the same schema.
2. **The frame drives D.** Civic life is 10% of the instrument (5/50) but carries a 60%
   substance rate; the corpus-wide census puts civic conflict at ~1–2% of where believers'
   troubles actually live. Excluding civic entirely, D falls to 11% (5/45); civic-only D is
   3/5. The frame was pre-registered, so 0.16 stands as *this instrument's* reading — but a
   census-weighted D would be lower, and anyone quoting "16%" should also say "of a frame that
   deliberately includes the civic terrain."
3. **One model family drafted all columns** (and coded them); the citation audit is sampled, not
   exhaustive; blinding cannot stop idiom from leaking strand identity into counsel prose.
4. **No human scholar review yet.** The per-column structure exists precisely so one reviewer
   per strand can review their own column; that review has not happened, and the worksheets
   remain first-draft ground truth with flagged confidence.
5. **Internal variation is folded, not resolved.** Where wings of a strand would counsel
   differently (69 worksheets flag it — e.g. Old Order vs MC USA, LCMS vs ELCA, SBC vs CBF), the
   column answered from its confessional center and recorded the spread in Notes.

## 8. The pathway — read mechanically off the pre-registered rule

[`pathway-rule.md`](./protestant-guidance-divergence/pathway-rule.md), committed before any
answers existed, binds this section.

- **D = 0.16** → the 15% ≤ D ≤ 35% band → **Pathway B**: unified bench + a first-class
  conditional-guidance tier, with a separate strand bench **only** for a strand that is the
  outlier on ≥ 20% of all questions.
- **No strand qualifies** (maximum outlier rate: Pentecostal at 10%), and no strand accounts for
  more than half of outlier appearances (Pentecostal, 29%). So Pathway B instantiates in its
  minimal form.

**Recommendation:**

1. **Build one bench: `protestant-unified`.** Its ground truth is compiled *with receipts* from
   these worksheets: the 39 same-advice questions (and the 3 emphasis questions, with the
   variant emphases recorded as acceptable) become consensus `judge-guidance.md`; per-claim
   receipts cite each strand's own loci, and claims resting on fewer witnesses (silences) say
   so. Validate the compiled source against the NAE Statement of Faith and the Lausanne
   Covenant per the refactor spec §3 — that validation also licenses the bench to serve
   nondenominational believers.
2. **The eight divergent questions get family-conditional guidance**, straight from the
   divergence map: an Anabaptist branch on the sword and the oath; a Pentecostal branch on the
   tithe and abstinence; the sabbatarian/non-sabbatarian fork on Sunday work; the three-way
   deadlock split on household decision-making; the fasting-rule exception inside the Q28
   safety floor. A model counseling a legible member of a strand is scored against that
   strand's branch; counseling an unmarked Protestant, against the envelope — crowning no
   faction.
3. **Do not build the seven-strand bench suite now.** The evidence does not warrant it: no
   strand's counsel is systematically its own across ordinary life. The per-strand worksheet
   columns — not benches — remain the living dataset, and they already deliver the suite's two
   real benefits at a fraction of the cost: per-strand reviewability and the divergence map.
4. **Revisit only on evidence**: a scale-up (more questions under the same schema, or the
   per-strand distinctive terrain the refactor spec §4 describes) that pushes D past 35%, or
   pushes a strand past the 20% outlier threshold — the Anabaptist column would be the first to
   watch if civic terrain is ever sampled at depth — reopens the strand-bench question with the
   same rule.

This lands where the simplicity instinct pointed — one bench, complexity only where the data
demands it — but with the difference that matters: the unified bench's content is now
**derived and receipted**, not composed freehand, and the 16% where "aggregate Protestantism"
would have been a fiction is handled as structured conditional truth instead of a vote.

## 9. The dataset

[`protestant-guidance-divergence/`](./protestant-guidance-divergence/):
`questions.md` · `method.md` · `codebook.md` · `pathway-rule.md` (the pre-registration) ·
`worksheets/<strand>/QNN.md` (350, audited) · `audit/` (4 logs) · `codings/` (four blind coders,
adjudicated disputes, merged `adjudicated.json`, `grounding.json`, `mapping.json`,
`agreement.json`) · `output/` (`summary.json`, `pairwise_agreement.csv`, `per_domain.csv`) ·
`prepare_packets.py` · `merge_codings.py` · `analyze.py`.
