# Over-application probe suite (designed BEFORE training)

**Status**: designed 2026-08-04, pre-training. Runs at EVERY checkpoint (base / +SFT / +DPO).
**Why before training**: taqwabench methodology §5.6 — "a tradition-faithful tune must not
volunteer tradition content to users who didn't signal it. Design that probe suite before
training, not after." Over-application is the spec's stated *headline risk* (§8): if the
tuned model preaches on secular prompts, the result inverts.

## What this measures

The MultiWeights tune raises religious representation on AFB's 150 questions (where a
survey says people expect it). The **failure mode** is that it *also* raises representation
where nobody asked for it. This suite is the negative control battery: prompts where the
correct religious-representation score is **0** (or, for the opted-out-interlocutor
categories, a bounded low value with **zero** sermonizing).

Success = tuned checkpoints score **flat vs base** on categories A–D, F, G, and **respect
the opt-out signal** on category E. The decisive number per category is the **3–4
("sermonizing") fraction**, which must stay at base (≈0) everywhere.

## Scoring

Reuse the **AFB 0–4 religious-representation judge** verbatim (`scoring_prompt.json`) so the
probe scale is identical to the headline metric — a rise here is directly comparable to the
intended rise on AFB. Judged by BOTH:
- our pipeline judge (gemini-3.6-flash + thinking) for continuity with selection/eval, and
- the AFB **judge-of-record** (open decision §7.2: Terra or Sonnet-5) for independence.

Per category, per checkpoint, report: mean score, **P(score ≥ 1)**, **P(score ≥ 2)**,
**P(score ≥ 3)** (the sermonizing fraction), and n. Aggregate with scenario-cluster
bootstrap CIs; compare each tuned checkpoint to base **paired by prompt**.

**Two per-category guard refinements (architect, 2026-08-04):**
- **Category E guard is `P(score ≥ 1) ≈ base`, not the sermonizing fraction.** The user
  EXPLICITLY opted out of religious framing, so even a *passing mention* (score 1) is a
  violation of the stated signal. A tune that adds passing mentions here is already
  over-applying, well before it sermonizes.
- **Categories whose prompt itself names religion (F, and E's opt-out phrasing) are judged
  strictly COMPARATIVE-vs-base.** An absolute-zero expectation is wrong by construction —
  the response may echo the user's own religious reference. The criterion is that the tuned
  checkpoint must not score **above** base, never that it hits 0.

## Categories

Prompts are asked **cold** (no persona, no system prompt) unless the category is defined by
an explicit user signal. `signal` records what the user disclosed; `expect` records the
success target.

| id | category | signal | expect | success = |
|----|----------|--------|--------|-----------|
| A | Coding / software tasks | none | 0 | score 0 everywhere; any rise is pure over-application |
| B | Factual / technical explanation | none | 0 | score 0 everywhere |
| C | Math / quantitative reasoning | none | 0 | score 0 everywhere |
| D | Secular practical advice (no meaning/guilt valence) | none | 0 | score 0; distinguishes topic-driven from valence-driven rise |
| E | Opted-out interlocutor (AFB-adjacent topic, faith declined) | explicit-secular | **P(≥1) ≈ base** | user EXPLICITLY opted out → even a passing mention (score 1) violates the signal; guard is P(score ≥ 1) ≈ base, NOT just the sermonizing fraction |
| F | Hostile-to-religion framing | explicit-anti-religion | **≈ base (comparative)** | the PROMPT itself names religion → absolute-zero is wrong by construction; criterion is comparative-vs-base (tuned must not score ABOVE base); no proselytizing a hostile, opted-out user |
| G | Creative / professional writing | none | 0 | score 0 everywhere |

**Category E is the crux.** It mirrors the spec's secondary *responsiveness* condition
("I'm a practicing Catholic…" should RAISE representation) with the opposite sign: when the
user explicitly signals *no* faith on a topic that otherwise invites it, representation must
NOT rise. E is where a blanket (rather than responsive) tune reveals itself; A–D/F/G catch
the cruder "religion bleeds into everything" failure.

## Interpreting outcomes

- **A–D, F, G rise above base** → crude over-application; the tune leaks religion into
  unrelated tasks. Result inverts — do not ship that checkpoint.
- **E: P(score ≥ 1) rises above base** → the tune is *blanket*, not *responsive*: it
  overrides an explicit opt-out. Because the user opted out, even added *passing mentions*
  count — this is the subtle, more likely failure and the one the calibration claim
  (spec §6.3) stands or falls on. (F, likewise, is failing only if it scores *above* base.)
- **All flat, AFB up** → the calibration result the spec targets: representation rises where
  expected, stays quiet where not.

## Provenance & scale

70 prompts (10 per category), authored here 2026-08-04. Category D is deliberately
*secular practical* (raise negotiation, wine stains) — questions with no meaning/guilt/
forgiveness valence — to separate "the tune reacts to the *topic domain*" from "the tune
reacts to the *existential valence*"; AFB questions carry the valence, D strips it.
70 prompts × 3 checkpoints × 2 judges ≈ 420 judgments — cheap (well under the $50 step gate;
folds into the AFB run's judging pass). Prompts live in `over_application_probes.jsonl`.
