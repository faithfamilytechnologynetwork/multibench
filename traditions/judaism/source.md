# Source — *Mesillat Yesharim* and the mussar constellation

MultiBench judges each response against the **tradition's own** canonical counsel literature,
never the evaluator's theology. Sunni Islam has one near-perfect analogue for this — *Riyāḍ
al-Ṣāliḥīn*, a single cross-school virtue compilation that ships its own proof texts. Judaism —
across Sephardi and Ashkenazi, rationalist and kabbalistic, Litvish Mussar and Chassidic — has
no single book that the whole tradition reads as that. It has a **constellation** of *sifrei
mussar* (works of ethical instruction). The faithful move, as for Eastern Christianity and
Buddhism, is to choose a primary spine and supplement it for coverage.

## Primary spine — *Mesillat Yesharim* (the Path of the Upright)

The **Mesillat Yesharim** of Rabbi Moshe Chaim Luzzatto (the Ramchal, Italy/Amsterdam/Acre,
1707–1746) is the closest structural match to *Riyāḍ al-Ṣāliḥīn* and the most widely studied
work of mussar across the Jewish world:

- **Organized as a ladder**, not a treatise — it expounds, rung by rung, the *Baraita of Rabbi
  Pinchas ben Yair* (Avodah Zarah 20b): Torah leads to **watchfulness** (*zehirut*), watchfulness
  to **alacrity** (*zerizut*), to **cleanliness** (*nekiyut*), to **separation** (*perishut*),
  to **purity** (*taharah*), to **piety** (*chasidut*), to **humility** (*anavah*), to **fear of
  sin** (*yir'at chet*), to **holiness** (*kedushah*). The rungs cluster naturally into distinct
  measurements.
- **Counsel literature by genre** — a guide to forming the self, addressed to a real person who
  wants to become upright (*yashar*), each chapter a "word" of formation that ships its own
  proof text from Tanach and Chazal.
- **Read across the whole observant world** — Litvish yeshivot and Chassidic *batei midrash*,
  Sephardi and Ashkenazi alike — which keeps the bench out of live communal disputes by
  construction.

### The chapter map (the locus)

`canonical_source.locus_unit` is `perek`, and each scenario's `source_locus` is the chapter of
*Mesillat Yesharim* whose rung best fits its terrain (with `locus_label` naming the specific
rung, the proof text, and any further source). The 26 chapters, grouped by the rung of the
ladder, are:

| # | Chapter | Rung |
|---|---|---|
| 1 | The duty of a person in their world (*chovat ha-adam b'olamo*) | the ground of the ladder |
| 2 | The trait of watchfulness (*zehirut*) | Watchfulness |
| 3 | The components of watchfulness | Watchfulness |
| 4 | Acquiring watchfulness | Watchfulness |
| 5 | The detractors of watchfulness | Watchfulness |
| 6 | The trait of alacrity (*zerizut*) | Alacrity |
| 7 | The components of alacrity | Alacrity |
| 8 | Acquiring alacrity | Alacrity |
| 9 | The detractors of alacrity (laziness, *atzlut*) | Alacrity |
| 10 | The trait of cleanliness (*nekiyut*) | Cleanliness |
| 11 | The details of cleanliness — the specific sins (theft, forbidden speech, oaths) | Cleanliness |
| 12 | Acquiring cleanliness | Cleanliness |
| 13 | The trait of separation / abstinence (*perishut*) | Separation |
| 14 | The components of separation | Separation |
| 15 | Acquiring separation | Separation |
| 16 | The trait of purity (*taharah*) — purity of motive | Purity |
| 17 | Acquiring purity | Purity |
| 18 | The trait of piety (*chasidut*) | Piety |
| 19 | The components of piety | Piety |
| 20 | The weighing of piety (*mishkal ha-chasidut*) — discernment against misguided excess | Piety |
| 21 | Acquiring piety | Piety |
| 22 | The trait of humility (*anavah*) | Humility |
| 23 | Acquiring humility | Humility |
| 24 | The trait of fear of sin (*yir'at chet*) | Fear of Sin |
| 25 | Acquiring fear of sin | Fear of Sin |
| 26 | The trait of holiness (*kedushah*) and how to acquire it | Holiness |

Chapter 20, the *mishkal ha-chasidut* — Ramchal's insistence that piety be **weighed** by
discernment, lest a person's "stringency" become a sin against others or against themselves — is
the spine of the bench's `middle_path` axis and its `against_excess` pole.

## Secondary spines, for coverage and ordering

- **Orchot Tzadikim** ("The Ways of the Righteous," anon., Ashkenaz, 15th c.) — the great
  anatomy of the *middot*, organized as 28 **gates** (*she'arim*), each a trait taken with its
  opposite: pride and humility, anger and good-will, hatred and love, envy, stinginess and
  generosity, the gate of *lashon ha-ra*, of truth, of flattery, of joy, of worry, of
  repentance. It is the structural home of the bench's `middot` and `virtues` taxonomies.
- **Chovot ha-Levavot** ("Duties of the Heart," Bachya ibn Paquda, al-Andalus, 11th c.) — the
  inward duties the limbs cannot perform: the gates of trust (*bitachon*), of devotion and pure
  motive (*yichud ha-ma'aseh*), of self-accounting (*cheshbon ha-nefesh*), of humility, of
  repentance, of abstinence, of the love of God. The deepest classical anchor for **intention**
  and the inner life.
- **Pirkei Avot** (the Mishnaic Ethics of the Fathers) — the Tannaitic root: *"make for yourself
  a teacher and acquire for yourself a friend"* (1:6); *"who is wise / strong / rich / honored"*
  (4:1); *"be of the disciples of Aharon — loving peace and pursuing peace"* (1:12); *"envy,
  desire, and the pursuit of honor remove a person from the world"* (4:21).
- **Tomer Devorah** (Rabbi Moshe Cordovero, the Ramak, Tzfat, 16th c.) — *imitatio Dei* through
  the thirteen attributes of mercy (Micah 7:18–20): to be, in one's own conduct, patient,
  forbearing, and merciful as God is.
- **Sha'arei Teshuvah** (Rabbeinu Yonah of Gerona, 13th c.) — the gates of repentance, and the
  gravest treatment of the speech-sins and their levels.
- **The Rambam's Hilchot De'ot** (Mishneh Torah) — the **middle path** (*shvil ha-zahav*): every
  trait has two extremes and virtue is the mean, *except* arrogance and anger, where one leans to
  the far pole of humility and calm. The anchor for the bench's `middle_path` axis.
- **The Mussar movement** (Rabbi Yisrael Salanter, Lithuania, 19th c., and its schools) — the
  systematic practice of mussar: *cheshbon ha-nefesh*, the repeated emotional study that moves a
  truth from the head to the heart, the *va'ad*. Its schools differ by emphasis — **Slabodka** on
  *gadlut ha-adam* (the greatness and dignity of the human being), **Novardok** on *shiflut* and
  radical *bitachon* (breaking the ego's hold), **Kelm** on order and *menuchat ha-nefesh* — which
  is itself a witness that the tradition has no single school.
- **Sefer Chofetz Chaim** (Rabbi Yisrael Meir Kagan, 1873) — the definitive halachic-mussar
  codification of *shemirat ha-lashon* (guarded speech), binding for the bench's many
  *lashon ha-ra* scenarios.
- **The Chassidic stream** — *Tanya* (Rabbi Schneur Zalman of Liadi) on the *beinoni* and the two
  souls, and the Chassidic masters on *simcha* against *atzvut* (joy against the corrosive sadness
  that is the yetzer's gateway) — so the bank is not Litvish-only.
- **Iggeret ha-Ramban** (Nachmanides' letter to his son) — humility as the gate of all the
  traits, and *"accustom yourself to speak all your words gently"* (*b'nachat*).

## Why it is consensus-grade — and where it is not single-canon

- **Pan-Jewish.** *Mesillat Yesharim*, *Orchot Tzadikim*, *Chovot ha-Levavot*, *Pirkei Avot*, and
  the *Chofetz Chaim* are common ground across the observant Jewish world — Litvish and Chassidic,
  Sephardi and Ashkenazi. This tradition is scoped to that **shared ethical-formation
  inheritance**, not to one community's particular *halachic* ruling, *nusach*, or *hashkafah*.
- **Ships its own ground truth.** In this format the proof texts live per scenario in
  `judge-guidance.md`, so the judge is anchored locally and never supplies its own theology.
- **Not single-canon.** Unlike *Riyāḍ al-Ṣāliḥīn*, this is a constellation, not one book. So two
  safeguards apply: each scenario carries its own anchors in `judge-guidance.md`, and the whole
  bank is flagged **draft, pre–scholar-review** (`scholar_review.status: none`). Anchor texts are
  paraphrased to classical sources and **must be verified against the original Hebrew/Aramaic and
  competent halachic authority before any normative use** — and questions of practical *halacha*
  belong to a person's own *rav*, never to the bench.

## The intrinsically-Jewish scenarios and the locus

A minority of scenarios hinge on matter *Mesillat Yesharim* addresses only obliquely — a
practical *she'eilah* (Shabbat, kashrut, mourning observance), the appeasing of a wronged fellow
before Yom Kippur, religious scrupulosity (OCD-adjacent *chumra*-piling), the limits of
*tochacha* (rebuke). For these, `source_locus` maps to the nearest *Mesillat Yesharim* chapter
(e.g. guarded speech → 11 the details of cleanliness; misguided over-piety → 20 the weighing of
piety; pure motive → 16 purity; the bereaved and the fear of Heaven → 24 fear of sin), while the
**real** binding anchors — the *Chofetz Chaim* on *lashon ha-ra*, Yoma 8:9 on *bein adam
la-chavero*, the Rambam on the mean, Rabbeinu Yonah on teshuvah — are carried in that scenario's
`judge-guidance.md`. The locus is honest provenance; the judge seam is the ground truth.
