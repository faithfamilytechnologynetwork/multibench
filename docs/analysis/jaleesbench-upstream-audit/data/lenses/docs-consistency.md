# Lens: Documentation / Consistency Editor

Scope: reconcile top-level `README.md` ↔ paper (`docs/paper/jaleesbench-paper.tex`)
↔ design doc (`docs/jaleesbench-design.md`) ↔ companionship guide
(`docs/jaleesbench-guide.md`) ↔ `prompts.py` GUIDE ↔ harness `jaleesbench/README.md`.
No edits made; every item is a proposal for the JaleesBench authors.

## Confirmed strengths

- **The Guided-framing guide that was RUN matches the paper appendix.** The paper's
  App. guide (`app:guide`, tex lines 1011–1093) is a faithful, substantively verbatim
  reproduction of `prompts.py` `GUIDE` (the string actually prepended at collection
  time): same opening Stated sentence, same three practice bullets, same four pillars,
  same ten heart states in the same order, same seven prophetic techniques, same "Hold
  your ground with warmth" and "Never" blocks. The paper's claim that the guide is
  "reproduced verbatim" (tex 889–890, 1007) is honest modulo LaTeX typography. Readers
  can trust that the published guide is the instrument.
- **Band scale is coherent everywhere except the top README strip.** `Burns/Sparks/
  Inert/Scent/Perfume` with the raw −2..+2 emitted by the judge and the halved −1..+1
  reporting scale is stated identically in the paper (tex 312–314, 945–949), design doc
  (§6.1), `prompts.py` JUDGE_PROMPT, `html_report.py` (BAND_NAMES, line 17 + strip line
  137), `export_web.py` (lines 42–43), and the harness README (Burns −1 … Perfume +1).
- **Design doc is correctly self-labeled as a stale draft.** Header (lines 3–5):
  "draft v0.3 — June 2026 … discussion draft for review. Not yet scholar-reviewed."
  Its staleness (10-probe pilot, 139 probes) is disclosed, not passed off as current.
- **Grid numbers are internally consistent** across top README, harness README, and
  paper: 140 scenarios × 6 pressures × 3 framings; 8 subject systems; 20,160 sittings.

## Defects found

### D1 (revise, public-facing). README band strip uses wrong band names "Smoke" and "Neutral".
- Locus: `README.md` lines 53–54 (the band ASCII strip).
- Premise: the strip reads `Burns (−1) · Smoke (−0.5) · Neutral (0) · Scent (+0.5) ·
  Perfume (+1)`. Every other artifact (paper tex 312–314 & 945–949, design doc §6.1,
  `prompts.py`, `html_report.py`, `export_web.py`) names bands −0.5 and 0 **Sparks** and
  **Inert**. `grep` confirms "Smoke"/"Neutral" as band labels occur ONLY in this README
  strip; the CLI `smoke` command (harness README line 62, `cli.py` line 18) is an
  unrelated key-check test, not a band.
- Fix (doc): rename to `Sparks (−0.5)` and `Inert (0)` in the README strip. fix_type=doc.

### D2 (revise, cross-doc arithmetic). "143 clusters, four excluded" cannot yield 140 probes.
- Locus: paper tex 254–255 (`sec:clustering`) and design doc §3.1 (lines 155–158).
- Premise: paper says "**140 probes** from 369 mapped chapters / 143 clusters (four
  etiquette-only clusters excluded)" — but 143 − 4 = 139, not 140. The design doc, from
  the same map, states "**139 probes** … 143 clusters, of which 4 … are excluded"
  (arithmetically self-consistent at 139) while the shipped bank is 140
  (`probes.json`, harness README line 76). So the *paper's own sentence* is internally
  inconsistent (140 vs 143−4), and the *design doc's total* (139) disagrees with the
  shipped 140. Exactly one of {cluster count 143, exclusion count 4, probe count 140}
  is mis-stated in the paper.
- Fix (doc/statistics): reconcile the three numbers against the actual chapter-map
  exclusion count (shared with the taxonomy/statistics lens, which counts the
  `(etiquette-leaning)` clusters). Likely the paper should read "143 clusters, three
  excluded → 140" or "144 clusters, four excluded → 140". fix_type=doc.

### D3 (minor, staleness). Design doc probe count (139) and pilot narrative (10 probes) are stale vs the shipped 140-probe / 8-system bench.
- Locus: design doc exec summary ("Pilot: 10 probes × 3 framings × 6 pressures … two
  frontier models … two … as judges") and §3.1/§3.2 ("139 probes", "The 139 drafts").
- Premise: shipped bank is 140 probes over 8 subject systems (paper, harness README).
  Design doc still describes the pre-run 10-probe pilot and a 139-probe plan.
- Fix (doc): add a one-line "superseded by the paper for final numbers" pointer at the
  top, or refresh 139→140 and the pilot framing. Disclosed as a draft, so severity is
  low. fix_type=doc.

### D4 (minor, doc-consistency). `docs/jaleesbench-guide.md` claims to be "this exact text … used in the Guided framing" but is not byte-identical to what was run, and is labeled an older draft.
- Locus: `docs/jaleesbench-guide.md` header (lines 2–3): "*Draft v0.1 for review — this
  exact text (between the rules) is the system prompt used in the Guided framing.*"
- Premise: the run version is `prompts.py` GUIDE — plain ASCII, no markdown bold, uses
  "al-Ghazali / Abu Ghudda / Qur'an". `docs/jaleesbench-guide.md` adds **bold** section
  headers and full Arabic diacritics (al-Ghazālī / Abū Ghudda / Qurʾān). Substance is
  identical, but it is NOT the byte-exact prompt, and "Draft v0.1" is older than the
  paper's App. guide. The "this exact text" phrasing overstates fidelity.
- Fix (doc): soften to "a formatted rendering of the Guided system prompt" and/or bump
  the draft label to match the paper appendix as the canonical copy. fix_type=doc.

### D5 (minor, repo-layout). README "Repository layout" table omits the `apps/` frontend directory that exists in the tree.
- Locus: `README.md` lines 74–81 (layout table lists `jaleesbench/`, `docs/paper/`,
  `docs/`, `codev/`/`.codev/`).
- Premise: the repo tree also has a top-level `apps/` (containing `jaleesbrowser`, the
  results-browsing SPA) plus `AGENTS.md`/`CLAUDE.md`; none are listed. Everything the
  table *does* list resolves correctly (docs/paper, docs design+standards+chapter-map+
  HTML report, codev all present).
- Fix (doc): add an `apps/` row (or note it is out of scope for the benchmark artifact).
  fix_type=doc.

### D6 (note, cross-doc — flagged for the citation lens). Design doc §6.4 describes citation detection as "transparent text patterns … not by the judge"; the paper (sec citation) describes a temperature-0 LLM grader.
- Locus: design doc §6.4 ("Detection is by transparent text patterns over the
  transcripts, not by the judge") vs paper `sec:citation` (LLM grader) and the harness
  `detect-citations` = Gemini Flash-Lite (harness README line 67, `citation.py`).
- Premise: the two docs describe different detection mechanisms for the same column.
  This is primarily the citation/code-repro lens's finding; noted here only as a
  README↔paper↔design consistency touchpoint. The design doc's draft label partly
  covers it. fix_type=doc.

### D7 (note, presentation). Paper band-definition table labels Burns "−1" while the judge emits −2.
- Locus: paper tex 945–949 (band table gives values −1/−0.5/0/+0.5/+1 directly).
- Premise: the judge (`prompts.py`) emits integer bands −2..+2; the paper's headline
  band table presents the *halved reporting* values as the band values. Text at tex
  312–314 does disclose the rescaling, so this is a presentation choice, not an error —
  but a reader of the table alone would think Burns = −1. The design doc §6.1 handles
  this more transparently (shows raw −2 then explains halving). fix_type=doc (optional:
  add "(raw −2, reported −1)" to the paper table).
