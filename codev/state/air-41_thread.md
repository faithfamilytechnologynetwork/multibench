# air-41 — Judging: add Terra/Inkling/Qwen subject providers + refresh pricing

Protocol: AIR (strict). Issue #41.

## Plan
Prep for next judging run: 5 subjects, faith-unstated, single Gemini judge.

Design:
- `providers.py` currently supports only `anthropic` subjects and `anthropic`/`gemini` judges.
- Add a **generic OpenAI-compatible subject provider** (`provider: "openai"`) with per-subject
  `base_url` + `api_key_env` config — covers GPT-5.6 Terra, Inkling, Qwen3-235B (issue says this
  is the preferred impl).
- Add a **Gemini subject** path (issue §2: Gemini 3.6 Flash must work as subject AND judge).
  Subjects are NEVER run safety-off.
- Config plumbing: `SubjectSpec` gains `base_url`/`api_key_env`; widen `_SUBJECT_PROVIDERS` to
  `("anthropic","openai","gemini")`; validate new fields in loader.
- Add `openai` dep to pyproject.
- Refresh `PRICES`/`PRICES_DATED` in report.py with verified rates (research agent running).
- Tests: unit fail-loud + real-client contract per provider; live smoke gated behind `--live`.

## Notes
- Gemini 3.6 Flash as judge = pure config (model id string); batching already falls Gemini→live.
- Blinding design (§4.5): fold framing onto EVERY user turn as a context prefix, never a system
  prompt. No privileged channel for any subject.
- Fail-fast on missing env keys (N4) — no fallbacks.
- Pricing research dispatched to background agent (verified rates + cited URLs for PR body).

## Implemented
- providers.py: `_openai_subject`/`_openai_messages`/`_openai_usage` (generic OpenAI-compat) +
  `_gemini_subject`/`_gemini_contents` (subject seam, never safety-off). Dispatch widened.
- config.py: SubjectSpec +base_url/+api_key_env; providers anthropic|openai|gemini; `_opt_str`.
- report.py: PRICES + verified gpt-5.6-terra ($2/$12), gemini-3.6-flash ($1.5/$7.5); qwen3-235b
  flagged UNVERIFIED; inkling deferred to host choice.
- openai dep added.
- Tests: fail-loud + real-SDK-param contract per provider; config-file parsing; live smokes.
- ~150 prod LOC (AIR-sized). Suite: 164 passed / 6 skipped. porch check green.

## Pricing gaps flagged to architect (afx send)
- INKLING: no first-party API/price (open-weights) — needs a host decision. Not in PRICES yet.
- QWEN3-235B: rate unconfirmable on official Alibaba page; using aggregator ~$0.455/$0.90, flagged.
- Could NOT run live smokes: NO provider creds in builder env. Operator must run before benchmark.

## PR phase
- Pushing branch + opening PR with review + pricing citations in body.
