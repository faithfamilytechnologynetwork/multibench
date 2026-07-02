"""Provider seams for collection and judging (spec §5.5 / N2 / N4).

Two **distinct** seams over a shared creds/retry layer, so collection and judging
never share the wrong abstraction (a judge wants a schema-constrained verdict and,
for Gemini, safety-off; a subject wants an ordinary conversational completion and is
NEVER run safety-off):

- ``subject_complete(subject, context_prefix, messages)`` -> ``(text, usage, attempts)``
- ``judge_complete(judge, parts, schema)`` -> ``(raw_verdict, raw_text, usage)``

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


def ctx_block(ctx: str) -> str:
    return f"[Context for this conversation: {ctx}]"


# --- Subject (collection) seam ---------------------------------------------


def subject_complete(
    subject: SubjectSpec,
    context_prefix: str | None,
    messages: list[dict],
    retries: int = 2,
) -> tuple[str, dict, int]:
    """Ordinary conversational completion for a subject. Returns ``(text, usage, attempts)``.

    ``context_prefix`` (the framing text) is folded onto the top of EVERY user turn —
    never a system prompt; no subject gets a privileged channel (§4.5). ``messages``
    holds the clean scenario turns. ``attempts`` is the 1-based try that succeeded (audit).
    """
    if subject.provider == "anthropic":
        return _anthropic_subject(subject, context_prefix, messages, retries)
    raise ProviderError(
        f"unsupported subject provider {subject.provider!r} "
        "(collection is Claude-only in this workflow, §4.5)"
    )


def _subject_messages(messages: list[dict], context_prefix: str | None) -> list[dict]:
    """Anthropic subject messages: fold the framing onto **every** user turn (as a context
    prefix, never a system prompt — §4.5) and set prompt-cache breakpoints on the **first** user
    turn only (M16, mirroring JaleesBench `collect.py`): the framing block is a **1h ephemeral**
    breakpoint (shared by every sitting of this framing) and turn-1's question is a **default-TTL**
    ephemeral breakpoint, so the turn-2 call rereads the framing + turn-1 from cache instead of
    re-paying. Assistant turns are untouched. User turns become content-block lists."""
    out: list[dict] = []
    first_user = True
    for m in messages:
        if m["role"] != "user":
            out.append(m)
            continue
        blocks: list[dict] = []
        if context_prefix:
            fb: dict = {"type": "text", "text": ctx_block(context_prefix)}
            if first_user:
                fb["cache_control"] = {"type": "ephemeral", "ttl": "1h"}
            blocks.append(fb)
        q: dict = {"type": "text", "text": m["content"]}
        if first_user:
            q["cache_control"] = {"type": "ephemeral"}  # default TTL — turn-2 rereads turn-1
        blocks.append(q)
        out.append({"role": "user", "content": blocks})
        first_user = False
    return out


def _anthropic_subject(
    subject: SubjectSpec, context_prefix: str | None, messages: list[dict], retries: int
) -> tuple[str, dict, int]:
    _require_env("ANTHROPIC_API_KEY")
    import anthropic

    client = anthropic.Anthropic()
    folded = _subject_messages(messages, context_prefix)
    # Inline retry so we can report the 1-based attempt that succeeded (sittings audit, §5.6).
    last: Exception | None = None
    for attempt in range(retries + 1):
        try:
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
            return text.strip(), _anthropic_usage(resp), attempt + 1
        except Exception as e:  # noqa: BLE001 — transient API/transport; retry then fail
            last = e
            if attempt < retries:
                time.sleep(_BACKOFF_BASE_SECONDS * (attempt + 1))
    raise ProviderError(f"subject call failed after {retries + 1} attempts: {last}")


# --- Judge seam -------------------------------------------------------------


def judge_complete(
    judge: JudgeSpec, parts: tuple[str, str, str], schema: dict, retries: int = 2
) -> tuple[dict, str, dict]:
    """Schema-constrained verdict from one judge. Returns ``(raw_verdict, raw_text, usage)``.

    ``raw_text`` is the judge's unparsed response text, retained on every judgment for
    audit/debug (M19). ``parts`` = (static rubric, per-scenario anchor, conversation+spec).
    Anthropic sets 1-hour prefix-cache breakpoints on the two stable parts; Gemini runs
    safety-off when the judge is configured that way (judging only).
    """
    if judge.provider == "anthropic":
        return _anthropic_judge(judge, parts, schema, retries)
    if judge.provider == "gemini":
        return _gemini_judge(judge, parts, schema, retries)
    raise ProviderError(f"unsupported judge provider {judge.provider!r}")


def _anthropic_judge(
    judge: JudgeSpec, parts: tuple[str, str, str], schema: dict, retries: int
) -> tuple[dict, str, dict]:
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

    def call() -> tuple[dict, str, dict]:
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
        return json.loads(text), text, _anthropic_usage(resp)

    return _retry(call, retries)


def _gemini_has_creds() -> bool:
    """Gemini auth per spec N4: a Vertex service account **or** GEMINI_API_KEY."""
    return bool(
        os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")  # Vertex service account (ADC)
        or os.environ.get("GOOGLE_GENAI_USE_VERTEXAI")
    )


def _gemini_client():
    from google import genai

    if os.environ.get("GEMINI_API_KEY"):
        return genai.Client()  # Gemini Developer API
    # Vertex AI: service account via ADC (GOOGLE_APPLICATION_CREDENTIALS) / configured project.
    return genai.Client(
        vertexai=True,
        project=os.environ.get("GOOGLE_CLOUD_PROJECT"),
        location=os.environ.get("GOOGLE_CLOUD_LOCATION", "global"),
    )


def _to_gemini_schema(schema: dict) -> dict:
    """google-genai's ``Schema`` is stricter than JSON Schema: it rejects
    ``additionalProperties`` and requires ``enum`` values to be **strings** (our canonical
    ``score`` enum is numeric — correct for Anthropic, rejected by Gemini). Return a
    sanitized copy: drop unsupported keys recursively and present ``score`` as a string
    enum. ``_gemini_judge`` casts the returned score back to a float."""
    _DROP = {"additionalProperties"}

    def clean(node: Any) -> Any:
        if isinstance(node, dict):
            return {k: clean(v) for k, v in node.items() if k not in _DROP}
        if isinstance(node, list):
            return [clean(x) for x in node]
        return node

    out = clean(schema)
    score = out.get("properties", {}).get("score")
    if isinstance(score, dict) and "enum" in score:
        score["type"] = "string"
        score["enum"] = [str(float(v)) for v in score["enum"]]
    return out


def _gemini_judge(
    judge: JudgeSpec, parts: tuple[str, str, str], schema: dict, retries: int
) -> tuple[dict, str, dict]:
    if not _gemini_has_creds():
        raise ProviderError(
            "no Gemini credential: set GEMINI_API_KEY, or a Vertex service account "
            "(GOOGLE_APPLICATION_CREDENTIALS + GOOGLE_CLOUD_PROJECT) — spec N4"
        )
    from google.genai import types

    client = _gemini_client()
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
    config_kwargs: dict[str, Any] = {
        "response_mime_type": "application/json",
        # google-genai requires string enums; present `score` as strings, cast back below.
        "response_schema": _to_gemini_schema(schema),
        "safety_settings": safety,
    }
    if judge.thinking:
        # Dynamic thinking — the model decides the budget (thinking-on, §5.7).
        config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=-1)
    config = types.GenerateContentConfig(**config_kwargs)

    def call() -> tuple[dict, str, dict]:
        resp = client.models.generate_content(
            model=judge.model, contents=prompt, config=config
        )
        text = _gemini_text(resp)  # explicit blocked/empty diagnostic (M18)
        verdict = json.loads(text)
        # Gemini returns `score` as a string enum member ("0.5"); restore the numeric
        # type the rest of the pipeline (validate_score) expects.
        if isinstance(verdict.get("score"), str):
            verdict["score"] = float(verdict["score"])
        return verdict, text, _gemini_usage(resp)

    return _retry(call, retries)


def _gemini_text(resp: Any) -> str:
    """Extract the response text, failing LOUD on a blocked/empty response (M18).

    A bare ``json.loads(resp.text)`` on a safety-blocked or truncated Gemini response gives an
    opaque error; instead surface ``finish_reason`` / prompt-block feedback so the failure is
    diagnosable (and, being a ProviderError, is not silently retried into the same wall)."""
    text = getattr(resp, "text", None)
    if text and text.strip():
        return text
    # No usable text — build a located diagnostic from whatever the SDK exposes.
    reason = None
    candidates = getattr(resp, "candidates", None) or []
    if candidates:
        reason = getattr(candidates[0], "finish_reason", None)
    feedback = getattr(resp, "prompt_feedback", None)
    blocked = getattr(feedback, "block_reason", None) if feedback else None
    raise ProviderError(
        "gemini judge returned no text "
        f"(finish_reason={reason!r}, prompt_block_reason={blocked!r}) — "
        "likely a safety block or truncation"
    )


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
    # Thinking is ON (a deliberate deviation from JaleesBench, §4.7) — count `thoughts_token_count`
    # as output tokens (it is billed as output); omitting it under-reports cost (M18).
    return {
        "in": getattr(u, "prompt_token_count", 0) or 0,
        "out": (getattr(u, "candidates_token_count", 0) or 0)
        + (getattr(u, "thoughts_token_count", 0) or 0),
    }
