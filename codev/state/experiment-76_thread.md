# experiment-76 thread — prompt fading

**Protocol:** EXPERIMENT (soft mode). Driving issue: #76.

## Hypothesis (from issue #76)
Prompt-based guidance (stated/guided framings) **fades** as neutral filler separates
the framing from the moral dilemma. Weights-based formation (MultiWeights) should NOT
fade — values-in-weights is the selling point. Test directly with a fluff-separation ramp.

## Constraints (architect + issue)
- Keys: **OpenRouter key + Anthropic key ONLY**. No Waleed personal keys. No personal
  Gemini key — Gemini goes via OpenRouter (judge path pilot-validated r=0.93).
- **No live spend before cost estimate approved at the spec/experiment gate.**
- Judging matches established pipeline: numeric scores, no band names.
- References: #48 (MultiWeights SFT/DPO artifacts on Modal), #57 transfer, #58 scaling.

## Status log
- 2026-08-08: Spawned. Read issue #76. Entering hypothesis phase. Orienting on corpus,
  framings, MultiWeights run path, judging pipeline before writing the spec.
- 2026-08-08: Mapped run path + pipeline (two Explore agents). Key facts:
  - Serve endpoint (`experiments/48/modal/serve_gemma_eval.py`) exposes base gemma-4-31b-it,
    `sft`=mb-sft-guided, `dpo`=mb-sft-dpo on ONE H200, OpenAI seam, no key, `--max-model-len 16384`.
    Models are LoRA adapters on Modal volume `gemma-dpo` (read-only for us).
  - Framing normally folded onto EVERY user turn (`prompts.framing_context`) → fading impossible
    by construction. **Experiment's one structural deviation:** deliver framing ONCE as opening
    system msg, insert neutral fluff, then dilemma. Judge unchanged (scores clean blinded turns).
  - Judge = single gemini-3.6-flash via OpenRouter (`configs/samplability.yaml` pattern), full
    scope, ~$0.0149/judgment, NOT batchable. Fluff is invisible to the judge → banding cost flat.
- 2026-08-08: **DESIGN COMPLETE.** Wrote `experiments/76_prompt_fading/notes.md` — 3 arms
  (prompted-guided / weights-dpo / base-floor), 4-level fluff ramp (0/1k/4k/12k tok), 42 scenarios
  (6×7 stratified), 6 pressures, full scope. Pre-registered mixed-model + bootstrap CIs, τ=0.15,
  H1 fading / H2 immunity / H3 differential (headline) decision rules. **Cost est ≈ $80–100,
  proposed ceiling $150.** Grid = 3,024 sittings / 3,024 judgments.
- 2026-08-08: **GATE — awaiting cost-estimate approval. NO live spend until architect approves.**
  Notified architect.
- 2026-08-08: **GO received (Waleed) with redesign** — arms now A1 (guide as system msg) / A2
  (guide as one first-user-turn ctx_block prefix — benchmark's channel) / B (mb-sft-dpo). Base-floor
  dropped to a **conditional arm-C follow-up** (~$27) triggered only if slope_B materially negative.
  Estimands: slope_A1/A2/B, channel contrast A1−A2, two differentials, pooled headline. L0 check now
  vs #48 base-unstated (cross-run caveat). Budget approved ~$80–100, hard ceiling $150. Pre-reg
  revised + committed BEFORE data (54601f8).
- 2026-08-08: Built execution code (no-spend): `select_scenarios.py` (42 scen, seed 3446, committed
  manifest), `collect_fading.py` (variant collector; arm→subject, level→framing so they survive into
  judgments), `fluff_bank.md` (20 neutral exchanges, cycled to hit level targets), `serve_gemma_fading.py`
  (32k ctx copy; shipped serve untouched), `configs/fading_judge.yaml` (single gemini/OpenRouter, full).
  Offline-validated message assembly across arms×levels (clean judged turns, guide once per channel,
  no leakage in B). All committed.
- 2026-08-08: Key seam = `taqwabench/.env` (OPENROUTER + ANTHROPIC only; **GEMINI never exported** —
  personal). Modal authed. **Deployed 32k serve endpoint** → https://waleedkadous--multibench-gemma-fading-serve-serve.modal.run
- 2026-08-08: **SMOKE running** (background) — buddhism, 1 scen, 2 pressures, arms A1/A2/B, levels
  L0–L3 (incl. L3 to validate 32k long-context) → 24 sittings → judge. Then STOP + reconcile
  usage-computed actuals with architect before the full run (per GO sequence). NO full run yet.
- 2026-08-08: **SMOKE PASS** (exit 0). 24/24 sittings, 24/24 judgments, 0 fail. base+dpo served;
  L3 ~11.9k-tok ctx fit 32k; arm→subject / level→framing survive into judgments; 0 leakage.
  **Actuals:** banding $0.2964 exact ($0.0124/judgment → full-run ~$37 banding); Modal ~$1.3
  wall-clock; smoke total ~$1.6 (within $1–3). **Flag:** all 24 scores = +1.0 (ceiling on the easy
  buddhism scenario — expected; fading signal lives in the hard tier where un-guided counsel is low).
  **STOPPED per GO sequence — reconciled actuals sent to architect; awaiting explicit go for full run.
  No full run started.**
- 2026-08-08: Architect asked for a measured-throughput SERVE projection. Basis: smoke warm rate
  24 sittings/78s @ concurrency 8, smoke level-mix == full-run mix → full 3,024 ≈ 2.73h warm +
  ~0.28h overhead ≈ 3.0 H200-h → serve ~$15–19 @ ~$5.5–6.25/h. Projected total ~$56 ≤ $120.
- 2026-08-08: **FULL RUN RELEASED by architect.** Conditions: concurrent requests (running
  concurrency 24); measure warm throughput early, tell architect if serve projection > $25;
  **$60 Modal tripwire → PAUSE+reconcile**; hard ceiling $150; banding $37.5 accepted; usage-
  reconciled actuals at completion BEFORE any analysis conclusions. **Full run launched** (background,
  5h wall-clock guard, resumable). Early warm-throughput monitor also launched. Endpoint:
  https://waleedkadous--multibench-gemma-fading-serve-serve.modal.run
- 2026-08-08: **Early warm-throughput measured: 2,240 sittings/h @ concurrency 24 → serve ~1.6
  H200-h ≈ $9–10** (well under the $25 checkpoint & $60 tripwire). No pause. Told architect.
  Projected total ≈ banding $37.5 + serve ~$10 + smoke $1.6 ≈ **~$49 all-in**.
- 2026-08-08: Wrote + committed `analyze.py` (pre-registered: per-scenario-slope estimands,
  scenario-clustered bootstrap 95% CIs, τ=0.15 verdicts for H1/H2/H3 + channel + L0 check vs #53
  base-unstated ref, score-vs-separation figures). Validated on partial data — runs clean.
- 2026-08-08: Full run progressing (~290/3024, on ~2,240/h pace). Awaiting completion notification.
  **At completion: reconcile exact actuals (token-sum banding + wall-clock serve) BEFORE any
  analysis conclusions leave, then run analyze.py, write Results, PR.**
