# Review — Experiment 57: MultiWeights-split (50/50 scenario-holdout retrain)

**Status**: Complete (2026-08-06). **Deliverables**: `mb-sft-split50` + `mb-dpo-split50` — companion
gemma-4-31b LoRA adapters trained on a clean *train half*, evaluated on a true held-out half. The
shipped full-data model (`mb-sft-dpo`, #48) is **untouched**.
**Driving issue**: #57 · **Full trail**: `experiments/57_multiweights_split/notes.md`.

## 1. Question & outcome — TRANSFER CONFIRMED (STRONG)

Does the MultiWeights recipe improve counsel on the **actual benchmark, measured properly** — i.e. on
never-trained scenarios, cross-tradition — or was #48's on-bench lift memorization? This is the
single-fold retrain deferred by #48 §4.3 and #53. Answer, under a **pre-registered** rule written
before any number: **yes, it transfers, strongly.**

| stage | held-out lift (95% CI) | post-model mean | verdict |
|---|---|---|---|
| SFT (`mb-sft-split50`) | **+0.778** [+0.700, +0.856] | +0.574 (crosses +) | STRONG |
| DPO (`mb-dpo-split50`) | **+0.897** [+0.820, +0.972] | +0.693 (crosses +) | STRONG |

All 7 traditions transfer (every CI excludes 0); the hard tier is strongest (held-out RC +1.07/+1.15,
sunni +0.67/+0.85). Memorization inflation is small and stable: train−held-out Δ ≈ **+0.12** both
stages (base difficulty balanced across halves by the random split, Δ_base +0.05).

## 2. This revises #53 (heterogeneity, not contradiction)

#53 read the +0.83 aggregate as "memorization-driven, ~4× overstated" (transferable only +0.22). That
+0.22 came from an **adversarially-biased holdout** — its zero-exposure cells were exactly the
samplability-filter *failures* (hardest, mostly sunni-islam, 13 scenarios, 4 traditions absent) — and
#53 explicitly could not separate memorization from latent trainability. The clean random 50/50
retrain **breaks that confound**: the on-bench lift is **~85–88% genuine cross-tradition transfer**,
not 4× memorization. #53's +0.22 was the biased-sample **lower bound its own caveat predicted**.

## 3. Deliverable decisions & honest caveats

- **Both split adapters are the deliverable**; the shipped #48 `mb-sft-dpo` is unchanged (hard rule).
- **Shipped-vs-companion (paper must state):** +0.78/+0.90 is the **half-data companion** retrain, not
  the shipped full-data model. The shipped model has no clean holdout; its unseen-scenario behavior is
  **bounded [+0.22, ~+0.9]**. The companion establishes the recipe *generalizes*; it does not
  re-measure the shipped model.
- **DPO increment (+0.12) is judge-alignment-confounded:** DPO pairs were gemini-banded and the
  descriptive is gemini-judged (sole selection+eval judge — #48's caveat), so the SFT→DPO increment is
  plausibly selection-judge alignment, not clean quality. This experiment cannot separate them on a
  gemini metric; the OOD arbiter is Experiment B's AFB battery (different judge, already answered for
  the shipped model, **not** re-run here). DPO's *weak training signal* (pref_acc ~0.5) reproduces #48.
- Inherited same-stack caveat (OpenRouter base vs vLLM eval), small vs the lifts.

## 4. Mining characterization (train-half full grid)

480 max-gap pairs from 1,554 cells (31%); sunni-islam contributes the most (168), softening the
hard-tier under-representation caveat again; 846 cells have zero within-cell gap — SFT already
uniformly good (#48's "no-pair cells are good, not bad" reproduces at clean-split scale).

## 5. Spend — reconciled, UNDER ceiling (contrast #48's overshoot)

**$216 / $250.** Gemini **usage-exact $181.86** (SFT descriptive 45.75 + mining band 92.25 + DPO
descriptive 43.86); GPU ~$34 (SFT 6 + DPO 3 + endpoint H200 ~25). Held by: (a) three usage-reconciled
gates (G1/G2/G3) — never rolling estimates; (b) stating up front that **gemini is not batchable**
(only the Anthropic judge batches — verified in `batching.py`), so the ceiling was planned honestly
rather than discovered late. Dominant line: the mining band ($92).

## 6. Lessons

1. **A biased holdout gives a biased bound, and a clean retrain is worth it.** #53's exposure
   pseudo-holdout was the best zero-spend proxy available, but its selection (filter-failures) both
   depressed and confounded the estimate. The $216 retrain converted a "~4× memorization, mostly-sunni"
   caution into a "~85% cross-tradition transfer" result. Pre-registering the rule made the flip honest.
2. **`modal volume put` silently corrupts — verify volume-side.** (exp-58 scar.) The DPO-pairs upload
   was guarded by a SHA-256 + line-count round-trip computed *on the volume* (`verified_put.sh` +
   `modal_volume_verify.py`); the training log's loaded-pair count (60 steps = 480/8) is a second guard.
   Also: parse the verify tool's JSON line explicitly (a `tail -1` grabbed a Modal log line and cried a
   false mismatch — the upload was actually perfect).
3. **A stalled wait is often a dead producer.** When the Modal workspace disabled mid-mining, the
   sampler "looked alive" but was hanging on a disabled endpoint. A disable-aware health check + a
   throughput probe (not a blind wait) caught it; keyed-idempotent resume made the stop cost nothing.
4. **Concurrency ≠ throughput past the GPU ceiling.** Raising the sampler 12→32 only bought ~1.7×
   (25→43 sittings/min) — a single H200 is generation-bound; higher concurrency wouldn't have helped.

## 7. Paper path

- **§3.4 headline:** the recipe's on-bench lift is ~85–88% genuine cross-tradition transfer (held-out
  SFT +0.78 / DPO +0.90, both cross positive, all 7 traditions), **revising** #53's memorization
  reading to a heterogeneity one. Figures: `fig_transfer_{sft,dpo}.pdf`.
- Report the shipped-vs-companion bound and the DPO-increment judge-alignment caveat plainly.
- **Not done (out of scope):** re-measuring the shipped full-data model on a holdout (would need a
  second full retrain); DPO's OOD value (Experiment B / AFB, already in hand).
