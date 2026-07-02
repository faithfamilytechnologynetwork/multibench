# Plan: Spec 8 — `workflows/judging` — JaleesBench fidelity remediation

## Metadata
- **ID**: plan-2026-07-02-workflows-judging-fidelity
- **Status**: draft (supersedes the delivered v1 plan; see Appendix)
- **Specification**: [codev/specs/8-workflows-judging-the-judging-.md](../specs/8-workflows-judging-the-judging-.md) (amended 2026-07-02, §4.6/§4.7, M13–M21)
- **Reference (port source)**: JaleesBench = `/Users/mwk/Development/fftn/taqwabench/jaleesbench/jaleesbench/` (`collect.py`, `judge.py`, `batching.py`, `providers.py`, `prompts.py`, `score.py`)
- **Created**: 2026-07-02

## Executive Summary

v1 of `workflows/judging/` shipped functionally complete and CMAP-approved (PR #20) plus a live
Gemini-schema bugfix (PR #24) — both **merged**. A live 5-scenarios-per-tradition run then showed
v1 had **dropped JaleesBench's throughput/cost fidelity**, a real regression for a *port*:
collection and judging ran **serially** (`config.concurrency` was a **dead field**), there was
**no batch path**, and subject-side prompt caching was missing; the deliverables rubric was
compressed and several judge diagnostics dropped. The spec was amended (§4.6/§4.7) to promote the
dropped non-functional behavior to REQUIREMENTS (**M13–M21**).

This plan restores full fidelity in **three phases**, exactly the architect's phasing
(**parallelism → batching → Tier-2 judge-quality + live verification**), each independently
testable with the provider boundary mocked **plus** real-client contract checks (the mock boundary
is what hid the Gemini 400 + these cost regressions, so it is no longer trusted alone). The two
**deliberate deviations** (judge thinking ON; Gemini `gemini-3.5-flash`) and the intentional
reframes (numeric scores; guide+judge-guidance anchor; Claude-only subjects; citation/mapping/
HTML/web out of scope; Arabic deferred) stand — documented, not "fixed".

**Concurrency approach:** a bounded `ThreadPoolExecutor` over the existing **sync** provider
seams (bounded by `config.concurrency`, `threading.Lock` around each JSONL append) — this wires
concurrency without rewriting the provider layer to async (lower risk; JaleesBench's
`asyncio.Semaphore+gather` is an equivalent shape and stays an acceptable alternative).

## Success Metrics

Amended-spec criteria are the acceptance bar; per-phase **Acceptance** maps each. Rollup:

- [ ] Fidelity MUSTs **M13–M21** met (parallel collect+judge, batch judging + 0.5× cost, subject
      caching, full rubric, Gemini thinking-token/diagnostic/schema, raw text, v2 re-judge
      verification, live verification).
- [ ] New test scenarios **T18–T27** implemented; the default suite includes **real-client/schema
      construction** checks; the opt-in **`--live` smoke (T27)** is actually run before done.
- [ ] No regression of the delivered M1–M12 / N1–N5 behavior (self-judge skip, blinding, coverage,
      fail-fast, idempotent resume all preserved); no coverage reduction.
- [ ] Single remediation PR (`Refs #8`); phase commits on `builder/spir-8`; architect runs the
      integration CMAP + pr gate; merge with a merge commit on approval.

## Phases (Machine Readable)

```json
{
  "phases": [
    {"id": "phase_r1", "title": "Parallel collection + judging + subject-side caching"},
    {"id": "phase_r2", "title": "Batch judging + batch & thinking-token cost accounting"},
    {"id": "phase_r3", "title": "Judge-quality fidelity + live verification + docs"}
  ]
}
```

## Phase Breakdown

### Phase r1: Parallel collection + judging + subject-side caching
**Dependencies**: none (builds on the merged v1 on `main`)
**Restores**: M13, M15, M16 · **Tests**: T18, T19 (+ M16 request-construction; live cache-read in r3)

#### Objectives
- Wire the **dead `config.concurrency`** into both `collect` and `judge` (base **and** re-judge
  passes) as a bounded `ThreadPoolExecutor` over per-cell provider calls; keep runs deterministic,
  idempotent, blinded, and fail-fast exactly as today.
- Restore JaleesBench **cell-major interleave** in collection.
- Restore **subject-side Anthropic prompt caching** (framing block 1h ephemeral + turn-1 default
  TTL) so turn-2 does not re-pay.

#### Files (modify)
- `collect.py` — replace the serial `for` over `todo` with a `ThreadPoolExecutor(max_workers=
  config.concurrency)`; reorder the grid to **cell-major interleave** (`(scenario_id, pressure,
  framing)` outer, subject inner — JaleesBench `collect.py:269`); `threading.Lock` around the
  `sittings.jsonl` append; preserve resume/`--limit`/`--scenarios`/failed-count/exit-code.
- `judge.py` — parallelize `_judge_pass` (base) and the re-judge pass under `config.concurrency`
  (JaleesBench `Semaphore(16)+gather`); keep the lock-guarded append, self-judge skip recording,
  and idempotent keying.
- `providers.py` — `subject_complete`/`_fold`: add `cache_control` on the framing block (`ttl:1h`
  ephemeral) + the turn-1 exchange (default TTL), mirroring the judge path (JaleesBench
  `collect.py:176-186`). No change to the judge caching (already present).

#### Acceptance
- [ ] `config.concurrency>1` runs collect/judge concurrently: a test observes **max in-flight >1
      and ≤ concurrency** (e.g. an injected fake that records overlap); `concurrency=1` is serial
      (T18, T19; M13, M15).
- [ ] Output with concurrency is **set-equivalent** to serial — the **same set of records**,
      regardless of JSONL **line order** (concurrency makes append order non-deterministic; do NOT
      enforce byte-identical output). Resume is still idempotent, and blinding +
      non-zero-exit-on-failure are unchanged.
- [ ] **Real-client construction (M21):** a **default-suite** test builds the Anthropic **subject**
      request payload (with the framing 1h + turn-1 `cache_control` blocks) via the real client's
      params and asserts it constructs without error — not just that a dict has the right keys
      (this is the anti-mock-boundary check for the subject path) (M16, M21).

#### Test Plan
- **Unit/integration (mocked):** concurrency honored + overlap bound; **set-equivalent** (not
  byte-identical) serial-vs-parallel output; cell-major order; no dropped/duplicated JSONL lines
  under load. **Real-client construction (default suite):** the Anthropic subject-request payload
  (framing/turn-1 `cache_control`) constructs against the real client. No network calls.

#### Risks
- **Thread-safety of JSONL append / shared dicts.** → Single `threading.Lock` around every append;
  per-cell work is otherwise independent. Test asserts no dropped/duplicated lines under load.

---

### Phase r2: Batch judging + batch & thinking-token cost accounting
**Dependencies**: r1 · **Restores**: M14, M18 (cost) · **Tests**: T20 (+ cost)

#### Objectives
- Port JaleesBench **batch judging** at ~50% price with a durable manifest and a live fallback,
  and make the cost model **batch-aware** and **Gemini-thinking-aware**.

#### Files
- **Create** `batching.py` — port JaleesBench `batching.py`: submit **Anthropic Message Batches**
  for the pending cells; a `batch_state.json` manifest keyed like `judgments` for idempotency; on
  collect, write verdicts (parsed/validated exactly like the live path) and mark the manifest;
  anything a batch leaves pending falls back to the **live `judge`**. **Gemini is NOT batched** —
  Vertex has no developer file-batch (matches JaleesBench `batching.py:120-127`; its line-4
  docstring is stale — derive from code, not docs), so Gemini judge cells go to the live fallback.
- **Modify** `cli.py` — add `batch-judge submit` and `batch-judge collect` (share config/`--config`).
- **Modify** `providers.py` — `_gemini_usage` counts `thoughts_token_count` (JaleesBench
  `providers.py:120-122`); add the batch submit/poll helpers used by `batching.py`.
- **Modify** `report.py` — cost model prices batched tokens (`b_in/b_out/b_cache_write/b_cache_read`)
  at **0.5×** (JaleesBench `score.py:50-76`); include Gemini thinking tokens in usage/cost.

#### Acceptance
- [ ] `batch-judge submit` then `collect` produces the same validated verdicts as live, priced at
      **0.5×**; `batch_state.json` makes re-collect idempotent; a cell the batch leaves pending
      falls back to live `judge` (T20; M14).
- [ ] The feature is operable **from the actual CLI** (`batch-judge submit|collect`), not only via
      lower-level helpers: CLI-level tests exercise the command wiring and the `batch_state.json`
      **manifest lifecycle** (submit writes it; collect consumes + updates it; re-collect is a
      no-op). Extends the existing `tests/test_cli_smoke.py` coverage.
- [ ] **Real-client construction (M21):** a **default-suite** test builds the **Anthropic** batch
      request (incl the `output_config` schema field) via the real SDK batch-request type and
      asserts it constructs without error and bites on a bad request (anti-mock check; Gemini is
      not batched, so there is no Gemini batch payload to validate here).
- [ ] `report` cost is batch-aware (0.5× batch rows) and counts Gemini `thoughts_token_count`
      (M18-cost); unpriced-model handling still graceful.

#### Test Plan
- **Unit/integration (mocked batch client):** submit→collect→verdicts + 0.5× cost; manifest
  idempotency; pending→live fallback; gemini-thinking-token cost; batch-aware report totals.
- **CLI-level:** `batch-judge submit|collect` command wiring + manifest lifecycle.
- **Real-client construction (default suite):** the batch submit payload constructs against the
  real client for each provider. No network calls.

#### Risks
- **Batch API shape drift (Anthropic/Gemini).** → Encapsulate submit/poll/collect behind
  `batching.py` helpers with a mocked-client contract test; the live batch path is exercised by
  the r3 `--live` smoke only if cheap, else documented.

---

### Phase r3: Judge-quality fidelity + live verification + docs
**Dependencies**: r1, r2 · **Restores**: M17, M18 (diagnostic), M19, M20, M21 · **Tests**: T21–T27

#### Objectives
- Restore the judge-quality details v1 dropped, and add the **anti-mock-boundary** verification the
  amended spec now requires (real-client/schema construction in the default suite + an opt-in
  `--live` smoke actually run before done). Update docs.

#### Files
- `rubric.py` — restore the **full deliverables boundary rule** (artifact-sets-−1.0-ceiling +
  **exit-ramp-eligible** clause + worse-of-both) and the **five worked boundary examples** from
  JaleesBench `prompts.py:112-137`, de-Islamicized (M17).
- `providers.py` — **(a) `raw`-passthrough seam change (M19).** Today `judge_complete` /
  `_anthropic_judge` / `_gemini_judge` do `return json.loads(text), usage` — the raw response
  **text is discarded**. Retaining `raw` therefore requires a **provider return-shape change**
  (return the raw text alongside the parsed dict, e.g. `(verdict_dict, raw_text, usage)` or a
  `raw` key), threaded through `judge_fn`/`_judge_pass`/`_record` — **not** a `judge.py`-only edit.
  Update `JudgeFn`'s type + every call site + `parse_verdict`/`_record` + the affected tests.
  **(b)** Gemini judge path: explicit `finish_reason`/empty-response **diagnostic** (clear located
  error, not a bare `json.loads(resp.text)`) (M18-diagnostic). **(c)** Schema sanitization already
  landed in PR #24 — keep it and its **real-client construction** test (M21).
- `judge.py` — record the passed-through **`raw`** text on every judgment (M19, depends on the
  providers seam change above); **verify** JaleesBench `rejudge_disagreements`: if it truly uses a
  stricter v2 prompt, port it (add to `prompts.py`); else record the finding as a no-op (M20).
- **Tests** — real-client/schema construction (T23) in the **default** suite; `raw` present (T25);
  Gemini thinking-token + blocked diagnostic (T24); rubric worked examples present (T22); opt-in
  `--live` subject-cache `cache_read>0` (T21) + a **tiny `--live` `run` smoke** (T27).
- **Docs** — `workflows/judging/README.md`: parallelism (`concurrency`), `batch-judge`, subject
  caching, `--scenarios`, the two deviations + reframes; update the arch/lessons cold docs in Review.

#### Acceptance
- [ ] Rubric text carries the full deliverables rule + five worked examples (T22; M17).
- [ ] Every judgment carries `raw` (T25; M19); Gemini blocked/empty → clear located error, thinking
      tokens counted (T24; M18); the sanitized schema **constructs as `google.genai.types.Schema`**
      in a default-suite test (T23; M21).
- [ ] v2 re-judge prompt: ported if stricter, else documented no-op (M20).
- [ ] `--live` tiny `run` smoke completes end-to-end and is **run before done**; subject-cache
      `cache_read>0` observed (T27, T21; M21, M16).

#### Test Plan
- **Default suite:** rubric examples; `raw`; gemini diagnostic + thinking tokens; **real-client
  schema construction**. **Opt-in `--live`:** subject-cache hit + tiny end-to-end smoke.

#### Risks
- **`--live` cost/flakiness.** → Keep the smoke to 1–2 cells, `--live`-gated, skip cleanly without
  creds; it is the required real-path check, run once before done (M21).

## Dependency Map
```
r1 (parallel + subject caching) ──→ r2 (batch + cost) ──→ r3 (judge-quality + live verify + docs)
```
Sequential: r2's cost model reports r1's usage; r3's live smoke exercises r1+r2 end-to-end.

## Risk Analysis

| Risk | Prob | Impact | Mitigation |
|------|---|---|---|
| Concurrency introduces races (dropped/dup JSONL, shared-dict corruption) | M | H | One lock around appends; independent per-cell work; serial==parallel output test (r1). |
| Batch API shape drift (Anthropic/Gemini) | M | M | Encapsulate in `batching.py`; mocked-client contract test; manifest idempotency (r2). |
| Mock boundary hides live failures **again** | M | H | M21: real-client/schema construction in the default suite + a `--live` smoke actually run before done (r3). |
| Regressing delivered v1 behavior (blinding, skip, coverage, exit codes) | L | H | Keep the existing tests green; parallel paths reuse the same per-cell logic; add serial==parallel equivalence test. |
| JaleesBench reference unavailable | L | M | Source confirmed at the reference path; if absent, fetch from GitHub (as in the original Specify phase). |

## Validation Checkpoints
1. **After r1**: concurrency honored (overlap bound), serial==parallel output, subject-cache
   `cache_control` on requests; all prior tests still green.
2. **After r2**: batch submit→collect→0.5× cost + manifest idempotency + live fallback; report
   batch-aware + gemini thinking tokens.
3. **After r3**: full rubric + worked examples; `raw`; gemini diagnostic; real-client schema test;
   **`--live` smoke run**; READMEs updated. Then PR.

## Documentation Updates Required
- [ ] `workflows/judging/README.md` — parallelism/`concurrency`, `batch-judge`, subject caching,
      `--scenarios`, deviations + reframes.
- [ ] Review-phase: arch/lessons cold-doc updates (parallel+batch+caching fidelity; the mock-boundary
      lesson).

## Notes
- **Consultation:** per-phase consult is **codex + claude** (Gemini per-phase sandbox can't see the
  worktree); the architect runs the full 3-way integration CMAP at the PR gate.
- **PR strategy:** one remediation PR (`Refs #8`, not `Closes` — #8 already closed); phase commits
  on `builder/spir-8`; do not open per-phase PRs; do not self-approve/merge.
- **Deviations (do not "fix"):** judge thinking **ON** (cost counted via M18); Gemini judge
  **`gemini-3.5-flash`**. **Reframes stand:** numeric scores; guide+judge-guidance anchor;
  Claude-only subjects; citation/mapping/HTML/web out of scope; Arabic deferred (§4.7).

## Appendix — delivered v1 (superseded phases)
The original 6 phases (scaffold → loaders/rubric/prompts → providers/judge → collector → report →
run/docs) are **delivered and merged** (PR #20 feature; PR #24 Gemini-schema live bugfix). This
plan is the fidelity remediation on top of that merged baseline; it does not re-do v1.

## Change Log
| Date | Change | Reason |
|------|--------|--------|
| 2026-06-30 | Initial 6-phase plan (delivered; PRs #20/#24) | Spec 8 approved |
| 2026-07-02 | **Fidelity remediation plan** (r1 parallel+caching → r2 batch+cost → r3 judge-quality+live-verify) | Live audit found dropped JaleesBench fidelity; spec amended M13–M21 |
| 2026-07-02 | Plan-iter-2 consult (Codex REQUEST_CHANGES, Claude APPROVE): (1) M21 real-client construction checks distributed across phases — Anthropic subject payload in r1, batch submit payload in r2, Gemini schema in r3 (not Gemini-only); (2) M19 `raw` retention made an explicit **provider return-shape seam change** (text is discarded at `json.loads` today), threaded through `JudgeFn`/`_judge_pass`/`_record` + tests; (3) added explicit `batch-judge submit\|collect` CLI-level + manifest-lifecycle tests in r2; (4) r1 serial-vs-parallel acceptance clarified to **set-equivalence** (line order non-deterministic under concurrency) | Address review |
