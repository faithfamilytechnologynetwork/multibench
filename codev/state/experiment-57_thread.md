# experiment-57 thread — MultiWeights-split (50/50 scenario holdout SFT+DPO)

Issue #57. Experiment A of the two-experiment framing: does the MultiWeights recipe help on the
**actual benchmark, measured properly** (clean held-out half)? The single-fold retrain deferred by
#48 §4.3 and #53. Experiment B (OOD/AFB) is already answered by `mb-sft-dpo` — that model is NOT
touched; new adapters are `split50`-suffixed.

## 2026-08-06 — session start, at the PRE-TRAINING GATE

**Context read:** issue #57, #48 notes + review, #53 notes. Architect brief + two directive updates
absorbed (train-half SFT is a scenario_id subset of `/pairs/sft_guided_mb.jsonl` on the gemma-dpo
volume — no re-collection; base ref = committed `per_scenario.csv`; use `split50` names, don't touch
#48 adapters; **full-grid** train-half mining, no subsetting; **hard ceiling $250 all-in**).

**Split BUILT + committed** (`split.py`, `SEED=5757`, stratified-by-tradition, deterministic):
- train **259** scenarios / **1,362** SFT examples (matches issue's ~1,370); holdout **260** scenarios.
- **Every tradition has a real held-out arm (24–70 scen)** — fixes #53's core limitation (its strict
  holdout was 13 scen, mostly sunni-islam, 4 traditions absent).
- Artifacts: `split/{train_scenarios,holdout_scenarios,split_manifest}.json`.

**Pre-registered interpretation rules written BEFORE any number** (in notes.md): held-out transfer
lift (primary) vs train-half memorization-reference lift vs #48 +0.83 / #53 +0.22; τ=0.15; clean
because random stratified split balances base difficulty across halves (breaks #53's
memorization-vs-trainability confound); scenario-clustered bootstrap CIs.

**KEY COST FINDING — batch is unavailable.** The judging pipeline batches only the Anthropic/Opus
judge; **Gemini is not batchable** (Vertex has no dev file-batch — verified in `batching.py`). Issue
mandates gemini for comparability → every judging line is full price, so the $250 ceiling is tight.

**Costed plan (planning estimates; actuals reconciled at gates):**
- Core path (SFT + split-SFT descriptive both halves + full-grid mining + DPO train): **≈ $170–185
  all-in** (~$65 margin). Answers the experiment's question.
- Full path (+ split-DPO descriptive): **≈ $220–245 — rides the ceiling**. Made the split-DPO
  descriptive the swing item, decided at the post-mining gate (G2) only if ≥$50 headroom.
- Three usage-reconciled gates: G1 post-SFT, G2 post-mining-band, G3 post-DPO.

**→ GATED to architect. STOP. Nothing trained or judged yet; zero spend so far. Awaiting Waleed's
$250 authorization before any Modal/gemini spend.**

## 2026-08-06 — GO (core path authorized ~185, DPO-descriptive contingent on G2 headroom>=50)

Architect approved. Executing core path; three reconciled gates G1/G2/G3; stop+ping on projection
breach. Writeup req: report held-out lift + CI alongside BOTH refs (train-half memorization ref +
#48 +0.83 / #53 +0.22) — that three-way is the deliverable.

- **Train-half SFT subset BUILT on volume** (`modal_split_subset.py`): kept **1,362 == expected**
  (validates the exposure-derived costing!). 251/259 train scen present (8 zero-exposure). Rows carry
  scenario_id+tradition. → `/pairs/sft_guided_mb_split50train.jsonl`.
- **SFT LAUNCHED** `mb-sft-split50` (detached+spawn, app ap-w2qY9dwyHUQn7fDunsKRzt), reusing #48's
  `modal_gemma_sft.py` unchanged (bf16 LoRA r32 B200, ~341 steps, 2 epochs, seed 3446). Distinct run
  name — does NOT touch #48 adapters (gemma-sft-guided/gemma-sft-dpo). ~55 min expected (~half #48).
  Polling volume for completion (config.json marker) via background task.

**G1 — SFT COMPLETE + reconciled (PASS).** 341 steps (=1,362×2/8 exact), 2 epochs, loss **2.72 →
0.48** (near-identical to #48's 2.64→0.47 — recipe behaves the same on half-data). bf16/B200 peak
65GB, clean (config.json written, state file gone). **Wall-clock 06:15:25 → ~07:09:30 ≈ 54 min B200
@ $6.25/hr ≈ $5.6–6.0.** Actual ≤ $8 plan. **Running total ≈ $6 / $250.** No breach → proceeding
(directive: ping only on breach). Loss log saved to scratchpad.

**Descriptive phase (held-out transfer measurement) STARTED.** Deployed `serve_split_eval.py` (app
multibench-gemma-eval-serve-split, base + sft=mb-sft-split50, DPO-tolerant) →
`…-serve-split-serve.modal.run/v1`. Config `multibench_descriptive_split.yaml` (subject "sft",
unstated/full, gemini judge, max_tokens 4096 to dodge #48's 16384→400 bug). Base REUSED from #53
per_scenario.csv (same OpenRouter base → lift directly comparable). Running a 1-scenario buddhism
**smoke** (bg btprpib5q) to validate the seam before the ~$45 full 3,114-cell run.

**Smoke PASSED**: collect 6/6, judge 6/6, 0 failed, scores clean 5-pt bands (5×+1.0, 1×+0.5 for a
buddhism scenario — recipe working). Seam validated, no max_tokens bug.

**Full descriptive run** (all 519 scen, unstated/full, gemini): first launch failed INSTANTLY on a
bash empty-array quirk (`set -u` + macOS bash 3.2) at line 28 — **before any collect/judge, zero
spend**. Fixed with the safe `${arr[@]+…}` idiom; relaunched (bg bpt4tmuwx), buddhism collect running
(endpoint cold-start). Self-completing driver → notifies on all-7-traditions done.

**Analysis script READY** (`analyze.py`, zero-spend prep during the wait): aggregates split-SFT
per-cell→per-scenario, joins reused base, partitions by committed split, emits the **three-way
deliverable** (held-out lift+CI vs train-half memo ref vs #48 +0.83 / #53 +0.22), per-tradition
held-out CIs (★ hard tier), base-balance check, and the pre-registered verdict. Reuses #53's
bootstrap machinery; scenario-clustered CIs.

## 2026-08-06 — SFT RESULT (STRONG transfer) + DPO stage started

**Descriptive complete**: all 7 traditions, 3,114 cells, 0 failed. **Held-out transfer lift +0.778
[+0.700,+0.856]**, post-SFT +0.574 (crosses positive); train-half memo +0.900; Δ +0.122 (small);
base-balanced (Δ+0.053). **PRE-REG VERDICT: TRANSFER CONFIRMED (STRONG).** Every tradition transfers
(CI>0); hard tier strong (RC +1.07, sunni +0.67). **Revises #53**: +0.83 was ~85% genuine transfer,
not 4× memorization — #53's +0.22 was its biased-holdout lower bound. Committed a0fedd1, reported to
architect, **verdict ACCEPTED**. Writeup caveat logged: +0.778 is the COMPANION half-data retrain, not
the shipped full-data model (shipped model's unseen behavior bounded [+0.22, ~+0.78]).

**Spend reconciled ≈ $58/250** (SFT ~6 + descriptive gemini **45.75 exact** + endpoint ~6). Headroom ~192.

**DPO stage — mining sampling LAUNCHED** (bg br8nw1aw4, `mine_dpo_split.py`): train-half FULL grid
(259 scen × 6 × K4 = **6,216 sittings**, no subsetting per Waleed), model="sft"=mb-sft-split50 via the
split endpoint, temp 1.3. Endpoint-GPU only (~$8), NO gemini yet. Writing sittings (alive). Prepped
(zero-spend): `run_mining_judge.sh` (the ~$90 G2 gemini band), `build_dpo_pairs_split.py` (max-gap
pairs, gap≥1.0). NEXT: sampling done → G2 band → reconcile → pairs → mb-dpo-split50 → G3 → decide the
split-DPO descriptive add-on (headroom will be ~76 ≥ 50 → likely affordable).
