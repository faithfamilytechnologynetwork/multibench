# JaleesBench (sunni-islam) ultracode audit — shared brief for all audit agents

## What is being audited
The **sunni-islam** tradition of MultiBench, at `/home/user/multibench/traditions/sunni-islam/`.
It is the verbatim port of **JaleesBench** (Kadous, Olsen & Hwang) — a benchmark measuring whether
an AI assistant is *al-jalīs al-ṣāliḥ* (the righteous companion) to a Muslim user, judged by the
residue an exchange leaves on the user (hadith of the perfume-seller and the blacksmith,
Bukhārī 5534 / Muslim 2628). The full paper text is at
`/tmp/claude-0/-home-user-multibench/628967ea-87df-5eb4-9a1f-3b7d1ecfdf98/scratchpad/jaleesbench-paper.txt` — read it for construct, protocol, bands, and framings.

## HARD RULES for every agent
1. **READ-ONLY.** Do not edit, create, or delete ANY file in the repo. Your output is your report.
2. **Quote the actual repo text** you are flagging (file path + exact phrase). A finding whose
   premise misstates the current text is worthless.
3. Every finding needs an explicit `fix_type`: one of
   `framing | citation | re-tag | new-scenario | safety | neutrality | boundary | consistency | idiom | wording | other`.
4. Do not propose re-tagging as a fix for distribution imbalances — imbalances are fixed by
   *authoring new scenarios*, never re-tagging (MultiBench house rule).
5. The bench deliberately stays **out of live intra-Sunni scholarly disputes by construction**
   (consensus-grade source). A finding of the form "the bench should take a side on X" is almost
   certainly wrong; "the bench should *state* its neutrality as a scoring contract" may be right.
6. Preserve the bank's known strengths — do not propose reopening them:
   the disguised first-person probe form (never a quiz); the per-probe authored pressures;
   the false-authority corrective lines; the deliverable rule; proof-text-anchored judging
   (judge-guidance.md IS the ground truth — never propose a separate proof-text corpus).

## File layout (per scenario `scenarios/JLS-NNN/`)
- `scenario.yaml` — id, tags.pillars (Ibn al-Qayyim: courage/justice/patience/restraint/cross_cutting),
  tags.hearts (al-Ghazālī stations), source_locus (Riyāḍ al-Ṣāliḥīn bāb number, 1–370),
  locus_label (chapter title), identity_signal (clean = nothing Islamic; leaky = Islamic hints;
  intrinsic = dilemma hinges on Islamic ritual/ruling).
- `turn1.md` — the disguised first-person scenario.
- `pressures.md` — six sections: secularize, insistence, false_authority, good_cause, flattery,
  personal_appeal (per-probe authored user pushback, second turn).
- `judge-guidance.md` — the scenario's binding ground truth: Riyāḍ al-Ṣāliḥīn proof texts
  ("Riyad as-Salihin NNNN: … [collection]"), possibly "(+N further hadith in this chapter)",
  usually a "False-authority corrective: …" line; 10 scenarios also carry "Judge note (pilot): …".

Tradition-level files: `tradition.yaml`, `README.md`, `source.md`, `guide.md` (the one-page
companionship guide used in the Guided framing — identical in substance to paper Appendix E).

## Established structural facts (do not re-derive; you may cite)
- 140 scenarios, 140 unique loci. identity_signal: clean 58 / leaky 40 / intrinsic 42.
- Pillar tag counts: restraint 107, cross_cutting 67, justice 66, patience 36, courage 26.
- Hearts tag counts: love_contentment 81, self_accounting 79, intention_sincerity 59,
  vigilance 45, fear_hope 40, reliance_on_god 36, truthfulness 34, patience_gratitude 16,
  repentance 15, patience 14.
- **No `register` field exists** (no per-scenario safety tagging) and there is **no
  tradition-level safety overlay** in tradition.yaml/README/guide.md.
- **No balance/mean axis taxonomy exists** (sibling traditions have pivot / middle_way /
  middle_path / mean / economia axes tagging which pole of failure a scenario stages).
- The universal judge rubric (workflows/judging/judging/rubric.py) is numeric (−1…+1, five
  scores, NO band names); direction is settled only by judge-guidance.md; the deliverable rule
  and "changing HOW is mercy; changing WHAT is caving" are already universal boundary rules.
- guide.md's Ghazālī station list does not match the `hearts` taxonomy values
  (guide: repentance; patience and gratitude; fear and hope; simplicity and detachment;
  reliance on God; love and contentment; sincerity of intention and truthfulness; vigilance and
  self-accounting; reflection; remembrance of death — taxonomy: ten values including separate
  `patience`, `patience_gratitude`, `intention_sincerity`, `truthfulness`, `vigilance`,
  `self_accounting`, and NO simplicity/detachment, reflection, or remembrance-of-death).
- "False-authority corrective:" line missing in JLS-001, 002, 003, 007, 010 (JLS-001's pilot
  judge note carries corrective content inline).

## Sibling standard (what the other traditions gained from their audits)
Read for comparison (post-audit exemplar): `traditions/eastern-christianity/tradition.yaml`,
`README.md`, `guide.md` — note their Safety overlay sections, stated Neutrality contracts, and
balance-axis disclosure. The cross-tradition recommendations that produced them are in
`docs/analysis/synodiabench-ultracode-audit.md` §"Cross-tradition recommendations" (items 1–6:
balance-axis distribution, numbered-locus citation sweep, tradition-level safety overlay,
teacher-authority boundary both directions, inter-school neutrality contract, sibling idiom
leakage). JaleesBench was written BEFORE those recommendations and was deliberately left
untouched by both prior audits — checking it against them is a core purpose of this audit.

## Web grounding
When checking citations (Riyāḍ al-Ṣāliḥīn numbers, Bukhārī/Muslim attributions, Qurʾān āyāt),
prefer web sources (sunnah.com uses the same Riyāḍ numbering the bank uses; quran.com for āyāt).
If the network blocks a fetch, say so and ground from internal knowledge with a stated
confidence. NOTE: Riyāḍ al-Ṣāliḥīn numbering varies by edition — the bank's numbers should match
sunnah.com's continuous numbering; treat a mismatch against a DIFFERENT edition as a numbering
variant, not an error.
