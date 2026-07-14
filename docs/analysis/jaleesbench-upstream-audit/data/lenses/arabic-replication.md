# Lens: Bilingual (Arabic/English) Replication Audit

Scope: `jaleesbench/jaleesbench/data/probes_ar.json` vs `probes.json`, and the Arabic
code path in `jaleesbench/jaleesbench/prompts.py` (`_ar_prompts`, `framings_ar`,
`judge_blocks_ar`), with wiring in `collect.py`, `judge.py`, `batching.py`, `cli.py`.
Upstream README states "An Arabic-language replication of the protocol is in progress."

READ-ONLY audit. All items are proposals for the JaleesBench authors.

---

## Strengths confirmed

- **Full structural parity of the two banks.** Both files are `{pressures, probes}`
  dicts with 140 probes, ids `JLS-001..JLS-140`, in identical order (verified: `in EN
  not AR = []`, `in AR not EN = []`, `order match = True`). The six pressure keys match.
- **Metadata copied verbatim, not re-derived.** `chapter`, `bab`, `pillars`, `hearts`,
  `islamic`, and `proof_texts` are byte-identical EN vs AR across all 140 (0 mismatches
  on every field). So the Arabic bank cannot drift on cluster mapping, pillar/heart tags,
  or the judge's ground truth.
- **All prose actually rendered in Arabic.** Every `turn1`, all 6 `pressure_turns`, and
  every `title` contain Arabic script; none were left in English (0 English-only fields).
- **proof_texts deliberately kept English in both banks** (verified identical), matching
  the `prompts.py` design comment ("proof texts stay English", lines 163, 179/182). This
  is methodologically sound: the judge's binding ground truth is the same Riyāḍ text, and
  keeping the anchor and the judge's reasoning language stable removes a translation
  confound from the direction call. Reasonable design, correctly documented.
- **`judge_blocks_ar` mirrors the English three-part prefix-caching structure**, and
  correctly *appends* the boundary rules rather than splicing at the English marker
  ("the English splice marker is not language-stable", line 178) — a considered choice.
- **Translation quality (where present) is fluent and preserves the argument.** Spot-checks
  (JLS-001, 002, 069, 103, 109, 110, 122, 133) show the emotional register and each
  pressure vector (flattery, personal_appeal, false_authority correctives) carried over
  intact and idiomatically.

---

## Defects found

### 1. [SERIOUS] Arabic prompt/judge scaffolding is not shipped — the whole Arabic path throws
`prompts.py:_ar_prompts()` reads `RESULTS / "prompts_ar.json"` (i.e.
`jaleesbench/results/prompts_ar.json`). That file **does not exist** in the repo —
`results/` contains only `commentary.json`, and a repo-wide search finds `prompts_ar` only
in the two `prompts.py` lines that *read* it. Therefore `framings_ar()` and
`judge_blocks_ar()` raise `FileNotFoundError` on any real call. The only test that touches
the Arabic judge (`test_units.py::test_judge_blocks_ar_structure`) **monkeypatches
`_ar_prompts` with a fake dict**, so CI passes while the shipped path is non-functional.
Consequence: the Arabic **bank** (`probes_ar.json`) ships, but the Arabic **framings +
judge rubric** (the Stated/Guided system prompts and the five-band / seven-technique judge
in Arabic) do not — and because the actual Arabic rubric text is absent, a reader cannot
even verify that the Arabic judge scores on the same bands/techniques as the English one.
Fix: commit `results/prompts_ar.json` (or move Arabic prompts into `data/` alongside the
bank), and add a test that exercises the real loader.

### 2. [REVISE] No CLI entry point runs the Arabic variant
The library layer is lang-aware (`collect(probes_path=...)`, `judge_all(lang="ar")`,
`batching._cfg("ar")`), but **no `cli.py` command passes `probes_ar.json`, `framings_ar()`,
or `lang="ar"`**: `collect`, `smoke`, `judge`, and `batch-judge` are all hardwired to the
English bank and default framings. So even with defect #1 fixed, the released CLI offers no
way to reproduce the Arabic run without writing custom Python. Fix: add a `--lang ar` option
(or `collect-ar`/`judge-ar`) that threads `probes_ar.json` + `framings_ar()` + `lang="ar"`.

### 3. [REVISE] Natural Arabic leaks Muslim identity into probes tagged `islamic="clean"`
`islamic` is copied verbatim from EN, but idiomatic Arabic introduces near-obligatory pious
formulae that the English deliberately avoided, breaking the clean/leaky stratification for
the Arabic run:
- **JLS-020 (clean):** EN "They actually took it well." → AR "**والحمد لله** تقبّلوا الكلام"
  (adds *alhamdulillah*).
- **JLS-109 (clean):** EN "my **late** mother's gold set" → AR "طقم الذهب تبع أمي **الله
  يرحمها**" (adds the "God rest her" formula).
- **JLS-133 (clean):** EN "my wife **passed** last spring" → AR "زوجتي **الله يرحمها**
  توفّت" (same formula).
- **JLS-069 (clean):** EN's euphemism "said **the praise**" becomes the explicit "قلت
  **الحمد لله**" (faithful, but converts an oblique cue into an overt marker).

Because the paper's citation table (sec. citation) splits clean vs leaky and reads religious
identity off the surface text, these copied `clean` tags are wrong for the Arabic subject —
the user now visibly presents as Muslim. This is a *structural* tension (Arabic politeness
formulae for death/good-news are hard to omit naturally), not a one-off typo. Fix: either
re-audit `islamic` per-probe on the Arabic surface text (a *measurement* correction, not
balance re-tagging), or document that the clean/leaky axis is defined on the English bank and
does not transfer verbatim to Arabic. This is a false-authority-symbol case too (see #6).

### 4. [REVISE] Uncontrolled dialect — no stated policy, and intra-probe mixing
The bank is written in **mixed regional colloquials**, not a single controlled register:
- Egyptian (`دلوقتي`, `عايز`, `الجروب`, `معايا`, `إزاي`): JLS-001, JLS-002.
- Gulf/Najdi (`الحين`, `أسوي`, `أبغى`, `مو`, `هالشي`, `تقرا`): JLS-018, 020, 069, 109, 110, 133.
- Levantine markers (`هلأ`, `هاي`, `شو`, `لقيتني`): JLS-122; and **mixed within one probe**
  in JLS-103 (Levantine `شو أقول` beside Gulf/other features) and JLS-109 (`هلأ` beside
  Gulf `أقلها`).

Dialect is itself a demographic/identity signal and shifts how a model reads register and
formality; leaving it uncontrolled (and inconsistent within a probe) is a confound for a
benchmark that measures companionship register. Fix: adopt and document a dialect policy
(single controlled dialect, or MSA, or an explicit dialect field per probe) and remove
intra-utterance mixing.

### 5. [MINOR] Paper is silent on the Arabic replication; no methodology statement
`docs/paper/jaleesbench-paper.tex` mentions "Arabic" only in the etymology of *jalīs* and a
LaTeX macro — it does **not** describe the Arabic replication, the proof-texts-stay-English
decision, dialect, or Arabic-judge parity. Only the README says "in progress." Fix: add a
short methods paragraph (even as future work) stating the design decisions the code already
encodes.

### 6. [MINOR] Schema drift + no bank-parity test
`probes.json` carries a top-level `"version": 2`; `probes_ar.json` omits it. No test asserts
EN/AR id/order/metadata parity — the structural soundness I verified by hand is unguarded, so
future edits to one bank can silently desync. Fix: mirror the `version` key and add a parity
test (ids, order, and the copied metadata fields).

### 7. [NOTE] Titles are fresh Arabic labels, not translations; one numeric localization drift
AR `title` fields are independently authored (JLS-001 "The team message" → "زميلة تسرق
مجهودي" ≈ "a colleague stealing my effort"); harmless as labels but not translation-equivalent,
worth noting for anyone diffing titles. Separately, JLS-110 localizes currency **and** shifts
the amount: EN "$40,000" → AR "خمسة وأربعين ألف **ريال**" (45,000), while EN "$3,500" → AR
"3,500". The $→riyal localization is fine; the 40k→45k change is an incidental content drift.

---

## Bottom line
The **Arabic bank itself is strong**: complete, id/order/metadata-faithful, fully translated,
fluent, with proof texts correctly held in English. The **replication as a runnable artifact is
half-shipped** — the Arabic framings/judge prompts are absent (#1) and unwired from the CLI
(#2), and a test masks the gap. The most substantive *content* issue is that copying the
`islamic` clean/leaky tags into Arabic is unsound because natural Arabic leaks identity (#3),
compounded by an uncontrolled dialect policy (#4).
