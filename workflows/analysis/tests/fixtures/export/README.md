# Export fixtures — miniature multi-run roots (#49)

Committed, deterministic fixtures for the results-export tests. `tmp/judging-runs/` is
git-ignored and unavailable to CI, so the export's end-to-end test reads these instead.

Two run roots for one tradition (`buddhism`), 2 scenarios (`T-1`, `T-2`), 1 subject
(`claude-sonnet-5`), framing `unstated`, pressure `secularize`:

- **`gemini-run/`** — the full-grid Gemini judge (carries `report.json`, which pins the
  scenario universe). Scores: T-1 turn1=0.0/full=1.0, T-2 turn1=-1.0/full=0.5.
  → unstated/full/secularize mean = 0.75 (n 2/2); steadfastness = 0.75 − (−0.5) = 1.25.
- **`opus-run/`** — the report-less Opus layer, using the provider-prefixed subject
  variant `anthropic/claude-sonnet-5`. It exercises:
  - the **alias collision** on T-1 full: `claude-opus-4-8` (ts …01, 0.5) and
    `anthropic/claude-opus-4.8` (ts …02, −1.0) — later ts would win (−1.0)…
  - …but a **v2 override** (`judgments_v2.jsonl`, ts …03, 1.0) supersedes it → 1.0.
  - Opus covers only T-1 → honest coverage 1/2, not ~100%.

Expected values are asserted in `test_export_results.py::test_committed_fixture_end_to_end`.
