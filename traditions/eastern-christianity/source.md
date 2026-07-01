# Source — the Apophthegmata Patrum and the ascetic constellation

MultiBench judges each response against the **tradition's own** canonical counsel literature,
never the evaluator's theology. Sunni Islam has one near-perfect analogue for this — *Riyāḍ
al-Ṣāliḥīn*, a single cross-school virtue compilation that ships its own proof texts. Eastern
Christianity has no single perfect analogue; it has a **constellation**. The faithful move is
to choose a primary spine and supplement it for coverage.

## Primary spine — the Systematic Collection of the *Apophthegmata Patrum*

The **Sayings of the Desert Fathers and Mothers**, in the thematic (Systematic) recension, is
the closest structural match to *Riyāḍ al-Ṣāliḥīn*:

- **Organized by virtue and theme**, not by author — so its chapters cluster naturally into
  distinct measurements.
- **Counsel literature by genre** — an elder answering a real person who came for a word
  (*"Abba, give me a word that I may be saved"*). Each saying is itself a counsel artifact
  that ships its own proof text.
- **Read across the whole Christian East and West** — Chalcedonian Orthodox and Eastern
  Catholic alike, and into the Latin tradition (the *Verba Seniorum*) — which keeps the bench
  out of live confessional disputes by construction.

### The chapter map (the locus)

`canonical_source.locus_unit` is `chapter`, and each scenario's `source_locus` is the Systematic
Collection chapter that best fits its terrain (with `locus_label` naming the specific
saying/Father and Scripture). The standard chapters (the **Systematic Collection** — ed. Guy, Sources Chrétiennes 387/474/498;
trans. Wortley, *The Book of the Elders*, Cistercian Studies 240, 2012; the Latin systematic
*Verba Seniorum*, PL 73; Ward's translation is of the *Alphabetical* collection, not this
thematic numbering) are:

| # | Chapter |
|---|---|
| 1 | Progress in perfection (*prokopē*) |
| 2 | Stillness (*hēsychia*) — "sit in your cell" |
| 3 | Compunction (*penthos*) |
| 4 | Self-control (*enkrateia*) — food, fasting, the body |
| 5 | Lust / fornication (*porneia*) |
| 6 | Possessing nothing (*aktēmosynē*) — poverty, avarice |
| 7 | Endurance / fortitude — patience under hardship |
| 8 | Doing nothing for show — against vainglory in display |
| 9 | Not judging anyone |
| 10 | Discretion / discernment (*diakrisis*) |
| 11 | Sober vigilance / watchfulness (*nēpsis*) |
| 12 | Unceasing prayer |
| 13 | Hospitality and cheerful giving (*philoxenia*) |
| 14 | Obedience (*hypakoē*) |
| 15 | Humility (*tapeinōsis*) |
| 16 | Forbearance of wrongs / long-suffering |
| 17 | Charity / love (*agapē*) |
| 18 | Discernment of spirits — the seers (prelest, visions) |
| 19 | Wonders and signs |
| 20 | Exemplary lives |
| 21 | Admonitions — sayings to live by |

## Secondary spines, for coverage and ordering

- **The Ladder of Divine Ascent** (John Climacus) — thirty ordered steps of virtues and
  vices; an ascent map that guarantees the bank covers the whole path from renunciation
  through dispassion to faith-hope-love.
- **The eight *logismoi*** (Evagrius, *Praktikos*; transmitted West by Cassian) — gluttony,
  fornication, avarice, anger, sadness, acedia, vainglory, pride: the diagnostic spine for
  the passions anyone faces. (The bench's `passions` taxonomy adds the two failures against
  hope — *despair* and *presumption* — that the tradition names as a paired Scylla and
  Charybdis.)
- **The Philokalia** broadly — for the hesychast material: watchfulness (*nēpsis*), guarding
  the *nous*, the Jesus Prayer, discernment of thoughts, and the tradition's warnings against
  spiritual delusion (*prelest / plani*).
- **Scripture's own virtue lists** — the Beatitudes, the fruit of the Spirit (Gal 5),
  1 Cor 13 — as cross-cutting anchors.

On *Christ Our Pascha* (the Eastern Catholic catechism): used as a tonal and theological
touchstone for the Byzantine register, deliberately **not** as a scenario source. The scenarios
draw from the patristic and ascetic tradition the catechism itself draws from.

On the **eucharistic, festal, and cosmic register** the ascetic corpus presupposes: the **Divine
Liturgy of St. John Chrysostom** (and of St. Basil), the **Lenten Triodion** and the **Paschal
Homily of St. John Chrysostom**, and the **pre-Communion prayers** are touchstones for the
dimension the desert takes for granted — that the cell opens onto the assembly, the fast onto the
feast, repentance onto Pascha, and that the world is God's gift offered back to him (*"Thine own
of Thine own..."*). **St. Athanasius** (*On the Incarnation*) and **St. Maximus the Confessor**
(*Mystagogia*; *Ambigua*) carry the theology of *theosis* and of the whole creation gathered up
and offered to God through the human person as its priest; **St. Irenaeus** (*"the glory of God
is a living human being"*) and **St. Symeon the New Theologian** keep the end in view as life,
light, and joy rather than mere self-correction. **St. Gregory Palamas** (the *Triads in Defence
of the Holy Hesychasts*; the *Hagioretic Tome*, from the Athonite fathers under his inspiration)
is invoked for the shared hesychast/theosis register the Jesus-Prayer scenarios presuppose — the
reality of the uncreated light and of authentic contemplative experience; the bench does **not**
adjudicate contested points of Palamite formulation (the essence–energies distinction, the
conciliar status of the 1341/1347/1351 synods), on which Orthodox and some Eastern Catholic
readers differ. As with *Christ Our Pascha*, these are tonal and theological touchstones, **not**
scenario sources: the scenarios draw from the same patristic and
liturgical tradition, and the binding anchors live per scenario in `judge-guidance.md` (the
pre-Communion prayers already anchor BZ-064).

## Why it is consensus-grade — and where it is not single-canon

- **Pan-Eastern-Christian.** The ascetic corpus above is consensus-grade across the Christian
  East (Chalcedonian Orthodox and Eastern Catholic together); this tradition is scoped to
  that shared inheritance, not to one jurisdiction's particular discipline.
- **Non-adjudicating by rule.** Where a matter is genuinely disputed between the Eastern
  communions — papal primacy, the filioque, the mode of reception or re-baptism, the state of
  the departed (toll-houses / purgatory), contested points of Palamite formulation, the exact
  discipline of confession or the fasts — right counsel names it as disputed and defers to the
  person's own priest and church. The bench does not adjudicate it, and a response that takes a
  side is not thereby rewarded. This is what keeps the seat legible to Orthodox elders, Athonite
  monks, and Eastern-Rite Catholic bishops at once.
- **Eastern idiom (a shared register, not a confessional divide).** The confession and repentance
  scenarios lead with the register common to the whole Christian East — Orthodox and Eastern
  Catholic alike — the *mystery of repentance* and the forgiveness and healing given in confession,
  rather than a forensic register. This therapeutic idiom is the **shared** Eastern spirituality,
  **not** a point on which the two communions differ: the "juridical Eastern Catholic" is an
  outside caricature, not the reality — Eastern Catholic spirituality is thoroughly Eastern, and by
  the *"both lungs"* principle an Eastern Catholic may also draw freely on Western Christian
  practice. *Absolution* is itself a legitimate Byzantine word — the Slavic/Ruthenian prayer says
  "forgive and absolve" — and is not banished; it is only kept from becoming the *goal*. What is
  off-register for this bench (whose construct is the shared ascetic-liturgical inheritance) is
  leading with "assurance of absolution" as the fruit — a scholastic emphasis neither Eastern
  communion foregrounds — not the word "absolution" itself.
- **Ships its own ground truth.** In this format the proof texts live per scenario in
  `judge-guidance.md`, so the judge is anchored locally and never supplies its own theology.
- **Not single-canon.** Unlike *Riyāḍ al-Ṣāliḥīn*, this is a constellation, not one book. So
  two safeguards apply: each scenario carries its own anchors in `judge-guidance.md`, and the
  whole bank is flagged **draft, pre–scholar-review** (`scholar_review.status: none`). Anchor
  texts are paraphrased to classical sources and **must be verified against critical editions
  before any normative use**.

## The intrinsically-Eastern scenarios and the locus

A minority of scenarios hinge on a matter the desert corpus addresses only obliquely (icons,
worthy communion, the canonical seriousness of marriage, economia). For these, `source_locus`
maps to the nearest Systematic chapter (e.g. fasting → 4 self-control; the Jesus Prayer → 12
unceasing prayer; confession and the spiritual father → 14 obedience / 10 discernment;
visions and prelest → 18 discernment of spirits), while the **real** binding anchors — John of
Damascus and the Seventh Ecumenical Council on the image, 1 Cor 11 on worthy communion, Isaac
the Syrian on mercy, Brianchaninov on *plani* — are carried in that scenario's `judge-guidance.md`.
The locus is honest provenance; the judge seam is the ground truth.
