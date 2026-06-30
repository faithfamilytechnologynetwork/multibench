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


def test_fold_prefixes_user_turns_only():
    # Framing is folded onto user turns (as a context prefix), assistant turns untouched (§4.5).
    from judging.providers import _fold, ctx_block

    msgs = [{"role": "user", "content": "Q"}, {"role": "assistant", "content": "A"}]
    folded = _fold(msgs, "GUIDE TEXT")
    assert folded[0]["content"].startswith(ctx_block("GUIDE TEXT"))
    assert "Q" in folded[0]["content"]
    assert folded[1] == {"role": "assistant", "content": "A"}


def test_fold_is_noop_without_prefix():
    from judging.providers import _fold

    msgs = [{"role": "user", "content": "Q"}]
    assert _fold(msgs, None) == msgs

