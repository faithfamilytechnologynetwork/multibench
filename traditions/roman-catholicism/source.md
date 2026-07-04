# Source — the *Catechism of the Catholic Church* and the counsel constellation

MultiBench judges each response against the **tradition's own** canonical counsel literature,
never the evaluator's theology. Roman Catholicism is unusually well supplied here: unlike
traditions that must elect one classic among many, the Latin Church possesses a single,
paragraph-numbered, magisterially promulgated summary of the whole of faith and morals — the
**Catechism of the Catholic Church** — and around it a vast, explicitly cross-referenced counsel
literature. The faithful move is the same as its siblings': one primary source, supplemented for
coverage.

## Primary source — the Catechism of the Catholic Church (CCC)

Promulgated by Pope St. John Paul II with the apostolic constitution *Fidei Depositum* (1992;
Latin *editio typica* 1997) and declared *"a sure norm for teaching the faith and thus a valid
and legitimate instrument for ecclesial communion."* It is consensus-grade by construction:

- **Magisterial, not scholastic.** It is not one school's manual but the Church's own summary,
  drafted by the world's bishops and promulgated by the pope — the one text every catechist,
  seminary, and diocese is bound to. It stands above the live disputes between theological
  schools by design.
- **It ships its own proof texts.** Every paragraph is woven from Scripture, the Fathers, the
  councils (above all Vatican II), the saints, and prior magisterium, with the citations printed
  in place — the bench's judge-guidance can anchor to a numbered paragraph and inherit its
  sources.
- **Numbered for citation.** 2,865 paragraphs in four parts; `canonical_source.locus_unit` is
  `paragraph`, and each scenario's `source_locus` is the CCC paragraph nearest the heart of its
  terrain (`locus_label` names it and any supplementary anchors).

### The map (the locus)

| Paragraphs | Part | Bench terrain |
|---|---|---|
| 1–1065 | I. The Profession of Faith | providence, the Church, forgiveness of sins, the last things (despair/presumption scenarios, grief, purgatory and prayer for the dead) |
| 1066–1690 | II. The Celebration of the Christian Mystery | the sacraments: Eucharist and worthy reception, Penance and the confessor, Matrimony, Anointing and Christian death |
| 1691–2557 | III. Life in Christ | the virtues (1803–1845), sin and the capital sins (1846–1876), the Decalogue in full (2052–2557) — the moral life the majority of scenarios stage, including the social doctrine (1877–1948, 2401–2463) |
| 2558–2865 | IV. Christian Prayer | the life of prayer, its battle — dryness, distraction, acedia (2725–2758) — and the Lord's Prayer |

## The supplementary constellation

The Catechism is a norm, not a director; the Church's actual counsel voice lives in the wider
patrimony each scenario's `judge-guidance.md` may bind alongside its CCC anchor:

- **The Code of Canon Law (1983).** The Latin Church's binding discipline — the precepts,
  worthy reception (can. 916), the Sunday obligation (can. 1247), marriage and its defects of
  consent (can. 1095–1107), the inviolable seal of confession (can. 983), separation of spouses
  (can. 1151–1155) — crowned by its famous final canon: *the salvation of souls, which must
  always be the supreme law in the Church* (can. 1752).
- **The moral and social magisterium.** *Rerum Novarum* through *Laborem Exercens*,
  *Centesimus Annus*, and the Compendium of the Social Doctrine; *Humanae Vitae*; *Veritatis
  Splendor*; *Evangelium Vitae*; *Deus Caritas Est* and *Spe Salvi*; *Evangelii Gaudium* (the
  art of accompaniment, 169–173); *Laudato Si'*; *Amoris Laetitia*; *Gaudete et Exsultate*;
  *Fratelli Tutti*; *Dilexit Nos* — Francis's encyclical on the Heart of Christ, whose theme is
  this bench's very name, *cor ad cor loquitur*.
- **The Spiritual Exercises of St. Ignatius of Loyola.** The Church's most codified school of
  discernment: the Principle and Foundation (Sp. Ex. 23), the director's restraint (annot. 15),
  the rules for the discernment of spirits (313–336) — consolation and desolation, *"in time of
  desolation never make a change"* (Rule 5), *agere contra* — and the times and rules of a sound
  election (169–189).
- **The counsel classics of the schools.** The Rule of St. Benedict (stability, work, hospitality,
  the instruments of good works); *The Imitation of Christ*; St. Francis de Sales' *Introduction
  to the Devout Life* — lay spiritual direction by genre, "devotion must be practiced differently"
  by each state in life (I, 3); St. John of the Cross and St. Teresa of Ávila on dryness and the
  dark night; St. Thérèse's little way; the Dominican *veritas* of St. Thomas's *Summa* on the
  virtues and vices, from which the Catechism's own treatment descends.

**Why not a single devotional classic as the primary source?** No one of them (Imitation, Devout Life,
Exercises) is read by the whole Latin Church the way the Catechism is promulgated to it; and none
is paragraph-numbered *and* doctrinally comprehensive. The CCC gives every scenario a numbered,
magisterial locus; the constellation gives its judge-guidance the pastoral voice. Both together
mirror how the Church herself counsels: the sure norm in one hand, the art of accompaniment in
the other.

**Caveat for normative use.** All anchor texts in `judge-guidance.md` are paraphrased. Verify
against the *editio typica* / official Vatican translations before any normative claim, and
remember the bench's own rule: questions of sacramental practice, canonical standing, and binding
moral judgment in a concrete case belong to a person's own pastor, confessor, or tribunal — the
bench measures companionship, it does not absolve, dispense, or rule.
