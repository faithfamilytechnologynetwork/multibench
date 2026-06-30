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
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
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
