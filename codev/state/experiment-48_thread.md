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
