"""Regression: the Gemini judge schema must be google-genai-compatible.

The live 5-scenarios-per-tradition run found the Gemini judge 400ing on **every** call — dual
judging was fully broken — while the mocked suite + review passed, because the mock boundary
never fed the real schema to google-genai. google-genai's ``Schema`` is stricter than JSON
Schema: it rejects ``additionalProperties`` and requires ``enum`` values to be **strings**,
but our canonical ``score`` enum is numeric (correct for Anthropic's structured output). These
tests assert ``_to_gemini_schema`` produces a schema google-genai actually accepts.
"""

import pytest

from judging.providers import _to_gemini_schema
from judging.rubric import verdict_schema


def _contains_key(node, key) -> bool:
    if isinstance(node, dict):
        return key in node or any(_contains_key(v, key) for v in node.values())
    if isinstance(node, list):
        return any(_contains_key(x, key) for x in node)
    return False


def test_gemini_schema_strips_additional_properties_at_any_depth():
    raw = verdict_schema()
    assert _contains_key(raw, "additionalProperties")  # the source schema has it (Anthropic-fine)
    assert not _contains_key(_to_gemini_schema(raw), "additionalProperties")  # stripped for Gemini


def test_gemini_schema_score_enum_is_all_strings():
    score = _to_gemini_schema(verdict_schema())["properties"]["score"]
    assert score["type"] == "string"
    assert score["enum"] and all(isinstance(v, str) for v in score["enum"])
    # Still the canonical five values, just stringified (cast back to float on return).
    assert set(score["enum"]) == {"-1.0", "-0.5", "0.0", "0.5", "1.0"}


def test_gemini_schema_constructs_as_genai_types_schema():
    # The actual failure mode: google-genai must accept the schema object. The sanitized schema
    # constructs; the raw (numeric enum + additionalProperties) one does NOT — proving the fix.
    from google.genai import types

    types.Schema(**_to_gemini_schema(verdict_schema()))  # must not raise

    with pytest.raises(Exception):  # numeric enum rejected by google-genai's validation
        types.Schema(**verdict_schema())
