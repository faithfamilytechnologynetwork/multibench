# ProtestantBench refactor — seven strand benches and a derived unified bench

**Status: adopted decision spec, executable.** This document records the maintainers' decision on
the future of the `protestantism` tradition module (*ProtestantBench*) and specifies the full run
that executes it. It follows from three prior artifacts, which it presumes and does not repeat:
the [construction record](./protestantbench-construction.md), the
["inside church" parity audit](./protestantbench-inside-church-parity.md), and the
[life-parity refinement prompt](./protestantbench-life-parity-prompt.md). It **supersedes the
in-place execution** of that refinement prompt: the prompt's composition targets, authoring rules
(A / A′ / B), non-negotiables, and seed inventory are **imported here by reference** and applied to
the new modules instead of to the monolith. Do not run both.

**How to execute this spec.** Hand this file plus the repository to an executing agent session.
The phases in §5–§7 land as separate PRs, each carrying the Codev spec/plan/review trail where
feature-scale (`.github/PULL_REQUEST_TEMPLATE.md`, `CONTRIBUTING.md`). Two human gates are built
in: **G1** after Phase 0 (maintainers sign off the pre-registration pack before any answers are
generated) and **G2** after Phase 5 (maintainers review the divergence findings and the derived
unified source before module authoring at scale). Phases 0–5 are a **no-edits pass on
`traditions/`** — the live bench stays untouched while the study runs.

---

## 1. The decision, and why

**We are refactoring ProtestantBench from one 100-scenario module into a suite: one small bench
per major Protestant strand, each grounded solely in that strand's own confessional standards,
plus one unified Protestant bench whose source is *derived* — compiled from what all the strands'
standards confess in common, with receipts.** The derivation is itself a study (the same ~50
ordinary-life moral questions answered independently from each strand's corpus, then compared),
and that study is a publishable result in its own right, whichever way it comes out.

Why — each reason tied to a measured finding or a structural fact:

| Problem (measured / structural) | How the refactor resolves it |
|---|---|
| **One `guide.md` cannot carry six binding corpora.** Guided-framing family spread 0.461 (lutheran 0.785 → methodist 0.324), replicated on both judges and in nine of ten judge × subject cells; the guide named *Baptist* zero times and its universal assurance paragraph took Dort's side against the Thirty-Nine Articles XVI and Wesley (parity audit §2.2). | Each strand module has **its own** `guide.md` in its own idiom and polity vocabulary. The Guided framing hands every family its own standards **by construction**. The 0.461 spread stops being a defect inside one instrument and becomes a legitimate cross-bench measurement. |
| **The Stated axis collapsed** — recovery ratio 0.27 against a floor-regime peer mean of 0.80, because 66% of scenarios pre-disclose identity and the generic prefix "*practising Protestant Christian*" cannot name which of six standards binds (parity audit §2.1). | Per-strand `adherent_noun` makes the Stated prefix informative ("*a practising Lutheran Christian*" names the binding corpus), and the per-family-binding pressure that pushed affiliation clauses into openers disappears — `clean` becomes the default posture, which is the measured lever (clean recovers 0.60). |
| **The bank tilted "inside church"** — 39% church-interior against a corpus median of 11%, driven by the terrain rule ("confessionally specific" operationalised as "ecclesial") and the 66%-intrinsic quota (parity audit §4). | The shared parity core (§4 below) is authored **life-first** under the refinement prompt's Rule A; confessional specificity now lives in *whose ground truth answers*, not in ecclesial staging. |
| **No single reviewer is an insider to all six families** — the heaviest scholar-review burden in the repo (construction record §7). | Per-strand modules and per-strand worksheet columns decompose review perfectly: one reviewer per strand reads only their own column. |
| **The intra-Protestant plurality question was unresolved** — merge answers into an aggregate, or keep per-family truth? | Both, in their right places: strand benches keep each family's own answer (no adjudication); the unified bench holds only the **demonstrated intersection**. Divergence is *measured* (the study), never voted away. |

**Why not patch the monolith in place.** The refinement prompt fixes composition (setting, signal,
length) but cannot fix the structural mismatch of per-family ground truth scored under one shared
guide — that mismatch is the 0.461 spread, and it is inherent to one-module-many-standards.

**Why not a single merged bank.** A single "universal Protestant" ground truth must either vote
(adjudication by arithmetic — exactly what the non-adjudication rule forbids) or flatten to a
lowest common denominator (the genericising failure mode the parity audit names). And it deletes
the suite's ability to measure whether a model can serve a *particular* believer by their own
church's lights — the construct is the residue counsel leaves on a believer, and a believer is
always a particular one.

---

## 2. The strand taxonomy

Six confessional strand modules now, one deferred, one derived. Scripture (the sixty-six-book
canon) remains the **primary source** (*norma normans*) of every module, exactly as the
construction record §2 argues; the table below lists each strand's **constellation**
(*norma normata*). Authority-status language follows the construction record's discipline: a
standard binds **as the body holding it provides**, and where adoption varies (Belhar, BF&M,
Book of Discipline) *whose* standard binds is part of the ground truth (construction §6.6).

| Module id | Strand | Confessional constellation | Seed from current bank | Id pattern | `adherent_noun` (default) |
|---|---|---|---|---|---|
| `lutheran` | Lutheran | The Book of Concord (1580) | 14 (`communion: lutheran`) | `LUT-\d{3}` | Lutheran Christian |
| `reformed-presbyterian` | Reformed / Presbyterian | The Westminster Standards (American revision where PCA/OPC subscribe) + the Three Forms of Unity; Belhar **where adopted**; Kuyper as non-binding background | 28 (`presbyterian` 14 + `reformed` 14) | `RFP-\d{3}` | Reformed Christian |
| `anglican` | Anglican | The Thirty-Nine Articles + the Book of Common Prayer (1662 as the classic standard; status varies by province — "historic formularies") | 12 | `ANG-\d{3}` | Anglican Christian |
| `baptist` | Baptist | The Baptist Faith & Message (1925/1963/2000, binding **where a congregation or convention adopts it**), the Second London Confession (1689) where confessionally Reformed, the church covenant | 14 | `BAP-\d{3}` | Baptist Christian |
| `methodist-wesleyan` | Methodist / Wesleyan-Holiness | The Articles of Religion, Wesley's Standard Sermons, the General Rules, the Large Minutes, the EUB Confession; Holiness extensions: the Nazarene Articles of Faith / Manual, the Wesleyan Church Discipline; the UMC Book of Discipline for the mainline body | 14 | `MTH-\d{3}` | Methodist Christian |
| `pentecostal` | Pentecostal | The AG Statement of Fundamental Truths + AG position papers; the Church of God (Cleveland) Declaration of Faith; the Foursquare Declaration; the COGIC Statement of Faith | 0 (new) | `PNT-\d{3}` | Pentecostal Christian |
| `anabaptist` | Anabaptist *(study column now; bench deferred — see §11)* | The Schleitheim Confession (1527), the Dordrecht Confession (1632), the Confession of Faith in a Mennonite Perspective (1995) | 0 | `ANB-\d{3}` | Anabaptist Christian |
| `protestant-unified` | Unified (derived) | **The derived common-witness source** (§3): the demonstrated intersection of the strand columns, with receipts; the ecumenical creeds as shared inheritance | 18 (`cross_cutting`) | `UNI-\d{3}` | Protestant Christian |

Three taxonomy decisions are **recorded here so they are not relitigated downstream**:

1. **Baptist and Anabaptist are separate columns, never merged.** The lineages are partly
   distinct (1689 is Westminster-with-Baptist-edits; Schleitheim is 1527), and the pastoral
   divergence is confessional: nonresistance and the refusal of oaths are articles for Anabaptists
   (Schleitheim VI, Dordrecht XIV) and absent for Baptists. A merged "Free Church" ground truth
   would either carry a permanent conditional branch on peace, oaths, and separation, or paper
   over exactly the kind of difference this project exists to surface.
2. **The sixth strand is "Pentecostal," not "Pentecostal/Charismatic."** Classical Pentecostal
   bodies have standards; the charismatic renewal is a movement across denominations, not a body
   with a book — a charismatic Anglican is an Anglican. COGIC's inclusion gives the strand part of
   the historic Black church coverage the construction record §7 flagged as absent; the Black
   Baptist and Methodist bodies belong to their lineage strands, and the module READMEs should say
   both things rather than staying silent.
3. **Nondenominational Christianity is the unified bench's constituency, not a strand.** Having no
   binding book is constitutive of the category; any corpus assigned to it would be an editorial
   fiction. Instead the unified bench serves it, and the category supplies the **validation test**
   in §3. The old module README's scope-limit paragraph (Pentecostal, Anabaptist, Restorationist,
   Adventist, historic Black church, non-denominational) is thereby half-resolved and half-carried:
   Restorationist and Adventist bodies remain out of scope, stated as a scope limit and not a
   judgment, each a well-formed future strand.

**Per-strand constructs.** The current construct decomposes into its own sources: *mutuum
colloquium et consolatio fratrum* is Luther's (Smalcald III.4) and belongs to `lutheran`;
*coram Deo* to `reformed-presbyterian`; "watch over one another in love" (the General Rules) to
`methodist-wesleyan`. Each module states the companion construct in its own idiom **derived from
its own texts with citations** — candidates to verify, not to assert: the church covenant's "watch
over one another in brotherly love" (Baptist), the Prayer Book's "mutual society, help, and
comfort" and the comfortable words (Anglican), the edification of the body in 1 Cor 14:26
(Pentecostal), *Gelassenheit* and mutual aid (Anabaptist). The unified module keeps the
pan-Protestant statement: the priesthood of all believers speaking the truth in love.

---

## 3. The unified bench and its derived source

The unified source is **"akin to the Nicene Creed" in the precise sense that it is received, not
composed**: it earns its standing the way the creeds did — as *what all confess* — and the study
in §5 is the derivation procedure. Discipline, in order of load-bearing-ness:

1. **Output, never input.** The unified source is compiled from the strand worksheet columns
   (§5), each claim carrying receipts — citations into *every* strand's standards that ground it.
   It is not written first and checked later; nothing enters it that the columns do not
   demonstrate.
2. **Status honesty**, in the register the construction record used for Belhar, Kuyper, and the
   New City Catechism: the document is the bench's own derived instrument. It **binds no church**,
   describes overlap, and says so in its first paragraph. It binds *content*, not creedal *form* —
   several strands affirm creedal content while rejecting creeds in principle ("no creed but the
   Bible"), and the source must note that rather than embarrass them.
3. **The validation test.** After derivation, check the intersection against the two real
   documents pan-evangelicalism actually subscribes in the aggregate: the **NAE Statement of
   Faith** and the **Lausanne Covenant**. Agreement is evidence that "aggregate Protestantism" is
   a real object rather than a pipeline artifact — a validation section for the paper — and it is
   what licenses the unified bench to serve the nondenominational population. Divergence is
   reported, not hidden.
4. **The non-adjudication rule relocates to the suite level.** Within a strand bench it is no
   longer needed — ground truth is unambiguous. At the suite level it is absolute: the suite never
   ranks strands against each other theologically; models are ranked, strands are contexts; the
   unified source is **intersection, not arbitration**.

---

## 4. The two-block scenario design

Every strand module carries two blocks:

- **The shared parity core** — the study's ~50 ordinary-life questions (§5), **identical stimuli
  in every module**, each with that strand's own `judge-guidance.md` compiled from its worksheet
  column. Identical scenarios with varying ground truth make the suite a controlled instrument:
  score differences across strands are attributable to ground-truth differences, not scenario
  differences. No tradition in the corpus currently has this property.
- **A distinctive tranche per strand** — the terrain only that strand can stage: assurance and
  perseverance for `methodist-wesleyan`, prophecy and guidance claims for `pentecostal`, the
  Supper and *Anfechtung* for `lutheran`, nonresistance for `anabaptist`, believer's baptism and
  the covenant for `baptist`, the Prayer Book rites for `anglican`, election and the covenant
  child for `reformed-presbyterian`. This preserves what the current bank did best (its
  `intrinsic` craft), now staged per the refinement prompt's Rule A′ — confessional depth without
  the insider tilt.

**Cross-module linkage.** Parity-core scenarios share a `parity_key` so the suite can join them
across modules. The per-scenario metadata schema is **closed** in the validator — so Phase 0 must
decide the mechanism: extend the validator schema with the optional field (small code change +
negative test, run the validator's own suite via the per-builder dispatcher), or carry the mapping
in a suite-level index file. Default: extend the validator — the field is load-bearing data, and
side-tables drift.

**Composition rules — imported wholesale from the refinement prompt** and applied per module:
Rule A (statable in one sentence with no church noun), Rule B (the opener carries the trouble, not
the credentials), `clean` as the default posture with signal balance per module, the length
targets (turn1 ~130 words, `pressures.md` ~400, `judge-guidance.md` ~750), the register mix and
overlays with the safety double rule, the locus-genre floor (open the Decalogue expositions,
wisdom literature, and prophets), and the difficulty bar: **ordinary-life staging does not mean
easy** — the monolith's `life_only` scenarios score *worse* than its mean (−0.256 Unstated);
every scenario must keep a genuine wrong answer a fluent model would give.

---

## 5. The divergence study (Phases 0–5) — and the paper

**The claim under test** (pre-registered in Phase 0): *the strands' theological differences mostly
do not produce different pastoral advice in ordinary life; where they do, the divergence
concentrates in a small number of nameable areas.* The parity audit half-corroborates this by
construction — where the families agree (the Decalogue expositions, vocation, providence, the use
of money) *is* the ordinary-life material — and supplies the known counterexamples that must be
reachable by the sampling frame: assurance and falling from grace, alcohol, divorce and
remarriage, guidance claims, the Lord's Day, nonresistance.

### Phase 0 — the pre-registration pack (gate G1)

One PR, committed **before any answers are generated** — git history is the timestamp, and
pre-registration is what makes the headline publishable rather than post-hoc. Contents:

- **The sampling frame**: a domain × disorder grid drawn from the 619-scenario census's
  life-domain distribution (work, family/household, money, body/mind, friendship/social, digital,
  the interior) crossed with the `disorders`/`graces` taxonomy. Hotspot domains enter **through
  the frame, not by hand**; report per-domain divergence alongside any headline percentage.
- **The question grain**: concrete pastoral situations, one-sentence-statable with no church noun
  (Rule A) — *not* abstract doctrine questions; abstract questions find divergence trivially and
  prove nothing about pastoral advice. Questions are authored as **proto-scenarios** (a person, a
  situation, an opener draft) so the study set upgrades into the parity core without rewriting.
- **The worksheet schema** (§5-W below), **the divergence codebook** (§5-C), the strand taxonomy
  of §2 locked (including adherent nouns), the module layout and id patterns, the `parity_key`
  mechanism decision, and the leaderboard rule of §7 stated as adopted.
- **The count**: 50 questions default; see §11.

### Phase 1 — corpus briefs, committed this time

The original build's Stage-1 briefs — anchor libraries with per-locus confidence flags
(certain / probable / unsure), idiom sheets, and risk notes — **were never committed**; they
survive only as descriptions in the construction record. Regenerate them (~1.1M subagent tokens
for nine agents last time), add the `pentecostal` and `anabaptist` briefs, and **commit them** as
the citation ground for every downstream worksheet. They are single-strand human-reviewable.

### Phase 2 — pilot: 5 questions × 8 columns, end-to-end

Full pipeline on five questions: author → eight independent worksheets → guilty-until-confirmed
citation audit → blind double coding → adjudication. Purpose: shake out the worksheet format
(especially the silence option and confidence flags), measure inter-coder agreement, recalibrate
cost. Fix the schemas *here*; Phase 3 runs them frozen.

### Phase 3 — the full run

The remaining 45 questions × 8 columns (~400 worksheets total including the pilot). Rules:

- **Column independence**: an answering agent sees only its own strand's brief and corpus — never
  another column's answer.
- **Anchored, not recalled**: every claim cites loci from the brief with its confidence flag
  carried through; the construction record's §6.4 failure catalogue (inflated paraphrase,
  right-number-wrong-sentence, attribution drift, edition hazards per §6.3) is the audit
  checklist, applied guilty-until-confirmed to every worksheet.
- **Silence is an answer**: a strand whose standards do not address the case codes as *silent* —
  forcing an answer manufactures fake consensus or fake divergence; the aggregate for that
  question then rests on fewer columns, and that is data.
- **Cross-model verification**: worksheets drafted by one model are citation-verified and coded by
  a different one (the `consult` machinery exists for this); report coder agreement in the
  methods, and disclose the shared-prior contamination risk there too.

### Phase 4 — analysis and the paper artifacts

`experiments/<PR#>_protestant_divergence/` in the house convention (`notes.md`, `analyze.py`,
`data/output/`), plus a narrative document in `docs/analysis/`. The money outputs: the **2×2**
(advice same/different × grounding same/different — the colleague's thesis lives in
*same-advice-different-grounding*), per-domain divergence rates, the clustered divergence areas,
and the **routing table**: every question classified consensus / family-conditional / contested.

### Phase 5 — derive and validate the unified source (gate G2)

Compile the unified source from the consensus tier with receipts (§3), run the NAE/Lausanne
validation, and put the findings plus the derived source to the maintainers before Phase 6.

### 5-W. The worksheet schema

Per question × strand: `question_id` · `strand` · **counsel** (what the standards *require /
license / forbid* here) · **loci** (each with confidence flag and edition note) · **idiom** (what
this strand's pastor would actually say — vocabulary, not doctrine) · **silence** (explicit,
when the standards do not reach the case) · `reviewed_by` (empty until scholar review). Worksheets
are authored **as draft per-strand `judge-guidance.md`** from day one, so Phase 6 ports them by
formatting, not rewriting.

### 5-C. The divergence codebook

Coded blind to the hypothesis, double-coded, agreement reported: **advice** (same / conditionally
different / different) × **grounding** (same / different), plus *silent* per column. **The merge
operator is a structured union, never a vote**: consensus core (all non-silent columns agree) /
family-conditional (counsel differs by strand, keyed to what the scenario makes legible) /
contested (an envelope of faithful options, every one acceptable, crowning none). No majority
voting and no population weighting — adjudication by arithmetic is still adjudication.

---

## 6. Building the modules (Phase 6)

- **Quarry, don't discard.** The current 100 scenarios decompose by their `communion` tag into
  strand seeds per the §2 table, re-staged on port under the refinement prompt's rules, with
  **fresh ids** in the new modules. The re-tagging guard from the prompt's §9 applies: every
  changed tag earned by changed prose.
- **Freeze `traditions/protestantism` on disk.** The raw viewer fetches `judge-guidance.md` live
  from HEAD for the frozen `20260813-protestantism` datasets (parity audit §9.1) — keep the folder
  so the viewer resolves, retire it from active scoring, and say so in its README and in
  `results/README.md`.
- **Each module is a full canonical tradition**: `tradition.yaml` + `guide.md` + `source.md` +
  `README.md` + scenario folders, scaffolded per the `create-tradition` contract and passing
  `uv --project apps/tradition_validator run python -m tradition_validator validate
  traditions/<id> --strict`. Per-strand taxonomies keep `disorders` / `graces` / `discernment` /
  `register`; the `communion` axis dies (module identity replaces it); the `office` axis is
  adopted **with the `none` value** (refinement prompt §7.1) and each module's own polity
  vocabulary in its description.
- **Each `guide.md` is ~1,100 words in the strand's own idiom** — the whole point of the
  refactor; the guide-budget arithmetic that failed at six families succeeds at one. Carry the
  refinement prompt's §7b amendment (the measure reaches a person who has not been in a pew in
  years) into every guide.
- **The unified module** seeds from the 18 `cross_cutting` scenarios plus the consensus-tier
  parity core; its `source.md` is the derived common witness with the §3 status paragraph.

## 7. Scoring and datasets (Phase 7)

- **Decouple building from scoring.** The study needs no model-scoring at all. When scoring
  starts, stage it: **`protestant-unified` first** (it is the headline and the cross-faith row),
  strands as budget allows — the strand modules are valuable as committed ground-truth datasets
  before any run touches them. Full battery per the Spec 89 convention (5 subjects × 6 pressures ×
  3 framings, both scopes, dual-judge); seven strand benches at ~50 scenarios ≈ 3.5× the Spec 89
  round — budget deliberately.
- **The leaderboard rule, adopted now, before any joint export**: the cross-faith leaderboard is
  an equal-weight mean of per-tradition means, and eight Protestant rows would make one faith half
  the corpus. **Only `protestant-unified` contributes to cross-faith leaderboards; strand runs are
  a family-internal comparison surface** (their own runs and views; any future grouped display in
  the SPA is its own spec). New run-ids always; `results/20260803` is never mutated (the
  leaderboard test pins it to the paper to nine decimals); `20260813-protestantism` stays as the
  monolith's record.

## 8. Guardrails

- **The judge seam holds.** Worksheets and briefs are authoring artifacts and a committed dataset;
  each scenario's `judge-guidance.md` remains the judge's **only** runtime ground truth. Do not
  reintroduce a proof-text corpus.
- **Universal core untouched**: three framings, six pressures, numeric bands, no band names in
  prose. The refactor is data-tier only — modules are drop-in directories; core code changes are
  limited to the optional `parity_key` validator field.
- **Citation discipline everywhere**: never invent Scripture, an article, a catechism answer, or a
  Reformer's words; paraphrase-hedge as the existing bank does; name editions.
- **Scholar review is now tractable — start recruiting at Phase 0**, longest lead time in the
  plan: one reviewer per strand, sampled worksheets (≥10 of 50) plus their strand's guide and
  distinctive tranche. This is the path off `scholar_review: none`.
- **Insider register**: each strand's scenarios and worksheets must read as that strand's own
  (the construction record's three-lens insider review — pastor of the family, member hurt by the
  church, benchmark engineer — applies per module).
- **Intra-strand splits are handled by adoption, not adjudication** (construction §6.6): where a
  strand's bodies divide (UMC/GMC, ELCA/LCMS, SBC/CBF), the scenario names whose standard binds
  because *this* congregation or body holds it, and a body that does not is not thereby in error.

## 9. Success criteria

1. Pre-registration demonstrably precedes answers in git history; G1 and G2 sign-offs recorded.
2. Every worksheet claim cited-with-confidence or explicitly silent; audit pass completed;
   inter-coder agreement reported.
3. The 2×2, per-domain rates, clustered divergence areas, and routing table published under
   `experiments/` + `docs/analysis/`.
4. The unified source carries receipts into every strand column and reports the NAE/Lausanne
   validation either way.
5. Every landed module passes the validator `--strict`; parity-core stimuli are byte-identical
   across modules; each module's guide is its own strand's.
6. The quarry is complete (all 100 monolith scenarios either ported with fresh ids or explicitly
   retired with a reason); `traditions/protestantism` and both frozen result tiers untouched.
7. The leaderboard rule is enforced in the first joint export.

## 10. Failure modes to guard against

- **Vote-merging** — any "5 of 7 strands say X, so X" reasoning in the unified source or a
  conditional scenario's guidance. The union is structured; minorities are named, never outvoted.
- **Silence-forcing** — a worksheet that answers where its standards are silent, manufacturing
  agreement or divergence. The audit checks for it explicitly.
- **Hotspot cherry-picking** — divergence-prone questions entering outside the pre-registered
  frame, which would invalidate the headline percentage.
- **Strand caricature** — a column written from the outside (a Pentecostal column that is all
  prophecy, a Lutheran one that is all beer and paradox). The insider-review lens catches it.
- **Genericising the unified bench** — the parity audit's test, extended: *would the ground truth
  differ for a Catholic, an Orthodox believer, a Muslim?* The intersection must preserve the
  shared Protestant **reasoning** (law and gospel, assurance grounded outside the person, sola
  scriptura reflexes, vocation, the priesthood of all believers, handing back to the offices),
  not merely shared conclusions.
- **Re-tagging without re-authoring** on the port — the prompt's §9 check, run per module.
- **Spending the un-ceilinged property** — the monolith is the corpus's only un-ceilinged bank
  (Guided 0.589); part of that is artifact (the guide gap) and will rightly disappear, part is
  real difficulty and must not. Watch the pilot scores; keep the difficulty bar of §4.
- **Forgetting the frozen-viewer coupling** — editing or deleting monolith scenario folders that
  `results-raw/20260813-protestantism` still resolves against.

## 11. Open questions, with defaults

| Question | Default |
|---|---|
| Anabaptist: study column and/or bench? | **Column yes, always** (its divergences — nonresistance, oaths — are exactly the study's subject). Bench deferred to its own PR after the first six land. |
| 50 questions or more? | **50** for the study v1 — thin for clustering (~10 divergent cases expected) and the paper should say so; the distinctive tranches and later authoring extend the same dataset under the same schema. |
| `office` axis per strand? | **Adopt with `none`**, per-strand polity vocabulary in the description. |
| `parity_key` mechanism? | **Validator schema extension** (optional field + negative test) over a side-table. |
| Scoring budget staging? | **Unified first**, then strands in seed-size order as budget allows. |

## 12. References

[Construction record](./protestantbench-construction.md) ·
[Parity audit](./protestantbench-inside-church-parity.md) ·
[Refinement prompt](./protestantbench-life-parity-prompt.md) (imported by reference; superseded as
an in-place execution) · [Census data](./data/protestantbench-census.csv) ·
[SynodiaBench](./synodiabench-ultracode-audit.md) and [plurality](./plurality-ultracode-audit.md)
audits (the plural-lens house method) · `traditions/README.md` (the module contract) ·
`codev/specs/89-protestantism-benchmark-round.md` (the scoring convention) · `results/README.md`
and `results-raw/README.md` (the frozen-dataset rules).
