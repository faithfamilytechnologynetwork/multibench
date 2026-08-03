# air-43 — OpenRouter live judge path + caching + timeouts + pricing

Protocol: AIR (strict). Issue #43 (amended 2026-08-03).

## Scope journey
- Original #43: OpenRouter migration + upgradeable Opus judge subsample (`scenario_fraction`).
- Architect HELD work: baked decision "OpenRouter has no batch API" was WRONG.
- Amended #43: subsample DROPPED; new scope = OpenRouter batch judging + cache_control fwd + timeouts.
- I assessed amended scope as ~450 LOC w/ tests + a new persisted-state batch subsystem + a
  cache-through-batch risk gate → recommended ASPIR escalation.
- **Architect split-approved**: #43 = live slice only (pieces 1/3/4/5); batch subsystem → #44 (ASPIR, after merge). DO NOT touch batch code (batching.py).

## This PR (#43) scope — live slice only (~100 LOC non-test)
1. Live OpenRouter judge path: add `_openai_judge` branch to `judge_complete`; `openai` in
   `_JUDGE_PROVIDERS`; `base_url`/`api_key_env` on `JudgeSpec`.
3. cache_control forwarding for `anthropic/*` slugs on the openai judge path (OpenRouter forwards
   Anthropic caching only if breakpoints are sent).
4. HTTP timeouts on ALL live provider calls (providers.py only; batch client is #44). 300s.
5. `PRICES`/`PRICES_DATED` OpenRouter slugs in report.py.

## Key facts verified
- SDKs: google-genai 1.60 (HttpOptions.timeout = **ms**), anthropic 0.96 (timeout=s), openai 2.37 (timeout=s).
- No API keys in env → live smokes need OPENROUTER_API_KEY from architect (subject via OR + gemini judge live).
- openai SDK passes through unknown content-block keys (cache_control survives) — how OR caching works via openai client.

## Surface touched (for aspir-44 coordination)
- `config.py`: JudgeSpec +`base_url`/`api_key_env`; `openai` added to `_JUDGE_PROVIDERS`; `_spec`/`_JUDGE_FIELDS` updated.
- `providers.py`: new `REQUEST_TIMEOUT_SECONDS=300.0`; new `_openai_judge` + `_openai_judge_content`;
  `judge_complete` routes `openai`; timeouts on anthropic/openai clients + `_gemini_client` (ms);
  `_openai_usage` now splits `prompt_tokens_details.cached_tokens` -> `cache_read`.
- `report.py`: PRICES += 6 OpenRouter slugs (opus-4.8, sonnet-5, gemini-3.6-flash, gpt-5.6-terra,
  qwen3-235b-a22b-2507, thinkingmachines/inkling); PRICES_DATED note. **aspir-44: I added a delimited
  OpenRouter block at the END of PRICES — merge should be clean if you append elsewhere.**
- **Did NOT touch batching.py** (batch is #44). openai judges fall through batch submit to live fallback.
- New: `workflows/judging/configs/openrouter-funded-run.yaml` (documents slugs/hosts/caching).

## Verified facts
- OpenRouter forwards Anthropic caching: 1h write 2x, read 0.1x (matches `_usage_cost`); `ttl:"1h"` works. [openrouter.ai/docs prompt-caching]
- Slugs verified on openrouter.ai pages: `anthropic/claude-opus-4.8` (DOT, $5/$25), `anthropic/claude-sonnet-5` ($2/$10 intro),
  `google/gemini-3.6-flash` ($1.50/$7.50), `openai/gpt-5.6-terra` ($2/$12 list, 50% promo), `qwen/qwen3-235b-a22b-2507` ($0.09/$0.55 host-dep), `thinkingmachines/inkling` ($0.95/$4.05, IS on OR).
- cache_control survives openai SDK RUNTIME transform (`maybe_transform`) even though the stricter TypeAdapter strips it — anti-mock test asserts both paths.

## Status
- Code + tests DONE. 178 pass, 6 skipped (pre-existing live tests). Committing.
- BLOCKER for PR: live smokes (subject via OpenRouter + Gemini judge live) need OPENROUTER_API_KEY (not in env) — will ask architect.
- OPEN RISK to confirm in smoke: (a) exact opus slug dot vs hyphen; (b) response_format json_schema strict + numeric `score` enum through OpenRouter/Gemini.
