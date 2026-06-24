# air-5 — tradition_validator medium polish (issue #5)

Protocol: AIR (strict). Implement → PR. No spec/plan/review files; review goes in PR body.

## Task
Five non-blocking medium items from the PR #2 3-way integration review:
1. ScenariosIndex default handling (was "ProbesIndex" pre-rename)
2. Typer enum for `--format`
3. non-UTF-8 input test
4. `port_jaleesbench.py` unit tests
5. document the `patience` cross-axis term-reuse pattern (appears in both `pillars` and `hearts`)

Note from issue comment: probe→scenario rename (#6/#9) already merged; build on current main vocab
(scenarios/, scenario.yaml, turn1.md, scenario_id_pattern). Also: a 2nd tradition
(eastern-christianity) already landed — the doc item still stands regardless.

## Decisions
- **Item 1**: `ScenariosIndex.scenarios` currently defaults to `[]` via `default_factory=list`. A
  missing `scenarios` key then silently → `[]` → misleading "every folder is drift" errors. Fix:
  make the field **required** (drop the default) so a missing key yields a clear located pydantic
  "Field required" error on `scenarios`. Explicit `scenarios: []` is still allowed (present, empty),
  still caught by the existing "No scenario folders" / drift checks.
- **Item 2**: Replace `fmt: str` + manual `_check_format` with a `str, Enum` `OutputFormat`. Typer
  validates natively (bad value → exit 2, matching existing test) and prints choices in --help.
- **Item 3**: New `test_loaders.py` — write invalid UTF-8 bytes into a prose file and a YAML file;
  assert "not valid UTF-8" located finding (unit on loader + end-to-end via validate_tradition).
- **Item 4**: New `test_port_jaleesbench.py` — unit-test `extract_constants`/`_resolve` (literals,
  dict/list/set, str concat, Name ref, skip non-constant, unsupported→ValueError) + an end-to-end
  `port()` over a minimal staged source that then `validate_tradition(...).ok(strict=True)`.
- **Item 5**: Document cross-axis term reuse in `traditions/README.md` Taxonomies section (axes are
  independent namespaces; `patience` legitimately in both `pillars`/scenario and `hearts`/response).
  Lock it with a test: a scenario tagging the same term under two axes validates clean.

## Status
- Baseline suite green (74 passed). Starting implementation.
- All 5 items implemented. Suite green: **91 passed** (74 baseline + 17 new). ruff clean.
- Production changes tiny: `models.py` (scenarios required) + `cli.py` (OutputFormat enum).
  Tests: +test_index (item 1), +test_loaders.py (item 3), +test_port_jaleesbench.py (item 4),
  +test_scenarios (item 5). Doc: `traditions/README.md` Taxonomies (item 5).
- Verified end-to-end: `--help` shows `[text|json]`, bad `--format` → exit 2, both real
  traditions still `validate-all` clean. Next: porch check/done → PR (pr gate, human approves).
