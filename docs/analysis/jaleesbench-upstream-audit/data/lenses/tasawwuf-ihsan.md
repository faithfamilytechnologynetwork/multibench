# Lens: Tasawwuf / Ihsan — Taxonomy Fidelity

Scholar of tasawwuf/ihsan and the bank's own scaffolding literature (al-Ghazali's
*Ihya* munjiyat; Ibn al-Qayyim's *Madarij* pillars; Abu Ghudda's *al-Rasul al-Muʿallim*).
Primary task: compare the operational taxonomy in code (`mapping.py`) against the
documented taxonomy (guide, design doc §7, paper) and against the classical sources.

## Sources checked (web-grounded)
- **al-Ghazali, *Ihya ʿUlum al-Din*, Quarter 4 (Rubʿ al-Munjiyat)** — 10 books.
  Confirmed via ghazali.org / Wikipedia listing: Book 34 = *On Poverty and Abstinence*
  (faqr & zuhd), Book 39 = *On Meditation* (tafakkur), Book 40 = *On the Remembrance of
  Death* (dhikr al-mawt) are all genuine munjiyat books.
- **Ibn al-Qayyim, *Madarij al-Salikin*** — noble character on four pillars: **Sabr**
  (patience), **ʿIffa** (chastity/continence), **Shajaʿa** (courage), **ʿAdl** (justice);
  four roots of ruin: jahl, zulm, shahwa, ghadab. Confirmed.

---

## STRENGTHS confirmed

**S1 — The Guided-framing heart-state list is faithful to al-Ghazali's Quarter 4.**
`prompts.py` GUIDE (also `docs/jaleesbench-guide.md`, design §7, paper App guide) lists
exactly the ten Rubʿ al-Munjiyat book titles, correctly paired as al-Ghazali pairs them:
repentance · patience & gratitude · fear & hope · simplicity & detachment · reliance on
God · love & contentment · sincerity of intention & truthfulness · vigilance &
self-accounting · reflection · remembrance of death. This is accurate scholarship.

**S2 — The four conduct pillars are faithful to Ibn al-Qayyim.** patience/restraint/
courage/justice = sabr/ʿiffa/shajaʿa/ʿadl, with the four roots of ruin (ignorance,
injustice, appetite, anger) correctly paired. Design §7 even notes the contrast with the
Greek scheme (wisdom-rooted vs patience-rooted) — a genuinely learned observation.

**S3 — The seven teaching techniques are honestly labeled "ours, not a classical list."**
Design §6.2 ("The consolidation into seven scoreable dimensions is ours"), paper §rubric
("ours is a consolidation, not a classical list"), and the guide ("after Abu Ghudda")
consistently refuse to overclaim the seven as classical. Abu Ghudda's ~40 methods are
correctly cited as the genre reference, not as a seven-item source. Good scholarly hygiene.

---

## DEFECTS found

**D1 (serious) — The *operational* heart-state taxonomy in `mapping.py` is NOT
al-Ghazali's munjiyat, though the paper labels it "al-Ghazali's stations."**
`mapping.py:23-25`:
```
HEARTS = {"fear_hope", "intention_sincerity", "love_contentment", "patience",
          "patience_gratitude", "reliance_on_god", "repentance",
          "self_accounting", "truthfulness", "vigilance"}
```
Diffed against the faithful guide list (= the munjiyat), the code:
- **DROPS three genuine munjiyat**: faqr/zuhd (simplicity & detachment, *Ihya* Bk 34),
  tafakkur (reflection, Bk 39), dhikr al-mawt (remembrance of death, Bk 40). These are
  therefore structurally unmeasurable — never tagged on any of the 140 probes.
- **SPLITS two paired books into four codes**: al-Ghazali's *Kitab al-Niyya wa'l-Ikhlas
  wa'l-Sidq* → `intention_sincerity` + `truthfulness`; *Kitab al-Muraqaba wa'l-Muhasaba*
  → `vigilance` + `self_accounting`.
- **ADDS a bare `patience`** that is not a munjiya (the book is *Patience & Gratitude*,
  already present as `patience_gratitude`) and duplicates the pillar `patience`.

Count is preserved (10 − 3 dropped + 2 from splits + 1 added = 10), which is why the
divergence hides. The established candidate is **fully confirmed**. Operational proof:
`probes.json` tags use `self_accounting` (79), `patience` (14) etc., and never faqr/zuhd,
tafakkur, or dhikr al-mawt. The paper (fig:hearts, "by heart state (al-Ghazali's
stations)") reports an axis that includes bare `patience` (not a station) and omits three
real stations — so a reader is told "al-Ghazali's stations" but shown a different set.
*Fix (taxonomy):* reconcile HEARTS to the guide's ten munjiyat (restore faqr/zuhd,
tafakkur, dhikr al-mawt; merge the two split pairs; drop bare `patience`), OR relabel the
paper/figures as "an operational heart-state set adapted from al-Ghazali's munjiyat" and
document the deviations. The former preserves the §7 fidelity claim; the latter is honest
about what is actually measured. Re-tagging to preserve balance is not the point here — the
enum itself is the defect.

**D2 (revise) — The bare `patience` heart-state duplicates the `patience` pillar and
overlaps `patience_gratitude`.** `mapping.py:22` PILLARS contains `patience`; `mapping.py:23`
HEARTS also contains `patience`; and HEARTS separately contains `patience_gratitude` (the
actual munjiya). A probe can be tagged patience-as-pillar and patience-as-heart
simultaneously, and `patience` vs `patience_gratitude` are undistinguished in guidance to
the mapper model. This muddies the two-tier design (§7: "the pillar classifies the
scenario, the heart state classifies the response") precisely on the one term that lives in
both tiers. *Fix (taxonomy):* remove bare `patience` from HEARTS; if patience-of-response is
wanted, fold it into `patience_gratitude` (its munjiya).

**D3 (revise) — The paper/design §7 claim "every category name appears verbatim in a
citable classical text" is overbroad and contradicted by the bench's own text.** Two
reported category axes have names with no classical verbatim source: (a) the **seven
teaching techniques** ("reads the person," "engages reason," "exit ramp," "open door,"
etc.) — reported as "by prophetic method" (§6.3) yet admitted in §6.2/paper as "ours, not
a classical list"; and (b) **`cross_cutting`**, a pillar-axis category (67 probes; the
paper reports "cross-cutting virtues" scores) that is a bench utility bucket, not a
classical term. *Fix (framing/doc):* scope the claim — "the conduct-pillar and heart-state
*names* are drawn from Ibn al-Qayyim and al-Ghazali; the technique consolidation and the
cross-cutting bucket are the bench's own." §7 already concedes "the assignment is ours";
it should also concede that two of the reported category *names* are ours.

**D4 (minor) — Rendering ʿiffa as generic "restraint," then applying it to 107/140
probes, stretches the classical term.** ʿIffa in Ibn al-Qayyim is specifically the
faculty that governs shahwa (appetite/lust) — continence/chastity — paired against that
one root of ruin. As `restraint` it becomes the single most-used pillar tag (107 probes:
restraint of tongue, of anger, of spending…), absorbing terrain that classically belongs
to courage-vs-anger (hilm) and to justice. The translation is disclosed (design §7:
"restraint (ʿiffa)") and defensible, but the breadth of application is a mild fidelity
stretch worth a footnote. *Fix (doc):* note that "restraint" is used as a broad cover term
wider than classical ʿiffa, or split anger/tongue restraint off the ʿiffa tag.

---

## Net assessment
The *documented* taxonomy (guide, §7 list) is scholarly and faithful to both al-Ghazali
and Ibn al-Qayyim, and the seven techniques are honestly owned. The defect is a **silent
divergence between that faithful documentation and the operational code enum** (`HEARTS`),
which drops 30% of the munjiyat, adds a non-station, and splits paired books — while the
paper still labels the resulting axis "al-Ghazali's stations." That mislabel, plus the
overbroad "every category verbatim" claim, are the fixable items.
