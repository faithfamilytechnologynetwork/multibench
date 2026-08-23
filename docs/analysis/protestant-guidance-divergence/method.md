# Method — the answering protocol (pre-registered)

**The study question**: when the seven Protestant strands' own standards are asked the same
ordinary-life pastoral questions, does the *guidance* (concrete counsel) differ, even where the
*theology* (grounding) differs? Committed before any answers were generated.

This is the v1, deliberately simple execution of the divergence study specified in
[`protestantbench-refactor.md`](../protestantbench-refactor.md) §5, run at the maintainers'
direction with the simplifications listed in **Limits** below. Its purpose is to produce the
evidence for the pathway decision (`pathway-rule.md`) *before* any benchmark architecture is
committed to.

## The seven columns

Each column answers **independently, from its own corpus only** — an answering agent sees its own
strand's brief and never another column's answers. Scripture (the sixty-six-book canon) is the
primary source of every column; the briefs below are each strand's *norma normata* and
guidance-dense secondary layer. Authority-status language follows the construction record: a
standard binds as the body holding it provides.

| Column | Corpus |
|---|---|
| `lutheran` | The Book of Concord (1580): the creeds, the Augsburg Confession and Apology, the Smalcald Articles, the Treatise, Luther's Small and Large Catechisms, the Formula of Concord. The catechisms' Decalogue and Lord's Prayer expositions are the moral core. Cite catechism material by commandment / petition / article **name**, never by paragraph number (numbering varies by edition). Note LCMS/WELS vs ELCA variation as `internal_variation` where counsel would differ. |
| `reformed-presbyterian` | The Westminster Confession with the Larger and Shorter Catechisms (American revision; describe sections rather than number them where numbering moves) and the Three Forms of Unity: the Belgic Confession, the Heidelberg Catechism (cite by Lord's Day / question number; paraphrase, do not quote as verbatim — translations vary), the Canons of Dort. WLC 91–152 on the commandments is the dense moral corpus. Belhar only where a church has adopted it. PCA/OPC vs mainline variation as `internal_variation`. |
| `anglican` | The Thirty-Nine Articles; the Book of Common Prayer (1662 as the classic standard — the general confession, the comfortable words, the communion exhortations, the catechism, the marriage, burial, and visitation-of-the-sick rites); the Books of Homilies as Article XXXV commends them. Province variation (e.g. ACNA vs TEC) as `internal_variation`. |
| `baptist` | The Baptist Faith & Message (cite as BF&M 2000; the 1925/1963 texts differ), especially the articles on the Christian and the Social Order, Stewardship, Religious Liberty, and the Family; the Second London Confession (1689) where a congregation is confessionally Reformed; the church covenant tradition; denominational position statements as the considered word of a body, binding as its polity provides. Local-church autonomy: note where counsel binds because a congregation adopted a standard. |
| `methodist-wesleyan` | The Articles of Religion (Wesley's twenty-five); Wesley's Standard Sermons (e.g. *The Use of Money*, *The Almost Christian*, the sermons on the Sermon on the Mount); the General Rules with their named examples; the Large Minutes; the EUB Confession of Faith; for the mainline body the UMC Book of Discipline's Social Principles, and for the Holiness wing the Church of the Nazarene Articles of Faith and Covenant of Christian Conduct. UMC/GMC and mainline/Holiness variation as `internal_variation`. |
| `pentecostal` | The Assemblies of God Statement of Fundamental Truths and the AG position papers (the guidance-dense layer: e.g. divine healing and medicine, abstinence, gambling, divorce and remarriage, the sanctity of life); the Church of God (Cleveland) Declaration of Faith and practical commitments; the COGIC Statement of Faith. |
| `anabaptist` | The Schleitheim Confession (1527); the Dordrecht Confession (1632); the Confession of Faith in a Mennonite Perspective (1995) — with its articles on peace and nonresistance, truth-telling and the oath, and mutual aid. Note the Old Order ↔ MC USA spectrum as `internal_variation` where counsel would differ. |

## The worksheet

One file per question per column:
`worksheets/<column>/Q<NN>.md`, exactly this shape:

```markdown
---
question: Q07
strand: lutheran
silence: false            # true when the standards do not reach the case
confidence: high          # high | medium | low — overall confidence in the grounding
internal_variation: false # true when bodies within the strand would counsel differently
---
## Counsel
(3–6 sentences of concrete advice — what a faithful pastor of this strand, formed by these
standards, would actually counsel this person to do, say, seek, or stop. Actionable sentences.
No doctrine here; doctrine goes below.)

## Grounding
(The named loci this counsel stands on — confession article, catechism question, sermon,
position paper, Scripture — each with a confidence flag: (certain) / (probable) / (unsure).
Paraphrase-hedged, never quoted as verbatim where translations vary.)

## Idiom
(1–2 sentences: how this strand's own pastor would say the heart of it, in the strand's
vocabulary.)

## Notes
(Conditionals; where internal bodies differ; edition cautions; if silence: true, the nearest
principle the standards do offer, clearly marked as extension rather than address.)
```

## Answering rules

1. **Guidance first.** The `## Counsel` field is the unit of comparison. It must be advice, not
   theology — separable, concrete, and complete on its own.
2. **Never invent a citation.** The construction record's §6.4 failure catalogue is the hazard
   list: inflated paraphrase, the right number on the wrong sentence, attribution drift, edition
   variance. When unsure of a number, cite by name and flag `(unsure)`; generalise to the level
   actually supported.
3. **Silence is an answer.** Where the standards do not reach the case, say so (`silence: true`)
   and give the nearest principle separately marked. Forcing an answer manufactures fake
   convergence or fake divergence.
4. **Column independence.** Answer only from this strand's corpus and Scripture. Do not consider,
   quote, or triangulate against any other tradition.
5. **Insider register, no caricature.** Each column should read as that strand's own voice — a
   faithful reporter, not an apologist and not a cartoon.
6. **Safety floor.** Where a situation carries a live safety edge (Q29, Q31 adjacent), counsel
   includes the appropriate professional/medical help *alongside* the spiritual counsel — every
   strand's column, per the corpus-wide double rule.

## Verification

After all columns are written and **before coding**, a sampled citation audit
(guilty-until-confirmed, per the construction record's discipline): for every column, five
questions' worksheets are adversarially re-checked — against standard published editions online
where reachable — and corrections applied in place with a changelog. The sampled error rate is
reported in the study.

## Coding and analysis

See `codebook.md`. The primary outcome (advice similarity) is coded **blind**: coders receive
only the `## Counsel` fields, order-shuffled per question and pseudonymised R1–R7 (mapping held
outside the repo until coding is complete), double-coded by independent coders with disagreement
adjudicated by a third. Grounding similarity is coded unblinded afterwards (the citations
identify the strand by nature). `analyze.py` computes the aggregates from the committed codings.

## Limits, declared up front

- **v1 scale**: 50 questions; ~10 substantively divergent cases expected under the 80/20
  hypothesis — enough for a directional finding and named divergence areas, thin for a strong
  taxonomy. The dataset is extensible under the same schema.
- **Inline corpus briefs**, not the committed research briefs of the full spec's Phase 1; a
  scale-up should build those first.
- **One model family** drafts all columns (shared-prior contamination risk); verification is
  web-anchored sampling rather than an independent model. Disclosed, not solved.
- **Blinding is partial**: idiom can leak strand identity into `## Counsel` even with labels
  stripped.
- **No human scholar review yet.** The per-column structure is designed so one reviewer per
  strand can review their own column; that review has not happened. Anchors are first-draft.
