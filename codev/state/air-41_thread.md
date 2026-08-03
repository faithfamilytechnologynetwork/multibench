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
