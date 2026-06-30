"""Provider seams for collection and judging (spec §5.5 / N2 / N4).

Two **distinct** seams over a shared creds/retry layer, so collection and judging
never share the wrong abstraction (a judge wants a schema-constrained verdict and,
for Gemini, safety-off; a subject wants an ordinary conversational completion and is
NEVER run safety-off):

- ``subject_complete(subject, context_prefix, messages)`` -> ``(text, usage)``
- ``judge_complete(judge, parts, schema)`` -> ``(raw_verdict, usage)``

SDKs are imported **lazily** inside each provider branch, so importing this module is
cheap and unit tests can mock at the seam without the SDK present. A missing credential
fails loud (N4); transient errors get bounded retries with backoff, then fail (N2).
"""

from __future__ import annotations

import json
import os
import time
from typing import Any, Callable

from judging.config import JudgeSpec, SubjectSpec

_BACKOFF_BASE_SECONDS = 2.0


class ProviderError(Exception):
    """A provider call failed (credentials / transport / parse) — fail loud."""


def _require_env(*names: str) -> None:
    missing = [n for n in names if not os.environ.get(n)]
    if missing:
        raise ProviderError(
            f"missing credential env var(s): {', '.join(missing)} "
            "(set them, or reconfigure the panel to a provider you have creds for)"
        )


def _retry(call: Callable[[], Any], retries: int) -> Any:
    last: Exception | None = None
    for attempt in range(retries + 1):
        try:
            return call()
        except ProviderError:
            raise  # creds / non-transient: don't retry
        except Exception as e:  # noqa: BLE001 — transient API/transport; retry then fail
            last = e
            if attempt < retries:
                time.sleep(_BACKOFF_BASE_SECONDS * (attempt + 1))
    raise ProviderError(f"provider call failed after {retries + 1} attempts: {last}")


def _ctx_block(ctx: str) -> str:
    return f"[Context for this conversation: {ctx}]"


# --- Subject (collection) seam ---------------------------------------------


def subject_complete(
    subject: SubjectSpec,
    context_prefix: str | None,
    messages: list[dict],
    retries: int = 2,
) -> tuple[str, dict]:
    """Ordinary conversational completion for a subject. Returns ``(text, usage)``.

    ``context_prefix`` (the framing text) is folded onto the top of EVERY user turn —
    never a system prompt; no subject gets a privileged channel (§4.5). ``messages``
    holds the clean scenario turns.
    """
    if subject.provider == "anthropic":
        return _anthropic_subject(subject, context_prefix, messages, retries)
    raise ProviderError(
        f"unsupported subject provider {subject.provider!r} "
        "(collection is Claude-only in this workflow, §4.5)"
    )


def _fold(messages: list[dict], context_prefix: str | None) -> list[dict]:
    if not context_prefix:
        return messages
    folded = []
    for m in messages:
        if m["role"] == "user":
            folded.append(
                {"role": "user", "content": f"{_ctx_block(context_prefix)}\n\n{m['content']}"}
            )
        else:
            folded.append(m)
    return folded


def _anthropic_subject(
    subject: SubjectSpec, context_prefix: str | None, messages: list[dict], retries: int
) -> tuple[str, dict]:
    _require_env("ANTHROPIC_API_KEY")
    import anthropic

    client = anthropic.Anthropic()
    folded = _fold(messages, context_prefix)

    def call() -> tuple[str, dict]:
        kwargs: dict[str, Any] = {
            "model": subject.model,
            "max_tokens": subject.max_tokens,
            "messages": folded,
        }
        if subject.thinking:
            kwargs["thinking"] = {"type": "adaptive"}
        resp = client.messages.create(**kwargs)
        text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
        if not text.strip():
            raise RuntimeError("empty subject response")
        return text.strip(), _anthropic_usage(resp)

    return _retry(call, retries)


# --- Judge seam -------------------------------------------------------------


def judge_complete(
    judge: JudgeSpec, parts: tuple[str, str, str], schema: dict, retries: int = 2
) -> tuple[dict, dict]:
    """Schema-constrained verdict from one judge. Returns ``(raw_verdict, usage)``.

    ``parts`` = (static rubric, per-scenario anchor, conversation+spec). Anthropic sets
    1-hour prefix-cache breakpoints on the two stable parts; Gemini runs safety-off when
    the judge is configured that way (judging only).
    """
    if judge.provider == "anthropic":
        return _anthropic_judge(judge, parts, schema, retries)
    if judge.provider == "gemini":
        return _gemini_judge(judge, parts, schema, retries)
    raise ProviderError(f"unsupported judge provider {judge.provider!r}")


def _anthropic_judge(
    judge: JudgeSpec, parts: tuple[str, str, str], schema: dict, retries: int
) -> tuple[dict, dict]:
    _require_env("ANTHROPIC_API_KEY")
    import anthropic

    client = anthropic.Anthropic()
    rubric, anchor, tail = parts
    # The two stable parts are 1h cache breakpoints (rubric is shared by every judgment;
    # the anchor by all judgments of one scenario). The conversation block is uncached.
    content = [
        {"type": "text", "text": rubric, "cache_control": {"type": "ephemeral", "ttl": "1h"}},
        {"type": "text", "text": anchor, "cache_control": {"type": "ephemeral", "ttl": "1h"}},
        {"type": "text", "text": tail},
    ]

    def call() -> tuple[dict, dict]:
        kwargs: dict[str, Any] = {
            "model": judge.model,
            "max_tokens": judge.max_tokens,
            "output_config": {"format": {"type": "json_schema", "schema": schema}},
            "messages": [{"role": "user", "content": content}],
        }
        if judge.thinking:
            kwargs["thinking"] = {"type": "adaptive"}
        resp = client.messages.create(**kwargs)
        text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
        return json.loads(text), _anthropic_usage(resp)

    return _retry(call, retries)


def _gemini_judge(
    judge: JudgeSpec, parts: tuple[str, str, str], schema: dict, retries: int
) -> tuple[dict, dict]:
    _require_env("GEMINI_API_KEY")
    from google import genai
    from google.genai import types

    client = genai.Client()  # reads GEMINI_API_KEY
    prompt = "\n\n".join(parts)
    safety = None
    if judge.safety_off:
        # The judge SCORES transcripts; it must not refuse benign-but-sensitive content.
        # Subjects are never run safety-off.
        safety = [
            types.SafetySetting(category=c, threshold="BLOCK_NONE")
            for c in (
                "HARM_CATEGORY_HARASSMENT",
                "HARM_CATEGORY_HATE_SPEECH",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "HARM_CATEGORY_DANGEROUS_CONTENT",
            )
        ]
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=schema,
        safety_settings=safety,
    )

    def call() -> tuple[dict, dict]:
        resp = client.models.generate_content(
            model=judge.model, contents=prompt, config=config
        )
        return json.loads(resp.text), _gemini_usage(resp)

    return _retry(call, retries)


# --- Usage extraction (best-effort; defensive) ------------------------------


def _anthropic_usage(resp: Any) -> dict:
    u = getattr(resp, "usage", None)
    if u is None:
        return {}
    return {
        "in": getattr(u, "input_tokens", 0) or 0,
        "out": getattr(u, "output_tokens", 0) or 0,
        "cache_write": getattr(u, "cache_creation_input_tokens", 0) or 0,
        "cache_read": getattr(u, "cache_read_input_tokens", 0) or 0,
    }


def _gemini_usage(resp: Any) -> dict:
    u = getattr(resp, "usage_metadata", None)
    if u is None:
        return {}
    return {
        "in": getattr(u, "prompt_token_count", 0) or 0,
        "out": getattr(u, "candidates_token_count", 0) or 0,
    }
