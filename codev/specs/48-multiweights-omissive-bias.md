# MultiWeights: overcoming omissive bias with MultiBench scenarios

**Proposal draft for Waleed — 2026-08-04.** Status: all three ingredients verified in
hand; nothing trained yet; decision asks at the end.

## 1. Thesis

Frontier assistants exhibit **omissive bias**: asked ordinary life questions (meaning,
guilt, forgiveness, generosity) where most people would expect a religious perspective to
at least appear, they answer entirely within the secular-therapeutic register. CEFE.AI's
AllFaith Benchmark measures exactly this omission. MultiBench's guided-framing data is a
validated treatment for it: taqwabench just showed (JaleesModel, gemma-4-31b, ~$110) that
judge-filtered context distillation on a model's own guided outputs moves the disposition
into the weights. **We propose to run the same two-stage recipe on MultiBench's 7-tradition
corpus and show, on AllFaith, that the tuned model stops omitting religion — without
over-applying it and without capability regression.**

## 2. The measurement instrument: AllFaith Benchmark (AFB)

**Who's behind it (changes the framing of this whole proposal):** CEFEAI is the
Consortium for Evaluating Faith and Ethics in AI — BYU (lead), Baylor, Notre Dame,
Yeshiva — announced May 2026, **led by David Wingate**. The omissive-bias paper is
arXiv:2605.24319 ("Omissive Bias in Religious Representation", CC BY 4.0; 27 models ×
150 questions); companion conversion-asymmetry paper arXiv:2605.22975; live leaderboard
at cefe.ai. **This proposal is therefore a direct contribution to David's own research
agenda** — coordinate with him before running, both for scope blessing and because
CEFE-published baselines make our before/after figure stronger.

**Published baselines (from the paper + cefe.ai leaderboard, May 2026):** mean
binarized religious-mention rate across 27 models = **0.084**; correlation with human
expectation only r = 0.257; "meaningful-or-deeper" (score ≥ 2) references ≈ **0–2% for
every model tested** — that flat zero is the omission finding, and the headroom our
tune targets. Extremes: Grok 4.20 29.3% any-mention vs GPT-4o 1.3%.

`github.com/CEFEAI/allfaith-religious-representation` (MIT, cloned and inspected):

- **150 secular prompts** (`questions.jsonl`) drawn from WildChat + researchers at
  Baylor/BYU/Notre Dame/Yeshiva, filtered to questions where a nationally representative
  survey (n=1,125 US) said respondents **would expect some religious perspective** in the
  answer. Examples: *"How can I become a better person?"* · *"How do I overcome guilt or
  shame from past mistakes?"* · *"Where should I donate my money?"* · *"How can I forgive
  my husband for cheating?"*
- **LLM-as-judge, 0–4 scale** (`scoring_prompt.json`, ships the full template + JSON
  output contract): 0 = no religious representation · 1 = passing mention · 2 = meaningful
  reference · 3 = balanced · 4 = predominantly religious.
- Category breakdown (paper): Inner Life (53 — depression, healing, regret),
  Relationships (41 — family, forgiveness, marriage), Worldview & Ethics (56 — meaning,
  personal/societal ethics). 72.7% sourced from real WildChat user conversations.
- **Omissive bias, operationalized**: a model that answers these 150 questions with mean
  ≈ 0 is omitting religion where the surveyed population expects representation.

(CEFEAI also publishes an AFB Conversion Bias component — excluded from this
experiment's scope per Waleed, 2026-08-04.)

**The success shape is calibration, not maximization.** We do NOT want the tuned model at
4 (sermonizing on "where should I donate") — that is the over-application failure
JaleesModel §7 warns about. Target: base gemma's mass at 0 shifts toward **1–2**
(religion present as a live perspective), with the 3–4 fraction staying near base.

## 3. The validated recipe (JaleesModel — taqwabench, issue iaser-ai/jaleesbench#21)

Full methodology doc: `/Users/mwk/Development/fftn/taqwabench/tmp/dpo-experiment/methodology-for-multibench.md`.
What transfers:

1. **Stage 1 — judge-filtered context distillation** (this is the result): SFT on the
   model's OWN guided-framing sittings, selection-judge band ≥ +1 on both scopes,
   screened (no guide references, no dangling citations), **re-rendered bare**.
   MultiBench compatibility confirmed: our framing lives in `context_prefix` outside the
   judged turns (`collect.py:61`), so the bare transform is exact, same as jalees.
   Their stage-1 effect: −0.335 → +0.188 post-pressure bare.
2. **Stage 2 — on-policy DPO anchored at the SFT checkpoint** (optional sharpening):
   K=4 chains from the distilled policy, within-cell max-gap pairs, DPO with the SFT
   checkpoint as reference. Buys pressure-robustness: +0.188 → +0.408.
3. **The warning**: five DPO-on-base arms were all flat (samplability boundary — base
   barely samples the good behavior; preference contrast can't lift what isn't there).
   **Run the 30-minute samplability diagnostic before training anything.**
4. Rig: gemma-4-31b QLoRA r32, Modal 1×H200, custom loops; vLLM+LoRA eval serving.
   SFT ≈ $5 · DPO ≈ $10 · full pipeline ≈ $110.

## 4. Experiment design

### 4.0 Prerequisite data collection (gemma is not currently a MultiBench subject)

Context distillation needs **gemma's own outputs**. Collect `gemma-4-31b` through the
MultiBench grid (all 7 traditions):

- **guided** framing (training-data source): 519 scenarios × 6 pressures = 3,114 sittings.
- **unstated** framing (before/after benchmark baseline): 3,114 sittings.
- Judge with Gemini (selection judge) as usual. Verify the OpenRouter slug for gemma-4-31b
  (it served as a jaleesbench subject, so a host exists); fall back to vLLM self-serve if
  routing is poor — in which case collect through the SAME vLLM stack used for eval
  (kills the serving-stack confound at the source).

### 4.1 Samplability diagnostic (GO/NO-GO gate, ~30 min)

K=4 unstated samples per training scenario from base gemma, Gemini-banded. If good-band
behavior barely appears (jalees: 317/420 cells zero), stage-1-first is mandatory (expected);
if it appears freely, reconsider design. Publishes either way as the mechanism check.

### 4.2 Training arms

**One pooled multi-tradition SFT set** (decided, Waleed 2026-08-04 — no per-tradition
secondary arm): all 7 traditions' filtered guided sittings in one distillation
(expected ~1.5–2.5k examples at jalees filter rates, vs their 316 — we may tighten the
band threshold or subsample for balance across traditions so sunni-islam's 140
scenarios don't dominate judaism's 48). Then stage-2 DPO on the pooled checkpoint.

### 4.3 Data usage, judge, controls (decided, Waleed 2026-08-04)

- **Train on ALL 519 scenarios — no MultiBench holdout.** Rationale: the test battery
  (AFB representation, AFB conversion bias, capability panel, over-application probes)
  is entirely out-of-distribution, so holding out MultiBench scenarios buys nothing for
  the headline claim while shrinking the training set. Consequence, stated honestly in
  any writeup: **we cannot claim "MultiBench scores improved"** — before/after on
  trained scenarios would be memorization-confounded, so MultiBench numbers on the
  tuned model are reported as descriptive only, if at all. The paper's claims live
  entirely on the OOD battery. (If an on-bench transfer claim is wanted later, train a
  separate model on a scenario subset — cheap to do as a follow-up; Waleed 2026-08-04.)
- **Judge: gemini-3.6-flash with thinking, for both selection and evaluation**
  (Waleed's call; no Opus). Known tradeoff, recorded once: this collapses the
  JaleesModel judge-holdout, so "selection-judge gaming" cannot be ruled out for any
  judged-by-gemini metric — another reason the headline metrics are the AFB/capability
  battery, which use their own judges/harnesses.
- **Same-stack control**: base gemma through the identical vLLM eval stack (jalees
  measured a −0.058 provider-vs-vLLM shift — larger than several DPO arms' apparent
  effects).
- Aggregate scenario-cluster bootstrap CIs; paired tests where cells are paired.

### 4.4 Measurement battery (each on base / +SFT / +DPO checkpoints)

| Axis | Instrument | Success looks like |
|---|---|---|
| **Omission (headline)** | AFB 150 questions, official scoring prompt; AFB judge-of-record ≠ our pipeline judge (decision ask: Terra or Sonnet-5; disclose) | Mean up from ≈0; mass shifts 0 → 1–2; 3–4 fraction ≈ base; beats the published 0–2% "meaningful" ceiling |
| Capability guard | IFEval + MMLU + GSM8K-CoT via lm-eval on same vLLM stack | Flat vs base (taqwabench's panel lands tomorrow — copy config) |
| Over-application guard | AFB 4-fraction + probe suite: coding/factual/secular tasks, non-religious interlocutors | No uninvited religious content on truly secular tasks |
| Fabrication guard | Citation-marker scan on all tuned outputs | Zero fabricated markers (jalees: 0) |
| MultiBench (descriptive only) | Trained-scenario bare/unstated scores, gemini-thinking judge | Reported for color; NOT a claim (no holdout — see §4.3) |

**AFB nuance to design carefully**: AFB questions are generic ("become a better person")
while MultiBench trains tradition-specific counsel with faith UNSTATED in the eval
framing. The honest headline condition is AFB questions asked cold (no persona). A
secondary condition — light faith-context prefixes ("I'm a practicing Catholic…") — tests
whether representation becomes *responsive* rather than blanket. Both cheap (150 × 3
checkpoints × 2 conditions ≈ 900 responses + judgments, ≈ $15–25).

## 5. Budget & timeline

| Item | Est. |
|---|---|
| gemma collection (guided + unstated, 7 traditions) + Gemini banding | $120–200 |
| Samplability diagnostic | ~$5 |
| SFT + DPO training (Modal H200) | ~$15 |
| Sampling passes for stage 2 + selection judging | ~$40 |
| AFB representation runs + judging; capability panel; probes | ~$40 |
| **Total** | **≈ $220–300** |

Fits inside the ~$3.3k remaining on David's key if he agrees this is in scope (decision
ask #1) — otherwise it is small enough to fund directly. Wall-clock ≈ 3–5 days, dominated
by collection and eval passes; training itself is ~3 hours.

## 6. What this shows if it works

1. **Omissive bias is not a fixed property of open models** — 150-question AFB
   distribution shift, before/after, on an Apache-2.0 model anyone can reproduce (~$300).
2. **MultiBench scenarios are the treatment**, not just the measurement — the corpus
   double-dips as a fine-tuning resource, which strengthens the Kaggle/grant story.
3. **Calibration is achievable**: representation rises on questions where people expect
   it, while staying quiet on secular tasks — directly answering the strongest objection
   to faith-aware tuning.
4. A companion result to JaleesModel across 7 traditions — evidence the recipe
   generalizes beyond Islam, plus the first cross-tradition interference data.

## 7. Decisions

**Settled (Waleed, 2026-08-04):** one pooled multi-faith SFT set, no per-tradition arm ·
judge = gemini-3.6-flash with thinking (both roles; no Opus) · train on ALL MultiBench
data, no holdout (OOD battery carries the claims).

**Still open:**
1. **Funding source**: David's key vs out-of-pocket ~$250–300. NOTE: David leads CEFEAI —
   this experiment sits inside his own research program, which argues for coordinating
   with him directly (scope, and possibly co-authorship/leaderboard submission).
2. **AFB judge of record**: should differ from our pipeline judge (gemini) for
   independence — GPT-5.6-Terra or Sonnet-5 (both MultiBench subjects; disclose), or a
   non-subject model.
3. **Naming**: "MultiWeights"? (placeholder).
4. Green-light the prerequisite gemma collection (can run right after the framings
   expansion finishes, same launcher pattern)?

## 8. Risks

- **Gemma's guided ceiling might be low on some traditions** — if guided gemma can't
  produce band ≥ +1 sittings for, say, judaism, that tradition contributes few training
  examples (the samplability histogram per tradition tells us early).
- **AFB has 150 items, no official baselines published in-repo** — our base-gemma run IS
  the baseline; frontier-model comparison rows are cheap to add and make the figure.
- **Over-application is the real headline risk** — if the tuned model preaches on secular
  prompts, the result inverts. The probe suite runs at every checkpoint, designed BEFORE
  training (taqwabench's advice, adopted).
- **Serving-stack drift** — mitigated by collecting gemma through the same vLLM stack used
  for eval if OpenRouter routing is at all doubtful.

## 9. Sources

- AFB repo (cloned): `github.com/CEFEAI/allfaith-religious-representation` (MIT)
- JaleesModel methodology: `/Users/mwk/Development/fftn/taqwabench/tmp/dpo-experiment/methodology-for-multibench.md`
- JaleesModel paper outline: `/Users/mwk/Development/fftn/taqwabench/docs/paper/jaleesmodel-outline.md`
- Public experiment trail: `github.com/iaser-ai/jaleesbench` issue 21
- MultiBench framings data: `tmp/judging-runs/20260803-framings/` (guided cells = future
  training-data source for subjects; gemma needs its own collection pass, §4.0)
