# task-hbmD — ProtestantBench benchmark round (issue #89)

Charter: run the full benchmark round on `traditions/protestantism/` (100 scenarios,
PRO-001..PRO-100, landed in #82, validator-clean). All models, dual-judged. Waleed-directed
2026-08-13.

## Derived config (from the REAL 20260803 record, not docs)

Read from `results/20260803/manifest.json`, `results-raw/20260803/manifest.json`,
`workflows/judging/configs/openrouter-funded-run.yaml`, and the actual record raw run dirs on
the MAIN checkout (`tmp/judging-runs/20260803-*`).

- **Subject roster (5):** `openai/gpt-5.6-terra`, `anthropic/claude-sonnet-5`,
  `google/gemini-3.6-flash`, `qwen/qwen3-235b-a22b-2507`, `thinkingmachines/inkling` — all via
  OpenRouter (`provider: openai` + base_url + `OPENROUTER_API_KEY`). Canonical ids in the
  manifest normalize the slugs back (export `_SUBJECT_VARIANTS`).
- **Judges (dual):**
  - **Gemini ranking judge** — `google/gemini-3.6-flash` via OpenRouter, `safety_off: false`
    (record decision 2026-08-03: OpenRouter can't forward BLOCK_NONE; refusals surface as failed
    cells), thinking on. **Full grid** (all framings/pressures/subjects/scopes). Bears report.json.
  - **Opus validation judge** — `claude-opus-4-8` **direct via ANTHROPIC_API_KEY**
    (record `20260803-unstated-opus` used the direct `claude-opus-4-8` id), thinking on. Marked
    `full_grid: false` in the export (`JUDGE_UI`). Record coverage = **full unstated grid** +
    a **partial sample** of stated/guided (`20260803-framings-opus-sample`). Never re-ranks
    (leaderboard is Gemini-only; Opus is a badged validation layer).
- **Framings:** unstated / stated / guided. **Pressures:** all 6. **Scopes:** turn1, full.
- **Run params:** concurrency 8, retries 2 (config defaults; funded config didn't override).

Grid per framing = 100 scenarios × 5 subjects × 6 pressures = 3000 cells.
Collection grid = 3000 × 3 framings = 9000 sittings. Gemini judgments = 9000 × 2 scopes = 18000.

## Integration shape (open design point — proposal at smoke checkpoint)

20260803 is guarded by the paper-reconciliation test (paper stays a 7/519 snapshot) — NEVER
mutate it. Proposal: **new run-id `20260813-protestantism`** (protestantism-only score tier via
`analysis export` + raw tier via `export-raw`), own source fingerprint, additive/drop-in. The
copied-shard superset (8-tradition unified leaderboard) is the alternative — heavier fingerprint
story, more risk. Will present both to architect.

## ⚠️ Cost finding (record-derived, pre-smoke)

Record 20260803 per-tradition report.json cost blocks (Gemini-judging only, **NO Opus**):
stable **$4.67/scenario** across all 7 traditions (band $4.14–5.35; ~55% judging, ~45%
collection). Projected protestantism (100 scen) @ record rate ≈ **$467 Gemini-only, before
Opus validation** — already ~1.5–2× over the $250–300 prior estimate. Opus validation adds
materially on top (Opus ~3× Gemini per-token). **The prior $250–300 estimate looks too low by
~2×.** Binding number will be the SMOKE actuals (×50 projection, incl. Opus split by framing).
This is the alert Waleed asked for — will surface prominently at the smoke checkpoint.

## Progress log

- 2026-08-13: Oriented. Derived config from real record (above). Tradition verified
  validator-clean (100 scenarios, judge-guidance present). CLI surface confirmed
  (`run TRADITION --scenarios N --config --results-dir`). Keys present in taqwabench/.env
  (OPENROUTER + ANTHROPIC + GEMINI — will export ONLY OpenRouter + Anthropic per ground rules).

- 2026-08-13 SMOKE DONE (`tmp/judging-runs/89-smoke`, 2 scenarios, both judges full,
  end-to-end). Canonical report.json total **$30.79** (fully-priced). Health: 180/180 sittings
  collected (0 fail); 714 judgments, **7 Opus cells failed (~1%, JSON truncation/empty** —
  "Unterminated string"/"Expecting value"; Opus judge max_tokens default 4096 + thinking crowds
  the verdict → bump Opus `max_tokens` to ~8000 for the full run). Gemini cells: 0 fail.
  - Split: collection **$4.75** | Gemini judge **$5.62** | **Opus judge $20.43** (Opus = 66% of
    cost; 5/25 pricing + thinking output dominates).
  - **PROJECTIONS ×50 to 100 scenarios:** collection $238 + Gemini full grid $281 =
    **$519 IRREDUCIBLE FLOOR** (all-models + Gemini ranking, full battery). Opus on top:
    (A) unstated-only +$365 → **$883**; (B) unstated+25% s/g sample (record-like) +$529 →
    **$1048**; (C) full grid +$1021 → **$1540**. Batch-Opus (~50% off, Anthropic batches; Gemini
    not batchable): (A)+batch ≈ **$701**, (B)+batch ≈ **$785**.
  - Corroborated by record 20260803 ($4.67/scen Gemini-only → $467 for 100; floor $519 consistent).
  - **BUDGET ALERT: prior $250–300 estimate is low by ~2.3–3.5×. No config of the full battery
    lands near $300.** Sent projections + integration proposal to architect. **HOLDING — full run
    NOT started; awaiting explicit go + budget/Opus-coverage decision.**
  - Integration proposal: new run-id `20260813-protestantism` (protestantism-only score+raw
    tiers, own fingerprint, additive, 20260803 untouched). Alt: copied-shard 8-tradition superset
    (follow-up).

- 2026-08-13 **EXPLICIT GO (Waleed via architect):** Option **C** — Opus FULL GRID via **Anthropic
  Message Batches** (~$1030 projected). Config: full 100-scen battery, 5 subjects, Gemini
  full-grid ranking (LIVE) + Opus full-grid validation (BATCHED), Opus `max_tokens` 4096→8000.
  Integration CONFIRMED: new run-id `20260813-protestantism` (additive; 20260803 pristine; superset
  deferred). **HARD CEILING $1150** (usage-computed report.json). Tripwires: alert at $900 cum;
  PAUSE+report if cumulative trends >20% over smoke pace OR hits ceiling; reconcile exact actuals
  at collect-end AND judge-end (report both).
  - **Execution plan:** (1) `collect` full config → 9000 sittings [running, PID 83221,
    tmp/judging-runs/89-full]. (2) parallel: `judge` with gemini-only config (live Gemini) +
    `batch-judge submit` full config (Opus → Anthropic batches, server-side). (3) after BOTH
    Gemini-live done AND batches ended: `batch-judge collect --fallback` (writes Opus batch-priced
    verdicts; fallback mops up only stragglers — Gemini already judged/idempotent). (4) `report`
    full config → report.json cost. (5) `analysis export` + `export-raw` single root `89-full`
    → results/20260813-protestantism + results-raw/20260813-protestantism.
  - Safety verified: `batch-judge collect` live-fallback fires ONLY when `open_batches==0` (all
    Opus batches ended) — Opus never accidentally live-judged mid-batch.
  - SPA discovery: enumerates `results/<id>/manifest.json`; defaults to NEWEST by generated_at →
    protestantism-only run becomes default (20260803 via run selector / `?run=`). Will document
    this UX note in the tier README + flag at PR.
  - Configs: `workflows/judging/configs/protestantism-run.yaml` (full, Opus max_tokens 8000) +
    `protestantism-gemini.yaml` (gemini-only live-judge). Both tracked (committed with PR).

- 2026-08-14 COLLECT-END reconciled: **9000/9000 sittings, 0 failed; $226.02** (−4.9% vs smoke
  proj, 19.7% of ceiling). Reported to architect. Judging launched:
  - **Opus batch SUBMITTED**: 18000 cells → **2 Anthropic Message Batches** (batch_state.json in
    tmp/89-full; batch_id msgbatch_01HJchEJDm3eUad4ksRraiKv + one more). Processing server-side.
  - **Gemini live judge running** (PID 47597, gemini-only config) → judgments.jsonl. ~70 rows/min
    → ~3–4h for 18000 cells.
  - **ORDERING GUARD:** must NOT run `batch-judge collect` until the Gemini live judge FINISHES —
    collect writes opus verdicts to judgments.jsonl, same file the gemini judge is writing
    (concurrent-writer hazard). Batches complete server-side regardless (results retained 29d), so
    no time lost. Sequence: gemini-done → reconcile gemini → poll batches via `collect
    --no-fallback` until 0 open → final `collect --fallback` (opus batch-priced + straggler mop-up)
    → report → export.

- 2026-08-14 **KEY CORRECTION (Waleed via architect):** Opus must bill to `ANTHROPIC_JUDGE_API_KEY`
  (sk-ant-api03-uDu…TAAA), NOT plain `ANTHROPIC_API_KEY` (sk-ant-api03-F…xgAA). Investigated the
  already-submitted batches:
  - **Both batches ENDED (not cancellable).** FPL key **ran out of credit** — every error is
    `invalid_request_error: "Your credit balance is too low"`. batch1 (10000): 9680 errored / 320 ok;
    batch2 (8000): 16 errored / **7984 ok**. Total **8304 succeeded / 9696 errored**.
  - **FPL waste (billed, counts toward ceiling): $262.56** (8304 succeeded Opus cells, batch-priced;
    in=20.8M out=13.6M cache_r=41.5M). Retrieval of results needs NO credit (read-only) → harvestable.
  - **Ceiling decision surfaced to architect** (facts diverged from "cancel open batches"):
    - Path A (discard 8304, resubmit all 18000 on JUDGE): ≈$1338 total → **OVER $1150 ceiling**.
    - Path B (harvest 8304 valid FPL verdicts, resubmit only 9696 errored on JUDGE): ≈$1077 → under.
    Recommended **B** (valid Opus verdicts; only path honoring the ceiling; no NEW FPL billing).
    HOLDING resubmission for architect's A/B decision.
  - Any harvest/resubmit is GATED on the Gemini live judge finishing (concurrent judgments.jsonl
    writer). Gemini at ~22% (4029/18000), ETA ~3h. Gemini NOT disturbed per instruction.
  - Key-swap mechanism ready: Opus-batch wrapper will export ANTHROPIC_API_KEY:=value of
    ANTHROPIC_JUDGE_API_KEY (the `anthropic` provider branch ignores config `api_key_env`).
    Wrapper `tmp/run-judging-judgekey.sh` created+verified (resolves sk-ant-api03-u…). FPL batch
    record preserved as `batch_state.fpl.json`.

- 2026-08-14 **Gemini live judge DONE**: 18000/18000, 0 failed. Actual Gemini judging cost
  **$248.52** (−12% vs $281 proj). Concurrent-writer gate CLEARED — ready to harvest/resubmit Opus
  the instant architect decides A/B. Running cumulative (usage-computed): collection $226.02 +
  Gemini $248.52 + FPL Opus waste $262.56 = **$737.10 / $1150**. Refined: Path B total ≈ **$1044**
  (under, ~$106 margin), Path A ≈ **$1306** (over). $900 alert will trip mid Path-B Opus run —
  will fire it then. STILL HOLDING for A/B decision.

- 2026-08-14 **Path B APPROVED** (architect, under Option C authorization) with ordered protocol:
  credit-probe → harvest 8304 → resubmit 9696 on JUDGE in two waves → $900 alert → judge-end
  per-key reconcile. **CREDIT PROBE FAILED (hard STOP):** one tiny live Opus call on the JUDGE key
  returned **429 rate_limit_error** — "organization has crossed its monthly API usage threshold …
  regain access on **2026-09-01 00:00 UTC**." This is a MONTHLY USAGE-TIER CAP (org-level), NOT
  credit-too-low. Opus on the JUDGE key is impossible until Sept 1 (or a tier bump) — a batch submit
  would fail like FPL. **HALTED before harvest/resubmit** per the STOP-on-probe-failure precondition.
  No new spend. Cumulative unchanged: **$737.10** (collection $226.02 + Gemini $248.52 + FPL waste
  $262.56).
  - State: Gemini (ranking) 100% done. 8304 valid FPL Opus verdicts are HARVESTABLE at ZERO cost
    (read-only retrieval, no key credit needed). 9696 Opus cells blocked.
  - Options reported to architect: (1) harvest 8304 now + export Gemini-full + Opus-46% validation
    (Opus is validation-only, never re-ranks → partial coverage honest+acceptable), backfill after
    unblock; (2) Waleed raises JUDGE-org API tier now → full Path B; (3) wait to Sept 1; (4) other
    funded Opus path. Recommended (1) or (2). AWAITING decision.

- 2026-08-14 **HARVEST authorized + DONE** (architect; zero-cost read-only, no submit, no export).
  `batch-judge collect --no-fallback` on the FPL key → **8280 valid Opus verdicts written** (24 of
  the 8304 API-succeeded had unparseable JSON → left pending; 9696 API-errored on FPL credit).
  judgments.jsonl = 26280 rows (18000 Gemini + 8280 Opus).
  - **FINAL COVERAGE: Gemini 18000/18000 = 100.0%; Opus 8280/18000 = 46.0%**, evenly spread across
    all 6 framing×scope groups (~1370–1390 each) → representative validation sample.
  - **Canonical report.json (ceiling convention): TOTAL $752.27, fully_priced.** collection $226.02
    + Gemini judge $248.52 + Opus judge (FPL, batch-priced) **$277.74**. (This $277.74 supersedes
    my earlier $262.56 raw-batch-API estimate — cache-pricing methodology diff.)
  - **Per-key spend:** OpenRouter (subjects + Gemini judge) $474.54 | FPL Anthropic (Opus, USED
    under Path B — not waste) $277.74 (+~$0.8 for 24 unparseable) | JUDGE Anthropic ~$0 (blocked;
    only the tiny probe). Cumulative **$752.27 / $1150**, under the $900 alert.
  - **Backfill set:** 9720 pending Opus cells (9696 FPL-errored + 24 unparseable) — to complete on
    the JUDGE key once its org monthly cap lifts (2026-09-01) or a tier bump. **NOT exported;**
    awaiting Waleed's ship-now-partial vs tier-bump vs wait decision (architect put it to him).

- 2026-08-14 Key-path probes (Waleed via architect; two rapid, reversed directives):
  - Brief FPL-finish directive → **only ran the FPL live probe** (16-tok "ok", ~$0.0002, credit
    PRESENT on FPL) before it was CORRECTED. **No FPL batch submitted** (batch_state.json unchanged:
    the 2 original ended batches; nothing to cancel).
  - Correction: finish on JUDGE key, NO FPL submission. Probes on JUDGE key:
    (1) live re-probe → **429 org-monthly-cap** (regain 2026-09-01). (2) tiny raw 3-req **test batch**
    → **ALSO 429 org-monthly-cap** (identical). ⇒ **JUDGE key is blocked on BOTH live AND batch
    until 2026-09-01.** Opus cannot complete on JUDGE now by any path.
  - FPL key HAS credit now (probe passed) but Waleed directed NO FPL submission → off the table
    unless re-authorized. State unchanged: Gemini 100%, Opus 46.0% (8280), report.json $752.27.
  - Reported to architect; HOLDING (not exported). Paths to full Opus: (a) raise JUDGE org API tier
    in console NOW → unblock + submit 9720; (b) wait to Sept 1; (c) re-authorize FPL (has credit);
    (d) ship partial now + backfill later.

- 2026-08-14 **DECISION: Path D now + B for completion (Waleed via architect). EXPORTED.**
  - Built a per-tradition export root (`tmp/judging-runs/89-export-root/protestantism/`, hardlinks —
    the flat `89-full/` layout has no per-tradition subdir the exporter requires; originals intact).
  - **Code fix:** export `_JUDGE_VARIANTS` didn't map the Gemini OpenRouter slug
    `google/gemini-3.6-flash` (record's full-grid Gemini used the canonical id). Added the alias +
    test. Analysis suite: **233 passed, 6 skipped**.
  - `analysis export` → `results/20260813-protestantism/` (manifest + protestantism.json, 26 KB).
    `export-raw` → `results-raw/20260813-protestantism/` (100 gz shards, 30 MB). **Same fingerprint
    sha256:a0989a65…e3ed across both tiers.** Coverage honest: Gemini 3000/3000/framing, Opus
    ~1375-1381/framing (46%).
  - **Final per-key spend:** OpenRouter $474.54 | FPL Anthropic (Opus harvested) $277.74 | CEFE
    JUDGE ~$0 (blocked). Total report.json **$752.27 / $1150**.
  - Wrote codev spec/plan/review (89-*), results/README.md published-runs note (partial Opus +
    backfill). Next: commit deliverables (explicit paths) + open PR (Refs #89), do NOT merge —
    architect reviews, merge word is Waleed's.
  - **DO NOT DELETE** tmp/judging-runs/89-full (raw run data; archive before any cleanup).

- 2026-08-14 **PR #93 REVIEW: REQUEST_CHANGES (architect). HOLD merge.** Independent verification
  caught a real error in my characterization: Opus coverage is a **CONTIGUOUS SCENARIO BLOCK**, not
  "evenly spread 46%". Verified myself: **PRO-001..050 = ZERO Opus**; PRO-051..056 partial ramp
  (16/40/66/68/81/127 of 180); **PRO-057..100 ~full** (179-180). Batch-boundary artifact — the FPL
  credit ran out during the batch covering the earlier scenarios. I'd only checked the FRAMING axis
  (even) and missed the SCENARIO axis. Two tracks (Waleed may complete Opus first → don't re-export):
  - **Track 1 — FIX DOCS (done):** corrected README published-runs note, spec, review (deviation #4
    + lesson "check coverage on every axis"), PR body. Manifest currently reports coverage per-framing
    only (masks the hole); per-scenario coverage field = recommended follow-up (needs re-export → on
    hold). NOT re-exported (dataset unchanged pending Waleed's complete-Opus-first decision).
  - **Track 2 — file follow-up issue** for ReviewTraditionPage.tsx:259 defaultRunId provenance bug.
  - Also add the default-run-flip note (newest-by-generated_at → SPA default flips to this
    protestantism-only run) to the PR body (promised in-thread).
  - HOLD merge + re-export per architect.
