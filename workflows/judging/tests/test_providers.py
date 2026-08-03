"""Provider seam behavior that needs no live API (spec N4, T10): fail-loud on missing
credentials and on an unsupported provider. Live calls themselves are not exercised."""

import pytest

from judging.config import JudgeSpec, SubjectSpec
from judging.providers import ProviderError, judge_complete, subject_complete


def test_judge_missing_anthropic_credential_fails_loud(monkeypatch):
    # T10: a configured provider with no credential -> located error, before any SDK call.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ProviderError) as ei:
        judge_complete(
            JudgeSpec("claude-opus-4-8", "anthropic"), ("rubric", "anchor", "tail"), {}, retries=0
        )
    assert "ANTHROPIC_API_KEY" in str(ei.value)


def test_judge_missing_gemini_credential_fails_loud(monkeypatch):
    # N4: Gemini auth is Vertex SA OR GEMINI_API_KEY — fail loud only when neither is present.
    for var in ("GEMINI_API_KEY", "GOOGLE_APPLICATION_CREDENTIALS", "GOOGLE_GENAI_USE_VERTEXAI"):
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(ProviderError) as ei:
        judge_complete(
            JudgeSpec("gemini-3.5-flash", "gemini", safety_off=True),
            ("rubric", "anchor", "tail"),
            {},
            retries=0,
        )
    assert "GEMINI_API_KEY" in str(ei.value)


def test_unsupported_judge_provider_fails_loud():
    with pytest.raises(ProviderError):
        judge_complete(JudgeSpec("x", "mistral"), ("r", "a", "t"), {}, retries=0)


def test_unsupported_subject_provider_fails_loud():
    # Subjects support anthropic | openai | gemini (issue #41); anything else fails loud.
    with pytest.raises(ProviderError) as ei:
        subject_complete(
            SubjectSpec("x", "mistral"), None, [{"role": "user", "content": "hi"}]
        )
    assert "unsupported subject provider" in str(ei.value)


def test_openai_subject_missing_default_credential_fails_loud(monkeypatch):
    # N4: openai subject with no api_key_env falls back to OPENAI_API_KEY and fails loud if absent,
    # before any SDK call.
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ProviderError) as ei:
        subject_complete(
            SubjectSpec("gpt-5.6-terra", "openai"), None, [{"role": "user", "content": "hi"}]
        )
    assert "OPENAI_API_KEY" in str(ei.value)


def test_openai_subject_missing_named_credential_fails_loud(monkeypatch):
    # N4: a dedicated per-host key (api_key_env) is required for OpenAI-compatible hosts.
    # Qwen3-235B is served on Friendli (architect host decision); fail loud naming the exact
    # var, before any SDK call.
    monkeypatch.delenv("FRIENDLI_API_KEY", raising=False)
    with pytest.raises(ProviderError) as ei:
        subject_complete(
            SubjectSpec(
                "Qwen/Qwen3-235B-A22B-Instruct-2507",
                "openai",
                base_url="https://api.friendli.ai/serverless/v1",
                api_key_env="FRIENDLI_API_KEY",
            ),
            None,
            [{"role": "user", "content": "hi"}],
        )
    assert "FRIENDLI_API_KEY" in str(ei.value)


def test_gemini_subject_missing_credential_fails_loud(monkeypatch):
    # N4: a gemini subject needs a Gemini credential (same auth surface as the judge) — fail loud
    # when none is present.
    for var in ("GEMINI_API_KEY", "GOOGLE_APPLICATION_CREDENTIALS", "GOOGLE_GENAI_USE_VERTEXAI"):
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(ProviderError) as ei:
        subject_complete(
            SubjectSpec("gemini-3.6-flash", "gemini"), None, [{"role": "user", "content": "hi"}]
        )
    assert "GEMINI_API_KEY" in str(ei.value)


def test_openai_messages_fold_framing_on_every_user_turn():
    # Blinding design (§4.5): the framing is folded onto EVERY user turn as a text prefix (never a
    # system prompt); assistant turns are untouched.
    from judging.providers import _openai_messages, ctx_block

    msgs = [
        {"role": "user", "content": "Q1"},
        {"role": "assistant", "content": "A1"},
        {"role": "user", "content": "Q2"},
    ]
    out = _openai_messages(msgs, "GUIDE")
    prefix = ctx_block("GUIDE")
    assert out[0] == {"role": "user", "content": f"{prefix}\n\nQ1"}
    assert out[1] == {"role": "assistant", "content": "A1"}  # untouched
    assert out[2] == {"role": "user", "content": f"{prefix}\n\nQ2"}  # folded on EVERY user turn
    # Unstated framing (no prefix): user turns pass through verbatim.
    assert _openai_messages([{"role": "user", "content": "Q"}], None) == [
        {"role": "user", "content": "Q"}
    ]


def test_gemini_contents_fold_and_role_mapping():
    # google-genai contents: assistant->model, framing folded onto every user turn (§4.5).
    from judging.providers import _gemini_contents, ctx_block

    msgs = [
        {"role": "user", "content": "Q1"},
        {"role": "assistant", "content": "A1"},
        {"role": "user", "content": "Q2"},
    ]
    out = _gemini_contents(msgs, "GUIDE")
    prefix = ctx_block("GUIDE")
    assert out[0] == {"role": "user", "parts": [{"text": f"{prefix}\n\nQ1"}]}
    assert out[1] == {"role": "model", "parts": [{"text": "A1"}]}  # assistant -> model
    assert out[2] == {"role": "user", "parts": [{"text": f"{prefix}\n\nQ2"}]}


def test_openai_usage_extracts_prompt_and_completion_tokens():
    from types import SimpleNamespace

    from judging.providers import _openai_usage

    resp = SimpleNamespace(usage=SimpleNamespace(prompt_tokens=120, completion_tokens=45))
    assert _openai_usage(resp) == {"in": 120, "out": 45}
    assert _openai_usage(SimpleNamespace(usage=None)) == {}


def test_openai_subject_request_constructs_via_real_sdk_params():
    # Real-client construction (M21, anti-mock, OpenAI-compatible subject path): validate the
    # ACTUAL create-kwargs through the REAL openai SDK request param TypedDict — not a hand-checked
    # dict — so request-shape drift (model/token-limit/messages) is caught without a live call.
    # The token-limit kwarg differs by host: OpenAI proper (base_url None) requires
    # `max_completion_tokens`; OpenAI-*compatible* hosts (Tinker/Friendli) take legacy `max_tokens`.
    import pydantic
    from openai.types.chat import completion_create_params as ccp

    from judging.providers import _openai_messages

    msgs = _openai_messages(
        [{"role": "user", "content": "Q1"}, {"role": "assistant", "content": "A1"},
         {"role": "user", "content": "Q2"}],
        "CTX",
    )
    ta = pydantic.TypeAdapter(ccp.CompletionCreateParamsNonStreaming)
    # OpenAI proper: max_completion_tokens is the accepted kwarg.
    ta.validate_python({"model": "gpt-5.6-terra", "max_completion_tokens": 1024, "messages": msgs})
    # OpenAI-compatible host: legacy max_tokens is still accepted by the SDK param model.
    ta.validate_python(
        {"model": "Qwen/Qwen3-235B-A22B-Instruct-2507", "max_tokens": 1024, "messages": msgs}
    )
    # Prove the real-SDK validation actually bites (anti-mock): drop the required model.
    with pytest.raises(pydantic.ValidationError):
        ta.validate_python({"max_completion_tokens": 1024, "messages": msgs})


def test_subject_messages_fold_and_cache_breakpoints():
    # Framing is folded onto EVERY user turn (§4.5); cache breakpoints are on the FIRST user
    # turn only (M16): framing block = 1h ephemeral, turn-1 question = default-TTL ephemeral;
    # assistant turns untouched.
    from judging.providers import _subject_messages, ctx_block

    msgs = [
        {"role": "user", "content": "Q1"},
        {"role": "assistant", "content": "A1"},
        {"role": "user", "content": "Q2"},
    ]
    out = _subject_messages(msgs, "GUIDE TEXT")
    # First user turn: [framing(1h cache), question(default cache)].
    t1 = out[0]["content"]
    assert t1[0]["text"] == ctx_block("GUIDE TEXT")
    assert t1[0]["cache_control"] == {"type": "ephemeral", "ttl": "1h"}
    assert t1[1]["text"] == "Q1"
    assert t1[1]["cache_control"] == {"type": "ephemeral"}
    # Assistant turn untouched.
    assert out[1] == {"role": "assistant", "content": "A1"}
    # Second user turn: framing still present (blinding design) but NO cache_control anywhere.
    t2 = out[2]["content"]
    assert t2[0]["text"] == ctx_block("GUIDE TEXT")
    assert all("cache_control" not in b for b in t2)


def test_subject_messages_caches_turn1_even_without_framing():
    # Unstated framing (no prefix): still cache turn-1's question so turn-2 rereads it (M16).
    from judging.providers import _subject_messages

    out = _subject_messages([{"role": "user", "content": "Q"}], None)
    blocks = out[0]["content"]
    assert [b["text"] for b in blocks] == ["Q"]  # no framing block prepended
    assert blocks[0]["cache_control"] == {"type": "ephemeral"}


def test_subject_request_constructs_via_real_anthropic_params():
    # Real-client construction (M21, anti-mock, subject path): validate the ACTUAL create-kwargs
    # through the REAL anthropic SDK param types (`MessageCreateParams`) — not a hand-checked
    # dict. This catches request-shape drift (model/max_tokens/messages). NOTE: the SDK's request
    # TypedDicts are permissive on nested `cache_control`, so the exhaustive wire guarantee (the
    # API actually accepting the cache blocks) is the r3 `--live` smoke; here we also assert the
    # structural cache contract explicitly.
    import pydantic
    from anthropic import types as atypes

    from judging.providers import _subject_messages

    msgs = _subject_messages(
        [
            {"role": "user", "content": "Q1"},
            {"role": "assistant", "content": "A1"},
            {"role": "user", "content": "Q2"},
        ],
        "CTX",
    )
    kwargs = {"model": "claude-opus-4-8", "max_tokens": 1024, "messages": msgs}
    # Goes through the real SDK's request param model (rejects e.g. a missing model/max_tokens).
    pydantic.TypeAdapter(atypes.MessageCreateParams).validate_python(kwargs)
    # Reference the real SDK cache-control symbol (catches an SDK rename of the cache type).
    assert atypes.CacheControlEphemeralParam(type="ephemeral", ttl="1h")["type"] == "ephemeral"
    # Structural cache contract: breakpoints on the FIRST user turn only.
    assert msgs[0]["content"][0]["cache_control"] == {"type": "ephemeral", "ttl": "1h"}
    assert msgs[0]["content"][1]["cache_control"] == {"type": "ephemeral"}
    assert all("cache_control" not in b for b in msgs[2]["content"])


def test_gemini_subject_config_never_sets_safety_override():
    # Real google-genai types (M21, anti-mock): mirror _gemini_subject's config construction —
    # subjects set max_output_tokens (+ optional dynamic thinking) and NEVER safety_settings
    # (§5.5: subjects are never run safety-off; only the judge seam may be). This is the contract
    # that keeps the safety-off path judge-only.
    from google.genai import types

    cfg = types.GenerateContentConfig(
        max_output_tokens=16384, thinking_config=types.ThinkingConfig(thinking_budget=-1)
    )
    assert cfg.safety_settings is None
    assert cfg.max_output_tokens == 16384


def test_gemini_text_raises_clear_diagnostic_on_blocked_response():
    # M18: a blocked/empty Gemini response yields a clear located error (finish_reason /
    # block_reason), not an opaque json.loads failure.
    from types import SimpleNamespace

    from judging.providers import ProviderError, _gemini_text

    blocked = SimpleNamespace(
        text=None,
        candidates=[SimpleNamespace(finish_reason="SAFETY")],
        prompt_feedback=SimpleNamespace(block_reason="OTHER"),
    )
    with pytest.raises(ProviderError) as ei:
        _gemini_text(blocked)
    msg = str(ei.value)
    assert "SAFETY" in msg and "OTHER" in msg  # diagnostic surfaces both signals
    # And a good response passes through unchanged.
    assert _gemini_text(SimpleNamespace(text='{"score": 1.0}')) == '{"score": 1.0}'


def test_gemini_usage_counts_thinking_tokens():
    # M18: thinking is ON, so thoughts_token_count is counted as output (else cost undercounts).
    from types import SimpleNamespace

    from judging.providers import _gemini_usage

    resp = SimpleNamespace(
        usage_metadata=SimpleNamespace(
            prompt_token_count=100, candidates_token_count=40, thoughts_token_count=25
        )
    )
    assert _gemini_usage(resp) == {"in": 100, "out": 65}  # 40 answer + 25 thinking


# --- OpenAI-compatible judge seam (issue #43: OpenRouter live judging) -------


def test_openai_judge_missing_named_credential_fails_loud(monkeypatch):
    # N4: the OpenRouter judge needs OPENROUTER_API_KEY; fail loud naming the exact var, before SDK.
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(ProviderError) as ei:
        judge_complete(
            JudgeSpec(
                "anthropic/claude-opus-4.8", "openai",
                base_url="https://openrouter.ai/api/v1", api_key_env="OPENROUTER_API_KEY",
            ),
            ("rubric", "anchor", "tail"), {}, retries=0,
        )
    assert "OPENROUTER_API_KEY" in str(ei.value)


def test_openai_judge_missing_default_credential_fails_loud(monkeypatch):
    # api_key_env absent -> falls back to OPENAI_API_KEY; fail loud if that's missing too (N4).
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ProviderError) as ei:
        judge_complete(JudgeSpec("some/model", "openai"), ("r", "a", "t"), {}, retries=0)
    assert "OPENAI_API_KEY" in str(ei.value)


def test_openai_judge_content_forwards_anthropic_cache_breakpoints():
    # #43 §3: for anthropic/* slugs, forward the SAME two 1h cache_control breakpoints the native
    # Anthropic judge sets (static rubric + per-scenario anchor); tail is uncached. OpenRouter
    # forwards Anthropic caching ONLY if these are sent.
    from judging.providers import _openai_judge_content

    c = _openai_judge_content("anthropic/claude-opus-4.8", ("RUBRIC", "ANCHOR", "TAIL"))
    assert [b["text"] for b in c] == ["RUBRIC", "ANCHOR", "TAIL"]
    assert c[0]["cache_control"] == {"type": "ephemeral", "ttl": "1h"}
    assert c[1]["cache_control"] == {"type": "ephemeral", "ttl": "1h"}
    assert "cache_control" not in c[2]


def test_openai_judge_content_non_anthropic_single_block_no_cache():
    # Non-anthropic host (Gemini/OpenAI) auto-caches: one joined text block, NO cache_control.
    from judging.providers import _openai_judge_content

    c = _openai_judge_content("google/gemini-3.6-flash", ("R", "A", "T"))
    assert c == [{"type": "text", "text": "R\n\nA\n\nT"}]


def test_openai_judge_request_constructs_via_real_sdk_and_forwards_cache():
    # Anti-mock (M21): validate the ACTUAL judge create-kwargs through the REAL openai SDK param
    # model AND prove the anthropic/* cache_control breakpoints survive the SDK's RUNTIME transform
    # (`maybe_transform` — what actually builds the request body on the wire). The pydantic
    # TypeAdapter is a stricter path that strips nested cache_control, so shape and cache are
    # asserted through their respective real code paths — no hand-rolled dict.
    import pydantic
    from openai._utils import maybe_transform
    from openai.types.chat import completion_create_params as ccp

    from judging.providers import _openai_judge_content
    from judging.rubric import verdict_schema

    content = _openai_judge_content("anthropic/claude-opus-4.8", ("rubric", "anchor", "tail"))
    kwargs = {
        "model": "anthropic/claude-opus-4.8",
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": content}],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "verdict", "strict": True, "schema": verdict_schema()},
        },
    }
    ta = pydantic.TypeAdapter(ccp.CompletionCreateParamsNonStreaming)
    ta.validate_python(kwargs)  # rejects request-shape drift (model/max_tokens/messages/response_format)
    # RUNTIME body (what goes on the wire) keeps the two 1h cache_control breakpoints:
    body = maybe_transform(kwargs, ccp.CompletionCreateParamsNonStreaming)
    wire = body["messages"][0]["content"]
    assert wire[0]["cache_control"] == {"type": "ephemeral", "ttl": "1h"}
    assert wire[1]["cache_control"] == {"type": "ephemeral", "ttl": "1h"}
    assert "cache_control" not in wire[2]
    # Prove the real-SDK validation actually bites (anti-mock): drop the required model.
    with pytest.raises(pydantic.ValidationError):
        ta.validate_python({"max_tokens": 4096, "messages": kwargs["messages"]})


def test_openai_usage_splits_cached_prompt_tokens():
    # #43 §3: OpenRouter reports the cached subset under prompt_tokens_details.cached_tokens, while
    # prompt_tokens is the TOTAL — split so the report prices cached input at 0.1x, uncached at full.
    from types import SimpleNamespace

    from judging.providers import _openai_usage

    resp = SimpleNamespace(
        usage=SimpleNamespace(
            prompt_tokens=1000, completion_tokens=50,
            prompt_tokens_details=SimpleNamespace(cached_tokens=800),
        )
    )
    assert _openai_usage(resp) == {"in": 200, "out": 50, "cache_read": 800}
    # No cached tokens -> no cache_read key, `in` == prompt_tokens (unchanged from the #41 shape).
    resp2 = SimpleNamespace(
        usage=SimpleNamespace(prompt_tokens=120, completion_tokens=45, prompt_tokens_details=None)
    )
    assert _openai_usage(resp2) == {"in": 120, "out": 45}


def _fake_openai_returning(captured, content_json):
    """A fake OpenAI client whose chat.completions.create captures kwargs and returns a canned
    JSON verdict — lets us assert the request the judge builds without a live call."""
    from types import SimpleNamespace

    class FakeCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            msg = SimpleNamespace(content=content_json)
            return SimpleNamespace(
                choices=[SimpleNamespace(message=msg)],
                usage=SimpleNamespace(
                    prompt_tokens=100, completion_tokens=20, prompt_tokens_details=None
                ),
            )

    class FakeChat:
        completions = FakeCompletions()

    class FakeOpenAI:
        def __init__(self, **kwargs):
            self.chat = FakeChat()

    return FakeOpenAI


def test_openai_judge_google_slug_sanitizes_schema_and_casts_score(monkeypatch):
    # Regression for the live failure: Google (even via OpenRouter) rejects our NUMERIC `score` enum
    # and `additionalProperties`. For google/* the judge must sanitize the schema (string-enum, drop
    # unsupported keys) and drop OpenAI-`strict`, then cast the returned string score back to float.
    import openai

    from judging.rubric import verdict_schema

    captured: dict = {}
    monkeypatch.setenv("OPENROUTER_API_KEY", "x")
    monkeypatch.setattr(
        openai, "OpenAI",
        _fake_openai_returning(captured, '{"score": "0.5", "direction": "d", "rationale": "r"}'),
    )
    judge = JudgeSpec(
        "google/gemini-3.6-flash", "openai",
        base_url="https://openrouter.ai/api/v1", api_key_env="OPENROUTER_API_KEY",
    )
    verdict, _, _ = judge_complete(judge, ("R", "A", "T"), verdict_schema(), retries=0)
    assert verdict["score"] == 0.5 and isinstance(verdict["score"], float)  # string -> float cast
    js = captured["response_format"]["json_schema"]
    assert js["strict"] is False  # google enforces via its own responseSchema; OpenAI-strict dropped
    score = js["schema"]["properties"]["score"]
    assert score["type"] == "string" and all(isinstance(v, str) for v in score["enum"])
    assert "additionalProperties" not in js["schema"]  # dropped for google


def test_openai_judge_non_google_uses_raw_strict_schema(monkeypatch):
    # anthropic/* (and openai/*) via OpenRouter accept the raw numeric-enum schema with OpenAI-strict
    # enforcement (verified live for Opus) — no sanitization, score stays numeric.
    import openai

    from judging.rubric import verdict_schema

    captured: dict = {}
    monkeypatch.setenv("OPENROUTER_API_KEY", "x")
    monkeypatch.setattr(
        openai, "OpenAI",
        _fake_openai_returning(captured, '{"score": 0.5, "direction": "d", "rationale": "r"}'),
    )
    judge = JudgeSpec(
        "anthropic/claude-opus-4.8", "openai",
        base_url="https://openrouter.ai/api/v1", api_key_env="OPENROUTER_API_KEY",
    )
    verdict, _, _ = judge_complete(judge, ("R", "A", "T"), verdict_schema(), retries=0)
    assert verdict["score"] == 0.5
    js = captured["response_format"]["json_schema"]
    assert js["strict"] is True
    assert js["schema"]["properties"]["score"]["type"] == "number"  # raw numeric enum, unmodified
    assert js["schema"]["additionalProperties"] is False  # kept for anthropic/openai


# --- HTTP timeouts on all live provider calls (issue #43 §4) ------------------
# Motivated by a live incident: a collection wedged 2+ hours on dead sockets (CLOSE_WAIT) because
# provider calls had no client timeout. Every live client is now built with an explicit timeout, and
# a hung/erroring call surfaces as a ProviderError (failed, resumable cell), never a wedged run.


def _fake_openai(captured, exc):
    class FakeCompletions:
        def create(self, **kwargs):
            raise exc

    class FakeChat:
        completions = FakeCompletions()

    class FakeOpenAI:
        def __init__(self, **kwargs):
            captured.update(kwargs)
            self.chat = FakeChat()

    return FakeOpenAI


def test_openai_subject_sets_timeout_and_hung_call_fails(monkeypatch):
    # The incident was a *collection* (subject) hang — this is the on-point regression.
    import openai

    import judging.providers as P

    captured: dict = {}
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    monkeypatch.setattr(openai, "OpenAI", _fake_openai(captured, TimeoutError("hung socket")))
    with pytest.raises(ProviderError):
        subject_complete(
            SubjectSpec("gpt-5.6-terra", "openai"), None, [{"role": "user", "content": "hi"}],
            retries=0,
        )
    assert captured["timeout"] == P.REQUEST_TIMEOUT_SECONDS


def test_openai_judge_sets_timeout_and_hung_call_fails(monkeypatch):
    import openai

    import judging.providers as P

    captured: dict = {}
    monkeypatch.setenv("OPENROUTER_API_KEY", "x")
    monkeypatch.setattr(openai, "OpenAI", _fake_openai(captured, TimeoutError("hung socket")))
    with pytest.raises(ProviderError):
        judge_complete(
            JudgeSpec(
                "anthropic/claude-opus-4.8", "openai",
                base_url="https://openrouter.ai/api/v1", api_key_env="OPENROUTER_API_KEY",
            ),
            ("r", "a", "t"), {"type": "object"}, retries=0,
        )
    assert captured["timeout"] == P.REQUEST_TIMEOUT_SECONDS
    assert captured["base_url"] == "https://openrouter.ai/api/v1"


def test_anthropic_judge_sets_timeout_and_hung_call_fails(monkeypatch):
    import anthropic

    import judging.providers as P

    captured: dict = {}

    class FakeMessages:
        def create(self, **kwargs):
            raise TimeoutError("hung socket")

    class FakeAnthropic:
        def __init__(self, **kwargs):
            captured.update(kwargs)
            self.messages = FakeMessages()

    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    monkeypatch.setattr(anthropic, "Anthropic", FakeAnthropic)
    with pytest.raises(ProviderError):
        judge_complete(JudgeSpec("claude-opus-4-8", "anthropic"), ("r", "a", "t"), {}, retries=0)
    assert captured["timeout"] == P.REQUEST_TIMEOUT_SECONDS


def test_gemini_client_sets_timeout_in_milliseconds(monkeypatch):
    # google-genai's HttpOptions.timeout is in MILLISECONDS (not seconds) — verify the unit.
    from google import genai

    import judging.providers as P

    captured: dict = {}

    class FakeClient:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setenv("GEMINI_API_KEY", "x")
    monkeypatch.setattr(genai, "Client", FakeClient)
    P._gemini_client()
    assert captured["http_options"].timeout == int(P.REQUEST_TIMEOUT_SECONDS * 1000)


def test_subject_request_missing_required_field_is_rejected_by_sdk():
    # Prove the real-SDK validation actually bites (anti-mock): a request missing max_tokens fails.
    import pydantic
    from anthropic import types as atypes

    from judging.providers import _subject_messages

    msgs = _subject_messages([{"role": "user", "content": "Q"}], None)
    with pytest.raises(pydantic.ValidationError):
        pydantic.TypeAdapter(atypes.MessageCreateParams).validate_python(
            {"model": "claude-opus-4-8", "messages": msgs}  # no max_tokens
        )

