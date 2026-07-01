# Lessons Learned

Durable, cross-cutting engineering wisdom captured across the project's work. This is the cold
reference archive; the always-on distillation lives in
[`lessons-critical.md`](lessons-critical.md), whose "Map of lessons-learned.md" indexes the
sections below. Add during the review phase of any work that surfaces a generally-applicable
pattern, gotcha, or constraint.

## Toolchain & protocol environment (Python + porch)

- **npm-default porch checks block a Python repo.** Porch's implement/review checks default to
  `npm run build` / `npm test` and hard-block `porch done`. The `.codev/config.json` `porch.checks`
  override (skip `build`; tests = `uv run pytest`, `cwd: apps/tradition_validator`) is in place —
  keep it. Don't edit `status.yaml` to bypass a check.
- **Gemini's per-phase impl/code consult can't see the worktree here** — its sandbox is empty, so
  it returns no verdict and parses as REQUEST_CHANGES, forcing every phase to its iteration
  ceiling. Per-phase consult is `["codex","claude"]`; do the full 3-way only where the diff is fed
  inline (the PR integration CMAP).
- **Porch only re-extracts plan phases at the plan→implement transition.** Adding a phase
  mid-implement needs `porch rollback <id> plan` + plan re-approval.
- A consult run occasionally fails to write its output — a tooling hiccup, not a real failure;
  re-run that single model (porch's "run remaining consultations" handles it).

## Data-format design

- **Derive a format from the real reference data, not its docs.** The load-bearing details (e.g.
  the judge anchoring to the *embedded* proof text, not a corpus lookup — the "seam") only show up
  in the real data, and that insight shaped the whole tradition format.
- **Closed + strict schemas pay for themselves.** Pydantic closed schemas (unknown key = error)
  with no string coercion give precise, located errors almost for free and catch typos a permissive
  parser would silently swallow.

## Testing LLM pipelines

- **Put the provider call behind an injectable seam.** A multi-stage LLM pipeline (collect →
  judge → report) is fully testable with *zero* live API calls if each stage takes an optional
  `subject_fn` / `judge_fn` (default = the real provider, tests pass a fake returning canned
  `(text, usage, attempts)` / `(verdict, usage)`). The whole end-to-end path — grid, resume,
  re-judge, coverage, cost, non-zero-exit-on-failure — then runs deterministically in CI.
- **Gate costly/credentialed tests behind an opt-in flag, don't just skip them.** A pytest
  `--live` option (`pytest_addoption` + a `pytest_collection_modifyitems` hook that skips
  `@mark.live` unless `--live` is passed) keeps real-API tests out of the default suite while
  keeping them runnable and discoverable. Add `skipif(no creds)` so they degrade cleanly.
- **Verify a judge anchors to its *supplied* guidance, not its own prior, with a flip test.**
  Score the same fixed transcript twice, changing only the guidance so the two rewards are
  opposite; assert the verdict moves with the guidance. This is the real test that "the seam is
  the ground truth" — a judge that ignored guidance would score both identically.

## Verification discipline

- **"It compiled" / "tests pass" is not "it works."** Verify the real user path before calling
  something done.
- **Test-first against fixtures, then the real artifact as the acceptance test.** Building the
  format against fixtures and then porting the real 140-scenario tradition as the final gate proved
  the format expresses a real tradition with no gaps.
