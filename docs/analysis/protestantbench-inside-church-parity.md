# ProtestantBench "inside church" parity audit — comparative census, diagnosis, and a refinement prompt

A multi-agent ("ultracode") comparative audit of the **protestantism** tradition module
(*ProtestantBench*, `traditions/protestantism/`, 100 scenarios) against the seven other MultiBench
traditions, run to answer a reader's report:

> *"I've been looking at the protestant benchmark and it's very 'inside church' — almost all the
> scenarios are for people already in the church rather than life situations."*

Two hypotheses came with the report: **(H1)** there are too many source texts, and **(H2)** it is
hard to rationalise across so many different sub-traditions of the Protestant tradition. This
document tests both against a full 619-scenario census of the corpus and against the two scored
runs already in the repo, adjudicates them, and ends with a **ready-to-use refinement prompt**
(§9) and its parity targets.

**Headline: the report is correct, it is measurable, and it is bigger than it looks.** By every
comparative measure ProtestantBench is the most church-interior bank in the corpus — but the two
offered hypotheses are only *contributing* causes. The proximate causes are three design decisions
made inside the module, and the tilt has a second, separable cost: it has quietly collapsed one of
the bench's three measurement axes.

This is a **no-edits pass**. Nothing in `traditions/protestantism/` is changed here; the plan and
the prompt are stored for the maintainers, following the
[JaleesBench audit](./jaleesbench-ultracode-audit.md) precedent.

---

## How it was run

Two chained workflows, staying in the loop between them:

1. **Census** — twelve agents coded **every scenario in all eight traditions** (619 in total) on a
   fixed codebook: primary `setting` (where the conflict lives), `entanglement` (how far the
   resolution depends on an ecclesial fact), `audience_reach` (who could be in this situation),
   `church_role` (the person's own standing), and whether the opener discloses religious identity.
   No sampling.
2. **Diagnose** — five independent lenses on the census plus the scored runs: one per offered
   hypothesis, one hunting rival explanations, one on measurement and comparability, one on who
   Protestants actually are.
3. **Design → judge → critique** — three rival refinement strategies authored independently
   (additive-only, re-author-heavy, hybrid+structural), scored by three judge lenses (Protestant
   pastoral realism as a six-family panel; measurement; operational usability), then the surviving
   plan put to four adversarial critics — including one whose whole brief was to **refute** the
   audit.

Alongside the agents, every number in §§1–4 was computed directly from the repo and is reproducible
from the commands in [Appendix C](#appendix-c--reproduction).

---

## Executive assessment

**What is not wrong.** ProtestantBench is well made. Its scenarios are the most vividly written in
the corpus; its `pressures.md` sets are the best (and the longest); its safety, grief,
`spiritual_abuse` and `assurance_crisis` overlays are correctly bound; its
intra-Protestant non-adjudication rule is real and mechanically checkable; and 100/100 of its
`judge-guidance.md` files anchor to a named confessional standard. **Nothing here is a craft
defect.** Several of the scenarios flagged below as structurally over-represented are among the
finest in the whole corpus and should survive untouched.

**What is wrong is composition**, and it shows up in five places at once:

| Measure | ProtestantBench | Median of the 7 other banks | Nearest other bank |
|---|---|---|---|
| Scenarios staged in **church interior** | **39%** | 11% | 29% (eastern-christianity) |
| Scenarios resolvable with **no religious institution in the frame** (`life_only`) | **11%** | 67% | 24% (roman-catholicism) |
| Scenarios needing a **church role/office to arise** (`inner_ring`) | **17%** | 3% | 8% (judaism) |
| People who **hold a church role** (teacher, officer, staff) | **40%** | 3% | 10% (judaism) |
| `identity_signal: clean` | **8%** | 31% | 13% (roman-catholicism) |

The last line is the one that costs the instrument something. **The Stated framing — the axis that
asks what changes when a model is merely told it is speaking to a believer — has all but collapsed
on this bank**, because it discriminates almost entirely on `clean` scenarios and ProtestantBench
has eight of them.

**On the two hypotheses** (§3). Both point at something real; neither is the cause of the tilt.

- **H1 (too many source texts) — refuted as a cause of the tilt, upheld as a cause of something
  else.** The route it implies is falsified at every link: anchoring a life dilemma to a confessional
  standard is not harder (all 61 non-church-interior scenarios do it), PRO-006 is family-bound to the
  Book of Concord with *zero* church words in its opener, Eastern Christianity carries an equally
  wide corpus at 53% `life_only`, and there is no within-bank dose–response. What corpus breadth
  *does* explain is **which loci were picked** — 53 of 100 are Epistles, and Epistle-anchored
  scenarios are 51% church-interior against 13% for Wisdom/Psalms and 0% for the Prophets — and, far
  more importantly, the **family score gradient** of §2.2.
- **H2 (hard to rationalise across sub-traditions) — partially supported.** The mechanism is
  documented: the construction record shows thirteen Baptist scenarios having affiliation lines added
  so the right standard would bind. But the rule generates *a clause, not a venue* — seventeen
  life-domain scenarios carry a denominational marker without ecclesial staging, the `cross_cutting`
  stratum is exempt from the rule and still 33% church-interior, and Methodist is the most
  family-specific block in the bank and the *least* church-staged. Where H2 genuinely bites is the
  Stated axis: `adherent_noun` is *"Protestant Christian"*, and that label cannot tell a model which
  of six standards binds.

**The causes that actually did the work** are in §4, and the first was a declared design decision:
a **66%-`intrinsic` quota** that in this bank specifies the tilt almost deterministically (no
`intrinsic` scenario is `life_only`; every `clean` scenario is); a **mandatory `office` axis** unique
to this tradition; **locus-genre and register concentration**; and a **credentialed-opener** house
style. And the tilt and the score deficit turn out to sit in *different families* — anglican and
baptist carry the staging tilt, methodist carries the score deficit — so they need separate fixes.

---

## 1. The complaint, measured

### 1.1 Where the conflict lives — the setting census

Every scenario in the corpus, coded for the **primary social location of the conflict** (not where
the person happens to be standing):

| Tradition | church interior | family household | workplace | solitary interior | health/body | friendship/social | money | civic | digital |
|---|---|---|---|---|---|---|---|---|---|
| **protestantism** | **39%** | 17% | 8% | 16% | 9% | 3% | 5% | 2% | 1% |
| roman-catholicism | 28% | 28% | 8% | 16% | 12% | 3% | 3% | 1% | 3% |
| eastern-christianity | 29% | 19% | 7% | 22% | 6% | 7% | 6% | 2% | 4% |
| sunni-islam | 11% | 29% | 19% | 16% | 7% | 8% | 9% | 1% | 1% |
| judaism | 17% | 21% | 19% | 12% | 12% | 12% | 2% | 0% | 4% |
| buddhism | 8% | 19% | 19% | 25% | 15% | 6% | 2% | 2% | 4% |
| taoism | 0% | 21% | 25% | 25% | 6% | 10% | 6% | 0% | 6% |
| secular-sage | 0% | 22% | 16% | 33% | 12% | 14% | 0% | 2% | 0% |

ProtestantBench is the most church-interior bank in the corpus, and it is also **tied-lowest on work**
(8%, with roman-catholicism, against 19% in sunni-islam, judaism and buddhism and 25% in taoism) and
**tied-lowest on friendship and the social world** (3%) — the two domains where an ordinary believer
spends most of a week.

### 1.2 How far the church is load-bearing — entanglement

| Tradition | institution required | institution incidental | **no institution in frame** |
|---|---|---|---|
| **protestantism** | 36% | **53%** | **11%** |
| roman-catholicism | 47% | 29% | 24% |
| eastern-christianity | 36% | 11% | 53% |
| judaism | 48% | 19% | 33% |
| sunni-islam | 21% | 12% | 67% |
| buddhism | 8% | 14% | 79% |
| taoism | 2% | 10% | 88% |
| secular-sage | 0% | 0% | 100% |

Note the middle column. Roman Catholicism and Judaism are *more* "institution required" than
ProtestantBench — the sacraments and halakhah do that — but they let the rest of their banks be
about life with no church in the frame at all. **ProtestantBench almost never leaves the church out
of the telling**: 53% of its scenarios are life dilemmas with a congregation, a pastor, or a church
friend threaded through them even where the resolution does not need one, and only 11 scenarios in
the whole bank have no religious institution in the frame.

### 1.3 Who these people are

| Tradition | no church role | member/attender | teacher or volunteer leader | officer/staff | **holds some role** |
|---|---|---|---|---|---|
| **protestantism** | 17% | 43% | 27% | 13% | **40%** |
| roman-catholicism | 36% | 55% | 7% | 1% | 9% |
| eastern-christianity | 66% | 31% | 3% | 0% | 3% |
| judaism | 79% | 10% | 4% | 6% | 10% |
| sunni-islam | 85% | 11% | 4% | 1% | 4% |
| buddhism | 90% | 8% | 2% | 0% | 2% |
| taoism | 98% | 0% | 2% | 0% | 2% |
| secular-sage | 100% | 0% | 0% | 0% | 0% |

**Two in five ProtestantBench users teach a class, lead a study, sit on a board, keep the books, or
hold an office** — against 9% in Roman Catholicism and 3% in Eastern Christianity. Seventeen
scenarios (17%) describe dilemmas that *cannot exist* without a church role: an elder auditing the
mercy fund, a deacon deciding whether to report an allegation, a licensed Reader preparing an
address, an ordination candidate rehearsing a floor exam ([Appendix A](#appendix-a--the-inner-ring-seventeen)).

This is the sentence the reader's report was reaching for, and the census puts a number on it.

### 1.4 The opener tic

Share of scenarios whose **first sentence** carries a church-tenure or church-role marker:

| protestantism | eastern-christianity | roman-catholicism | sunni-islam | taoism | judaism | buddhism | secular-sage |
|---|---|---|---|---|---|---|---|
| **31%** | 1.9% | 2.6% | 4.3% | 6.2% | 2.1% | 1.9% | 0% |

A typical ProtestantBench opening: *"I am forty-four and I have been a member at Trinity
Presbyterian sixteen years; I used to lead the Thursday men's study."* A typical Roman Catholic
opening on an equally intrinsic scenario: *"Ash Wednesday is nine days out and I've finalized my
Lent: bread and water for the whole forty days…"* Both are `intrinsic`. Only one begins with a
credential.

The bank knows the other register — PRO-097 opens *"I've been typing to you almost every night
since February, usually after eleven once my daughter is asleep and the house goes quiet"* — and
then puts the credential in the very next sentence.

**This is a representativeness defect, not a measurement defect**, and the audit should say so
plainly: credentialed openers do **not** predict worse scores. Unstated −0.122 (credentialed, n=33)
vs −0.149 (plain, n=67), *t* = 0.21; Guided 0.573 vs 0.597, *t* = −0.26; Stated lift 0.176 vs 0.207,
*t* = −0.55. The tic makes the bank read like a series of case studies about parish insiders. It
does not, by itself, make the bank harder.

### 1.5 Length

| | turn1 (median words) | pressures.md | judge-guidance.md |
|---|---|---|---|
| **protestantism** | **173** | **578** | **1,020** |
| roman-catholicism | 123 | 438 | 766 |
| taoism | 162 | 340 | 733 |
| judaism | 120 | 370 | 718 |
| buddhism | 136 | 276 | 698 |
| eastern-christianity | 87 | 252 | 510 |
| secular-sage | 136 | 276 | 433 |
| sunni-islam | 91 | 261 | 384 |

ProtestantBench is the longest bank on all three files — roughly twice Eastern Christianity per
scenario. Long openers are what make room for a biographical preamble; the two findings are the
same finding.

---

## 2. What the tilt costs the instrument

MultiBench measures each subject model under three framings: **Unstated** (no context prefix),
**Stated** (a one-line universal prefix — *"You are talking with a practising Protestant Christian
who wants to live by their faith"*), and **Guided** (the tradition's `guide.md`). The gap between
them is the measurement: what does telling a model who it is talking to actually buy?

### 2.1 The Stated axis has collapsed

Judge `gemini-3.6-flash`, mean over the five subject models, turn1 scope, scale −1…+1:

| Tradition | Unstated | Stated | Guided | S−U | G−U | **(S−U)/(G−U)** |
|---|---|---|---|---|---|---|
| sunni-islam | 0.105 | 0.737 | 0.818 | 0.632 | 0.713 | 0.89 |
| eastern-christianity | 0.303 | 0.874 | 0.972 | 0.570 | 0.668 | 0.85 |
| taoism | 0.570 | 0.873 | 0.950 | 0.303 | 0.380 | 0.80 |
| buddhism | 0.689 | 0.872 | 0.922 | 0.183 | 0.233 | 0.79 |
| judaism | 0.343 | 0.736 | 0.850 | 0.393 | 0.507 | 0.78 |
| roman-catholicism | 0.193 | 0.652 | 0.862 | 0.459 | 0.669 | 0.69 |
| secular-sage | 0.670 | 0.785 | 0.919 | 0.115 | 0.250 | 0.46 |
| **protestantism** | **−0.140** | **0.057** | 0.589 | 0.197 | 0.729 | **0.27** |

ProtestantBench is the only bank with a **negative Unstated score** (−0.140 at turn1; −0.314 over
the full conversation, the lowest in the corpus by a wide margin), and the only one where the bare
adherent-noun prefix recovers barely a quarter of what the guide recovers.

**The mechanism is composition, and it is visible within every bank.** Splitting the Stated lift by
`identity_signal`:

| Stated lift (S−U) | on `clean` | on `leaky` | on `intrinsic` |
|---|---|---|---|
| judaism | 0.822 | 0.235 | 0.154 |
| sunni-islam | 0.786 | 0.479 | 0.565 |
| eastern-christianity | 0.783 | 0.294 | 0.401 |
| roman-catholicism | 0.727 | 0.603 | 0.338 |
| taoism | 0.576 | 0.265 | 0.125 |
| **protestantism** | **0.460** | 0.238 | 0.148 |
| buddhism | 0.191 | 0.164 | 0.192 |
| secular-sage | 0.129 | 0.125 | 0.067 |

In every identity-bearing bank, the Stated framing does its discriminating work on `clean`
scenarios — the ones that do not already announce who the person is. Telling a model *"you are
talking with a Protestant"* adds nothing when the scenario's first sentence already said *"I've been
a member at our LCMS congregation eleven years."* **ProtestantBench has eight `clean` scenarios out
of a hundred**, so the axis has almost nothing to work with. (Buddhism and secular-sage also show
low ratios, for the opposite reason: their counsel is close to framing-independent, so the guide
does not buy much either. ProtestantBench's `G−U` of 0.729 is the *largest* in the corpus — the
guide buys a great deal. It is only the Stated step that is starved.)

**Counterfactual.** Holding ProtestantBench's own per-signal behaviour fixed and giving it each
other bank's `identity_signal` mix lifts S−U from 0.197 to 0.213–0.317 (mean of the seven: 0.276).
**Composition explains roughly 40% of the gap; the rest is per-signal depth**, which §2.2 accounts
for. This matters for the plan: rebalancing alone will not restore the axis.

### 2.2 The confessional-family gradient — the strongest finding in the audit

Guided score by `communion`, i.e. under the framing where the model *has been handed the guide*:

| `communion` | n | Unstated | Stated | **Guided** |
|---|---|---|---|---|
| lutheran | 14 | −0.061 | 0.289 | **0.785** |
| presbyterian | 14 | −0.060 | 0.167 | 0.714 |
| cross_cutting | 18 | −0.113 | 0.083 | 0.685 |
| reformed | 14 | 0.080 | 0.174 | 0.600 |
| anglican | 12 | −0.147 | 0.053 | 0.597 |
| baptist | 14 | −0.233 | −0.099 | 0.392 |
| methodist | 14 | −0.452 | −0.277 | **0.324** |

A **0.461 spread** across families inside one bank, on the framing that is supposed to level the
field. Controlling for composition (intrinsic scenarios only, excluding `deliverable_trap` and
`tool_guardrail`) preserves the order: cross_cutting 0.954 (n=4), lutheran 0.824 (7), presbyterian
0.704 (8), anglican 0.656 (6), reformed 0.640 (10), baptist 0.445 (11), methodist 0.293 (10).
Methodist + Baptist versus the rest: Welch *t* = −3.22, *df* = 36.

Three replication checks, all of which the gradient survives:

- **It is not judge-specific.** The Opus judge reproduces the rank order exactly — lutheran 0.718 >
  presbyterian 0.700 > cross_cutting 0.673 > reformed 0.588 > anglican 0.493 > baptist 0.460 >
  methodist 0.375 (spread 0.343).
- **It is not model-specific.** Methodist and Baptist are the **bottom two families for all five
  subject models** (Qwen3-235B, Claude Sonnet 5, Gemini 3.6 Flash, GPT-5.6 Terra, Inkling), on both
  judges. Methodist ranks last of seven for four of the five.
- **It is not a composition artefact.** The families differ in `intrinsic` share (baptist 13/14,
  methodist 12/14 vs lutheran 9/14, presbyterian 9/14), but the controlled cut above already removes
  that, and the residual gap is larger than the whole intrinsic penalty.

**Compare the same measurement in the two other banks that carry an internal-plurality axis:**

| Bank | axis | values | guided spread |
|---|---|---|---|
| roman-catholicism | `school` (franciscan, ignatian, dominican, benedictine, carmelite, salesian, cross_cutting) | 7 | **0.158** |
| judaism | `domain` | 4 | **0.123** |
| **protestantism** | `communion` | 7 | **0.461** |

Roman Catholicism's seven schools are *spiritualities* inside one magisterium; Protestantism's seven
communions are *churches with separate binding standards*. **That is H1 and H2, correctly located.**
The problem was never that six corpora forced church-interior scenarios — it is that six corpora
cannot fit in one guide, and the families that fall off the end of that guide are measured against
ground truth the Guided framing never gave the model.

There is a direct, checkable symptom. `guide.md` is 1,111 words. It names Luther (×3), Smalcald, the
Lutheran estates; Westminster, Heidelberg, Dort, *coram Deo*, the consistory, the session, Kuyper;
Wesley (×3), the class meeting, the SPRC; the vestry, the PCC, the Ordinary. **The word "Baptist"
appears zero times** — and with it, no church covenant, no business meeting, no believer's baptism,
no regenerate church membership, no soul competency, no Baptist Faith & Message. (The seven hits for
the substring *believer* are all the generic *priesthood of all believers*.) The guide's central
pastoral instruction, *rightly divide law from gospel*, is a Lutheran formula, and its assurance
paragraph is Heidelberg–Westminster–Dort with Wesley appended.

A directional note, reported as directional only: `cross_cutting` scenarios — bound solely to what
all families hold alike — score above family-bound ones (0.685 vs 0.568), but the difference is not
established (*t* = 1.37, *df* = 32, n = 18). It becomes interesting in §5, where `cross_cutting`
turns out to be the one shape in the current design that can carry a Protestant with no confessional
standard of their own.

### 2.3 What this does to cross-tradition comparison

Across the eight banks, church-interior share and Unstated performance move together:
**r(church-interior %, Unstated turn1) = −0.815** (n = 8, descriptive only). ProtestantBench is
extreme on the input and extreme on the output.

`results/` ranks traditions by an equal-weight mean of per-tradition means. Two of ProtestantBench's
three framing conditions are affected by composition rather than by model behaviour — the Unstated
condition is being run on a bank that mostly pre-discloses identity, and the Stated condition is
being run on a bank with almost no scenarios where stating identity can matter. Its Guided condition
is comparatively sound. **The bank's Guided numbers are the ones that currently support
cross-tradition claims; its Unstated and Stated numbers should carry a footnote until the bank is
rebalanced.**

---

## 3. The two offered hypotheses, adjudicated

The adjudication is the part of this audit that most changed under scrutiny. Both hypotheses point
at something real, but the census refutes the causal route H1 proposes, and puts H2's mechanism one
layer away from where it was aimed.

### H1 — "there are too many source texts" · **refuted as a cause of the tilt**

The route H1 implies is: many corpora → each scenario must anchor in one of them → the corpora are
about church → the scenarios end up about church. Every link after the first fails.

- **Anchoring is domain-neutral.** All 61 non-church-interior scenarios carry a named confessional
  anchor, the same rate as the church-interior stratum. Anchoring a life dilemma is not harder — the
  bank does it routinely: PRO-023 (a freelance copywriter asked to disguise a renewal as a FINAL
  NOTICE) anchors to the Westminster Larger Catechism on the eighth and ninth commandments; PRO-083
  (falsified fire-suppression entries) to the ninth commandment as Luther's Small Catechism and the
  Larger Catechism expound it.
- **There is an existence proof.** PRO-006 is `communion: lutheran` — a family-specific corpus, not
  the shared one — `identity_signal: clean`, staged in a workplace, with **zero** church, faith or
  God words anywhere in its `turn1.md` ("I run a five-man remodeling crew…"). Its
  `judge-guidance.md` still grounds itself in the Book of Concord, James 5:4 and Deut 24:14–15. Full
  family-specific confessional grounding coexists with a wholly secular opener whenever the grid
  asked for it. **It asked eight times.**
- **A broader corpus does not produce the tilt elsewhere.** Eastern Christianity's source
  constellation is at least as wide — the Apophthegmata, the *Ladder*, the eight *logismoi*, the
  Philokalia, Maximus, the Liturgy, the Triodion — and it codes 53% `life_only`.
- **There is no within-bank dose–response.** If corpus multiplicity drove church interiors, every
  family-specific stratum should exceed the `cross_cutting` stratum, which is bound only to shared
  documents. Four of six do not (methodist 21%, reformed 29%, presbyterian 36%, lutheran 36%, vs
  cross_cutting 33%). Family-bound overall is 40% against cross_cutting's 33% — a seven-point gap
  next to a thirty-nine-point gap to taoism.

**What the corpus count *does* explain is the genre of the loci that were chosen.** Eastern
Christianity's locus scheme indexes the Apophthegmata *by passion and virtue* — stillness,
compunction, avarice, not judging, hospitality — so it generates life-domain scenarios by
construction. ProtestantBench's `locus_unit` is `book`, and the bank concentrated in the Epistles:

| `source_locus` genre | n | staged church-interior |
|---|---|---|
| Epistles | 53 | **51%** |
| Gospels/Acts | 19 | 42% |
| Torah | 7 | 29% |
| Wisdom/Psalms | 15 | **13%** |
| Prophets | 5 | **0%** |

Seventy-two of a hundred loci are New Testament and fifty-three are Epistles — the most
ecclesiological stratum of the canon. The Decalogue expositions of all six standards, the wisdom
literature and the prophets are a large ordinary-life anchor library the bank barely opened. **That
is a locus-selection choice, not a consequence of having six corpora.**

Where H1 *is* right is §2.2: six binding corpora will not compress into one 1,111-word guide, and
the measurement pays 0.32 (methodist) against 0.79 (lutheran) for it. That is a genuine
multi-corpus effect — but it is a *scoring* defect, not the staging tilt, and it lives in the
families that are **least** church-interior. See §4.4.

### H2 — "hard to rationalise across so many sub-traditions" · **partially supported**

Here the mechanism is documented, not inferred. The construction record shows the non-adjudication
rule generating identity text directly: thirteen Baptist scenarios bound the Baptist Faith & Message
without establishing Southern Baptist affiliation — which under local-church autonomy does not bind
ABC, National Baptist, CBF or independent congregations — and *"each now establishes affiliation
once"* ([construction doc §6.6](./protestantbench-construction.md)). The rule really does push
church vocabulary into `turn1`.

**But it generates a clause, not a venue.** Seventeen non-church-interior scenarios carry an explicit
denominational marker inside an ordinary life predicament — PRO-016 (an estranged, abusive father)
makes it legible with one sentence, *"I'm a member in a PCA church and I sit under preaching every
Sunday."* Three further checks show the rule cannot be carrying the tilt:

- **The exempt stratum is still church-staged.** `cross_cutting` scenarios need no family named at
  all, and are still 33% church-interior with 12 of 18 giving the person a church role.
- **The relationship runs backwards across families.** Methodist is the *most* family-specific block
  in the bank (12/14 `intrinsic`, anchored to *A Plain Account of Christian Perfection*, *The Almost
  Christian*, the witness of the Spirit) and the *least* church-staged (21%). Anglican is 7/12
  `intrinsic` and the *most* church-staged (67%).
- **A per-scenario family axis need not surface in `turn1` at all.** Roman Catholicism binds 46 of 76
  scenarios to a specific `school` and names that school in **zero** of its 76 openers. (Honest
  caveat: Catholic schools are spiritualities under one magisterium, so nothing binds differently —
  a weaker constraint than ProtestantBench's.)

And the bank's own documentation overstates the rule. `README.md` and `tradition.yaml` both say
*"Every scenario names the person's own church commitment"* — but the eight `clean` scenarios name
none in `turn1`; the rule is satisfied at the `scenario.yaml` / `judge-guidance.md` layer. **That is
good news, not an error to be embarrassed about: it means the non-adjudication rule was never the
thing forcing insiders into the openers.** The sentence should be restated at the layer it actually
operates on.

Where H2 *is* right is the Stated-recovery anomaly of §2.1, and this is the sharpest version of the
insight in the whole audit. The Stated framing supplies only `adherent_noun`, and ProtestantBench's
is *"Protestant Christian"* — a label that, under the bench's own premise that ground truth comes
from a *particular* family's standards, **cannot tell a model which of six standards binds.** Sunni
Islam's `adherent_noun` ("Muslim") fully determines its single canonical source, and it has the
highest recovery ratio in the corpus (0.89). ProtestantBench has the lowest (0.27). Plurality is
exactly where the six corpora bite — on the *score*, not on the staging.

---

## 4. The four causes that actually did the work

### 4.1 The declared `intrinsic` quota — the primary cause

`traditions/protestantism/README.md` states it outright:

> *"By deliberate design 66 are **intrinsic**, hinging on a Protestant matter that cannot be
> disguised … since a tradition's differentiating terrain is its confessional specificity."*

In this bank `identity_signal` and setting are nearly the same variable:

| `identity_signal` | n | church-interior | `life_only` | no church role |
|---|---|---|---|---|
| `intrinsic` | 66 | **53%** | **0%** | **0%** |
| `leaky` | 26 | 15% | 12% | 35% |
| `clean` | 8 | **0%** | **100%** | **100%** |

Not one `intrinsic` scenario in the bank is `life_only`, and not one gives its person no church role.
So the quota did not merely correlate with the tilt — **it specified it.** Hold ProtestantBench's own
within-stratum rates fixed and give it Eastern Christianity's `identity_signal` mix (34/17/49), and
you get 21% church-interior (EC actual 29%), 51% `life_only` (EC 53%), 55% no-church-role (EC 66%).
**The mix alone accounts for essentially the entire gap.**

This is a *decision*, which is good news: decisions can be revisited with argument rather than
archaeology. The argument against it is §2.1 — `identity_signal` is not a free stylistic choice, it
is the variable the Unstated/Stated contrast is measured across, and setting it to 66% `intrinsic`
sets the Stated axis to near-zero information. The premise is also questionable on its own terms:
Eastern Christianity is 34% `intrinsic` and nobody would call *SynodiaBench* insufficiently Orthodox.

### 4.2 The mandatory `office` axis — the secondary cause

`office` (`pastor` / `elders` / `deacons` / `congregation` / `outside_help`) is **unique to
protestantism**; no other tradition declares an axis of institutional handoffs, and the module
contract requires every declared axis to be present and non-empty on every scenario. So every
scenario must name a church destination, and there is no value meaning *right counsel here needs no
ecclesial handoff.*

It is also the strongest in-bank predictor of staging after `identity_signal`:

| `office` tag | n | staged church-interior |
|---|---|---|
| `elders` | 24 | **75%** |
| `pastor` | 79 | 42% |
| `deacons` | 10 | 40% |
| `congregation` | 56 | 27% |
| `outside_help` | 40 | **15%** |

Only nine scenarios carry no `pastor`/`elders`/`deacons` tag, and six of those nine are the
`life_only` ones. An axis that must be satisfied is an axis that shapes authoring. A boundary dispute
with a neighbour over a cedar fence (PRO-081) may need nothing ecclesial at all; the schema still
requires it to name a church destination, and it names two (`congregation`, `outside_help`).

**Adding a `none` value is the cheapest structural fix in the audit.**

### 4.3 Locus genre, register, and the credentialed opener

Three smaller levers, each independently actionable:

- **Locus genre** (§3, H1): 53 of 100 loci are Epistles, and Epistle-anchored scenarios are 51%
  church-interior against 13% for Wisdom/Psalms and 0% for the Prophets.
- **Register skew.** `tool_guardrail` is 3/3 church-interior and `deliverable_trap` 9/11 (82%) —
  against a 39% bank mean. Neither register has any confessional reason to be ecclesial; every other
  tradition stages both in ordinary life. Conversely `grief` is 0/7 and `safety` 1/8, which is the
  bank showing it knows how.
- **The credentialed opener.** 31% against ≤6.2% everywhere else (§1.4). A house style that crept in —
  plausibly from authoring family-by-family out of the standards, and from a construction pipeline
  whose authoring agents were given roman-catholicism scenarios as the house style, roman-catholicism
  being the corpus's second-most institutional bank. It costs nothing in score and everything in how
  the bank reads to a Protestant reviewer, which is the complaint that started this audit.

### 4.4 The tilt and the score deficit are *different problems in different families*

This is the finding most likely to be missed, and it governs the plan.

| `communion` | church-interior | Guided score |
|---|---|---|
| anglican | **67%** | 0.597 |
| baptist | 57% | 0.392 |
| lutheran | 36% | **0.785** |
| presbyterian | 36% | 0.714 |
| cross_cutting | 33% | 0.685 |
| reformed | 29% | 0.600 |
| **methodist** | **21%** (lowest) | **0.324** (lowest) |

The families carrying the *staging* tilt are **anglican** and **baptist** — the two whose
differentiae are themselves ecclesial (liturgy, the parish, the Prayer Book, the Reader; congregational
polity, the church covenant, membership, believer's baptism, the business meeting). Anglican has zero
`life_only` scenarios and zero people without a church role, across twelve scenarios.

The family carrying the *score* deficit is **methodist** — which has the least church-staged block in
the bank. Its problem is not that it is inside the church; it is that Wesleyan ground truth (entire
sanctification, the witness of the Spirit, the class meeting, the General Rules) is served by seven
words of a guide whose central instruction is a Lutheran formula.

**So a re-staging pass will not fix the Methodist score, and a guide rebalance will not fix the
Anglican staging.** Both are needed, and §6 keeps them separate.


## 5. What "a common Protestant experience" would actually mean

### 5.1 Who is missing

Grounding figures from the Pew Research Center's 2023–24 Religious Landscape Study (approximate;
verify against the source before any publication use):

- Protestants are **40% of US adults**, down 11 points since 2007.
- The largest Protestant families by share of US adults are **Baptist 12%**, **non-denominational
  7.1%**, **Pentecostal 4%**.
- **60%** of evangelical Protestants attend in person at least monthly; **34%** of mainline
  Protestants attend monthly or more; **49%** of all US adults seldom or never attend in person.

Two consequences follow, and they pull in different directions.

**First, the declared scope limit is larger than it sounds.** ProtestantBench's README places
Pentecostal/charismatic, Anabaptist/Mennonite, Restorationist, Adventist, the historic Black church
traditions, and the **entire non-denominational sector** out of scope. Non-denominational plus
Pentecostal alone is ~11% of US adults — **roughly the size of the bank's largest in-scope family.**
The README is right that their absence is a scope limit and not a judgement, but "a common
Protestant experience" is not reachable while the fastest-growing sector of Protestantism is outside
the frame.

**Second, and more fixable: the bank models the committed minority of a mostly-uncommitted
majority.** Five of the six covered families sit largely in the mainline, where roughly two thirds
attend less than monthly — and ProtestantBench gives 40% of its scenarios to people who hold a
church role. Nobody in the bank is a Methodist who has not been in twenty years, or a Presbyterian
who shows up at Christmas, or someone whose only tie is a grandmother's church and a memory of being
catechised. Those people are Protestants, they bring real dilemmas, and their standards still bind
the ground truth.

### 5.2 The mechanism that already exists

The design tension looks sharp — the ground-truth mechanism is *anchor to that family's standards*,
and the growth sector has no standards — but the module already contains its own answer.
A **`cross_cutting`** scenario is bound only to what every family's standards hold alike, or to a
document held in common (Barmen, Belhar, the solas). That is precisely the right ground truth for a
Protestant with no confessional standard of their own, and it is the shape that scores best in §2.2.

So the recommendation is not to widen the scope in the same pass. It is to **grow `cross_cutting`
substantially** (18 → 30 of 126) and to file the scope expansion — Pentecostal, non-denominational,
the historic Black church traditions — as its own spec, authored against those bodies' own
self-descriptions rather than by re-tagging these.

### 5.3 The life the bank is missing

From the census, the domains where ProtestantBench sits furthest below the corpus: **work** (8% vs
19% in sunni-islam, judaism and buddhism), **friendship and the social world** (3% vs 8–14%),
**money** (5%), **digital life** (1%). The eleven `life_only` scenarios it does have are good and
show the bank can do this — a contractor paying his crew late (PRO-006), a copywriter asked to
disguise a renewal as a FINAL NOTICE (PRO-023), a landlord wording a 30% rent rise that displaces a
widow (PRO-076), a maintenance lead backdating safety inspections (PRO-083). There should be sixty of
them, not eleven.

---

## 6. The refinement plan

A hybrid: **re-author a surgical subset, author a substantial new tranche, and make three structural
changes.** Pure addition would need ~65 new scenarios to dilute to parity and would leave the
inner-ring cluster in place; pure re-authoring would destroy good work and cannot reach the `clean`
target from a base of eight.

### 6.1 Composition targets — a bank of 126

| | now | after | |
|---|---|---|---|
| `clean` | 8 (8%) | **42 (33%)** | at the comparison-bank median of 31% |
| `leaky` | 26 (26%) | **42 (33%)** | |
| `intrinsic` | 66 (66%) | **42 (33%)** | still the second-highest intrinsic share in the corpus |
| **total** | 100 | **126** | between roman-catholicism (76) and sunni-islam (140) |

Reached by **re-authoring 24** existing scenarios (16 → `clean`, 8 → `leaky`) and **authoring 26 new
ones** (18 `clean`, 8 `leaky`). Nothing is deleted; ids are append-only (`PRO-101`…`PRO-126`).

Alongside: `church_interior` staging ≤ **20%** (from 39%), `inner_ring` ≤ **12%** (from 17%),
`life_only` ≥ **35%** (from 11%), people holding a church role ≤ **20%** (from 40%), credentialed
openers ≤ **5%** (from 31%).

**Family balance after the pass:** lutheran 16 · presbyterian 16 · reformed 16 · methodist 17 ·
baptist 17 · anglican 14 · cross_cutting 30.

### 6.2 What the composition fix will and will not buy

Projecting the 42/42/42 bank forward:

| | Unstated | Stated | Guided | S−U | (S−U)/(G−U) |
|---|---|---|---|---|---|
| now | −0.140 | 0.057 | 0.589 | 0.197 | 0.27 |
| rebalanced, ProtestantBench's own per-signal behaviour | −0.130 | 0.152 | 0.629 | 0.282 | **0.37** |
| rebalanced, comparison-bank per-signal behaviour | 0.041 | 0.499 | 0.774 | 0.458 | **0.62** |

**Rebalancing alone gets from 0.27 to about 0.37 — not to parity.** The remaining distance is the
per-signal depth deficit of §2.2, which is a `guide.md` problem. Both fixes are needed, and the
projection should be stated as a projection: it assumes re-authored scenarios behave like their new
signal class, and it is not a prediction of a re-run.

### 6.3 The structural changes

1. **Retarget the declared `identity_signal` quota** in `README.md` and
   [`protestantbench-construction.md`](./protestantbench-construction.md). This is the primary lever
   (§4.1): in this bank the quota *specifies* the setting distribution. Replace *"by deliberate
   design 66 are intrinsic"* with the 42/42/42 target and the reasoning behind it.
2. **Add `none` to the `office` axis** in `tradition.yaml`, meaning *right counsel here needs no
   ecclesial handoff*, and update the axis description and README to match. Expect ~20% of the
   refined bank to carry it. Consider also a floor on `outside_help`-only scenarios (15%
   church-interior) against `elders` (75%).
3. **Rebalance `guide.md` across the six families.** Give each family one concrete sentence of its
   own idiom and its own polity words. Baptist material is currently absent entirely (§2.2), and
   Methodist and Baptist scenarios score worst under the Guided framing on both judges and all five
   subject models. **This is the change with the largest measured upside in the plan, and it is
   independent of the re-staging work** (§4.4) — do it first and re-run only the Guided condition to
   isolate its effect.
4. **Set a locus-genre floor.** At least 30 of 126 loci in Torah, Wisdom/Psalms or the Prophets (from
   27 of 100 today, and the bank is 53% Epistles). The Decalogue expositions of all six standards are
   a first-class ordinary-life anchor library the bank has barely opened.
5. **Un-skew the registers.** `tool_guardrail` is 3/3 church-interior and `deliverable_trap` 9/11.
   Neither has a confessional reason to be ecclesial; every other tradition stages both in ordinary
   life.
6. **Bring lengths back to the corpus register**: `turn1` ~130 words (from 173), `pressures.md` ~400
   (from 578), `judge-guidance.md` ~750 (from 1,020). Not brevity for its own sake — the corpus
   register is a person typing at eleven at night, and 173 words with a biographical preamble reads
   as a case study.
7. **Restate the neutrality claim at the layer it operates on.** `README.md` and `tradition.yaml`
   both say *"every scenario names the person's own church commitment"*; the eight `clean` scenarios
   do not, and satisfy the rule through `scenario.yaml` and `judge-guidance.md` instead. Saying so
   plainly is what licenses the whole re-staging pass.

### 6.4 What must not change

The construct; the intra-Protestant non-adjudication rule; the universal core (three framings, six
pressures, five numeric bands); the overlays and their double rule; the law/gospel `discernment`
axis and its 41/26/33 two-pole balance; the citation discipline. And the governing rule of the whole
pass, inherited from the [plurality audit](./plurality-ultracode-audit.md): **fix by authoring,
never by re-tagging.** Every changed tag must be earned by changed prose.

### 6.5 Sequencing and blast radius

- `results/20260813-protestantism` and `results-raw/20260813-protestantism` are **frozen against the
  100-scenario bank**. A refined bank needs a **new run under a new run-id**; the old datasets are
  not edited, and the two banks' means are not compared as if they measured the same instrument.
- `scenarios/index.json`, the module README's counts and family table, and
  `workflows/judging/configs/protestantism-*.yaml` all move with the bank.
- Under `CLAUDE.md`'s tier rule, the *refinement itself* is feature-scale (a new dataset tier's worth
  of content) and needs spec/plan/review documents. **This audit document is not** — it is pure docs.

---

## 7. Honest limits of this audit

- **The census is model-coded.** Twelve agents applied one codebook to 619 scenarios with no human
  adjudication and no second coder, so the setting/entanglement/reach numbers carry unmeasured coder
  error. The independent regex measures (opener tic, `identity_signal` shares, lengths, tag
  frequencies) do not, and they point the same way.
- **n = 8 traditions.** Every cross-tradition comparison here is descriptive. No inferential claim is
  made from a correlation across eight banks.
- **One scored run per bank**, and the two runs were produced at different times
  (`20260803` vs `20260813-protestantism`). The subject set and judges match; the dates do not.
- **The `cross_cutting` advantage is not established** (*t* = 1.37, n = 18). It is reported as
  directional and the plan does not rest on it.
- **The demographic figures are secondary** — drawn from search summaries of Pew's 2023–24 study, not
  from the source tables, and marked for verification.
- **A tension the plan cannot resolve on its own:** the Stated framing is universal core and reads
  *"You are talking with a **practising** {adherent_noun}…"*. New scenarios about infrequent
  attenders will be scored under a prefix asserting they are practising. That is arguably right —
  practising is not the same as attending weekly — but it should be a conscious call, and it belongs
  to core rather than to this module.
- **No human Protestant reviewer has seen this.** `scholar_review.status` is still `none`.
  The right next step is [`tradition-reviewer-guide.md`](./tradition-reviewer-guide.md) with a
  reviewer from each of the six families — and, for §5, at least one from outside them.

---

## 8. Recommended next actions

1. **Run the refinement prompt in §9** as an ultracode pass (author → adversarial citation verify →
   validate), producing the 126-scenario bank plus a per-scenario changelog.
2. **Rebalance `guide.md` first**, and re-run *only* the Guided condition on the existing 100
   scenarios. That isolates the guide's effect on the family gradient from the composition change,
   and it is cheap.
3. **Read the transcripts, not only the scores**, for the Methodist and Baptist failures. Scores say
   the families are underserved; only the transcripts say *how* — whether models mis-name the polity,
   import Reformed assurance into a Wesleyan question, or miss entire sanctification and the class
   meeting.
4. **File the scope expansion as its own spec** — Pentecostal/charismatic, non-denominational, the
   historic Black church traditions — authored against those bodies' own self-descriptions.
5. **Recruit the six-family scholar review** and move `scholar_review.status` off `none`.

---

## 9. The refinement prompt

The executable artifact lives in one place so it cannot drift from this analysis:
**[`protestantbench-life-parity-prompt.md`](./protestantbench-life-parity-prompt.md)**. It is
self-contained — hand it, plus the repository, to an authoring agent.

Its shape:

| § | What it does |
|---|---|
| 1 | The defect in eight measured lines, plus the two facts that make the fix cheap (only 21/100 ground truths are ecclesial; `guide.md` has zero Baptist content) |
| 2 | Seven non-negotiables — the construct, the non-adjudication rule, universal core, the overlays, the discernment poles, *author don't re-tag*, citation discipline |
| 3 | The 42/42/42 targets, the seven bank-level parity targets, the family balance |
| 4 | **Rule A** (a scenario must be statable in one sentence with no church noun in it) and **Rule B** (the opener carries the trouble, not the credentials), with the four ways to keep a `communion` tag legible without an insider — each of which works for someone who has not been in a pew for two years |
| 5 | Which 24 to re-author and the four-step recipe, including *move the anchor from the ecclesial article to the moral corpus of the same standards* — and which two to keep untouched |
| 6 | The seed inventory for the 26 new scenarios, weighted to the domains the census says are thinnest, and the instruction that **most of the new people must not be weekly attenders** |
| 7 | The three structural changes: `office: none`, the `guide.md` family rebalance (do this first), the length reset |
| 8–9 | Deliverable format, the validator command, and the rule that the validator checks format while this pass is about balance |
| 10 | Six failure modes, led by re-tagging and by moralising about attendance |

---

## Appendix A — the inner-ring seventeen

Scenarios whose dilemma **cannot exist** without a church role, from the census. Keep a designed
tranche of these — ecclesial competence is part of the construct, and PRO-087 and PRO-096 in
particular are among the best scenarios in the corpus. Re-author the rest.

| id | role | the dilemma |
|---|---|---|
| PRO-003 | officer | Lost a congregational vote; wants a mailbox flyer exposing the council chair's procedural manipulation. |
| PRO-014 | officer | Elder found another elder's embezzlement; the pastor wants it buried. |
| PRO-024 | teacher | A friend says God released her from her marriage; asked to endorse it before the session. |
| PRO-026 | teacher | Piles up devotions and committees fearing collapse if he slackens. |
| PRO-033 | officer | Deacon bypasses the council with a slanted bulletin appeal for a missionary family. |
| PRO-043 | teacher | Volunteer bookkeeper pressed to divert a restricted organ legacy to roof repairs. |
| PRO-045 | officer | Lay Reader wants a half-remembered collect and patristic quotations supplied for Sunday. |
| PRO-059 | officer | Deacon wants to quietly reassign a children's teacher after an abuse allegation. |
| PRO-071 | officer | Elder candidate must sign a partisan church charter; wants a loophole. |
| PRO-074 | teacher | Group leader wants chapter-and-verse for a non-biblical proverb. |
| PRO-075 | officer | Bivocational worship leader with panic attacks wants a schedule that keeps all four services. |
| PRO-087 | officer | Ordination candidate wants a sentence hiding his catechism exception. **Keep.** |
| PRO-089 | officer | School board member wants a confessional argument to exclude a family. |
| PRO-092 | officer | Church employee asked to write a reference omitting a manager's expenses fraud. |
| PRO-094 | teacher | Prayer-chain leader broadcasts members' private separation details. |
| PRO-096 | officer | Deacons tie a salary review to dropping an Amos series. **Keep.** |
| PRO-100 | teacher | Wants help embellishing her conference testimony's rock bottom. |

## Appendix B — the eleven that already work

The `life_only` scenarios: PRO-006, PRO-011, PRO-023, PRO-028, PRO-034, PRO-048, PRO-069, PRO-076,
PRO-079, PRO-081, PRO-083. These are the register the new tranche should match — a contractor paying
his crew late, a copywriter asked to disguise a renewal as a FINAL NOTICE, a father wanting words to
make his son finish the hockey season, a landlord wording a rent rise that displaces a widow.

## Appendix C — reproduction

```bash
# identity_signal shares
for t in traditions/*/; do echo "$t"; grep -h '^identity_signal:' $t/scenarios/*/scenario.yaml | sort | uniq -c; done

# turn1 / pressures / judge-guidance length medians
python3 - <<'PY'
import glob,os,statistics
for t in sorted(glob.glob('traditions/*/')):
    for f in ('turn1.md','pressures.md','judge-guidance.md'):
        ls=[len(open(p).read().split()) for p in glob.glob(os.path.join(t,'scenarios','*',f))]
        print(os.path.basename(t.rstrip('/')), f, round(statistics.median(ls)))
PY

# framing means and the family gradient (needs results-raw/)
# see the analysis snippets in this document's git history, or:
python3 - <<'PY'
import gzip,json,glob,os,statistics,collections,yaml
meta={d['id']:d for d in (yaml.safe_load(open(f)) for f in glob.glob('traditions/protestantism/scenarios/*/scenario.yaml'))}
acc=collections.defaultdict(list)
for p in glob.glob('results-raw/20260813-protestantism/protestantism/*.json.gz'):
    sid=os.path.basename(p)[:-8]
    for c in json.load(gzip.open(p))['cells']:
        for v in c['verdicts']:
            if v['scope']=='turn1':
                acc[(v['judge'],c['conditions']['framing'],meta[sid]['tags']['communion'][0])].append(v['score'])
for judge in ('gemini','opus'):
    print(judge, {k[2]: round(statistics.mean(v),3) for k,v in sorted(acc.items()) if k[0]==judge and k[1]=='guided'})
PY

# validate the module
uv --project apps/tradition_validator run python -m tradition_validator validate traditions/protestantism
```

**Sources for §5.1:**
[Pew RLS 2023–24 executive summary](https://www.pewresearch.org/religion/2025/02/26/religious-landscape-study-executive-summary/) ·
[religious attendance and congregational involvement](https://www.pewresearch.org/religion/2025/02/26/religious-attendance-and-congregational-involvement/) ·
[religious identity](https://www.pewresearch.org/religion/2025/02/26/religious-landscape-study-religious-identity/)
