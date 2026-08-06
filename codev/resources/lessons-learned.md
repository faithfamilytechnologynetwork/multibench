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
- **Porch force-advances a phase at its review safety ceiling (iter 3)** even if a reviewer's last
  verdict was REQUEST_CHANGES. Address the points and commit before the ceiling; note in the review
  that the phase force-advanced so the final PR CMAP re-checks the full diff.

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
- **The mock boundary is exactly where live-only bugs hide — add real-client contract checks +
  actually run a live smoke.** On Spec 8, mocking the provider seam let a Gemini schema
  incompatibility (numeric enum + `additionalProperties`) 400 on *every* live call while 100+
  mocked tests and a 3-way review passed; only a live run caught it. Defenses that belong in the
  *default* suite: build the provider's real request/schema object from your payload and assert it
  constructs (e.g. `pydantic.TypeAdapter(anthropic...MessageCreateParams)`, `google.genai
  types.Schema(**sanitized)`), and prove it *bites* on a bad payload. Then run the opt-in `--live`
  smoke for real before calling it done — and when a new live-gated test is added, it isn't
  "verified" until it has actually been observed green (a prior live pass doesn't cover it).

## Porting fidelity

- **A "port, don't redesign" carries NON-functional behavior as requirements, not extras.** On
  Spec 8 (a JaleesBench port), v1 was functionally complete + CMAP-approved but silently dropped
  the reference's throughput/cost machinery — parallel collection/judging (the `concurrency` field
  was defined but *never read* — dead), batch judging at 0.5×, and subject-side prompt caching —
  which cost real money on the first live run. When porting: enumerate the reference's
  concurrency/batch/caching/cost machinery up front and treat each as a MUST; a config field you
  add is a promise — wire it end-to-end or don't ship it.
- **Derive the port from the reference's CODE, not its docs/docstrings.** JaleesBench's
  `batching.py` line-4 docstring said it batched Gemini; the code (lines 120-127) explicitly does
  NOT (Vertex has no developer file-batch) and leaves Gemini to the live fallback. Reading the code
  gave the faithful contract; the docstring would have misled.
- **When a consumer must match an upstream aggregator, make the parity test a real cross-check.**
  Spec 26's `analysis` reproduces judging's `report.json` to ≤1e−9; its fixtures are real run
  slices whose `report.json` is **regenerated by the actual judging aggregator** (then trimmed), so
  the check compares two independent implementations, not a value against itself. It caught nothing
  because it *couldn't* be gamed — that's the point. Reuse the upstream's exact reducer (cell =
  mean of present judges; unweighted mean of cells) rather than re-deriving pooling, or the numbers
  drift.
- **Re-express a ported statistic so the reference's machinery ports verbatim.** JaleesBench's
  cluster bootstrap works on per-probe `(sum, count)` arrays. The MultiBench cell-mean aggregate is
  itself `sum(cell values)/count(cells)`, so the same `(sum, count)` point/CI code ports unchanged —
  just built over *cells grouped by scenario* instead of raw judgments (the asymmetric judge panel
  would double-weight two-judge cells otherwise). Keep the load-bearing fidelity detail: **one
  shared resample-draw list reused for point *and* difference** so paired diffs get correct CIs.
  Guard the small-N edge the source never hit (a resample that selects only zero-count clusters →
  divide-by-zero) by skipping that draw, not by dividing by zero.
- **Introduce a heavy optional dependency import-isolated, and prove it with a test.** `analysis`
  adds matplotlib for `--figures` only: imported *inside* the CLI branch, never at module top, so
  the default HTML path stays light. A subprocess test asserts `import analysis.cli` leaves
  `matplotlib` out of `sys.modules` — an in-process `sys.modules` check is unreliable because a
  sibling test module importing matplotlib pollutes the shared interpreter.
- **A JS-free static-SVG report is injection-safe by construction.** Rendering every chart as
  server-computed inline SVG (native `<title>` tooltips, no `<script>`) means untrusted
  model-produced strings can never reach a script context; route all of them through one `esc()`
  chokepoint and the whole surface is sealed.

## Verification discipline

- **"It compiled" / "tests pass" is not "it works."** Verify the real user path before calling
  something done.
- **Test-first against fixtures, then the real artifact as the acceptance test.** Building the
  format against fixtures and then porting the real 140-scenario tradition as the final gate proved
  the format expresses a real tradition with no gaps.
- **Builder worktrees share the host port namespace.** A real-server test (`serve -s dist`) that
  killed only the pnpm wrapper left a `serve` grandchild squatting on a fixed port for *days* after
  its worktree was gone — new serves silently fell back to ephemeral ports and the smoke test timed
  out with a misleading (node-version/PORT) cause. A spawned-server test must spawn `detached` and
  reap the process **group** (`process.kill(-pid, …)`) in `finally`, and pre-flight that the port is
  free with a diagnostic that names the leaked-serve cause.
