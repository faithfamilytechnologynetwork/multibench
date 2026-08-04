# experiment-48 — MultiWeights (omissive bias / gemma-4-31b fine-tune)

Soft-mode EXPERIMENT builder. Spec: `codev/specs/48-multiweights-omissive-bias.md`.

## 2026-08-04 — startup & orientation

Read spec + taqwabench methodology doc
(`/Users/mwk/Development/fftn/taqwabench/tmp/dpo-experiment/methodology-for-multibench.md`)
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
- Key: `set -a; source /Users/mwk/Development/fftn/taqwabench/.env; set +a`. NEVER into repo/logs/PR.

**TIMING reset:** collection now shares the framings key+quota → collection AND banding both
wait for architect's word (mop-up done within hours). Earlier "smoke cleared now" is superseded
by the route pivot. Environment verified ready (Modal authed, hf secret + volumes exist).

**Waiting (clean):** dormant config + probe tightenings + notes committed. Nothing run, no spend.
Ending turn to stay reachable; resume the moment the architect gives the collection go-word →
first action is the `--limit 1` smoke (incl. serving-host field discovery).
