# Lens: Harness Code Reviewer — Correctness & Reproducibility

Scope: does the released harness reproduce the paper's numbers? Central target: the
citation table (paper Table 2). Also judge safety asymmetry, band parsing/scaling, the
v2 overlay, retry/skip/silent-drop, the Qur'an/hadith regexes, and test coverage.
Files read: `score.py`, `citation.py`, `judge.py`, `prompts.py`, `collect.py`,
`providers.py`, `batching.py`, `html_report.py`, `cli.py`, `tests/`. Paper §sec:citation
(lines 548-613) and §sec:judge-agreement (615-618).

## Headline: the central hypothesis is INVERTED (and that is a strength to preserve)

The lens brief hypothesized "the released report reproduces the paper's Table 2 via the
regex over both turns while the paper reports an LLM grader over turn-1 only." The truth:

- The **canonical** released report is `html_report.build_html()` (CLI `report`;
  `cli.py:74-78` docstring: "HTML is the canonical output... no markdown is produced").
  It reads `citations_turn1.jsonl` (the **turn-1 LLM detector**), and splits by probe
  `islamic` class into exactly Table 2's three columns
  (`html_report.py:68-89, 259-281`: `klass_cols = clean→"not Islamic at all",
  leaky→"names Islam", intrinsic→"intrinsically Islamic"`). **This matches the paper's
  stated methodology.**
- `score.build_report()` / `score.cites()` (the regex over BOTH assistant turns, grouped
  by framing only) are **orphaned** — no CLI command and no caller invoke them (`grep`
  confirms `cites()` is called only by `build_report()`, and `build_report()` by nothing).

So Table 2 IS reproduced by the shipped canonical path. The regex is a vestigial *second*
detector, not the reproduction path. Two real defects remain around this, below.

## Defects

### A. CLI cannot generate the turn-1 file the canonical report needs (repro failure)
`cli.py:66-70` `detect-citations` calls `detect_all(limit=limit)` — `turn1` defaults to
`False` (`citation.py:47`), writing `citations_llm.jsonl` (BOTH turns). But `build_html`
reads **`citations_turn1.jsonl`** (`html_report.py:71`), produced only by
`detect_all(turn1=True)`, which **no CLI command or doc exposes**. `build_html` guards on
`if ctpath.exists()` (`html_report.py:72`); when the turn-1 file is absent, `ct={}`,
`cite_rate` returns `None`, and every citation cell renders `—` (`pc(None)`,
`html_report.py:57-58`). **A user running the documented CLI end-to-end gets a report whose
entire citation section (§6 + the scorecard citation rows) is blank — Table 2 is
unreproducible from the CLI.** Fix: add a `--turn1` flag (or `detect-citations-turn1`
command) wired to `detect_all(turn1=True)`, and/or have `build_html` fall back / warn.

### B. Two divergent citation detectors co-shipped (repro hazard)
`score.cites()` (`score.py:30-47`) regex over BOTH assistant turns, grouped by
`(subject, framing)` only (`score.py:190-210, 286-299`) — structurally cannot emit Table
2's per-class columns and uses a different detector and scope than the paper. It is dead
relative to the CLI but is public API; anyone calling `build_report()` obtains a
citation table that silently disagrees with the paper. Recommend deleting
`build_report`/`cites`/`QURAN_RE`/`HADITH_RE` or fencing them as explicitly non-canonical.

### C. "v2" re-judge is a resample of the identical prompt, and inflates reported agreement
`rejudge_disagreements` docstring (`judge.py:171-172`) claims a distinct "v2 boundary-rules
prompt," but it calls the **same** `judge_blocks()` as the base pass (`judge.py:217` vs
`judge_all`'s default `jb=judge_blocks`, `judge.py:101`). `V2_BOUNDARY` is already spliced
into **every** base judgment (`prompts.py:145`). So v2 is a plain re-sample of only the
`≥2`-band-disagreement cells (`judge.py:178-179`). `load_judgments()` overlays it (v2 wins,
`score.py:106-125`) and **every reported statistic — including inter-judge agreement — is
computed on the overlaid set** (`build_report` §2 and `build_html` both consume
`load_judgments`). Re-sampling cells *selected for maximal disagreement* regresses them
toward agreement, mechanically **inflating** the paper's 66% exact / 85% within-one
(paper line 617). No flag reproduces the pre-overlay (base) agreement.
(`judge_user_message`'s unused `v2` param, `prompts.py:150`, is a vestige of the
intended-but-absent distinct prompt.)

### D. Judge-side safety asymmetry can silently drop the Claude judge's sensitive cells
`judge.call_judge` runs the Gemini judge with `safety_off=True` (`judge.py:78-79`) but the
Anthropic judge has no analogue (the Anthropic API exposes no such knob). On a
benign-but-sensitive transcript the Claude judge may refuse → no JSON → `parse_judgment`
raises → all `RETRIES` fail → `judge_all` catches, increments `failed`, and **leaves the
cell pending** (`judge.py:148-152`) with exit 0. Sensitive cells can thus be dropped from
the **Claude judge only**; agreement pairing needs both judges present
(`score.py:219-228`), so those exact cells vanish from the agreement set and from Claude's
band means — a comparability/selection concern between the two judges. Magnitude needs the
run data (rate of Claude refusals). The `safety_off` comment ("Subjects never run with
safety off") correctly addresses *subject* symmetry but not *judge* symmetry.

### E. Silent partial results (minor)
`collect` fails loudly (`SystemExit(1)` if any sitting failed, `collect.py:303-304`), but
`judge_all` and `citation.detect_all` do not. `detect_all`'s except-handler `return`s and
drops the sitting with **no counter** (`citation.py:90-93`); `cite_rate` then divides by the
count of records actually present (`html_report.py:87-89`), silently shrinking the
denominator. `judge_all` prints "N failed (left pending)" but exits 0. A user can mistake an
incomplete run for a complete one. Recoverable (idempotent re-runs via done-sets) but not
enforced.

### F. Regex false pos/neg, if `build_report` is kept (minor, dead-code)
`QURAN_RE` (`score.py:30-33`) requires a digit within 3 chars of "Qur'an", so "Quran,
chapter 2" and surah-by-number-only references miss; `HADITH_RE`'s
`\bprophet\b[^.\n]{0,80}\b(said|says)\b` (`score.py:41`) matches "a false prophet ... says".
Low impact only because the path is dead; real if `build_report` is retained.

### Test-coverage gaps (note)
No test exercises: `citation.detect_all` turn1 vs both-turns routing / output filename; the
`detect-citations` CLI wiring (would have caught defect A); the judge-refusal→skip path
(D); `rejudge`'s prompt-identity with the base pass (C); or `build_report`/`cites`. Existing
suites (`test_units`, `test_seam`, `test_providers`) are strong on the tested surface.

## Confirmed strengths
- **Strict judge parsing** (`judge.parse_judgment`, `judge.py:27-48`): rejects non-int or
  out-of-range bands, unknown techniques, empty rationale; tolerates trailing prose via
  `raw_decode`. Well covered (`test_units.py:42-74`). Robust to judge output drift.
- **Band scaling** `SCORE_SCALE=0.5` maps native −2..+2 → −1..+1 exactly as the paper states
  (`score.py:90-98`), tested (`test_units.py:113-116`).
- **Canonical report reproduces the paper's citation method** — turn-1 LLM detector, split by
  `islamic` class into Table 2's three columns (`html_report.py:68-89, 259-281`).
- **Idempotent, resumable pipeline**: identity keys + done-sets across collect / judge /
  batch / citation make re-runs safe and non-duplicating (`collect.py:253-256`,
  `judge.py:112-125`, `batching.py:43-66`, `citation.py:54-62`).
- **Non-destructive, count-preserving v2 overlay** (`score.load_judgments`,
  `test_units.py:129-141`).
- **Clean provider seam**: uniform `(text, usage)` normalization incl. Anthropic cache
  fields and Gemini thoughts-token accounting, well tested (`test_providers.py`);
  cache-breakpoint layout asserted exactly (`test_seam.py:47-64, 97-107`).
