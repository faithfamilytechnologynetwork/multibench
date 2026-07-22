# air-38 — CI: validate-all --strict gate (issue #38)

## Implement
- Added `.github/workflows/validate.yml`: single job, triggers on push→main and all PRs.
- Steps: checkout → `astral-sh/setup-uv@v5` (enable-cache) → run validator from repo root.
- **Command note:** the issue's snippet omits the required `TRADITIONS_DIR` positional.
  `validate-all` errors with "Missing argument 'TRADITIONS_DIR'" without it. Used the
  working form `validate-all traditions --strict`.
- Verified locally: all 7 traditions PASS (exit 0). Broke a scratch copy of a
  tradition.yaml → exit 1 (gate fails as intended). Real traditions untouched.
- Validator-only per issue scope; app test suites stay with `.codev/checks/test.sh`.
