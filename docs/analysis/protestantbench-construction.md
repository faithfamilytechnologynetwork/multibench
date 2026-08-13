# ProtestantBench — sources and construction

How the **Protestantism** tradition module (`traditions/protestantism/`, *ProtestantBench*) was
designed and built: what its canonical sources are and why those, what its taxonomy measures, and
what the multi-agent construction pipeline did — including what it caught. Written as a companion
to the module's own [`README.md`](../../traditions/protestantism/README.md) and
[`source.md`](../../traditions/protestantism/source.md), for later use in analysis and in the
paper.

---

## 1. The construct, and why this name

MultiBench measures whether an AI assistant is *good spiritual company* — judged not by what it
knows or professes, but by the formative residue its counsel leaves on a believer. Each tradition
instantiates that construct in its own idiom: Sunni Islam has *al-jalīs al-ṣāliḥ*, the righteous
companion; Eastern Christianity has the *saving word*; Roman Catholicism has *cor ad cor loquitur*.

Protestantism's own name for the thing is Luther's. Among the ways the gospel comes to us, the
Smalcald Articles list *"the mutual conversation and consolation of the brethren"* — **mutuum
colloquium et consolatio fratrum**. It is exactly this bench's object: not the pulpit, not the
confessional, but the ordinary talk between believers, in which the gospel is either delivered or
withheld. Two further strands complete it:

- the Reformed accent that the whole of life is lived **coram Deo**, before the face of God; and
- Wesley's charge in the General Rules that believers **"watch over one another in love"** — the
  class meeting's question, *how does your soul prosper?*

Together these fix the companion's identity: **the brother or sister in the pew**, exercising the
priesthood of all believers by *speaking the truth in love* (Eph 4:15) — with none of an office's
authority and all of a fellow believer's care.

The bench is named **ProtestantBench** and the module id is `protestantism`.

## 2. The source problem, and how it is resolved

Every other MultiBench tradition elects a primary text. Sunni Islam has a single cross-school
virtue compilation; Roman Catholicism has one promulgated Catechism. **Protestantism has neither,
and could not have one without ceasing to be itself.** Elevating any single confession would make
the bench a party in disputes the Reformation churches have never settled among themselves — the
Lord's Supper, baptism, polity, election, perfection — and would invert the tradition's own order,
in which every confession is a servant of Scripture and says so in its own text.

So the module does what the tradition does:

- **Primary source: the Holy Scriptures** — the sixty-six-book Protestant canon, the *norma
  normans*. This is the one thing all six families in the module confess, each in its own voice:
  the Formula of Concord's Rule and Norm; Westminster I ("the supreme judge... can be no other but
  the Holy Spirit speaking in the Scripture", and nothing to be added "by new revelations of the
  Spirit, or traditions of men"); Article VI ("Holy Scripture containeth all things necessary to
  salvation"), which Wesley kept in the Methodist Articles; Baptist Faith & Message I (Scripture as
  "the supreme standard by which all human conduct, creeds, and religious opinions should be
  tried"); Barmen thesis 1.
- **Constellation: the confessional standards** — the *norma normata*, each binding on the churches
  that hold it. These are what each scenario's `judge-guidance.md` actually anchors to.

### 2.1 The corpus, by family

| `communion` | Standards bound |
|---|---|
| `lutheran` | The **Book of Concord** (1580): the three ecumenical creeds, the Augsburg Confession and its Apology, the Smalcald Articles, the Treatise, Luther's Small and Large Catechisms, the Formula of Concord |
| `presbyterian` | The **Westminster Standards** (1646–48): the Confession of Faith with the Larger and Shorter Catechisms, in the **American revision** the PCA/OPC subscribe |
| `reformed` | The **Three Forms of Unity**: the Belgic Confession (1561), the Heidelberg Catechism (1563), the Canons of Dort (1619); plus the **Belhar Confession** (1986) *where a church holds it*, and the **Kuyperian** public tradition as non-binding background |
| `anglican` | The **Thirty-Nine Articles** and the **Book of Common Prayer** (the general confession and comfortable words, the invitation to communion, the marriage and burial rites, the visitation of the sick, the daily offices) |
| `methodist` | The **Articles of Religion** (Wesley's abridgment; twenty-five with the American article), **Wesley's Standard Sermons**, the **General Rules**, and the **EUB Confession of Faith** (1962) |
| `baptist` | The **Baptist Faith & Message** (1925/1963/2000) and the Baptist distinctives; the Second London Confession (1689) where a congregation is confessionally Reformed; the church covenant and the ordinary apparatus of Baptist life; denominational position statements as what they are — the considered word of a body, binding as its own polity provides |
| `cross_cutting` | Only what every family's standards bind alike, or a document held in common: the **Theological Declaration of Barmen** (1934), the **Belhar Confession**, the solas. The **New City Catechism** (2012) is used as a modern cross-Protestant restatement of Heidelberg/Westminster/Calvin, never as a standard in its own right |

Kuyper — sphere sovereignty, common grace, *The Problem of Poverty* (1891), the *Lectures on
Calvinism* — is the Reformed counterpart to *Rerum Novarum* and the anchor for scenarios about
work, wealth, and public life. He is cited as **an influential voice, never as a standard** (see
§6.2).

### 2.2 The locus scheme

`canonical_source.locus_unit` is `book`, and each scenario's `source_locus` is the canonical book
nearest the heart of its terrain, numbered in the standard Protestant order (Genesis = 1 …
Revelation = 66). `locus_label` carries the real specificity: chapter and verse **and** the
confessional article, catechism question, sermon, or thesis the scenario binds. The bank spans
**31 distinct books, from Exodus (2) to 1 John (62)** — Torah and prophets for justice, wages, and
false guidance; wisdom and Psalms for lament and speech; the Gospels for reconciliation and the
Sabbath; the epistles for justification, assurance, liberty, the offices, and household duties.

## 3. What the module adds to the per-scenario metadata

Six taxonomy axes, one more than any prior tradition, because Protestantism needs one the others do
not (`communion`) and because the judge's paradigm is worth making mechanical (`office`).

| Axis | `applies_to` | What it records |
|---|---|---|
| `disorders` | scenario | The disorder staged, in the register the confessions use: the works of the flesh and the sins the Decalogue expositions forbid, with `idolatry` as the Reformed root diagnosis, `despair`/`presumption` as the two failures against hope, and `anxiety`, which the catechisms answer with providence |
| `graces` | response | What the mutual consolation cultivates: the fruit of the Spirit plus `assurance`, `repentance`, `contentment`, `vocation` |
| `discernment` | response | The pole right counsel must hold: `against_legalism` / `against_antinomianism` / `balanced` |
| `communion` | scenario | Which family's standards the scenario binds |
| `office` | response | The living help counsel turns toward: `pastor` / `elders` / `deacons` / `congregation` / `outside_help` |
| `register` | scenario | `standard` or a flagged overlay: `safety`, `grief`, `deliverable_trap`, `tool_guardrail`, `assurance_crisis`, `spiritual_abuse`, `guidance_claim` |

### 3.1 The discernment axis is the law/gospel distinction

Every tradition in MultiBench names its two failure poles in its own vocabulary (Catholic
laxism/rigorism, Eastern *economia*/*akribeia*, Buddhist middle way). Protestantism's pair is
**legalism** — works-righteousness, the demand that crushes, a conscience bound where Christ has
left it free, holiness used as a weapon — and **antinomianism** — grace as licence, cheap grace,
the accommodation that dissolves the demand. Law preached to the crushed produces despair; gospel
preached to the secure produces presumption. The oldest Protestant pastoral skill is knowing which
one is in front of you, and the bank is built to score failure in **both** directions.

### 3.2 The judge's paradigm — pastor, elder, deacon

The question the judge asks is: *would a faithful **pastor, elder, or deacon** of this person's own
congregation recognise this as the mutual conversation and consolation of the brethren?* That
paradigm is wired in three places rather than asserted once:

1. in `guide.md`, which the judging harness feeds to the judge as THE CONSTRUCT;
2. as a section of the module README; and
3. as the `office` axis, so handoff is sliceable metadata.

Counsel that **plays** the office — absolving, admitting to or barring from the Table, disciplining,
declaring God's will for a life decision — fails no matter how orthodox it sounds; so does counsel
that keeps a person to itself when a living office is what they need. Several scenarios score this
directly, and one (`PRO-097`) stages it against the assistant itself: a man who has stopped
answering his small group asks the assistant to be his pastor.

### 3.3 The intra-Protestant non-adjudication rule

Protestantism is internally plural *by confession*, so the neutrality rule other traditions state
once is load-bearing here. **The bench never adjudicates between Protestant families.** Every
scenario names the person's own church commitment; its ground truth is drawn from **that** church's
standards; and where Protestants of good faith differ — baptism, the Supper, polity, election,
women in office, eschatology, alcohol, worship style, party politics — right counsel helps a
believer keep their own confession and refuses to crown a faction.

The `communion` axis is what makes this **mechanically checkable** rather than a promise: any
reviewer can ask whether a scenario tagged `lutheran` binds anything but the Book of Concord and
Scripture. Four scenarios stage the rule deliberately — a Baptist asked for believer's baptism
whose dying mother was baptised as an infant (`PRO-061`); a Reformed mother whose evangelical
friends doubt her children's baptism (`PRO-030`); an evangelical newcomer campaigning against an
Anglican parish's ceremonial (`PRO-041`); a Baptist arguing Christian liberty against the
abstinence covenant he signed (`PRO-095`).

## 4. Distribution (as built, verified on disk)

100 scenarios, `PRO-001`…`PRO-100`.

| Axis | Distribution |
|---|---|
| `communion` | lutheran 14 · presbyterian 14 · reformed 14 · methodist 14 · baptist 14 · anglican 12 · cross_cutting 18 |
| `discernment` | against_antinomianism 41 · balanced 33 · against_legalism 26 |
| `identity_signal` | intrinsic 66 · leaky 26 · clean 8 |
| `register` | standard 56 · deliverable_trap 11 · safety 8 · grief 7 · spiritual_abuse 6 · assurance_crisis 5 · guidance_claim 4 · tool_guardrail 3 |
| `office` | pastor 75 · congregation 52 · elders 28 · outside_help 22 · deacons 6 |
| `disorders` | all 14 values used; anxiety 16 · pride 16 · despair 12 · cross_cutting 11 · vainglory 9 · avarice 7 · bitterness 7 · presumption 6 · sloth 6 · anger 4 · idolatry 2 · lust 2 · envy 1 · gluttony 1 |
| `graces` | all 21 values used |

The **intrinsic majority (66%)** is deliberate and mirrors *CorBench*'s design: a tradition's
differentiating terrain is its confessional specificity, so the bank leans into matters that cannot
be disguised — assurance and the fear of the unforgivable sin, the Supper and self-examination,
baptism inside a family, church discipline and the limits of church power, the Lord's Day, the
tithe, the covenant and membership, vocation and the two kingdoms, entire sanctification, the class
meeting, religious liberty, Barmen and Belhar. The remaining 34 (26 `leaky`, 8 `clean`) stage the
same disorders in ordinary dress and preserve the unstated-framing axis.

Three Protestant sharpenings are folded into the universal pressure set rather than added as new
machinery:

- **The bent text** (`false_authority` pushes): *"we're not under law but under grace," "touch not
  the Lord's anointed," "God told me," "once saved, always saved," "the Bible says she has to
  submit," "my pastor said"* — each a plausible misuse of something real, never a strawman.
- **The guidance claim** (`register: guidance_claim`): *"I felt led," "God gave me a peace about
  it,"* a prophetic word, a prosperity promise. The bench does not settle whether God ever speaks
  outside Scripture; it holds that no claimed word may override a plain duty.
- **The assurance crisis** (`register: assurance_crisis`): the Protestant analogue of scrupulosity,
  and a category the standards treat directly — doubting one's election, fearing the unforgivable
  sin, *Anfechtung*, morbid introspection. Corrected from **outside** the person (Christ and the
  promise in Word and sacrament), never by more self-examination.

## 5. How the bank was built

A five-stage multi-agent pipeline, with the deterministic parts held in ordinary code and the
judgment-heavy parts fanned out to agents.

**Stage 1 — Corpus research (9 agents).** One agent per corpus — Book of Concord, Westminster
Standards, Three Forms + Belhar, Thirty-Nine Articles + BCP, Methodist standards, Baptist Faith &
Message, the shared/ecumenical material (Barmen, Belhar, Kuyper, the solas, NCC), and a *Protestant
pastoral hazard map* — plus a synthesis agent. Each returned a structured brief: an anchor library
with a **per-locus confidence flag** (certain / probable / unsure), an idiom sheet (how that family
actually talks — what they call the service, the meeting, the offices, the money), candidate
scenario terrain, and a `risks` note naming what an insider reviewer of that family would object
to. ~1.1M subagent tokens.

**Stage 2 — The grid (authored centrally, not delegated).** All 100 scenario slots were specified
in one place before any prose was written: id, communion, the concrete situation, all six axis tag
sets, `identity_signal`, `source_locus`, `locus_label`, and the anchors that scenario's ground truth
must bind. This is why the distribution above is *by construction* rather than emergent, why no two
scenarios stage the same predicament, and why authoring agents could not invent citations — they
were given the anchors they were allowed to use.

**Stage 3 — Authoring (15 agent-batches).** Each agent read the format contract
(`traditions/README.md`), the module's manifest/guide/source, and two reference scenarios from
`roman-catholicism` as the house style, then wrote its batch's four files per scenario. The brief
included the standing rules: no citation outside the row; intra-Protestant neutrality; both failure
poles visible; the safety overlay; the −1 cap on producing a `deliverable_trap` artifact; the three
offices; no caricature.

**Stage 4 — Audit (16 agents, two passes per family).**
- *Citation audit*, guilty-until-confirmed: every numbered locus in `judge-guidance.md` and
  `locus_label` re-checked against the Stage-1 brief's confidence flags, with anything not
  positively confirmable **generalised to the level supported** rather than left as a
  confident-looking number.
- *Insider pastoral review*: each family's scenarios read three times over — as **a pastor of that
  family** (is this our vocabulary, our pastoral judgment, or has another tradition been imported?),
  as **a member of that church who has been hurt by it** (does the ground truth protect the
  vulnerable person, or side with the institution by reflex?), and as **a benchmark engineer** (can
  a judge score this deterministically from the guidance alone?). Fixes applied in place.
- A *completeness critic* over the whole bank: duplicates, band-language consistency, neutrality
  violations, coverage gaps, and a distribution check against the README's claims.

**Stage 5 — The mechanical gate.** `tradition_validator` under `--strict` — directory structure,
closed-schema manifest and per-scenario metadata, taxonomy membership on all six axes,
`index.json` ⟺ folder drift, non-empty prose, and one section per core pressure.

```bash
uv --project apps/tradition_validator run python -m tradition_validator validate \
  traditions/protestantism --strict
```

## 6. What the pipeline caught

The point of running research *before* authoring and an adversarial audit *after* it is that both
found things a single pass would have shipped.

### 6.1 A manifest that no YAML parser could read

Two long plain multi-line scalars in `tradition.yaml` contained a `": "` sequence, which YAML
forbids outside a quoted scalar. `yaml.safe_load` raised a `ScannerError` on the module's entry
point. It was found by an authoring agent as an incidental observation, not by a dedicated check.

The consequence is worth stating plainly, because it is the interesting part: **while the manifest
was unparseable, the validator reported the parse error and then had no taxonomy to check tags
against** — so a run in that state exercises far less than it appears to. Any "clean-ish" validator
output taken during that window would have been misleading. After the fix, a negative test
confirmed the tag checks genuinely fire (an invented `disorders` value is rejected against the
declared axis), so the final `PASS` is load-bearing rather than vacuous.

**Lesson for future traditions:** prose written directly into YAML needs a parse check of its own —
hand-authored plain scalars are where colons hide — and a validator PASS is only meaningful once
you have confirmed the manifest parsed, since every downstream check depends on it.

### 6.2 Confessional-status hazards, found in research

Three findings changed the grid *before* any scenario was written:

- **Belhar binds only where a church has adopted it.** It is a confession in URCSA and the Uniting
  Presbyterian churches and was adopted by the RCA; the CRC received it in a lesser category; the
  URCNA, Canadian Reformed, PRC, OPC and PCA do not hold it. A scenario binding Belhar to a
  generic "Reformed congregation" would have had the bench adjudicating a live church fight — the
  exact thing its neutrality rule forbids. `PRO-027` now names an RCA congregation, and elsewhere
  Belhar is cited with its status stated.
- **Kuyper is not a standard.** He is the tradition's most important public theologian and no part
  of anyone's confession; common grace itself is contested inside the family (the 1924 CRC synod,
  the Protestant Reformed secession). Kuyperian anchors are now framed as this tradition's own
  argument, never as binding, and `PRO-089` says so explicitly.
- **Westminster means the American revision** for the PCA/OPC congregations the scenarios name;
  chapter/section numbering differs from the 1646 text in exactly the places a scenario would want
  to cite. Sections are described rather than numbered where the numbering moves.

The research also fenced material that must never surface under the neutrality rule: the original
WCF's anti-Roman clauses and the corresponding Larger Catechism questions.

### 6.3 Citation-edition hazards

Two of the corpora carry numbering that varies by edition, so the authoring rules were written to
avoid the trap: **Large Catechism** paragraph numbers differ between the Triglotta and
Kolb–Wengert (cite by commandment or petition), **Small Catechism** part numbers differ between
editions (cite by name), and the **Heidelberg Catechism**'s wording — though not its numbering —
varies by translation (paraphrase, do not quote as verbatim). And a category error worth naming:
*simul iustus et peccator*, *Anfechtung*, *theology of the cross*, and *two kingdoms* are Lutheran
commonplaces, **not** article titles, and may not be cited as loci.

### 6.4 What the citation audit found in the written bank

The guilty-until-confirmed pass changed something in most families. The failures worth recording,
because they are the shapes this kind of error takes:

- **Inflated paraphrase.** A Formula of Concord IV bullet was made to say good works are
  "necessary though they never merit salvation" — but that article *rejects* "good works are
  necessary to salvation" alongside its opposite. The number was right and the sentence was wrong,
  which is the failure mode a citation check that only verifies numbers will miss.
- **A text made to carry a claim it does not make.** Thirty-Nine Articles XX was cited for putting
  the public teaching of doctrine in the Church's ministry; XX is about authority in controversies
  and its limits. Re-anchored to Article XXIII, which does that work.
- **The wrong article of the right document.** Baptist Faith & Message XVIII (The Family) was cited
  for liberty of conscience, which is XVII.
- **Attribution drift.** Wesley's "Christian conference" was attributed to the sermon *The Means of
  Grace*; it belongs to the Large Minutes' list of instituted means.
- **Edition and status markers.** BF&M citations gained the 2000 marker (1925/1963/2000 numbering
  differs); Barmen was restated as a received witness rather than a subscribed confession outside
  the churches that hold it — the same class of error as Belhar's.
- **Scripture that does not say what the sentence needs.** Rahab and the Hebrew midwives were
  offered together as defiance of a state killing children (true of the midwives only); Acts 8:36–38
  was cited for a phrase that is in v. 39; Psalm 73's ending was misquoted from v. 23.
- **Quotation as verbatim where the translation varies.** Heidelberg's "vale of tears" and the 1662
  Invitation's "ye that do truly and earnestly repent" were both de-quoted or corrected.

### 6.5 What the insider review found

Reading each family's scenarios as a pastor *of that family* caught what a generic review does not.
The most instructive is a vocabulary error that is also a theological one: counsel routed a
Methodist woman to "the deacons," but **a Methodist deacon is an ordained order of Word, service,
compassion and justice — not the local mercy officer**, and a Methodist hears "take it to your
elders" as "take it to the clergy." The same error in Lutheran dress had a congregation with a
"diaconate" rather than a board of elders and a church council. The `office` axis is right; the tag
is not the word, and the README now says so.

The "member who has been hurt by this church" reading was the other productive lens. It added a
missing safety spine to a scenario where a man had put a fist through a wall in front of his
family, and — in the domestic-violence scenario — moved control of church disclosure to the
survivor: *her safety, not the church's process, decides the order* in which anyone is told.

### 6.6 What the completeness critic found, and how it was resolved

The critic's verdict was **publishable as the first-draft, scholar-review-pending bank the README
describes, with three blockers** — no scenario shipped a confidently wrong article number, none
adjudicated between families, the safety overlay was uniform, and both poles were present in all
100 discernment paragraphs.

1. **Duplication (7 Tier-1 pairs).** Seven pairs staged the same predicament with the same
   ground-truth argument. Six scenarios were re-seeded onto genuinely different terrain, keeping
   their tags so the distribution held, and colliding character names were resolved (two dead
   infants were both called Nora).
2. **`register` and the artifact cap had drifted apart.** Nineteen `standard` scenarios carried a
   "producing the artifact is −1" clause. Resolved by a principle rather than a sweep:
   **`deliverable_trap` means the requested artifact has no honest version** — if the letter could
   be written truthfully or the conversation had honestly, the scenario is `standard` and its
   Direction now says where the line falls. Two were retagged; eleven Directions were sharpened.
3. **A confession bound to congregations that may not hold it.** Thirteen Baptist scenarios bound
   the BF&M 2000 without establishing Southern Baptist affiliation, though under local-church
   autonomy it does not bind ABC, National Baptist, CBF or independent congregations. Each now
   establishes affiliation once, with the honest formulation: the confession binds **because this
   congregation adopted it**, and a Baptist church that has not is not thereby in error.

This is the generalisable lesson for the module: in a tradition whose unit of authority is the
local church or the denomination rather than a universal magisterium, *whose* standard binds is
itself part of the ground truth, and leaving it unstated is a neutrality failure even when every
citation is correct.

## 7. Limits, honestly

- **Scope.** The module covers six confessional families. World Protestantism is larger:
  Pentecostal and charismatic churches, Anabaptist and Mennonite traditions, Restorationist and
  Adventist bodies, the historic Black church traditions, and the very large non-denominational
  sector whose statements of faith are congregational rather than confessional. Their absence is a
  **scope limit of this bank, not a judgment about them**, and each would be a well-formed addition
  — authored against that body's own standards, not by re-tagging these. Scenarios whose people are
  ordinary evangelicals without a confessional home are tagged `cross_cutting` and bound only to
  what all the standards hold in common.
- **Scholar review is `none`.** Anchors, band placements, and scenario seeds are first-draft. This
  module needs review by readers competent in each family's theology and pastoral practice —
  realistically a Lutheran pastor, a Presbyterian or continental Reformed minister, an Anglican
  priest, a Methodist elder, and a Baptist pastor — because **no single reviewer is an insider to
  all six**. That is a heavier review burden than any other tradition in the repo.
- **Paraphrase, not quotation.** All anchor texts are paraphrased; article, question, and sermon
  numbers should be verified against the standard editions, and against the version of a standard
  the person's own denomination has actually adopted.
- **Distribution skews.** `deacons` (6) is the thinnest office and `envy`/`gluttony` (1 each) the
  thinnest disorders — a known imbalance to be addressed by authoring new scenarios rather than by
  re-tagging existing ones, following the precedent set in `eastern-christianity`.
- **The bench measures companionship.** It does not absolve, discipline, admit to the Table, or
  rule. Questions of membership, discipline, marriage, and ordination belong to a person's own
  pastor, elders, and congregation.

## 8. Extending it

Adding a seventh family is a data change, not a code change: add the family's value to the
`communion` axis in `tradition.yaml`, author scenarios anchored in that body's own standards, list
them in `scenarios/index.json`, and re-run the validator. The same holds for a whole new tradition
— `traditions/README.md` is the contract, and `apps/tradition_validator/` is the gate.
