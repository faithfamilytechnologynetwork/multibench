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
