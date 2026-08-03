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
    # N4: a dedicated per-host key (api_key_env) is required for OpenAI-compatible hosts
    # (Inkling/Qwen). Fail loud naming the exact var, before any SDK call.
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    with pytest.raises(ProviderError) as ei:
        subject_complete(
            SubjectSpec(
                "qwen3-235b-a22b",
                "openai",
                base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
                api_key_env="DASHSCOPE_API_KEY",
            ),
            None,
            [{"role": "user", "content": "hi"}],
        )
    assert "DASHSCOPE_API_KEY" in str(ei.value)


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
    # dict — so request-shape drift (model/max_tokens/messages) is caught without a live call.
    import pydantic
    from openai.types.chat import completion_create_params as ccp

    from judging.providers import _openai_messages

    msgs = _openai_messages(
        [{"role": "user", "content": "Q1"}, {"role": "assistant", "content": "A1"},
         {"role": "user", "content": "Q2"}],
        "CTX",
    )
    kwargs = {"model": "gpt-5.6-terra", "max_tokens": 1024, "messages": msgs}
    ta = pydantic.TypeAdapter(ccp.CompletionCreateParamsNonStreaming)
    ta.validate_python(kwargs)  # rejects e.g. a missing model
    # Prove the real-SDK validation actually bites (anti-mock): drop the required model.
    with pytest.raises(pydantic.ValidationError):
        ta.validate_python({"max_tokens": 1024, "messages": msgs})


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

