# air-28 thread — Issue #28: drop Islam-derived techniques + restore full dual judging

## 2026-07-03 — start (implement phase, AIR strict)

Surveyed all touch points. Two independent reversals of Spec-8-port reframes:

1. **Techniques out of the universal seam**: `TECHNIQUE_IDS` + `techniques_used`
   appear in judging (`rubric.py`, `prompts.py`, `judge.py`, `report.py`) and
   analysis (`loaders.py` required-keys, `aggregate.py` recompute + parity,
   `html_report.py` section 6). Analysis fixtures (buddhism/taoism) are
   old-format (techniques + skipped.jsonl) — keeping them as-is doubles as the
   "old runs still load" regression test.
2. **Self-judge skip out**: `judge.py should_skip` + skips_path/skipped.jsonl
   audit trail, `batching.py` pending enumeration, `report.py` expected-cells
   subtraction + `skipped_self` count. Analysis keeps *reading* skipped.jsonl
   (old runs have it) but nothing new writes it.

Decisions:
- `parse_verdict` ignores an extra `techniques_used` key rather than rejecting
  it (schema no longer emits it; old raw blobs are audit-only).
- `skipped_self` disappears from summaries/counts (issue allows "disappear or 0").
- html_report "Judge asymmetry" caveat becomes a self-judgment-bias caveat per
  the issue's note.

## 2026-07-03 — implement done, verified

- 19 files, +157/−296 (net −139 LOC).
- Suites: judging 150 passed / 4 skipped (live opt-ins), analysis 81 passed.
- End-to-end acceptance checks (beyond unit tests):
  - `analysis report` over ALL FIVE real pre-#28 run dirs in
    `tmp/judging-runs/20260702` (main checkout) → renders fine; parity self-check
    passes with the fixture/old `techniques` block read through, not compared.
  - Fresh mocked new-format run with subject == judge model: 6 sittings × 2
    judges × 2 scopes = 24/24 cells covered, zero self-skips, no skipped.jsonl,
    no `techniques` in report.json, no `skipped_self` in counts; `analysis
    report` renders it with the new self-judgment-bias caveat and no Technique
    profile section.
- Kept: analysis loader still *reads* skipped.jsonl (old runs carry it);
  `judgments_v2` overlay and re-judge logic untouched except that re-judge
  targets now include self-judge cells like everything else.

Next: porch check → done → PR with review in body.

## 2026-07-03 — PR gate

- PR #29 created (review in body, per AIR). porch: pr gate registered, waiting
  for human approval. Architect notified via afx send.

## 2026-07-03 — CMAP doc round

- CMAP on PR #29: code unanimously sound; doc drift flagged. Fixed:
  workflows/judging/README.md updated to post-#28 contract (verdict fields,
  judge command outputs, config self-judge note, judgments table); fixtures
  README notes the pre-#28 format is intentional regression coverage; spec 8
  (§4.4, §5.4) and plan 8 got addendum blocks pointing to #28 — historical text
  untouched per architect ruling.
