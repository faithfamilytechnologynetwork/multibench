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


def test_subject_collection_is_claude_only():
    # Subjects are Claude-only in this workflow (§4.5).
    with pytest.raises(ProviderError):
        subject_complete(
            SubjectSpec("gemini-x", "gemini"), None, [{"role": "user", "content": "hi"}]
        )


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


def test_subject_messages_construct_as_anthropic_params():
    # Real-client construction (M21, anti-mock): the built user turns are valid Anthropic
    # message params (content-block lists the SDK accepts), not just arbitrary dicts.
    from judging.providers import _subject_messages

    out = _subject_messages([{"role": "user", "content": "Q"}], "CTX")
    for msg in out:
        assert msg["role"] in ("user", "assistant")
        if isinstance(msg["content"], list):
            for b in msg["content"]:
                assert b["type"] == "text" and isinstance(b["text"], str)
                if "cache_control" in b:
                    assert b["cache_control"]["type"] == "ephemeral"

