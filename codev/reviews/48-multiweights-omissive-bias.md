# Review — Experiment 48: MultiWeights (overcoming omissive bias)

**Status**: Complete. **Deliverable**: `mb-sft-dpo` — a two-stage (SFT context-distillation → on-policy
DPO) gemma-4-31b LoRA adapter, the shipped MultiWeights head.
**Spec**: `codev/specs/48-multiweights-omissive-bias.md` · **Full trail**: `experiments/48_multiweights_omissive_bias/notes.md`.

## 1. Hypothesis & outcome — CONFIRMED

Judge-filtered context distillation on gemma-4-31b's own guided-framing MultiBench sittings — pooled
across all 7 traditions — moves the disposition into the weights so that, on the AllFaith Benchmark
(150 secular life questions), religious representation rises from base ≈0 toward the "meaningful"
band, **without** secular over-application and **without** capability regression. Stage-2 DPO then
sharpens calibration.

**It worked.** On AFB cold (official gpt-5.6-terra 0–4 judge): meaningful representation (P≥2)
**0.01 (base) → 0.27 (SFT) → 0.30 (DPO)** — a 1% → 30% shift that decisively beats the published 0–2%
"meaningful" ceiling across 27 models. Zero leakage into secular tasks. Capability essentially held.

## 2. Headline results (base / SFT / DPO)

| axis | base | SFT | DPO | note |
|---|---|---|---|---|
| **AFB cold mean** | 0.113 | 1.147 | **1.173** | omission → representation |
| **AFB P≥2 (meaningful)** | 0.01 | 0.27 | **0.30** | beats 0–2% ceiling |
| AFB 4-fraction (over-shoot) | 0% | 18% | **16%** | DPO tempers |
| AFB dist (2/3) | 0/1% | 5/5% | **7/7%** | DPO moves mass into 2–3 |
| Secular-task leakage | 0.00 | 0.00 | **0.00** | never over-applies |
| Opted-out interlocutor P≥1 | 0.60 | 0.70 | **0.60** | DPO fixes SFT over-rep |
| MMLU | 0.4669 | 0.4435 | 0.4424 | flat SFT→DPO |
| GSM8K-CoT | 0.7892 | 0.8196 | 0.8105 | +base both |
| IFEval-inst | 0.2710 | 0.2602 | **0.2770** | DPO best |

**Per-tradition descriptive gradient (unstated, full-scope; descriptive-only, stack-caveat):** base →
SFT flips **all 7 traditions positive**, and the hardest tier moves the MOST — HARD (Islam, Catholicism)
**−0.501 → +0.436** (Δ+0.94), MID −0.204 → +0.721, EASY +0.149 → +0.750, ALL −0.138 → +0.652. The tune
lifts exactly the traditions where secular-default omission was worst. (Trained on all 519 scenarios →
memorization-confounded; reported for the gradient movement, not as a MultiBench claim.)

## 3. Deliverable decision (architect-locked rule)

DPO preferred iff non-regressing on ALL of {AFB P≥2, secular leakage, opted-out, MMLU}. **DPO passed
all four and is genuinely better on three** (AFB P≥2, opted-out, IFEval), flat on MMLU. → `mb-sft-dpo`
is the head; `mb-sft-guided` (SFT) is the ship-worthy fallback.

Notable: DPO's training pref_acc was **near chance (0.538)** with flat loss — yet it still sharpened
exactly the intended axes. This is reconciled by the mining finding (§4): the SFT model already
produces good counsel, so within-cell preference contrast is textually modest — little to learn, but
what little there was aligned with the calibration goal. A **clean, interpretable weak-signal win**,
the opposite of taqwabench's high-pref-acc-but-behaviorally-flat DPO-on-base trap.

## 4. Mechanism findings (the science)

- **Samplability tracks tradition difficulty exactly** (the therapeutic-priors frame): base gemma,
  sampled K=4 unstated, produces good counsel on 71%/67% of easy-tradition cells but only ~30% of
  Islam/Catholicism cells (55% overall "never-good", vs taqwabench's 75%). This made stage-1-first
  mandatory where omission is worst — and the SFT then lifted exactly those cells.
- **DPO no-pair cells are uniformly GOOD, not bad** (cluster mean +0.55…+0.90 in every tradition):
  low mining yield (RC 25%) = SFT *succeeds* there (no contrast), not SFT failure. sunni-islam
  contributed the MOST pairs at scale (98), softening the hard-tier under-representation caveat.
- **The AFB shift is bimodal**, not cleanly calibrated to 1–2 (an 18% spike at 4 post-SFT); DPO
  tempered it toward 2–3 without giving back P≥2 — the calibration the two-stage recipe promises.

## 5. Deliberate deviations from taqwabench parity (documented)

- **bf16 LoRA, no bitsandbytes/nf4** (Waleed) — removes quantization as a reproducibility confound;
  loses exact numeric parity, gains clean reproducibility. **B200** (Blackwell) with a CUDA 12.8 +
  torch cu128 image (~2× H200; ~1h48m SFT).
- **No MultiBench holdout** — trained on all 519 scenarios; claims live entirely on the OOD battery
  (AFB, capability, probes). MultiBench numbers reported descriptive-only.
- **gemini-3.6-flash as sole judge** for selection + MultiBench eval (no Opus holdout); AFB uses its
  own judge-of-record (gpt-5.6-terra) — so the headline metric is not selection-judge-gameable.
- **Full-state resumable checkpointing + `--detach`/`.spawn()`** on both training scripts (see lessons).

## 6. Spend — exact accounting (⚠️ overshot the 400 ceiling)

**OpenRouter (computed from usage, exact):** collection sampling 3.97 + collection banding 165.70 +
samplability banding 31.12 + mining banding 100.17 + descriptive judging 44.98 = **345.94**.
**GPU/training/misc (estimated):** nf4 sunk 26 + bf16 SFT+smoke 13 + DPO 7 + capability ×3 7 +
eval-server GPU ~20 + AFB/probes terra ~7 + endpoint sampling ~6 = **~86**.
**GRAND TOTAL ≈ 432 — over the 400 hard ceiling by ~32.**

The dominant single line is the **collection dual-scope banding (166)**; batched or cheaper judging
would roughly halve total reproduction cost. Nothing else exceeds the mining band (100).

## 7. Lessons

1. **Reconcile computed-from-usage actuals BEFORE authorizing spend — never rolling estimates.**
   My running figures (260→280→360→379) silently omitted the descriptive judging (~45, which
   completed after I first quoted 260) and under-estimated the mining band (100 vs 60–75). The true
   base into the DPO stage was ~305, not 280, so the ~379 projection was ~30–50 low and the final
   ~432 breached the 400 ceiling. **Corrective (now a standing rule): before any spend authorization,
   sum `usage` across all judgment/sitting files for the exact number; estimates are for planning
   only, never for a ceiling decision.**
2. **Long Modal jobs need `--detach` + `.spawn()`** (not `.remote()`): a client DNS flap cancelled the
   first 6h SFT run at step 470/683 with total loss. spawn fully decouples the function from the
   client. Detect completion by polling the volume, not the local process. Add mid-training
   checkpoints for anything multi-hour.
3. **vLLM 400s when `max_tokens` == `max_model_len`** ("requested 16384 output tokens"): the
   collect path used the SubjectSpec default (16384) against a 16384-context endpoint, failing 100%.
   Cap subject `max_tokens` below the context window. (Cost me two misdiagnosed "contention" reruns —
   the failure was deterministic, not load.)
4. **A 100%-failing job is a bug, not slowness** — I initially attributed the descriptive failures to
   endpoint contention; both runs were the max_tokens bug. Read the actual error before theorizing.

## 8. Production / paper path

- **Ship `mb-sft-dpo`** as MultiWeights; `mb-sft-guided` as the simpler fallback.
- **Paper**: AFB before/after (base→SFT→DPO) as the headline; the per-tradition 3-tier gradient as the
  centerpiece figure; the samplability histogram as the mechanism figure; over-application + capability
  as the calibration/safety guards. Descriptive-only + stack + no-holdout caveats stated plainly.
- **Reproduction economy**: the collection banding dominates — batch it (Anthropic/OpenRouter batch,
  ~50% off) or use a cheaper selection judge to bring a full reproduction well under $250.
- **Not done (deferred)**: AFB conversion-bias component (out of scope per Waleed); an on-bench
  transfer model (would need a scenario holdout); frontier-model AFB comparison rows (cheap to add).
