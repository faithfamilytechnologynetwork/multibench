"""Provenance capture (experiment 48): `_openai_subject` stashes the OpenRouter serving host
(`resp.provider`) into the per-call usage dict when present, and omits it when absent — backward
compatible. The provider boundary is mocked (no live API)."""
from types import SimpleNamespace

import pytest

from judging import providers
from judging.config import SubjectSpec

SUBJECT = SubjectSpec(
    model="google/gemma-4-31b-it", provider="openai",
    base_url="https://openrouter.ai/api/v1", api_key_env="OPENROUTER_API_KEY",
)


def _fake_resp(provider):
    """A minimal OpenAI-compatible chat.completions response; `provider` set to None omits it."""
    usage = SimpleNamespace(prompt_tokens=100, completion_tokens=40, prompt_tokens_details=None)
    msg = SimpleNamespace(content="counsel text")
    resp = SimpleNamespace(choices=[SimpleNamespace(message=msg)], usage=usage)
    if provider is not None:
        resp.provider = provider  # OpenRouter sets a top-level `provider`; direct OpenAI does not
    return resp


class _FakeClient:
    def __init__(self, provider):
        self._provider = provider
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **_kw):
        return _fake_resp(self._provider)


@pytest.fixture(autouse=True)
def _creds(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")


def _run(monkeypatch, provider):
    # _openai_subject does `from openai import OpenAI` at call time → patch the source symbol.
    monkeypatch.setattr("openai.OpenAI", lambda **_kw: _FakeClient(provider))
    text, usage, attempts = providers._openai_subject(
        SUBJECT, None, [{"role": "user", "content": "hi"}], retries=0)
    return text, usage, attempts


def test_provider_present_is_captured(monkeypatch):
    text, usage, _ = _run(monkeypatch, "Novita")
    assert text == "counsel text"
    assert usage["provider"] == "Novita"
    assert usage["in"] == 100 and usage["out"] == 40


def test_provider_absent_key_omitted(monkeypatch):
    # direct OpenAI (no top-level `provider`) → the key must NOT appear (backward compatible)
    _, usage, _ = _run(monkeypatch, None)
    assert "provider" not in usage
    assert usage["in"] == 100 and usage["out"] == 40


def test_provider_empty_string_omitted(monkeypatch):
    # falsy provider is treated as absent (guarded by `if provider:`)
    _, usage, _ = _run(monkeypatch, "")
    assert "provider" not in usage
