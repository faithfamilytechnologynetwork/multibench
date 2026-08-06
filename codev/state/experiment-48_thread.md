# experiment-48 — MultiWeights (omissive bias / gemma-4-31b fine-tune)

Soft-mode EXPERIMENT builder. Spec: `codev/specs/48-multiweights-omissive-bias.md`.

## 2026-08-04 — startup & orientation

Read spec + taqwabench methodology doc
(`<taqwabench>/tmp/dpo-experiment/methodology-for-multibench.md`)
+ reference DPO script suite (same dir) + `docs/therapeutic-priors.md`.

**Architect sequencing constraints (2026-08-04T21:47Z):**
1. Framings expansion STILL RUNNING on the shared OpenRouter key + Gemini quota —
   **do NOT start gemma collection** until architect gives the word (finishes within hours).
2. Samplability diagnostic is a **hard gate**: run it and REPORT the histogram before ANY training.
3. Any spend **>$50/step**: tell architect BEFORE, not after.
4. Env keys: ask the architect when needed — do not go hunting.
5. taqwabench capability-panel config (IFEval/MMLU/GSM8K) lands tomorrow — architect forwards.

**Wait-window setup tasks (no shared-key spend):** Modal script adaptation plan,
vLLM serving check plan for gemma-4-31b, OpenRouter slug verification / self-serve plan,
clone AFB repo, **design the over-application probe suite (required BEFORE training)**,
scaffold the experiment dir + notes.md.

State: project at `hypothesis` phase. Nothing trained, nothing collected. No spend yet.

## 2026-08-04 — setup deliverables (wait window, no spend)

Scaffolded `experiments/48_multiweights_omissive_bias/`:
- `notes.md` — hypothesis, falsifiable success criteria, design, battery, gates, ordered next steps.
- `probes/over_application_probes.{md,jsonl}` — **the over-application probe suite required
  BEFORE training** (methodology §5.6; over-application is the spec's headline risk). 70 prompts,
  7 categories (coding/factual/math/secular-practical/opted-out-interlocutor/hostile/creative).
  Category E (opt-out interlocutor) is the crux: blanket-vs-responsive tune reveals itself there.
  Scored with the AFB 0–4 judge verbatim; guard headline = P(score≥3) sermonizing fraction.
- `data/input/afb/` — vendored AFB instrument (150 Qs + official scorer, MIT).

Verified: gemma collection is a **config-only** change (SubjectSpec base_url/api_key_env seam
in `workflows/judging/judging/config.py`; `collect.py` globs traditions). Corpus = 519 scenarios,
sunni-islam 140 dominant → per-tradition balancing needed after banding.

Next (no spend): port taqwabench Modal scripts + write dormant gemma run config; ask architect
for OpenRouter key to verify the gemma-4-31b slug (else plan self-serve vLLM collection).

### De-risked the collection/training seams (research, no spend)
- **Run-config format nailed.** `configs/openrouter-funded-run.yaml` (the config CURRENTLY
  running the framings expansion) already uses the `provider: openai` + `base_url` +
  `api_key_env: OPENROUTER_API_KEY` seam. Gemma collection = a SEPARATE config
  (`gemma-collection.yaml`, subject `google/gemma-4-31B-it`, framings `[guided, unstated]`),
  run AFTER the expansion finishes. **Do NOT touch the live config.** Self-serve vLLM route is
  the same seam with `base_url` → a Modal-served OpenAI endpoint (doesn't exist yet).
- **SFT transform understood.** taqwabench `build_sft_guided.py` bands guided sittings
  (Gemini full-scope AND turn-1 band ≥ +1), screens guide-refs + dangling `[n]` markers,
  re-renders bare. It's keyed to taqwabench's judgment schema (`probe_id`, `split_70_70.json`).
  MultiBench differs: `scenario_id` + tradition, NO split (train on all 519). → adapt the
  builder AFTER collection produces our judgment records + add per-tradition balancing.

**Waiting state (clean):** setup committed (2b1e654), report + routing question sent to
architect. Blocked on: (a) green-light for gemma collection [framings expansion still running],
(b) architect's OpenRouter-vs-self-serve-vLLM routing call. Modal training ports deferred —
speculative ahead of the samplability GATE. Ending turn to stay reachable; will resume on reply.

## 2026-08-04 — architect decisions round 2

**Probe suite: approved** with two tightenings (applied to `probes/`):
- cat E (opted-out interlocutor): guard = **P(score ≥ 1) ≈ base**, not just sermonizing —
  the user explicitly opted out, so even a passing mention violates the signal.
- cat F (hostile-to-religion): **comparative-vs-base only** — the prompt itself names religion,
  so absolute-zero is wrong by construction (README + table note added).

**ROUTE PIVOT (Waleed revised): gemma collection → OpenRouter funded key, NOT self-serve vLLM.**
- Verified slug `google/gemma-4-31b-it` ($0.10/$0.34 Mtok). **Never** the `:free` variant.
- Config-only: wrote dormant `configs/gemma-collection.yaml` (openai seam → openrouter base_url,
  api_key_env OPENROUTER_API_KEY). Mirrors the funded-run's proven pattern.
- 3 consequences recorded in notes.md: (1) same-stack base control (base gemma thru vLLM eval
  stack) ABSORBS the collection-vs-eval shift; (2) OpenRouter may serve a quantized host →
  record serving host from response metadata per call (verify field at smoke, don't guess);
  (3) my Modal/vLLM work = the eval stack + same-stack control, not wasted.
- Key: `set -a; source <taqwabench>/.env; set +a`. NEVER into repo/logs/PR.

**TIMING reset:** collection now shares the framings key+quota → collection AND banding both
wait for architect's word (mop-up done within hours). Earlier "smoke cleared now" is superseded
by the route pivot. Environment verified ready (Modal authed, hf secret + volumes exist).

**Waiting (clean):** dormant config + probe tightenings + notes committed. Nothing run, no spend.
Ending turn to stay reachable; resume the moment the architect gives the collection go-word →
first action is the `--limit 1` smoke (incl. serving-host field discovery).

## 2026-08-04 — SMOKE run (cleared by architect, OpenRouter, 2 cells, negligible)

**Smoke green.** `collect --limit 1` on sunni-islam via `configs/gemma-collection.yaml`:
`{"grid":1680,"written":1,"failed":0}`. (One run hung ~2min mid-turn — architect confirms a
local network flap in that window; the retry was clean.)

**Confirmed:** distillation transform is exact — guide lives in `context_prefix` outside the
turns; stored turns are bare scenario text; dropping `context_prefix` ⇒ exact unstated re-render.
No framing leak.

**Serving-host field (verified on a RAW response, not guessed):** OpenRouter returns top-level
`provider`; SDK surfaces `resp.provider`. **KEY FINDING: host varies PER CALL, even within one
sitting** — one 2-turn sitting served by Friendli (turn1) + DeepInfra (turn2). ⇒ per-CALL capture
is the right granularity; provenance = "own outputs as served by a MIX of hosts."

**Provenance patch APPLIED** — `providers.py::_openai_subject`, 12 lines, stashes `resp.provider`
into the per-turn usage dict. Backward-compatible (only on the OpenRouter path); safe by the
existing non-int `usage["batch"]` precedent (`report._add_usage` sums only the token whitelist).
**Judging suite: 182 passed, 9 skipped, 0 failed.** Diff sent to architect for review.

**Still HELD:** full collection + Gemini banding wait for the architect's word (framings mop-up
mid-pass, roman-catholicism backfilling). Nothing else run.

**Architect decisions 2026-08-05:** (1) provenance diff APPROVED as written (committed 74b58aa);
(2) host-mix policy = ACCEPT & DOCUMENT, NO host pinning — judge-filter + samplability robust to
mild quant variance, same-stack control covers eval; obligation: record per-call provider
distribution as a table when collection runs (placeholder added to notes.md); revisit if one host
dominates pathologically or the mix looks wrong at the samplability stage. (3) Holds unchanged —
mop-up pass 2 mid-flight; collection + banding word comes when it lands clean.

Documented the policy + a fill-at-collection provider-distribution table in notes.md. Holding.

## 2026-08-05 — GO: full collection running

Architect cleared full collection (guided + unstated, all 7 traditions) at concurrency 32; banding
to follow on completion; report actual spend (~$10–20). Launched **background driver `b3w8q535y`**
(`scratchpad/collect_driver.sh`) — per-tradition resumable collect that rides the network-flap
waves (re-run on failed>0, bail a tradition after 3 no-progress attempts). Output →
`data/output/collection/<tradition>/sittings.jsonl` (gitignored). Verified alive (buddhism writing
within seconds). Will be re-invoked on completion → then: aggregate the per-call provider
distribution table, compute actual spend, report, and (on the banding go-word, already cleared)
run Gemini banding → samplability diagnostic (HARD GATE, report histogram before training).

Capability baseline in from taqwabench (no regression; GSM8K improved 0.792→0.867 at sft) — logged
in the battery table as the lm-eval reference for the capability-guard step. No action now.

Turn ending to stay reachable while collection runs in the background.

## 2026-08-05 — COLLECTION COMPLETE (clean)

Driver `b3w8q535y` exit 0. All 7 traditions done on **attempt 1**, `failed=0`, **no flap retries**.
**6,228 sittings** (3,114 guided + 3,114 unstated, exact). 12,456 calls, **0 missing provider**
(provenance patch 100%). **Actual spend ≈ $3.97** (tokens in 10.85M / out 8.25M / cache 8.0M).
Provider mix: Parasail 49.4% across 14 hosts — not pathological (table in notes.md).

Next: (a) report done+spend to architect [done]; (b) Gemini banding [RUNNING — driver brdqip0tm];
(c) samplability diagnostic = the HARD GATE.

## 2026-08-05 — Gemini banding launched (driver brdqip0tm)

Architect PRE-AUTHORIZED up to $250 for full both-framings dual-scope banding (12,456 judgments;
unstated bands double as gemma's benchmark baseline). MultiBench note: judge emits **bare −1…+1
scores** (5 canonical: −1,−0.5,0,0.5,1), NOT taqwabench "bands" — so the SFT filter's "band ≥ +1"
must translate to this score scale in the builder adaptation (noted for the SFT-build step).

**My cost estimate** from a 4-sitting judge smoke (8 judgments, canonical scores, guided→+1 /
unstated→0 signal): **$0.0122/judgment → ~$151 for the full 12,456** (below the architect's ~$240;
likely lower — the static rubric caches across the full run, cache_read=0 in the smoke's distinct
scenarios understates the saving). Within the $250 authorization.

Launched banding driver **brdqip0tm** (per-tradition `judge`, resumable, rides flap waves), output
→ `data/output/collection/<tradition>/judgments.jsonl` (gitignored). Verified alive. On completion:
report actual banding spend, then run the **samplability diagnostic** (HARD GATE) and report the
per-tradition histogram before any training.

## 2026-08-05 — BANDING COMPLETE + core findings (at the samplability gate)

12,456 judgments, all attempt 1, failed=0. **Actual banding ≈ $165.70** (my est $151 undershot ~10%
— gemini/OpenRouter cached less than hoped; cache_read only 1.56M). **Total spend so far ≈ $169.67.**
Within the $250 auth. Full tables in notes.md. Headlines:
- **Guided ceiling HIGH everywhere** (guided full mean +0.773, 86% at +1.0) — distillation source is
  rich; spec §8 low-ceiling risk did NOT materialize.
- **Unstated-under-pressure NEGATIVE** (−0.230, 51% at −1.0) — the omission/headroom.
- **SFT pool = 2,733** (≥+0.5 both scopes; ==+1.0 → 2,586, only 147 fewer). Keeping ≥+0.5 (default);
  balancing is the real lever (sunni-islam 641 + e-christianity 622 = 46% of pool).
- **Samplability preview (single-shot proxy) tracks difficulty:** hard RC 18.6% / Islam 21.2%, easy
  Buddhism 56.7% / Taoism 53.8%; total 34.3% good — richer than taqwabench's near-zero.

Reporting to architect + proposing the K=4 samplability-diagnostic design/spend before running it
(it's THE gate; single-shot data is a proxy). Stage-1 distillation is warranted + safe regardless.

## 2026-08-05 — architect decisions round 4 + no-spend prep

Architect: (1) Option A APPROVED (~$45) — run scoped K=4 exactly as designed; (2) SFT = full 2,733
pool, ≥+0.5, NO balancing (pool is corpus-representative — document proportions); (3) histogram is
the formal gate, plan same-turn training go if it matches the preview: histogram → go → SFT ~$5 →
eval baseline → DPO.

Actions:
- **Samplability K=4 sampler RUNNING** (driver `bm0a8blp0`, `samplability_sample.py`). Design:
  519 scenarios × 1 rotated pressure × K=4 unstated, base gemma temp 1.3, OpenRouter, 90s timeout +
  retries. → band full-scope → per-tradition "ever-good-across-4" histogram.
- **Proportions table added** to notes.md: pool share ≈ corpus share (sunni+EC 46.2% pool vs 47.4%
  corpus; sunni actually under-represented). Confirms no-balancing.
- **SFT set BUILT** (`build_sft_multibench.py`): 2,732 examples (2,733 − 1 guide-ref screen, 0
  dangling). Gitignored, sha256 06fa6d0d. Ready for post-gate training.

Waiting on the samplability sampler to complete → band → report histogram to architect (the gate).

## 2026-08-05 — samplability sampling COMPLETE, banding running

Sampling done (driver bm0a8blp0): **2,076 sittings** (519×4 exact per tradition), 0 failed
(flap-slowed, ~2h15m). Launched **full-scope banding** (driver brdclkzz5, `configs/samplability.yaml`
scopes:[full], ~$25 est). Verified alive. On completion → compute the per-tradition
"ever-good-across-4" histogram (fraction of scenarios with ≥1 of 4 samples good, ≥+0.5 full) +
the K=4 score distribution → **report to architect = the formal training gate.**

## 2026-08-05 — SAMPLABILITY HISTOGRAM (THE GATE) — reported, awaiting training go

Banding done (brdclkzz5), 2,076 full-scope judgments. Histogram (never-good = all 4 bad, taqwabench
75%): overall **55% never-good** — severe where it matters (sunni-islam 71%, roman-catholicism 67%),
free on easy traditions (buddhism 29%, taoism 33%). K=4 dist bimodal (51.9% at −1.0, 24.3% at +1.0).
**VERDICT: stage-1-first CONFIRMED mandatory** (DPO-on-base flat where the tune needs to work);
DPO-on-SFT unaffected (anchored on distilled policy). Gradient tracks difficulty exactly — clean
mechanism figure. Samplability spend $32.31 (sampling $1.18 + banding $31.12). **Total ≈ $201.98.**

**HARD GATE: reported the histogram to the architect. STOP — waiting for the explicit training go
before SFT.** On go: SFT ~$5 (2,732-example set, already built, sha256 06fa6d0d) → eval baseline → DPO.

## 2026-08-05 — GATE PASSED, TRAINING GO — SFT launching

Architect: GATE PASSED. Cleared SFT + eval sweep; AFB judge-of-record decided = **gpt-5.6-terra**
(OpenRouter, disclosed). Remaining gate = report SFT results + K=4-from-distilled mining yield
BEFORE DPO.
- Ported `modal/modal_gemma_sft.py` (recipe unchanged; deviations: scenario_id field, 683 steps for
  2,732 ex, +limit smoke knob). Uploaded set to gemma-dpo `/pairs/sft_guided_mb.jsonl`.
- **SFT smoke RUNNING** (b4iliggjl, mb-sft-smoke, 4 ex/1 ep) to de-risk the 6h full run. On smoke
  pass → launch full SFT `--detach` (background) → post-SFT eval sweep → checkpoint-before-DPO gate.
- **⚠️ Budget flagged:** SFT is ~$30-45 (8.6× taqwabench's data), remaining path ≈ $300-320 total,
  modestly over the $300 plan — flagged to architect to trim scope if they want to hold $300.
- **Architect ruled: keep 2 epochs + keep AFB faith-context condition, accept ~$315** (recipe
  fidelity > 5% over plan). Proceed full SFT on smoke-pass. Waiting on smoke b4iliggjl → then launch
  full `--detach`, report launch, run eval sweep, hit the pre-DPO checkpoint gate.

## 2026-08-05 — SFT smoke PASSED, full SFT training, eval harness built

Smoke b4iliggjl: **selective-head parity EXACT** (-534.878 vs -534.878), r32 engaged (244M/0.78%),
peak 27.8GB, max len 1323 (no truncation), adapter saved. Clean.
**FULL SFT training** — detached Modal `ap-USfALZXIo0BV5o2gA4TKEZ` (task bt77gq0cv, notifies at end),
mb-sft-guided, 2,732 ex × 2 ep = 683 steps, ~6h. Survives flaps.
**Eval harness BUILT during the window** (all syntax-checked, no spend): serve_gemma_eval.py (vLLM
OpenAI base+sft LoRA), eval_afb_probes.py (AFB-150 cold+faith + 70 probes, gpt-5.6-terra judge),
modal_gemma_capability.py (ported lm-eval panel). MultiBench-descriptive = collect.py config at run
time. Post-SFT: deploy serve → capability ∥ AFB+probes ∥ MultiBench descriptive → pre-DPO checkpoint.

Waiting on SFT (bt77gq0cv). Spend ~$202 + SFT accruing.

## 2026-08-05 — SFT run 1 CANCELLED by flap; fixed (spawn) + relaunched

**Incident:** SFT run 1 (`--detach` + `remote()`) was CANCELLED at **step 470/683** (~69%, epoch 2)
when the local client hit a DNS crash (`[Errno 8] nodename nor servname` — the network flap) and a
cancellation signal propagated to the function. `--detach`+`remote()` did NOT survive the abnormal
client death. Loss was excellent (nll 3.56 → ~0.47), so the recipe is validated — but no adapter
saved (volume dir empty) → full re-run needed (no mid-train checkpoint).
**Fix (taqwabench's drop-survival pattern): `--detach` + `.spawn()`** — spawn fully decouples the
function from the client; `--detach` keeps it alive after the entrypoint exits / client drops.
(Interim mistake: `modal run` WITHOUT `--detach` + spawn → ephemeral app tore down on entrypoint
exit, Tasks=0. Need BOTH `--detach` AND spawn.)
**Run 3 (app ap-3IotDJLAfHEUQL1CPaE2aS, call fc-01KZ9NKQXD9ZGX0N43YZY3B9X4): running (ephemeral,
Tasks=1), detached.** Completion poller `bisvachvg` watches the volume for config.json.
**Cost impact:** run 1 burned ~4h H200 (~$20-25 wasted); re-run adds ~$30. SFT total ~$50-60 →
experiment likely ~$320-340 total (over the $300 plan, mostly the wasted run). Flagged to architect.
Architect acked: spawn() fix right, surfaced ~$320-340 to Waleed, proceed; stop at pre-DPO checkpoint.

**DPO script PREPPED with resumable checkpointing** (architect: add before launching DPO, note as
deliberate deviation from taqwabench parity justified by 6h/run × real money). `modal/modal_gemma_dpo2.py`:
DPO machinery unchanged (β0.1, lr1e-5, 1ep, ref=SFT); ADDED periodic policy-adapter checkpoint every
100 steps + resume.json + vol.commit; RESUME loads policy from the last checkpoint and fast-forwards
the seed-deterministic shuffle (skips the init-equality check on resume); --detach+spawn launch;
scenario_id field. Syntax-checked. Won't run until after the pre-DPO gate (needs the mined pairs).
SFT run 3 (ap-3IotDJ...) still alive; poller bisvachvg watching.

## 2026-08-05 — full-state checkpointing added to SFT; B200 deferred

Architect extended: add FULL-state checkpointing to the SFT script too (adapter + optimizer state +
epoch/data-position + RNG state, + `--resume-from`). Done in `modal/modal_gemma_sft.py` (every 100
steps → adapter + `train_state.pt`{opt, order, pos, epoch, py/torch/cuda RNG} + vol.commit; resume
restores all and fast-forwards). Live run 3 NOT touched (it uses its mounted snapshot; edits are for
future runs). DPO currently has lighter (adapter+position) checkpointing — will ALIGN it to the same
full-state scheme (optimizer+RNG) when I finalize DPO at the pre-DPO gate (avoids churning unreviewed
code now; DPO won't run until then).

**B200 decision (architect):** stay on H200 for this SFT run AND DPO by default (bnb/Blackwell kernel
risk). If DPO wall-clock justifies, PROPOSE a B200 smoke test at the pre-DPO checkpoint — do not
switch unilaterally. Noted; will assess DPO wall-clock from the SFT step timing and raise at the gate.

## 2026-08-05 — RECIPE CHANGE (Waleed): nf4 → bf16 LoRA + B200

Waleed: KILL the nf4 SFT re-run, switch to **bf16 LoRA (no bitsandbytes anywhere)** — nf4 is a
reproducibility confound; accept losing exact taqwabench numeric parity (document as deliberate
human-directed deviation). Addendum: run bf16 SFT + DPO on **B200** (Blackwell); image bumped to
CUDA 12.8 + torch cu128 for sm_100; smoke doubles as B200 compat check. Expect ~2× H200 (~2h, $6.25/hr).

Done: killed nf4 run 3 (was at step 105, loss ~0.58); cleared stale `/runs/mb-sft-guided`; converted
BOTH `modal_gemma_sft.py` + `modal_gemma_dpo2.py` to bf16 (drop BitsAndBytesConfig +
prepare_model_for_kbit_training → bf16 load + gradient_checkpointing_enable + enable_input_require_grads),
gpu="B200", cu128 image. main() blocks (remote) for smokes, spawns for full runs. Syntax-checked.
**Sunk cost nf4 ~$25–28** (run1 ~$20-25 + run3 ~$2 + smoke ~$1).
**bf16 B200 smoke PASSED** (brntikm8q): torch 2.11.0+cu128 ran clean on B200 (no sm_100/kernel
errors → Blackwell compat CONFIRMED); grad-checkpointing active, LoRA r32 (244M/0.78%), selective-head
parity ok (−492.4 vs −493.1), loss sane (nll 3.56), **peak 63.2GB** (huge headroom on 192GB B200).
**FULL bf16 SFT LAUNCHED** — detached app ap-WB9C8dtq4lYQ1o7AkXD8fn, run mb-sft-guided, 2 ep = 683
steps, B200, ~2h expected. Poller bisvachvg (watches /runs/mb-sft-guided/config.json) still alive →
notifies at completion. Next: report to architect; on completion → eval sweep → pre-DPO checkpoint.

## 2026-08-05 — SFT COMPLETE; eval sweep launched

SFT `mb-sft-guided` done: 683 steps, 2 ep, **loss 2.64 → 0.47**, adapter saved, peak 65.5GB, ~1h48m,
clean. (On-disk config.json has a stale "nf4" quant label — actual = bf16; fixed the string in both
scripts, noted.) Fixed the quant-label string; committed.
**Eval sweep launched:**
- Eval server DEPLOYED: `https://waleedkadous--multibench-gemma-eval-serve-serve.modal.run/v1`
  (base = `google/gemma-4-31B-it`, sft = `sft`). Warming (bfmjm501j, cold-start ~10min).
- Capability panel RUNNING (b98pm4tbs, detached): lm-eval ifeval+mmlu+gsm8k on base + mb-sft-guided.
- On warm → run `eval_afb_probes.py` (AFB-150 cold+faith + 70 probes, gpt-5.6-terra judge).
- MultiBench-descriptive (collect via the endpoint, gemini judge) = optional bonus.
Then assemble base-vs-SFT table → **pre-DPO checkpoint report** (SFT results + K=4 mining yield).

## 2026-08-05 — eval sweep in flight (3 parallel jobs); mining plan

Server warm (base 425s cold-start, sft instant). Three parallel eval jobs running:
- **b98pm4tbs** — capability panel (lm-eval ifeval+mmlu+gsm8k, base + sft).
- **bhjbo1vrm** — AFB-150 (base+sft × cold+faith) + 70 over-application probes, gpt-5.6-terra judge.
- **bewydkbql** — MultiBench-descriptive: collect sft unstated via endpoint + gemini full-scope judge,
  all 7 traditions (compare per-tradition to existing base bands → the 3-tier gradient for Waleed).

**Mining plan for the pre-DPO gate (cost-aware):** full K=4-from-SFT mining over all 3,114 cells +
banding would be ~$150 judging — too much to spend before the gate. Plan: run a **mining PILOT**
(K=4 from the sft endpoint at temp on a subset), band, count within-cell max-gap pairs (gap ≥ 2) →
report the **yield estimate** (+ per-tradition) at the checkpoint, and let the architect green-light
the full mining spend. Mining sampler = adapt `samplability_sample.py` (sample model="sft" via the
endpoint at temp instead of base). Build after evals land.

Spend ~$217 + B200 SFT (~$12) + evals accruing. Next: assemble SFT eval table when the 3 jobs land.

## 2026-08-05 — SFT eval results landing

**AFB HEADLINE (gpt-5.6-terra):** base/cold mean 0.113 (P≥2=0.01) → sft/cold mean 1.147 (P≥2=**0.27**,
i.e. 1%→27% meaningful). Omission substantially reduced, beats the 0-2% ceiling. Nuance: bimodal,
18% spike at 4 (over-shoot for DPO to temper). Faith condition saturated (both ~4.0). Over-application
guard CLEAN: secular probes exactly 0.00 both; opted-out mild +0.10 (minor). Full tables in notes.md.
**CAPABILITY:** GSM8K +3.0, IFEval −1.1 (~flat), MMLU **−2.3** (mild dip). Base matches taqwabench's.
Essentially capability-preserving. Reported AFB to architect.
**DESCRIPTIVE:** first run FAILED (endpoint contention — AFB + descriptive hammering one H200 →
timeouts; buddhism gave up). Killed it, lowered concurrency 32→16, re-ran (bytpoy7m5) with the
endpoint now dedicated (AFB+capability done). Cold-start latency but no errors; collecting. Will
compute per-tradition base-vs-sft gradient on completion.
Next: on descriptive done → assemble full table → build+run K=4 mining pilot → pre-DPO checkpoint.

## 2026-08-06 — descriptive root cause fixed; mining pilot running

**Descriptive failures root-caused (BOTH runs):** NOT contention — the SubjectSpec default
`max_tokens=16384` == the endpoint's `max_model_len=16384`, so vLLM 400s ("requested 16384 output
tokens"). AFB worked because its runner sets max_tokens=1024. Fix: `max_tokens: 4096` on the subject
in `multibench_descriptive.yaml`. Verified (2 written, 0 failed). Descriptive re-running (bij4m15e7),
writing cleanly.
**Mining pilot BUILT + RUNNING (bjef48nqd):** `mine_dpo_sample.py` (K=4 from the SFT endpoint at
temp 1.3, per cell) + `build_dpo_pairs.py` (within-cell max-gap pairs, gap ≥ 1.0 = taqwabench's
≥2 rungs → yield). PILOT = 10 scenarios/tradition (1,680 sittings) for a cheap yield estimate before
the architect green-lights full mining. Both jobs share the endpoint (64-concurrent capacity; the
earlier failures were the max_tokens bug, not contention). On both done → band mining → yield table →
assemble pre-DPO checkpoint report.

## 2026-08-06 — checkpoint report: THREE scoped options (architect steer)

Architect corrected my lean cut: capability MUST re-run on +DPO (MMLU −2.3 is the watch item, only
~5); the right cut is SKIP descriptive re-run (judge-heavy, non-claim) + SKIP AFB faith-context
(saturated). Present three options with plain-digit totals (final numbers pin to the mining yield):
1. **stop-at-SFT** ≈ 280 (current 260 + pilot banding ~20 to produce the yield figure for the decision).
2. **DPO + lean battery** (AFB-150 cold + probes + capability on +DPO; skip descriptive + faith) ≈
   340–360 (current 260 + mining pilot-band 20 + scoped full-mining ~30-50 + DPO B200 ~7 + lean eval ~22).
3. **DPO + full battery** (adds descriptive re-run + faith) ≈ 390–420 — over the 320-340 gate.
Decision waits for the yield + descriptive numbers. SFT alone already delivers the headline
(P≥2 1%→27%), so stop-at-SFT is a real option.

**CEILING RAISED to 400 USD all-in (Waleed, 2026-08-06, supersedes 320-340).** Option 2 (DPO+lean
~340-360) comfortably inside; option 3 (DPO+full ~390-420) viable ONLY if it pins ≤400 — price
precisely from the pilot yield. Keep all three options; architect decides at the checkpoint.
Progress: descriptive 4/7 traditions clean (1,692 sit / 1,673 jud, 0 failed); mining sampling
1,506/1,680. On both done → band mining → yield → assemble checkpoint report.

**LEAN CONFIRMED (Waleed, 2026-08-06): stage-2 evals = AFB-150 cold + 70 probes + capability ONLY.
DROP option 3.** Checkpoint is now a TWO-WAY decision: **stop-at-SFT (~280)** vs **DPO+lean
(~340-360)**, gated on mining yield + total ≤400. Writeup note: SFT-stage MMLU (−2.3) is a
trajectory HINT only — **post-DPO capability is the number of record.**

## 2026-08-06 — mining sampled (1,680, 0 failed); banding + descriptive running

Mining pilot sampling DONE: 1,680 sittings (240/tradition = 10 scen × 6 press × K4), 0 failed.
Banding it full-scope (gemini) — driver **birz2e9au** (~1,680 judgments ≈ 20 USD, the pilot-band cost).
Descriptive **bij4m15e7** at 5/7 traditions (1,762/3,114 judgments, 0 failed; secular-sage/sunni/taoism left).
On mine-band done → `build_dpo_pairs.py` → per-tradition yield + projected full-mining cost.
On descriptive done → per-tradition base-vs-SFT gradient. Then assemble the two-way checkpoint report.

## 2026-08-06 — PRE-DPO CHECKPOINT COMPLETE (all data in) — STOPPED for architect decision

All four items in hand (full tables in notes.md):
1. **AFB headline** base 0.113 (P≥2 0.01) → SFT 1.147 (P≥2 **0.27**), 1%→27% meaningful. Bimodal 18% at 4.
2. **Capability** GSM8K +3.0, IFEval −1.1, MMLU −2.3 (trajectory hint). **Over-application** secular=0.00 both.
3. **Descriptive gradient** flips ALL 7 traditions positive; HARD tier −0.501→+0.436 (Δ+0.94), ALL −0.138→+0.652.
4. **Mining yield** 38% (158/420 pilot), ~632 pairs scoped (40/trad flat, +65). Low-yield=uniformly-good (benign).
**Spend 280.** Two-way: STOP-AT-SFT ~280 vs DPO+LEAN ~374 (≤400). **STOPPED — awaiting architect decision.**
Do NOT proceed to DPO without the explicit go.

## 2026-08-06 — GO: DPO+LEAN approved; stage-2 executing

Architect GO (overnight authority, 400 ceiling). Locked params: scoped mining 40 scen/tradition flat
(pilot-10 reused + 30 seeded-random seed 3446); DPO bf16 B200 anchored at SFT ref, resumable+detach/spawn;
lean battery = AFB-150 cold + 70 probes + capability. HARD ceiling 400 — stop+ping if any actual threatens.
Watch items for +DPO evals: (1) MMLU not worse past −2.3; (2) opted-out P≥1 0.70→toward 0.60; (3) 4-spike
temper toward 1-2 WITHOUT losing P≥2=0.27.

Budget track: 280 → scoped-mining band +65 (→345) → DPO +7 (→352) → lean eval +22 (→374). 26 headroom.

- Updated `mine_dpo_sample.py` selection rule (scoped_scenarios: pilot-10 + seeded-random). **Scoped
  mining sampling RUNNING (b2333x6t6)** — sampling the 30 new scen/tradition (pilot dedup'd). On done →
  band new sittings (full-scope gemini, ~60) → `build_dpo_pairs.py` (~632 pairs) → upload → DPO run.

Scoped mining sampled: 6,720 total (960/tradition = 40×6×4), 5,040 new + 1,680 pilot reused, 0 failed.
Banded (bp6oiay0z). **Pairs built: 487** (29% yield — lower than pilot's 38%, more representative;
sunni-islam contributes most, 98). Uploaded to `/pairs/pairs_sft2_mb.jsonl`.
**DPO RUNNING** (ap-HkapoJeENOdk3jxoCSKptM, bf16 B200, SFT ref, mb-sft-dpo); 487 pairs, max len 2102;
~61 steps. Poller b41aytc13.

**BUDGET UPDATE (actuals):** mining band ACTUAL = 100 total / ~75 for the new 5,040 (vs 60 est).
Current ≈ **360**. Projected final: DPO ~7 + lean eval ~12 = **~379** (under 400, ~20 margin — tighter
than the ~374 quoted). Flagged to architect (transparency; not threatening the ceiling). Lean eval is
the last discretionary spend.

## 2026-08-06 — DPO done (weak signal); lean battery next
DPO mb-sft-dpo: 61 steps, pref_acc ~0.538 (near chance), loss flat ~0.73 → WEAK signal (SFT already
good → little contrast to sharpen; opposite of taqwabench's high-pref-flat trap). Redeployed serve
with dpo model, warming (br51m6irr) → then lean battery (AFB cold + probes on dpo, capability --only
mb-sft-dpo). +DPO eval is the arbiter; likely ≈ SFT. Budget ~367; lean ~12 → ~379. Watch items: MMLU,
opted-out P≥1, 4-spike vs P≥2.

## 2026-08-06 — DELIVERABLE DECISION RULE (architect, locked)
Ship whichever adapter is WEAKLY BETTER on the lean battery. DPO preferred ONLY if non-regressing on
ALL of (AFB P>=2, secular leakage 0.00, opted-out, MMLU). If DPO moves nothing → SFT is the named
MultiWeights deliverable; DPO documented as a NULL stage with pref_acc 0.538 evidence + the
samplability/uniformly-good mechanism (interpretable null = good null). NO respin with different
hyperparams without pinging (respin unjustified by a mechanism we understand; budget ~379). Waiting on
dpo warmup (br51m6irr) → lean battery → apply rule → name deliverable → report.

## 2026-08-06 — EXPERIMENT COMPLETE + budget overshoot (owned)
DELIVERABLE: mb-sft-dpo (two-stage SFT+DPO) is the weakly-better head — all 4 gates pass: AFB P>=2
0.27->0.30, secular 0.00, opted-out 0.70->0.60, MMLU 0.4435->0.4424 (flat). IFEval improved
(0.2602->0.2770). DPO's weak pref_acc (0.538) still sharpened the intended axes.
⚠️ FINAL SPEND ~432, OVER the 400 hard ceiling by ~32. Cause (owned): rolling estimates OMITTED the
descriptive judging (~45) and mining band came in at 100 (vs 60-75 est); true base into DPO+lean was
~305 not 280. All spend REALIZED (jobs done). Tracking failure: should have reconciled computed-from-
usage actuals before the mining-band spend. Flagged to architect immediately on discovery.

## 2026-08-06 — WRAP-UP: figures + integration PR
Paper figures (no-spend, uv run --with matplotlib from saved data, MB paper style): (a) AFB-150 cold
distribution base/SFT/DPO grouped bars + P>=2 per head; (b) per-tradition base->SFT unstated-mean
gradient dotplot, tier-ordered. Vector PDFs in experiments/.../figures/. Visually verified.
Review doc at codev/reviews/48-*.md. Integration PR #52 opened (base main) — run outputs/datasets
excluded per gitignore. Spend FROZEN throughout wrap-up (all from on-disk data + local matplotlib).
EXPERIMENT COMPLETE. Deliverable mb-sft-dpo on the gemma-dpo volume.
