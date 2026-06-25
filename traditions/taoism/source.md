# Source — the Tao Te Ching and the Taoist constellation

MultiBench judges each response against the **tradition's own** canonical counsel literature,
never the evaluator's philosophy. Sunni Islam has a near-perfect single analogue in *Riyāḍ
al-Ṣāliḥīn*; Buddhism and Eastern Christianity have constellations. Taoism sits between: it has
one book that the whole tradition — philosophical (*dàojiā* 道家) and religious (*dàojiào* 道教)
alike — reads as central, the **Tao Te Ching**, but it has **no central authority** that fixes
the list of virtues or the one right reading. As the user of this bench put it: *Taoism may not
have as central an authority to define virtues, but regardless, the Tao Te Ching is central.* So
the faithful move is to take the *Laozi* as the spine and let the rest of the tradition — the
*Zhuangzi*, the *Liezi*, the great commentaries, the recovered manuscripts, and modern
scholarship — supply coverage and guard against any single idiosyncratic reading.

## Primary spine — the Tao Te Ching (道德經)

The **Tao Te Ching** ("Classic of the Way and its Power/Virtue"), also called the **Laozi**
after its traditional author, is the spine:

- **Eighty-one short chapters** (*zhang* 章), each a self-contained, aphoristic "word" on the
  Way and conduct — terse, memorable, and quotable, so each chapter ships its own proof text in
  the way *Riyāḍ al-Ṣāliḥīn*'s entries do.
- **Two parts.** Chapters 1–37 are the **Dao Jing** (道經, more on the Way itself); chapters
  38–81 are the **De Jing** (德經, more on *de* — power/virtue/conduct). The recovered Mawangdui
  manuscripts reverse the order (De first), which is why Henricks titles his edition the
  *Te-Tao Ching*; the bench uses the conventional 1–81 numbering of the received text.
- **Read across the whole tradition and beyond it.** The *Laozi* is common ground for every
  Taoist school and has been continuously translated and commented on for two millennia, which
  keeps the bench out of live sectarian disputes by construction.

### The locus and a themed index of the load-bearing chapters

`canonical_source.locus_unit` is `zhang`, and each scenario's `source_locus` is the Tao Te Ching
chapter that best fits its terrain (with `locus_label` naming the specific chapter and any
*Zhuangzi*, *Liezi*, or commentary). Rather than reprint all 81 chapters, here are the clusters
the scenarios draw on most:

| Theme | Chapters (zhang) |
|---|---|
| Water, softness, yielding overcoming the hard | 8, 36, 43, 76, 78 |
| Wú wéi, "doing without doing," governing by not-meddling | 2, 3, 37, 48, 57, 60, 63, 64 |
| The uncarved block (pǔ), simplicity, plainness | 19, 28, 32, 37, 57 |
| Emptiness and the usefulness of the void | 4, 5, 11, 16 |
| Stillness, returning to the root | 16, 26, 37, 45 |
| The three treasures — compassion, frugality, humility | 67 |
| Humility, lowliness, the valley and the sea | 8, 28, 61, 66, 68 |
| Knowing contentment, "enough" (against craving) | 33, 44, 46 |
| Self-knowledge and not-displaying-oneself | 22, 24, 33, 72 |
| Non-contention (bù zhēng) | 8, 22, 66, 68, 73, 81 |
| Reversal — what is forced "comes to an early end" | 9, 23, 29, 30, 55, 58 |
| The senses, desire, and "the belly not the eye" | 12, 13 |
| When the Tao declined, "benevolence and righteousness arose" (against contrived virtue) | 18, 19, 38 |
| Speech — "those who know do not speak"; "many words run dry" | 5, 23, 56, 81 |

## Secondary spines, for coverage and ordering

- **The Zhuangzi (莊子)** — the second great Taoist classic and the canonical home of Taoist
  **fable**. Each parable dramatizes the Way or its loss: **Cook Ding** carving the ox, his
  blade never dulling because it moves through the natural openings (*Yangshengzhu*, ch. 3) —
  the image of wú wéi as supreme skill, not idleness; the **useless tree** and the
  **goose that could not honk**, on the use of the useless; the **happiness of the fish** on
  the Hao river (ch. 17); the **empty boat** (ch. 20) — no one rages at an empty boat, so empty
  your own; **Penumbra and Shadow** and the **butterfly dream** (ch. 2) on the relativity of
  standpoints and the **pivot of the Tao** (*dào shū* 道樞); the death of **Zhuangzi's wife**,
  when he drummed on a tub and sang rather than wept (ch. 18); the carving of **Hùndùn**
  (Chaos), bored seven holes and killed by his friends' kindness (ch. 7) — the danger of
  improving what should be left whole.
- **The Liezi (列子)** — the third classic, a treasury of teaching-stories: the **old fool who
  moved the mountains** (Yúgōng) by sheer steadiness; the **man of Qi who feared the sky would
  fall**; the **lost-axe** parable on suspicion coloring perception; the **fasting of the mind**
  and the dexterity tales — useful for the everyday-conduct scenarios.
- **The Neiye (內業, "Inward Training")** — an early cultivation text (in the *Guanzi*; Harold
  Roth, *Original Tao*) on quieting the mind and aligning with the Way through stillness and
  breath; an anchor for the meditation/cultivation scenarios.
- **The great commentaries.** **Wang Bi** (王弼, 226–249), the philosophical reading that fixed
  the received text and treats *wu* (nothing/emptiness) as the root; **Heshang Gong** (河上公),
  the older reading oriented to self-cultivation, longevity, and government. Together they show
  the *range* of orthodox interpretation a scenario must respect rather than flatten.
- **The religious tradition (dàojiào 道教), as touchstone, not scenario-source.** The Celestial
  Masters, the *Quanzhen* (全真) monastic order, and internal alchemy (*neidan* 內丹) — and the
  ethical tracts such as the *Taishang Ganying Pian* (太上感應篇, "Treatise on Action and
  Response") — are used as tonal and ethical touchstones for the living tradition's seriousness
  about conduct and its warnings against reckless cultivation, **not** mined as primary anchors;
  the scenarios draw from the classical *Laozi/Zhuangzi* inheritance the religion itself draws on.

## Modern scholarship — ancient text, recovered and re-read

The user asked for grounding *"based on modern commentary all the way through to ancient."* The
modern recovery is part of why the *Laozi* is trustworthy ground:

- **The recovered manuscripts.** The **Mawangdui** silk texts (馬王堆, excavated 1973, c. 2nd c.
  BCE) and the **Guodian** bamboo slips (郭店, excavated 1993, c. 300 BCE — the oldest known
  *Laozi* material) let modern scholars test the received text against versions far older than
  any prior witness; **Robert Henricks** translated both (*Te-Tao Ching*, 1989; *Lao Tzu's Tao
  Te Ching*, 2000).
- **Modern translators and philosophers.** **D.C. Lau** and **Wing-tsit Chan** (the standard
  mid-century scholarly translations); **Roger Ames & David Hall** (*Daodejing: Making This Life
  Significant*, 2003 — a "philosophical translation" stressing process and correlation);
  **Hans-Georg Moeller** (*The Philosophy of the Daodejing*); **Edward Slingerland**
  (*Effortless Action*, 2003, and the popular *Trying Not to Try*, 2014 — wú wéi as spontaneity
  and the paradox of trying not to try); **Brook Ziporyn** (the leading recent *Zhuangzi*
  translation and commentary); **A.C. Graham** (*Chuang-Tzŭ: The Inner Chapters*; *Disputers of
  the Tao*); **Harold Roth** (*Original Tao*, on the *Neiye*); **Livia Kohn** (the standard
  surveys of Daoism); and **Red Pine / Bill Porter** (*Lao-tzu's Taoteching*, which gathers two
  millennia of Chinese commentary alongside the text). These are the lenses each scenario's
  `judge-guidance.md` reflects when a reading is genuinely contested.

## Why it is consensus-grade — and where it is not single-authority

- **One central text, many readings.** The *Laozi* itself is consensus-grade — every Taoist
  school reads it, and the core images (water, the uncarved block, wú wéi, the three treasures)
  are common ground. What Taoism lacks is a central *authority* to declare the one correct
  interpretation or a fixed catechism of virtues; the bench therefore scopes to the **shared
  inheritance** and, where readings genuinely differ, says so in `judge-guidance.md` rather than
  picking a winner.
- **Ships its own ground truth.** In this format the proof texts live per scenario in
  `judge-guidance.md`, so the judge is anchored locally and never supplies its own philosophy.
- **Draft, pre–scholar-review.** Each scenario carries its own anchors, and the whole bank is
  flagged **draft** (`scholar_review.status: none`). Anchor texts are paraphrased to classical
  sources and **must be verified against critical editions and standard translations** before any
  normative use.

## The intrinsically-Taoist scenarios and the locus

A minority of scenarios hinge on matter the *Laozi* addresses only obliquely — wú wéi misread as
passivity, "the Tao is beyond good and evil," the *Zhuangzi*'s stance on death and grief,
internal-alchemy attainments and "fire deviation" (*zǒu huǒ rù mó* 走火入魔), the danger of
"improving" what should be left whole (Hùndùn). For these, `source_locus` maps to the nearest
relevant Tao Te Ching chapter (e.g. wú wéi and non-meddling → 2, 48, 63, 64; "Heaven and earth
are not benevolent" → 5; the soft outlasting the hard → 76; what is forced comes to an early
end → 30, 55; contentment against craving → 44, 46), while the **real** binding anchors — the
specific *Zhuangzi* chapter, the *Neiye*, Wang Bi's gloss, Slingerland on wú wéi — are carried in
that scenario's `judge-guidance.md`. The locus is honest provenance; the judge seam is the
ground truth.
