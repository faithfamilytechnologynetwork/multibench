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

## 2026-08-06 — BLOCKED: Modal workspace DISABLED (architect advisory risk hit my run)

Architect advisory (14:46): Modal briefly disabled for exp-58 (~15m, billing/spend-cap suspected),
my DPO B200 shares the risk; if it disables during my run, STOP + ping, do NOT auto-retry.

**It disabled during my mining sampling.** Endpoint returns `workspace ac-l0vME5OV7qKzfAPu2VRZ3n is
disabled`; sampler stalled at **360/6,216** sittings (calls hanging). Per instruction I **STOPPED the
sampler, did NOT auto-retry, pinged architect.** State safe: 360 sittings saved (keyed dedup →
resume = zero rework); SFT deliverable already complete+committed; no spend lost (endpoint-GPU only,
nothing banded). Running total still ~$58/250.

**HOLDING for architect's "Modal re-enabled" signal.** Not polling Modal (that's the forbidden
auto-retry + could worsen a spend-cap). On recovery: redeploy endpoint → resume `mine_dpo_split.py`
(resumable) → G2 band → DPO. Local analysis/writeup is unblocked if needed meanwhile.

**Architect confirmed hold correct (14:50); both experiments' Modal legs paused pending Waleed's
billing check (2 disables in ~2h = spend-cap pattern). Directed local work — DONE:**
- **Figure polished to paper-grade** (`fig_transfer_sft.pdf`, committed): left panel states the finding
  ("~85% transfer, not memorization") with the Δ+0.12 gap annotated + #53 biased-LB hatched; right
  panel sorted, hard tier highlighted, pooled-held-out line. Numbers reproduce identically.
- **G2 decision memo pre-drafted** (`G2_decision_memo.md`, committed): plug-in-actuals decision for
  the split-DPO descriptive add-on. Reconciled SFT-stage $57.8; exact arithmetic (run iff headroom
  ≥ ~$59, i.e. S_G2 ≤ ~$191); pre-computed outcomes (RUNS under every non-pathological case, lands
  ≤ ~$230; only DEFERs if resumed sampling GPU is pathologically hot); exact G2 command checklist
  incl. verified DPO launch (`--sft-run mb-sft-split50 --run-name mb-dpo-split50`).
- DPO input format verified compatible (build_dpo_pairs_split → chosen_turns/rejected_turns).

**All local work complete. Genuinely blocked on Modal; awaiting architect's re-enable ping.**

## 2026-08-06 — GO: Modal stable (exp-58 probe 702/0-fail), mining RESUMED

Architect go (16:14). Ran `resume_mining.sh` (bg bz2pide3k): endpoint redeployed clean (no disable),
warmup cold-starting, then resumes sampling from 360 (keyed dedup). Stop-on-disable armed in the
warmup. Launched a throughput probe (bg bjnaf0rif) to measure true rate once sampling is underway
(catches a slow endpoint early — the pre-disable "0/min" reading was the disable, not slowness).
NEXT: mining complete → G2 (reconcile sampling GPU + band via usage) → swing decision per memo.

**Mining sampling COMPLETE: 6,216/6,216, 0 failed**, every tradition = train_cells×4 exactly. Concurrency
12→32 gave 25→43 sittings/min (single H200 near its generation ceiling; higher won't help). Endpoint
H200 wall-clock ≈ warmup(s) ~20m + sampling ~150m ≈ **~2.8h → sampling GPU ~$12–14 est** (reconcile
at G2; GPU is always an estimate, the band is usage-exact).

**G2 mining BAND launched** (bg bof6x8c1j, `run_mining_judge.sh`): gemini full-scope over all 6,216
mining sittings — the authorized ~$90 spend. On completion → reconcile band from usage (exact) → S_G2
→ apply swing decision (run split-DPO descriptive iff headroom ≥ ~$59) → build pairs → mb-dpo-split50.

## 2026-08-06 — G2 PASSED: band $92.25 exact, swing decision = RUN; DPO training

**Band complete** 6,216/6,216 full-scope, 0 missing/failed. **Mining band = $92.25 EXACT** (29.32M in
/ 6.42M out). **Running total reconcile: SFT-stage 57.8 + sampling-GPU ~13 + band 92.25 = S_G2 ≈ $163
→ headroom ~$87.** **SWING DECISION: 87 ≥ ~59 → RUN split-DPO descriptive** (full path ~$222 ≤ 250).

**Pairs: 480** max-gap (gap≥1.0) from 1,554 train-half cells (31%). sunni-islam 168 (most — softens
hard-tier caveat), taoism 59, EC 82, jud 48, RC 53, bud 43, sage 27. 846 cells gap=0 (SFT uniformly
good — #48 pattern reproduces). gap hist {0:846, .5:228, 1:70, 1.5:145, 2:265}.

**Verified upload**: volume sha256 == local EXACTLY (c19d6a24…, 480 lines, 6.04MB). (Wrapper had a
tail-1 parse bug → false mismatch; upload itself was perfect attempt-1; fixed parser, confirmed via
direct volume-side sha. exp-58 corruption guard satisfied.)

**DPO LAUNCHED** `mb-dpo-split50` (detached ap-pWlj33d0…, ref=mb-sft-split50, 480 pairs → 60 steps,
β0.1 lr1e-5). Polling config.json (bg bxdy0zvqs). Final step==60 double-checks loaded-pair count.
Stop-on-disable armed. NEXT: G3 reconcile → redeploy endpoint (serves dpo) → split-DPO descriptive
both halves → `analyze.py --model dpo` → DPO increment vs SFT.

**G3 — DPO COMPLETE + reconciled.** 60 steps (=480/8 exact → loaded-pair count verified = 480, 2nd
upload guard passes). Loss init 0.693 (ln2, policy==ref ✓); pref_acc near chance (0.0→0.625→0.5,
noisy) — **same weak/flat DPO signal as #48** (SFT already good, little contrast; expected null-ish).
bf16 B200 peak 66GB, clean. **Wall-clock 15:25→15:54 = 29 min B200 ≈ $3.** **Running total ≈ $166/250,
headroom ~$84.**

**Split-DPO descriptive STARTED.** Redeployed endpoint (now serves sft+dpo). Made
`multibench_descriptive_split_dpo.yaml` (subject model=dpo). Running a 1-scenario **dpo smoke** (bg
brkdjqrl7) to confirm the dpo LoRA serves before the full ~$46 run. Then full descriptive_dpo (519
unstated/full, gemini) → `analyze.py --model dpo` → held-out DPO lift + SFT-vs-DPO increment.

## 2026-08-06 — EXPERIMENT COMPLETE

**Split-DPO descriptive** done: 3,114 judgments, 0 missing/failed. **DPO descriptive gemini = $43.86
exact.** **Held-out DPO lift +0.897 [+0.820,+0.972]**, post-DPO +0.693 (crosses positive); all 7
traditions CI>0; **STRONG**. **DPO increment vs SFT = +0.119** (uniform both halves) — but **same-judge
confound** (DPO banded+evaluated by gemini → likely selection-judge alignment, not clean quality; OOD
arbiter = Exp B's AFB, not re-run). Both stages transfer strongly on the clean holdout.

**FINAL SPEND reconciled ≈ $216/250** (gemini EXACT $181.86 = 45.75+92.25+43.86; GPU ~$34). Clean
landing under ceiling — the 3 reconciled gates + batch-unavailable honesty upfront held it (vs #48's
overshoot). Committed 51b262b, notes.md Status=COMPLETE.

**Deliverables:** `mb-sft-split50` + `mb-dpo-split50` (companion split adapters; #48 shipped model
untouched); notes.md (full writeup); fig_transfer_{sft,dpo}.pdf; split lists; G2 memo.
**NEXT:** report completion to architect → review doc (`codev/reviews/57-…`) + PR.

## 2026-08-06 — PR #68 UP (awaiting architect review → Waleed merge word)

Architect approved review-doc + PR (no changes; keep the DPO judge-alignment caveat verbatim). Done:
- **Review doc** `codev/reviews/57-multiweights-split.md` (final-analysis framed): outcome, #53
  revision, caveats, spend, lessons, + §8 data inventory + §5 G1/G2/G3 gate reconciles.
- **Data persistence (#48 scar rule satisfied):** adapters mb-sft-split50/mb-dpo-split50 + pairs +
  train-subset volume-persisted (confirmed); 107MB raw audit trail tar.gz **archived sha-verified**
  to `/exp57-archive/data_output.tar.gz` (d1f18169…). Safe to cleanup on architect's word.
- **PR #68** (Closes #57): https://github.com/faithfamilytechnologynetwork/multibench/pull/68 — pushed
  builder/experiment-57 (16 commits). **NOT merging** — architect reviews, then Waleed gives merge word.

**EXPERIMENT DONE. Standing by for PR review / merge word. Worktree clean, no stray processes.**

## 2026-08-06 — PR #68 REQUEST_CHANGES addressed (science passed recomputation; hygiene only)

Pushed 8cd7151: (1) 4× taqwabench .env → `${TAQWABENCH_ENV:-…}` (exp-58 convention, unset-safe
fallback); (2) hardcoded worktree ROOT → dirname idiom in run_mining_judge/resume_mining/verified_put/
run_mining_sample (all 7 scripts pass `bash -n`); (3) status.yaml → terminal (phase complete /
build_complete true / gate passed); (4) bound reconciled to **[+0.22, ~+0.90]** across review+notes
(SFT-only +0.78, SFT+DPO +0.90 — single downstream bound for the paper). Commented on PR + pinged
architect for re-review. **Still NOT merging — Waleed's word.** Standing by.

**Correction (3693dc6):** architect flagged fix (1) — my `${TAQWABENCH_ENV:-/Users/…}` fallback kept
the absolute credential path committed in the PUBLIC repo (defeats the finding + breaks the standing
fail-fast/no-fallback rule). Fixed to **`${TAQWABENCH_ENV:?…}`** (fail-fast, no path in file) in all 4
scripts. Verified: zero absolute /Users or taqwabench/.env paths anywhere in exp57 scripts+docs; all 9
scripts pass bash -n. Items 2-4 unchanged. Commented + pinged. Awaiting re-verify → Waleed merge word.

## 2026-08-07 — PR #68 MERGED (6d48053); then a SCOPE-CORRECTION docs follow-up

PR #68 merged (merge commit **6d48053**), issue #57 auto-closed. Then Waleed flagged an **overreach**
in the claim: I'd written "cross-tradition transfer." **The 50/50 split is scenario-level WITHIN each
tradition** (each tradition contributes scenarios to both halves), so the result is
transfer/generalization to held-out **SCENARIOS** (uniform across all 7 traditions), **NOT**
cross-tradition transfer. The leave-one-tradition-out ablation that WOULD test cross-tradition
generalization is **untested / HELD** (not planned).

Docs-only PR off origin/main (branch `builder/experiment-57-docs`), architect-directed scope:
- **paper `multiweights-paper.tex` §3.4**: corrected the term; added the scenario-level scope note
  naming the untested leave-one-tradition-out ablation; **added the DPO stage** (held-out +0.90
  [+0.82,+0.97], train-half +1.02, judge-alignment caveat verbatim); bound → **[+0.22,~+0.90]**;
  **wired fig_transfer_dpo alongside fig_transfer_sft** (both final renders); removed a duplicate
  scope-note paragraph. Abstract + discussion already used correct "held-out scenarios" framing.
- **codev/reviews/57** + **experiments/57 notes.md**: same terminology correction + scope note.
- **Rebuilt PDF** via `latexmk -xelatex -cd <abs path>` (never manual cd; fontspec needs xelatex) —
  9pp clean; verified §3.4 text + two-panel Figure 4 render (read the PDF pages).
- Committed a22ea7f. NEXT: push → docs-only PR → architect review + merge go (Waleed's green-light
  covers it, no separate gate). **Cleanup still HELD until this lands.**
