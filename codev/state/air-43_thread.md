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

## LIVE SMOKE EVIDENCE (2026-08-03, via OpenRouter; numbers only, no secrets)
All 3 PASS. Command: `pytest workflows/judging -m live --live -k openrouter -s`.
- Subject `qwen/qwen3-235b-a22b-2507`: text='ok', usage in=14 out=2 cache_read=3.
- Judge  `google/gemini-3.6-flash`: score=1.0 (real rationale), usage in=2713 out=466.
- Judge  `anthropic/claude-opus-4.8` (cache): first cache_read=3799, second cache_read=3799.
  => **cache_control forwarding WORKS through OpenRouter on the LIVE path** (cache_read>0).

## FOR ASPIR-44 (batch): live path de-risks your cache gate
- Anthropic 1h cache_control breakpoints (rubric+anchor) forwarded via the openai-compat seam DO
  produce cache_read>0 through OpenRouter live. Your batch smoke (§3) should expect the same; if
  batch does NOT show cache_read>0, that's the STOP-and-report signal (live path proves it's possible).
- Resolved RISK: Google (via OpenRouter) rejects numeric `score` enum + additionalProperties. The
  openai judge path now sanitizes schema for `google/*` (string-enum, drop unsupported, strict=False,
  cast score back to float). anthropic/*/openai/* use raw strict schema. Batch requests to Google
  would hit the same — reuse this sanitization if you batch Gemini (you likely won't; Gemini isn't batched).
- Opus slug confirmed: `anthropic/claude-opus-4.8` (DOT) works live via OpenRouter.

## Integration review (REQUEST_CHANGES) — ADDRESSED (commit 37331b6)
1. `_openai_judge` honors judge.thinking (forwards OpenRouter `reasoning.enabled` via extra_body —
   OR infers from model default if omitted, so set explicitly) + judge.safety_off (raises loudly;
   OR has NO Google safety passthrough). Funded config: Gemini judge -> DIRECT gemini + safety_off.
2. PRICES corrected vs live models API: terra 1.00/6.00, qwen 0.15/0.60, inkling 1.00/4.05;
   sonnet basis documented; case-dup {I,i}nkling now identical rate + commented.
3. _openai_usage: honest cache-WRITE understatement note (writes billed 2x land in `in` at 1x);
   removed the _usage_cost parity claim.

## Re-run smoke evidence (after reasoning change; numbers only)
- Subject qwen: text='ok', priced. Gemini judge (openai path): score=1.0 in=2588 out=527.
- Opus cache: first in=4146 (WRITE), second in=347 cache_read=3799 (READ) — shows write->read AND
  the understatement (3799 write toks in `in` @1x). Opus out rose to 630/673 (reasoning now ON).

## ⚠️ ARCHITECT DECISION PENDING (flagged in PR): Gemini judge routing
OpenRouter can't forward Google safety_settings; Gemini judge needs safety-off (§5.5). Funded config
defaults to DIRECT gemini provider (safety-off, bills GEMINI_API_KEY not OpenRouter key). Alternatives:
(a) safety-ON Gemini via OpenRouter (refusal risk), (b) drop Gemini judge. Defaulted to spec-correct.

## FOR ASPIR-44 (batch) — updated
- `_openai_judge_content` + `_to_gemini_schema` are module-level/importable — reuse for batch bodies.
  Google needs the schema sanitize (string-enum) + safety-off is NOT forwardable via OpenRouter.
- Reasoning must be set EXPLICITLY in batch bodies too (`reasoning.enabled`), else model-default.
- Cache WRITE tokens not surfaced on OpenRouter openai-compat usage — your batch cache evidence should
  rely on cache_read (proven >0 live).

## Status — PR OPEN, at PR gate (awaiting human approval)
- **PR #45**: https://github.com/faithfamilytechnologynetwork/multibench/pull/45 (body updated w/ review responses).
- Suite: 182 pass, 9 skipped. porch check: PASSED. Still at GATE: pr — STOPPED, will NOT self-approve.
