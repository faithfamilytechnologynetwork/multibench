# G2 decision memo — split-DPO descriptive add-on (pre-drafted while Modal is paused)

**Purpose.** At **G2 (post-mining-band)**, decide with usage-reconciled actuals whether to run the
**split-DPO descriptive eval** (the "full path" add-on) or **defer** it. Pre-drafted so the decision
is a plug-in-actuals step the moment Modal returns — no deliberation on the critical path.

**Architect's rule (2026-08-06):** run the split-DPO descriptive add-on **iff usage-reconciled
headroom ≥ $50 at G2**; otherwise `mb-dpo-split50` ships **trained + mining-characterized**, with its
descriptive **deferred (noted, not skipped)** in the writeup. Hard ceiling **$250 all-in**.

## Reconciled spend through the SFT stage (fixed)

| item | $ | basis |
|---|---|---|
| Train-half SFT (`mb-sft-split50`) | ~6.0 | 54 min B200 @ $6.25/hr (wall-clock reconciled) |
| Descriptive gemini (split-SFT, 3,114 judgments) | **45.75** | usage-exact (14.94M in / 3.11M out @ #48 rates) |
| Descriptive endpoint H200 + smoke | ~6.0 | estimate (reconcile if a cleaner number is available) |
| Subset CPU fn | ~0.0 | negligible |
| **SFT-stage total** | **≈ 57.8** | |

Mining sampling so far (360/6,216 sittings before the disable): endpoint-GPU only, **< $1** — folds
into the resumed-sampling line below.

## What G2 adds (reconcile these from usage before deciding)

| item | planned $ | how to reconcile at G2 |
|---|---|---|
| Resume mining sampling (remaining ~5,856 sittings) | ~8–18 | endpoint H200 wall-clock × rate; **re-measure throughput on resume** (the pre-disable rate reading was corrupted by the disable) |
| **Mining band — gemini (6,216 full-scope judgments)** | **~88–95** | **usage-exact**: sum `usage.in/out` across `data/output/mining/*/judgments.jsonl`, price at #48 rates (in $1.50/Mtok, out $7.50/Mtok, cache $0.15/Mtok) — same one-liner as the descriptive reconcile |

**S_G2 = reconciled total through the mining band ≈ 57.8 + (sampling) + (band).**
Expected: 57.8 + 13 + 91 ≈ **$162**. Range: ~$154 (low) … ~$183 (high, slow endpoint + $95 band).

## Remaining items after G2

| item | planned $ | tier |
|---|---|---|
| DPO train (`mb-dpo-split50`, B200) | ~7 | **core** (always runs) |
| Split-DPO descriptive (both halves): endpoint ~6 + gemini ~46 | **~52** | **swing (this decision)** |

## Decision arithmetic (the precise version of "headroom ≥ $50")

Let `S_G2` = reconciled total through the mining band. Running the full remaining path costs
**DPO train (~$7) + split-DPO descriptive (~$52) = ~$59**, so:

- **final-if-run ≈ S_G2 + 59**, which must stay **≤ $250 → run iff S_G2 ≤ ~$191**
  (equivalently, **headroom `250 − S_G2` ≥ ~$59**).
- The architect's "≥ $50 headroom" is the rounded proxy; **$59 is the exact figure that also covers
  the core DPO train.** Recommend a **$5 safety buffer → run iff headroom ≥ ~$60 (S_G2 ≤ ~$185)**;
  defer if between $50–60 (too thin given soft endpoint GPU — the #48 breach pattern).

### Pre-computed outcomes (plug in the actual S_G2)

| scenario | sampling | band | S_G2 | headroom | decision | final-if-run |
|---|---|---|---|---|---|---|
| low | 8 | 88 | ~154 | ~96 | **RUN** | ~213 |
| expected | 13 | 91 | ~162 | ~88 | **RUN** | ~221 |
| high | 18 | 95 | ~171 | ~79 | **RUN** | ~230 |
| stress (slow GPU + hot band) | 28 | 100 | ~186 | ~64 | **RUN (buffer-thin)** | ~245 |
| breach-guard | 40 | 100 | ~198 | ~52 | **DEFER** | ~205 (DPO only) |

**Read:** under every non-pathological outcome the add-on **RUNS** and lands **≤ ~$230** (~$20+ under
ceiling). It only **defers** if resumed sampling GPU runs pathologically hot (~$40, i.e. the endpoint
is genuinely slow) — which the throughput re-measure on resume will catch early.

## G2 execution checklist (the moment Modal is confirmed stable)

1–2. **One command:** `bash experiments/57_multiweights_split/resume_mining.sh` — redeploys the
   endpoint, disable-aware warmup (exit 3 = disabled → STOP+ping; exit 2 = warmup timeout), then
   resumes sampling (keyed dedup from 360). **Re-measure throughput after ~2 min; if pathologically
   slow, raise sampler CONCURRENCY (12→~32) in `mine_dpo_split.py` and restart (still resumable).**
3. On sampling complete → **G2 band**: `bash .../run_mining_judge.sh` (the ~$90 gemini spend).
4. **Reconcile**: sum `mining/*/judgments.jsonl` usage → exact band $; add resumed-sampling GPU →
   `S_G2`. Apply the rule above → **RUN or DEFER** the split-DPO descriptive.
5. `uv --project workflows/judging run python .../build_dpo_pairs_split.py` → pairs + yield table.
   Upload + launch DPO (reuses #48's `modal_gemma_dpo2.py` unchanged; input format verified compatible):
   ```
   modal volume put gemma-dpo \
     experiments/57_multiweights_split/data/output/mining/pairs_sft2_mb_split50.jsonl \
     /pairs/pairs_sft2_mb_split50.jsonl
   modal run --detach experiments/48_multiweights_omissive_bias/modal/modal_gemma_dpo2.py \
     --pairs /pairs/pairs_sft2_mb_split50.jsonl --sft-run mb-sft-split50 \
     --run-name mb-dpo-split50 --batch 8
   ```
   Poll `/runs/mb-dpo-split50/adapter` for completion → **G3** reconcile (DPO GPU wall-clock).
6. If RUN: redeploy endpoint (now serves `dpo`) → `run_descriptive.sh …_dpo` → `analyze.py --model dpo`.
   If DEFER: note `mb-dpo-split50` as trained + mining-characterized, descriptive **deferred**.

**Modal-disable contingency (standing):** if the workspace disables again mid-run → **stop + ping,
do NOT auto-retry** (architect 2026-08-06). All Modal runs are checkpoint+resume+detach; state is
keyed-idempotent, so a stop costs nothing.
