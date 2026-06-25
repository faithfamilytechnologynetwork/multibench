# Source — the Dhammapada and the Buddhist constellation

MultiBench judges each response against the **tradition's own** canonical counsel
literature, never the evaluator's philosophy. Sunni Islam has one near-perfect analogue for
this — *Riyāḍ al-Ṣāliḥīn*, a single cross-school virtue compilation that ships its own proof
texts. Buddhism, spread across Theravāda, Mahāyāna, and Vajrayāna over twenty-five centuries,
has no single book that all schools read as that. It has a **constellation**. The faithful
move, as for Eastern Christianity, is to choose a primary spine and supplement it for
coverage.

## Primary spine — the Dhammapada

The **Dhammapada** ("path of Dhamma" / "verses of Dhamma") is the closest structural match to
*Riyāḍ al-Ṣāliḥīn*:

- **Organized by theme**, into 26 chapters (*vaggas*) — heedfulness, the mind, anger,
  craving, the path — so its chapters cluster naturally into distinct measurements.
- **Counsel literature by genre** — terse, memorable instruction on conduct and the taming of
  the mind, each verse a self-contained "word" that ships its own proof text.
- **Read across the whole Buddhist world.** It sits in the Pali Canon (Khuddaka Nikāya) for
  the Theravāda, and the same anthology survives in parallel recensions used by the northern
  traditions — the Gāndhārī *Dharmapada*, the Patna *Dharmapada*, and the Sanskrit
  *Udānavarga* — which keeps the bench out of live inter-school disputes by construction.

### The chapter map (the locus)

`canonical_source.locus_unit` is `vagga`, and each scenario's `source_locus` is the Dhammapada
chapter that best fits its terrain (with `locus_label` naming the specific verse and any sutta
or Jātaka). The 26 vaggas (with the common verse ranges) are:

| # | Vagga | Verses |
|---|---|---|
| 1 | The Pairs (*Yamaka*) | 1–20 |
| 2 | Heedfulness (*Appamāda*) | 21–32 |
| 3 | The Mind (*Citta*) | 33–43 |
| 4 | Flowers (*Puppha*) | 44–59 |
| 5 | The Fool (*Bāla*) | 60–75 |
| 6 | The Wise (*Paṇḍita*) | 76–89 |
| 7 | The Arahant (*Arahanta*) | 90–99 |
| 8 | The Thousands (*Sahassa*) | 100–115 |
| 9 | Evil (*Pāpa*) | 116–128 |
| 10 | The Rod / Violence (*Daṇḍa*) | 129–145 |
| 11 | Old Age (*Jarā*) | 146–156 |
| 12 | The Self (*Atta*) | 157–166 |
| 13 | The World (*Loka*) | 167–178 |
| 14 | The Buddha (*Buddha*) | 179–196 |
| 15 | Happiness (*Sukha*) | 197–208 |
| 16 | Affection (*Piya*) | 209–220 |
| 17 | Anger (*Kodha*) | 221–234 |
| 18 | Impurity (*Mala*) | 235–255 |
| 19 | The Just (*Dhammaṭṭha*) | 256–272 |
| 20 | The Path (*Magga*) | 273–289 |
| 21 | Miscellaneous (*Pakiṇṇaka*) | 290–305 |
| 22 | The Hell-Bound (*Niraya*) | 306–319 |
| 23 | The Elephant (*Nāga*) | 320–333 |
| 24 | Craving (*Taṇhā*) | 334–359 |
| 25 | The Monk (*Bhikkhu*) | 360–382 |
| 26 | The Brahmin (*Brāhmaṇa*) | 383–423 |

## Secondary spines, for coverage and ordering

- **The discourses (Sutta Piṭaka / Āgamas).** The doctrinal frame the verses presuppose: the
  Four Noble Truths and the **Noble Eightfold Path** (the first sermon,
  *Dhammacakkappavattana*, SN 56.11); the **Middle Way** between indulgence and mortification
  it opens with; the *Kālāma Sutta* on testing teachings by their fruits (AN 3.65); the
  *Mettā Sutta* (Snp 1.8); the four foundations of mindfulness (*Satipaṭṭhāna*, MN 10); the
  simile of the saw on unshakeable good-will (MN 21); the lute-string of right effort (Soṇa,
  AN 6.55); the five trades a lay follower should not take up (AN 5.177); the five marks of
  well-spoken speech (AN 5.198); the five subjects for daily recollection (AN 5.57); kamma as
  intention (*cetanā*, AN 6.63); Kisā Gotamī and the mustard seed; and the arrow of grief
  (*Salla Sutta*, Snp 3.8).
- **The Jātakas** — the 547 birth-stories of the Bodhisatta, the canonical home of Buddhist
  **fable**. Each dramatizes a perfection or a fault: the *Khantivādī Jātaka* (Jā 313, the
  ascetic of patience, unmoved while dismembered) for *khanti*; the *Sasa Jātaka* (Jā 316, the
  hare who offers its own body) and the *Vessantara Jātaka* (Jā 547) for *dāna*; the
  *Mahāsutasoma Jātaka* (Jā 537) for truthfulness.
- **The lists of qualities to cultivate** — the four **brahmavihāras** (the divine abodes:
  loving-kindness, compassion, appreciative joy, equanimity); the ten **pāramīs** of the
  Theravāda (Cariyāpiṭaka / Buddhavaṃsa) and the six **pāramitās** of the Mahāyāna; the seven
  factors of awakening; the five precepts (*pañca-sīla*).
- **Cross-school touchstones**, so the bank is not Theravāda-only: the Mahāyāna sūtras (the
  *Diamond Sūtra* on giving unattached to giver, gift, and receiver; the Heart Sūtra and
  Nāgārjuna's Madhyamaka on emptiness as the Middle Way, *not* nihilism); **Chan / Zen** (the
  ox-herding pictures; "if you meet the Buddha, kill the Buddha" — against grasping at
  attainment); **Pure Land** (Shinran's *other-power* / *tariki* for the scrupulous and the
  despairing); **Vajrayāna** (the *lojong* mind-training, and its warning against "idiot
  compassion" — help that only enables).

## Why it is consensus-grade — and where it is not single-canon

- **Pan-Buddhist.** The Dhammapada and the core lists — the Four Truths, the Eightfold Path,
  the brahmavihāras, the precepts — are common ground across Theravāda, Mahāyāna, and
  Vajrayāna. This tradition is scoped to that **shared inheritance**, not to one school's
  particular Vinaya, tantric commitments, or sectarian doctrine.
- **Ships its own ground truth.** In this format the proof texts live per scenario in
  `judge-guidance.md`, so the judge is anchored locally and never supplies its own philosophy.
- **Not single-canon.** Unlike *Riyāḍ al-Ṣāliḥīn*, this is a constellation, not one book. So
  two safeguards apply: each scenario carries its own anchors in `judge-guidance.md`, and the
  whole bank is flagged **draft, pre–scholar-review** (`scholar_review.status: none`). Anchor
  texts are paraphrased to classical sources and **must be verified against critical editions**
  (the PTS Pali texts and standard translations, the Taishō for the Chinese parallels) before
  any normative use.

## The intrinsically-Buddhist scenarios and the locus

A minority of scenarios hinge on matter the Dhammapada addresses only obliquely — the jhānas
and the stages of awakening, emptiness (*śūnyatā*), other-power and the Pure Land, the *lojong*
slogans, the corruptions of insight. For these, `source_locus` maps to the nearest Dhammapada
vagga (e.g. meditative attainment → 1 The Pairs / 25 The Monk; craving and letting go → 24
Craving; the heedless presumption that conduct does not matter → 2 Heedfulness), while the
**real** binding anchors — the relevant sūtra, the Visuddhimagga on the insight-corruptions,
Nāgārjuna on the two truths, Shinran on *tariki* — are carried in that scenario's
`judge-guidance.md`. The locus is honest provenance; the judge seam is the ground truth.
