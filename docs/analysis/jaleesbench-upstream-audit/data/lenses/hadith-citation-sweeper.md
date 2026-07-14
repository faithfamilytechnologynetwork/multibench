# Lens report — Hadith-sciences citation sweeper (web-grounded)

Scope: `proof_texts` across the 140 probes in
`jaleesbench/jaleesbench/data/probes.json`, all Quranic references in the
correctives, and the grading of anchor narrations. Web-grounded via WebSearch
(sunnah.com / quran.com direct fetch is blocked by egress policy — all
verifications below use sunnah.com/hadeethenc/abuaminaelias snippets returned
through WebSearch, and are flagged `needs_web_grounding=true`).

## How proof_texts is built (context)
Each probe's `proof_texts` is a string with (a) an **anchor block** of the
chapter's Riyāḍ al-Ṣāliḥīn texts, quoted verbatim as `Riyad as-Salihin NNNN: …
[Al-Bukhari and Muslim] .` — Riyāḍ's own **continuous numbering** with Riyāḍ's
own source brackets — and (b) a **False-authority corrective** (135/140 probes)
or a pilot **Judge note** (10 probes) that untangles the turn-2 shubha.

## PRIMARY FINDING — systematic mislabel: Riyāḍ numbers cited as Ṣaḥīḥ collection numbers

Nine probes cite `Muslim NNNN` / `Bukhari NNNN` inside a corrective. They split
cleanly into two groups:

**Genuine collection numbers (CORRECT) — the number is NOT a Riyāḍ number in the block:**
| Probe | Cited | Resolves to | Verdict |
|---|---|---|---|
| JLS-051 | Muslim 49 | Ṣaḥīḥ Muslim 49 (Kitāb al-Īmān), "whoever sees an evil, change it with his hand…" | ✅ correct |
| JLS-062 | Muslim 91 | Ṣaḥīḥ Muslim 91 (Kitāb al-Īmān), arrogance hadith incl. "Allah is beautiful and loves beauty" | ✅ correct |
| JLS-091 | Muslim 2664 | Ṣaḥīḥ Muslim 2664 (Kitāb al-Qadar), "the strong believer is better…"; ends "do not say *if only*…say Allah decreed" | ✅ correct |
| JLS-100 | Bukhari 1153 | Ṣaḥīḥ al-Bukhārī 1153 (Kitāb al-Tahajjud), ʿAbdullāh b. ʿAmr moderation hadith — on-topic, but see minor finding below | ⚠ number ok, quote mis-sourced |

**Mislabels — the cited number is exactly the Riyāḍ continuous number in the probe's own block:**
| Probe | Cited (wrong) | Actually is (Riyāḍ) | Correct Ṣaḥīḥ locus |
|---|---|---|---|
| JLS-069 | "Muslim 880, Bukhari 881" | Riyāḍ 880 (Abū Mūsā, [Muslim]); Riyāḍ 881 (Anas, [Bukhārī & Muslim]) | Abū Mūsā "reply only if he praised Allah" = **Ṣaḥīḥ Muslim 2992** (Kitāb al-Zuhd); Anas "two men sneezed" = **Ṣaḥīḥ al-Bukhārī 6225** (Kitāb al-Adab) |
| JLS-074 | "Muslim 917-918" | Riyāḍ 917 (Muʿādh, [Abū Dāwūd]); Riyāḍ 918 (Abū Saʿīd, [Muslim]) | "Exhort your dying — lā ilāha illā Allāh" = **Ṣaḥīḥ Muslim 916** (Kitāb al-Janāʾiz). NB Riyāḍ 917 is an **Abū Dāwūd** narration, not Muslim at all |
| JLS-105 | "Muslim 1578" | Riyāḍ 1578 (Abū Hurayra) | **Ṣaḥīḥ Muslim 67** (Kitāb al-Īmān), "two matters are signs of disbelief: defaming lineage, wailing over the dead" |
| JLS-131 | "Muslim 1766" | Riyāḍ 1766 (Abū Hurayra) | **Ṣaḥīḥ Muslim 971** (Kitāb al-Janāʾiz), "better to sit on a live coal than on a grave" |
| JLS-132 | "Muslim 1767" | Riyāḍ 1767 (Jābir) | **Ṣaḥīḥ Muslim 970** (Kitāb al-Janāʾiz), "forbade that graves be plastered / built over" |

Mechanically confirmed in-file: **every** mislabeled number equals a
`Riyad as-Salihin NNNN` present in that same probe's anchor block (5/5). The
error is triggered precisely when the author cites a hadith that is *already in
the block*: they reuse the Riyāḍ number under a Ṣaḥīḥ label. When they reach
outside the block (JLS-051/062/091/100) they correctly look up the real
collection number. So the mechanism is understood and the fix is mechanical.

**Harm:** the anchor TEXT the judge reads is correct and quoted in full, so
ground truth is intact. But the corrective's parenthetical resolves, in the
actual Ṣaḥīḥ Muslim collection, to an *unrelated* hadith (Muslim's topical
numbering for these matters is 67/916/970/971/2992, all far below 1578-1767).
Anyone verifying the citation lands on the wrong narration. Violates authoring
standard rule 14 (Bukhārī/Muslim preferred; sources labeled accurately) and the
project's citation-integrity posture. **fix_type: citation** — replace each
parenthetical with the corrected locus above (leave the anchor blocks untouched;
they legitimately use Riyāḍ numbering).

JLS-074 is the worst of the five: it labels an **Abū Dāwūd**-graded narration
(Riyāḍ 917) as "Muslim," compounding the collection error with a grading
misattribution.

## SECONDARY FINDING — JLS-091 sole anchor is ḍaʿīf (grading-filter leak)

JLS-091 ("The scan came back clear", chapter *Prostrating out of Gratitude*) has
a **single** Riyāḍ anchor: Riyāḍ 1159 (Saʿd b. Abī Waqqāṣ, the ʿAzwarāʾ triple
prostration for one-third of the Ummah, bracketed `[Abu Dawud]`). Al-Albānī
grades this **ḍaʿīf** (Irwāʾ al-Ghalīl 467; al-Ḍaʿīfah 3229) — it is on the
standard "ḍaʿīf aḥādīth in Riyāḍ al-Ṣāliḥīn" lists. Authoring rule 14 promises
"gradings verified for anything else [outside Bukhārī/Muslim]"; source.md
promises gradings "applied as a filter." Here the chapter's whole virtue rests on
a weak narration. The corrective supplies Ṣaḥīḥ Muslim 2664 (ṣaḥīḥ), so the probe
is not textless, but the *anchor* for the chapter's good is weak.
**fix_type: citation** — add a sound sujūd-al-shukr anchor (e.g. Abū Bakrah, the
Prophet prostrating on receiving good news — Abū Dāwūd 2774 / Tirmidhī 1578,
graded ḥasan) or drop Riyāḍ 1159 and lead with a graded-sound text.

## MINOR FINDING — JLS-100 hard-quote sourced to the wrong sibling hadith

Corrective: "…praying only what one can sustain (Bukhari 1153, **'pray as long as
you feel active, and when you get tired, sleep'**)". Ṣaḥīḥ al-Bukhārī **1153** is
the ʿAbdullāh b. ʿAmr moderation hadith (matn: "you pray all night and fast all
day… if you do, your eyesight will weaken…"). The **exact** hard-quoted formula
"pray as long as you feel active…" is the matn of Ṣaḥīḥ al-Bukhārī **1150**
(Anas, Zaynab's rope). Same chapter (Tahajjud), same authentic grade, same
meaning — a quote/locus mismatch, not a doctrinal error. **fix_type: citation** —
attribute the quoted words to Bukhārī 1150, or drop the quote marks and keep 1153
as a paraphrase.

## STRENGTHS CONFIRMED (this lens)
- **Quranic references are clean.** All 13 (Q49:12, Q4:148, Q65:2-3, Q98:5,
  Q39:53, Q4:48, Q2:155-156, Q17:23-24, Q31:15, Q3:134, Q4:32, Q49:6, Q2:286)
  are correctly numbered and accurately paraphrased/quoted — no sūra:āya error,
  no verse mis-scoped (e.g. JLS-004 correctly distinguishes Q4:48 shirk-unrepentant
  from Q39:53 all-sins-for-the-repentant).
- **The author demonstrably does look up real collection numbers** (Muslim
  49/91/2664, Bukhari 1153) — the mislabel is a narrow, mechanical block-reuse
  slip, not ignorance of the collections.
- **Anchor blocks preserve provenance:** Riyāḍ texts are quoted verbatim with
  Riyāḍ's own grading brackets, so the judge's ground-truth text is authentic and
  traceable even where a corrective's parenthetical is mislabeled.
- **Attributed sayings are correctly labeled as sayings, not hadith** (JLS-003:
  "the saying attributed to al-Fuḍayl b. ʿIyāḍ") — rule-14 compliant.
- **Corrective coverage is high:** 135/140 probes carry an explicit corrective
  for the false-authority shubha (rule 12/15), with the corrective text placed in
  the judge's package as designed.

All hadith claims flagged `needs_web_grounding=true` for the verify pass
(sunnah.com blocked to direct fetch here; confirm each corrected locus there).
