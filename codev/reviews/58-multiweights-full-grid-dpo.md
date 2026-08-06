# Review — Experiment 58: MultiWeights full-grid DPO (AFB / 100%-train track)

**Status**: Complete — **scaling-NEGATIVE**. **Outcome**: the incumbent `mb-sft-dpo` **stands** as the
MultiWeights deliverable; the full-grid head `mb-dpo-full` is retained as an **inert adapter for the
record** (nothing overwritten; serve endpoint torn down).
**Issue**: #58 · **Predecessor**: Experiment 48 (`codev/reviews/48-multiweights-omissive-bias.md`) ·
**Full trail**: `experiments/58_multiweights_full_grid_dpo/notes.md`.

## 1. Question & result

Would mining the **full scenario grid** for stage-2 DPO (903 within-cell max-gap pairs) beat the #48
scoped run (487 pairs)? Pre-registered decision rule: ship `mb-dpo-full` **iff weakly better than
`mb-sft-dpo` on ALL FOUR gates** — else the incumbent stands.

**It did not — it mildly regressed.** This is the empirical answer to "would more pairs help?": **no.**

| gate | mb-dpo-full | incumbent | threshold | verdict |
|---|---:|---:|---|:--:|
| 1. AFB P≥2 cold (gpt-5.6-terra 0–4) | **0.233** | 0.30 | ≥ 0.300 | **FAIL** |
| 2. secular-task leakage (max P≥1) | **0.20** | 0.00 | == 0.00 | **FAIL** |
| 3. opted-out interlocutor P≥1 | 0.60 | 0.60 | ≤ 0.60 | PASS |
| 4. chat-mode MMLU (re-anchored) | 83.41 | 83.14 | ≥ incumbent | PASS |

Fails gates 1 and 2 → **incumbent `mb-sft-dpo` stands.** AFB cold mean **1.173 → 0.940**, and the head
**omits more** (80/150 zeros); a new **creative-professional leakage** (P≥1 0.20 vs 0.00) appears.

## 2. Mechanism — why more pairs hurt (the science)

The DPO train **pref_acc ≈ 0.5** (near chance), exactly as in #48 (0.538). Within-cell preference
contrast is textually modest because the SFT already emits good counsel (#48's "DPO no-pair cells are
uniformly GOOD" diagnosis). So **doubling the pair set = ~2× optimization steps on near-zero-signal
contrast** → the head drifts off-calibration rather than sharpening. **The 487-pair scoped run was
near-optimal for this mechanism.** Capability is untouched (gate 4 passes; MMLU flat ~83), so the
damage is specifically to representation/calibration, not general ability — a clean, interpretable
scaling-negative.

Side observation (non-gated): **hostile-to-religion P≥1 = 1.00** (mean 2.90) — the head always engages
religiously even with anti-religion prompts. Not one of the four locked gates; recorded for the paper.

## 3. Capability — chat-mode four-checkpoint panel (measurement-defect remediation)

#48's capability numbers were **raw-completion-mode artifacts** (MMLU "0.4424" on an instruction-tuned
model). This run re-measured in **chat mode** (`--apply_chat_template --fewshot_as_multiturn`, max_len
8192), the paper's capability section of record. **Base anchor-guard passed** (MMLU 82.8 / GSM8K-s 95.83
/ IFEval-p 91.68, all within ±3 of taqwabench's independent 82.8 / 95.8 / 91.7) → the measurement is
valid, so the AFB regression is real, not a config artifact.

| checkpoint | MMLU | GSM8K-CoT strict | IFEval prompt-strict | IFEval inst-strict |
|---|---:|---:|---:|---:|
| base | 82.80 | 95.83 | 91.68 | 94.24 |
| mb-sft-guided | 83.28 | 95.15 | 90.57 | 93.41 |
| mb-sft-dpo (incumbent) | 83.14 | 95.07 | 89.28 | 92.45 |
| mb-dpo-full | 83.41 | 95.15 | 90.76 | 93.65 |

MMLU flat ~83 (no regression; the real chat-mode number, confirming #48's 0.4424 was an artifact);
GSM8K ceiling-flat ~95 (expected — chat mode collapses raw-mode gains); IFEval dip-then-recover shape
matches taqwabench. **No deployment-mode capability regression.**

## 4. Method (reproducibility)

- **Incremental, not full re-mine** (architect-directed, cost-saving): reused #48's surviving **487
  pairs** and mined only the **239 uncovered scenarios** (1,434 cells, K=4 @ temp 1.3 from the
  unchanged `mb-sft-guided` → on-policy consistent). Seed-recovery of the #48 scoped set was **exact**
  (`pair ⊄ mined = 0`, all 7 traditions). New yield **416/1,434 = 29%** → **combined 903 pairs, 0 cell
  collisions**.
- **One fresh DPO** from the SFT checkpoint (ref+init = `mb-sft-guided`; new name `mb-dpo-full`), not a
  continue-train from the incumbent — clean comparison. bf16, B200, β0.1, lr1e-5, 1 epoch, seed 3446.
- Banding via `judging judge --config samplability.yaml` (full-scope gemini-3.6-flash), all 5,736
  judgments, 0 failed.

## 5. Spend — reconciled ≈ $115 (ceiling $300)

Banding **$80.99 EXACT** (usage-summed) dominates; sampling ~$9, DPO ~$6, terra ~$4, capability+serve
+relaunch ~$15. ~38% of ceiling, ~$185 unspent. Usage-reconciled at every gate per standing rule; the
budget was never near-threatened.

## 6. Incidents & discipline

- **Modal workspace disabled twice** mid-run (account-level spend-cap/billing trip, concurrent with the
  taqwabench programme's GPU draw). First: transient, recovered, resumed. Second: per the pre-agreed
  rule, **stopped everything and pinged** — no auto-retry. Mining writes locally + dedups, so **zero
  data lost**; refill filled only the 702 missing sittings. Cautious resume as the serving-path probe
  (exp-57 gated on it). Net cost of both incidents: ~$1–2 retry-churn.
- **base-chat path collision** on the shared volume: my base capability job would have clobbered the
  taqwabench programme's `base-chat` AND the guard could have read *their* result (masking a config
  error). Fixed by renaming base → `mb-base` (distinct path) and relaunching the panel; taqwabench's
  outputs left untouched. ~$4–6 re-cost, accepted for guaranteed-mine, uncollided results.
- The **locked pre-registered rule did exactly its job**: a surprising regression was accepted as the
  result with no post-hoc gate relaxation.

## 7. Paper / production path

- **Ship `mb-sft-dpo`** (unchanged) — Experiment 58 confirms it as the better of the two DPO scales.
- **Stage-2 sections + `tab:dpo`**: add the scaling-negative as the answer to "would more pairs help?"
  (487 near-optimal; 903 mildly worse) and **replace #48's completion-mode capability numbers with this
  chat-mode four-checkpoint panel** (the defect remediation).
- `mb-dpo-full` kept inert on the volume for reproducibility; nothing serves it.
