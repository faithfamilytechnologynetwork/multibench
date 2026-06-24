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
saying/Father and Scripture). The standard chapters (following Wortley's and Ward's
recensions) are:

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

## Why it is consensus-grade — and where it is not single-canon

- **Pan-Eastern-Christian.** The ascetic corpus above is consensus-grade across the Christian
  East (Chalcedonian Orthodox and Eastern Catholic together); this tradition is scoped to
  that shared inheritance, not to one jurisdiction's particular discipline.
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
