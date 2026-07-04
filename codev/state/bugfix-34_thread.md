# bugfix-34 thread — judging cost registry: add claude-sonnet-5 pricing

## Investigate (2026-07-04)

- Issue #34: 20260704 run (sonnet-4.6 vs sonnet-5) shows `usd: null` for `claude-sonnet-5` cost rows.
- Reproduced against the real run data (`tmp/judging-runs/20260704/sunni-islam/report.json` in the main checkout): collection row for `claude-sonnet-5` has `usd: None`, `fully_priced: False`; `_usage_cost("claude-sonnet-5", ...)` returns `None`.
- Root cause: `workflows/judging/judging/report.py` `PRICES` dict (line 28) predates the model — has opus-4-8, sonnet-4-6, haiku-4-5, gemini-3.5-flash only. `_usage_cost` returns `None` for unlisted models by design.
- Fix plan: add `"claude-sonnet-5": (3.00, 15.00)` (standard rate per issue, verified 2026-07-04; durable vs intro rate), bump `PRICES_DATED` to `"2026-07"`. Regression test in `workflows/judging/tests/test_report.py` alongside existing cost tests.
- Scope: trivially within BUGFIX (< 10 LOC + test).

## Fix (2026-07-04)

- Verified pricing against the claude-api skill reference: Claude Sonnet 5 is $3.00/$15.00 per MTok standard (intro $2/$10 through 2026-08-31). Registered the durable standard rate per the issue's recommendation.
- Added `"claude-sonnet-5": (3.00, 15.00)` to `PRICES`; bumped `PRICES_DATED` to 2026-07.
- Regression test `test_cost_sonnet_5_priced` mirrors the 20260704 run shape (sonnet-5 collection row with cache + batch usage) and asserts the exact usd incl. cache-write 2x / cache-read 0.1x / batch 0.5x multipliers. Confirmed it fails without the fix.
- Full judging suite: 151 passed, 4 skipped. Re-ran `build_report` over the real `tmp/judging-runs/20260704/sunni-islam` data: sonnet-5 collection row now $4.09 (was null), `fully_priced: True`, total $11.84.
