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
