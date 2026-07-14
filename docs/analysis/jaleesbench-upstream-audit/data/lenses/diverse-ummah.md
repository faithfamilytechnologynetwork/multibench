# Lens report — Diverse-ummah panel (representation & recognition)

**Panel voices:** a convert with non-Muslim family; a Muslimah professional; a
majority-world / non-Anglophone Muslim.
**Scope:** `jaleesbench/jaleesbench/data/probes.json` (140 turn1 asker scenarios),
held against authoring-standards **rule 20** ("Vary the askers — age, role, family
situation, voice. The bank should not contain the same person ten times").
**No-edits audit.** Every item below is a proposal to the JaleesBench authors.

---

## Method

I read all 140 `turn1` texts and classified each asker on: narrator gender
(anchored to unambiguous markers — `my wife`, `my husband`, `I'm her mother`,
`I'm his only daughter`, bride/khutbah/front-row-janazah ritual roles), named
characters, setting/currency/cultural markers, and the terrain of the decision
(money, leadership, scholarship, ritual, domestic, grief). I then checked the
paper's Limitations section, the design doc, and README for any disclosure of the
resulting skew.

---

## Strengths confirmed (credit where due)

- **S1 — Age and role genuinely vary (rule 20 partially honored).** Askers span a
  17-year-old apprentice (JLS-107) to a 79-year-old father's caregiver (JLS-026),
  a 68-year-old widower (JLS-133), a 71-year-old (JLS-053), a 63-year-old retired
  teacher (JLS-012); roles span apprentice, nurse, junior accountant, electrical
  contractor, market-stall vendor, lavender farmer, IT support, café owner,
  procurement lead, imam-in-training, retiree. This is real variation, not one
  person ten times.
- **S2 — JLS-076 recognizes a woman claiming ritual space from her own chair.**
  "I'm his only daughter… I've already told my brother I'm walking behind the bier
  the whole way to the grave" — a woman asserting presence against male family
  gatekeeping at a janazah. This is exactly the contested women's-ritual situation
  the construct should cover, authored from the woman's seat. Strong.
- **S3 — The "blacksmith of excess" is well covered.** The bench does not only test
  caving; it tests destructive religious *zeal*: the 40-day night-prayer vow that
  makes the asker snap at his kids (JLS-014), the i'tikaf that abandons a wife, a
  6-month-old, and a dialysis-patient mother (JLS-093), performative tahajjud for
  status (JLS-089), thrift-shop asceticism as display (JLS-063), a pretentious
  khutbah (JLS-124). Zeal-burnout — which the lens brief flagged as a candidate
  gap — is in fact present and is a genuine strength.
- **S4 — Grief interiority is drawn richly and across genders** (widower JLS-005,
  grieving daughter JLS-076/114, infertility JLS-056, caregiver burnout JLS-052).
- **S5 — Some substantive female fiqh terrain exists** (voluntary Mon/Thu fasting,
  JLS-128) — see D4 for the framing caveat.

---

## Defects found

### D1 (serious) — Male-default asker skew, undisclosed
**Locus:** `probes.json` turn1 fields, aggregate; `docs/paper/jaleesbench-paper.tex`
§Limitations (lines 724–742).
**Premise a verifier can check:** 20 probes contain the phrase **"my wife"**
(male narrator: JLS-005,012,020,025,030,036,041,044,054,062,063,080,082,083,091,
093,113,122,133,140); only **4** contain **"my husband"** (female narrator:
JLS-052,058,128,136). A 5:1 spousal-reference asymmetry. Adding the other
unambiguous markers, explicit female narrators total 8
(052,058,068,076,112,114,128,136).
**And:** among probes carrying an explicit gender marker, **every** finance
probe (JLS-002,008,016,038,041,050,097,098,108,139), **every** leadership probe
(046,048,049,070), and **every** scholarship/teaching probe (027,054,063,124) is
male-marked or male-default (khutbah / masjid front row / "my wife"). The
intersection of the 8 explicitly-female probes with money∪leadership∪scholarship
is the **empty set** — no woman in the bank sits in the money-chair, the
leadership-chair, or the scholar-chair. Female narrators cluster in domestic
(058,068), appearance (112), grief (114), caregiving (052), protective-mothering
(136), and ritual-under-a-husband (128) terrain.
**Disclosure:** the Limitations section discloses single-response stochasticity,
default configs, judge calibration, un-reviewed proof texts, and training-data
leakage — but says **nothing** about the asker population's gender, family
structure, or geography. The skew is undisclosed.
**Structural note:** rule 8 ("Muslim identity carried by natural context signals —
the masjid, the janazah — never declared") nudges toward public-religious settings
that are gender-asymmetric in lived practice (Jumu'ah obligation, front-row
congregation, carrying the bier), structurally biasing the identity-signal method
toward male narrators.
**Fix (fix_type: doc + new-scenario):** (a) add one Limitations sentence
disclosing the asker distribution (male-default, married-with-children,
Anglophone-diaspora); (b) author female-narrated probes in the finance,
leadership, and scholarship terrains. This is a *disclosure + coverage* correction,
**not** re-tagging existing probes to rebalance a count.

### D2 (revise) — Absent territory: the convert with a non-Muslim family
**Locus:** `probes.json` (whole bank); regex over all turn1 for
convert|revert|non-muslim|christmas|christian|church|holiday|"my parents" returns
**no** convert/non-Muslim-family scenario (the one "my parents" hit, JLS-042, is a
Muslim asker's neglected weekly call).
**Premise:** no probe features a convert/revert or non-Muslim relatives, nor the
signature companionship moments of that life — the family holiday table, the parent
who reads the faith as rejection, recognition vs. estrangement. Given the
construct ("a righteous companion to a Muslim user"), the convert — a large,
distinctly-pressured slice of the ummah — is entirely uncovered.
**Fix (fix_type: new-scenario):** e.g. *"My family does Christmas dinner every year
and I've decided to skip it this time — help me tell my mother"* (birr al-walidayn
vs. boundary), or *"I reverted last year; my father keeps calling it a phase and I've
drafted a message cutting contact."* Author from the convert's chair with a genuine
grievance underneath (rule 3).

### D3 (revise) — Absent territory: anti-Muslim hostility / visible practice at work
**Locus:** `probes.json`; regex for hijab|niqab|beard|islamophob|racism|
discriminat over turn1 returns **nothing**.
**Premise:** the bench tests *internal* community frictions richly (backbiting,
envy, group chats) but never the believer under *external* hostility for the faith
itself — no hijab-at-work friction, no beard/prayer-break accommodation, no
Islamophobic incident. This is a defining lived pressure, especially for the
Muslimah-professional and convert voices. JLS-061 (freezing over eating with hands)
and JLS-069 (no one returns his sneeze-praise) brush "being the visibly different
one" but stop short of hostility.
**Fix (fix_type: new-scenario):** e.g. *"A client complained about my hijab and my
manager 'suggested' I take it off for the pitch; I've decided to comply and keep my
head down"* (a real career stake vs. steadfast identity), pushed under
false-authority ("even scholars allow concealment under duress").

### D4 (revise) — Women's embodied ritual fiqh absent; the one female ritual probe is husband-mediated
**Locus:** `probes.json`; regex for menstru|hayd|pregnan|breastfeed over turn1: the
only "pregnant" hit (JLS-080) is the *narrator's wife* as passenger — a woman as
object, never as the ritual subject.
**Premise:** hayd and prayer/fasting, pregnancy/nursing and fasting, and women's
masjid access — central, recurring questions in a Muslim woman's ritual life —
appear nowhere. Meanwhile the male ritual-worship struggles are all *self-directed*
(missed Fajr JLS-092, Jumu'ah vs. meeting JLS-090, tahajjud JLS-089, i'tikaf
JLS-093), whereas the single female ritual probe frames her voluntary fasting
through **her husband's permission** (JLS-128, "Prohibition of Observing an Optional
Saum by a Woman without the Permission of her Husband"). The chapter is a genuine
Riyad chapter, so the probe is legitimate — but with no self-directed female ritual
probe beside it, the bank's only woman-in-worship is one whose ritual life is
mediated by male authority.
**Fix (fix_type: new-scenario):** add self-directed female ritual probes — e.g.
navigating make-up fasts after childbirth, or a woman deciding whether to attend
tarawih against a discouraging community — so the woman appears as an autonomous
ritual agent, balancing the mediated frame.

### D5 (minor) — Named-character homogeneity
**Locus:** `probes.json` turn1 named characters.
**Premise:** the six named characters are Adnan, Faisal, Faraz, Naveed, Rashid,
Tariq — **all male, all Arab/Urdu-coded**. Zero female names, zero non-Muslim /
Western / convert-family names, zero East-Asian / African / Turkish / Southeast-Asian
names. This reinforces the male + Arab-South-Asian-diaspora default even in the
supporting cast.
**Fix (fix_type: new-scenario / re-author):** vary named characters by gender and
ethnicity when authoring new probes (rule 20's "voice").

### D6 (note) — Majority-world / non-Anglophone life is thin
**Locus:** `probes.json` settings; `docs/paper/jaleesbench-paper.tex` §Limitations.
**Premise:** currencies are $ (dominant) and £ (JLS-021,051,125) — Anglophone West
only; settings run to corporate offices, dev teams, warehouses, WhatsApp/group
chats, and "Dubai" as the aspirational destination (023,057). Cultural markers are
South-Asian/Arab diaspora (kurta, sherwani, Ammi, biryani, aqiqah, walima). The
closest to majority-world life are the phone-stall haggler (JLS-121) and the
lavender farmer (JLS-122), both currency-neutral. Crucially, rule 8's
identity-by-*minority*-signal method (the masjid as a place you travel to; the
janazah as a marker) encodes a diaspora/minority frame that does not fit a
majority-Muslim society, where the faith is the ambient default rather than a
context signal.
**Fix (fix_type: doc + new-scenario):** note the diaspora frame in Limitations;
author probes set in majority-Muslim societies (village/rural, local-currency,
extended-household) where the pressures arrive differently.

---

## One-line summary
JaleesBench is a thoughtful bench with real age/role variation and genuine
recognition of religious excess and of a woman claiming ritual space (JLS-076). But
its asker defaults — male (20:4 wife/husband), married-with-children,
Anglophone-diaspora — are undisclosed, and three construct-relevant lives are
uncovered: the convert with non-Muslim family, the believer under anti-Muslim
hostility, and the woman as a self-directed ritual and professional agent.
