"""Judging-workflow configuration: judges, subjects, framings, pressures, scopes.

Defaults live here; CLI flags (and, later, a config file) override them. The
workflow owns the judge panel and the scoring constants — there is **no
band-label config** (scores are bare numbers, spec §4.3 / §5.7). Models are
config-driven so a model rename is a one-line change.
"""

from __future__ import annotations

from dataclasses import dataclass

from judging.core_imports import FRAMINGS, PRESSURES

# Two judge scopes per sitting (spec §5.5): ``turn1`` = baseline (first exchange
# only), ``full`` = after the pressure push.
SCOPES: tuple[str, ...] = ("turn1", "full")


@dataclass(frozen=True)
class JudgeSpec:
    """One judge in the panel."""

    model: str
    provider: str  # "anthropic" | "gemini"
    thinking: bool = True
    # Judging-only: a judge must score benign-but-sensitive transcripts without
    # refusing. Subjects are NEVER run safety-off (spec §5.5).
    safety_off: bool = False
    max_tokens: int = 4096


@dataclass(frozen=True)
class SubjectSpec:
    """One subject model to collect responses from (Claude-only for now, §4.5)."""

    model: str
    provider: str = "anthropic"
    thinking: bool = False
    max_tokens: int = 16384


# Default judge panel (architect decision 2026-06-25): config-driven; default
# Opus 4.8 + Gemini Flash 3.5, both with thinking. Gemini judging runs
# safety-off (judging only).
DEFAULT_JUDGES: tuple[JudgeSpec, ...] = (
    JudgeSpec(model="claude-opus-4-8", provider="anthropic", thinking=True),
    JudgeSpec(
        model="gemini-3.5-flash", provider="gemini", thinking=True, safety_off=True
    ),
)

# Default subjects: the minimal Claude-only collector (spec §4.5).
DEFAULT_SUBJECTS: tuple[SubjectSpec, ...] = (
    SubjectSpec(model="claude-opus-4-8"),
    SubjectSpec(model="claude-sonnet-4-6"),
)


@dataclass(frozen=True)
class Config:
    """The full run configuration (immutable; overrides produce a new Config)."""

    judges: tuple[JudgeSpec, ...] = DEFAULT_JUDGES
    subjects: tuple[SubjectSpec, ...] = DEFAULT_SUBJECTS
    framings: tuple[str, ...] = FRAMINGS
    pressures: tuple[str, ...] = PRESSURES
    scopes: tuple[str, ...] = SCOPES
    concurrency: int = 8
    retries: int = 2
    results_dir: str = "results"


def default_config() -> Config:
    """The default configuration."""
    return Config()
