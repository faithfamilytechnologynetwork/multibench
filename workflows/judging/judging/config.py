"""Judging-workflow configuration: judges, subjects, framings, pressures, scopes.

Defaults live here; a YAML config file (``--config``, via ``load_config``) overrides them
field-by-field. The workflow owns the judge panel and the scoring constants — there is **no
band-label config** (scores are bare numbers, spec §4.3 / §5.7). Models are config-driven so a
model rename is a one-line change.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from pathlib import Path

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


class ConfigError(Exception):
    """A config file is missing or malformed (fail-loud, spec N2)."""


_JUDGE_PROVIDERS = ("anthropic", "gemini")
_SUBJECT_PROVIDERS = ("anthropic",)  # Claude-only collector for now (§4.5)


def _require_str(raw: dict, key: str, where: str) -> str:
    v = raw.get(key)
    if not isinstance(v, str) or not v.strip():
        raise ConfigError(f"{where}: {key!r} must be a non-empty string")
    return v


def _opt_bool(raw: dict, key: str, default: bool, where: str) -> bool:
    v = raw.get(key, default)
    if not isinstance(v, bool):
        raise ConfigError(f"{where}: {key!r} must be a boolean")
    return v


def _opt_pos_int(raw: dict, key: str, default: int, where: str) -> int:
    v = raw.get(key, default)
    if not isinstance(v, int) or isinstance(v, bool) or v <= 0:
        raise ConfigError(f"{where}: {key!r} must be a positive integer")
    return v


def _spec(raw: object, *, kind: str, allowed: set[str], providers: tuple[str, ...],
          default_provider: str | None, where: str):
    """Build a JudgeSpec/SubjectSpec from a mapping, failing loud on unknown/bad fields."""
    if not isinstance(raw, dict):
        raise ConfigError(f"{where}: each {kind} must be a mapping, got {type(raw).__name__}")
    unknown = set(raw) - allowed
    if unknown:
        raise ConfigError(f"{where}: unknown {kind} key(s): {sorted(unknown)}")
    model = _require_str(raw, "model", where)
    provider = raw.get("provider", default_provider)
    if provider not in providers:
        raise ConfigError(f"{where}: {kind} provider must be one of {list(providers)}, got {provider!r}")
    thinking = _opt_bool(raw, "thinking", kind == "judge", where)
    if kind == "judge":
        return JudgeSpec(
            model=model, provider=provider, thinking=thinking,
            safety_off=_opt_bool(raw, "safety_off", False, where),
            max_tokens=_opt_pos_int(raw, "max_tokens", 4096, where),
        )
    return SubjectSpec(
        model=model, provider=provider, thinking=thinking,
        max_tokens=_opt_pos_int(raw, "max_tokens", 16384, where),
    )


def _str_tuple(raw: dict, key: str, allowed: tuple[str, ...], where: str) -> tuple[str, ...]:
    v = raw[key]
    if not isinstance(v, list) or not v or not all(isinstance(x, str) and x.strip() for x in v):
        raise ConfigError(f"{where}: {key!r} must be a non-empty list of strings")
    bad = [x for x in v if x not in allowed]
    if bad:
        raise ConfigError(f"{where}: unknown {key} value(s) {bad}; allowed: {list(allowed)}")
    return tuple(v)


_CONFIG_FIELDS = {f.name for f in fields(Config)}
_JUDGE_FIELDS = {"model", "provider", "thinking", "safety_off", "max_tokens"}
_SUBJECT_FIELDS = {"model", "provider", "thinking", "max_tokens"}


def load_config(path: str | Path) -> Config:
    """Load a run config from a YAML file, overriding defaults field-by-field (spec §5.7).

    Only keys present override; unknown keys / bad shapes fail loud with a located
    ``ConfigError`` (N2). ``framings``/``pressures``/``scopes`` are validated against the
    universal core, judge providers against the supported set. Passing the same file to
    ``report`` is how coverage is computed against the panel/scopes that produced the artifacts.
    """
    import yaml  # lazy: pyyaml is a declared dep, kept off the import-time path

    p = Path(path)
    if not p.exists():
        raise ConfigError(f"{p}: config file not found")
    try:
        raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        raise ConfigError(f"{p}: invalid YAML: {e}") from e
    if not isinstance(raw, dict):
        raise ConfigError(f"{p}: config must be a mapping, got {type(raw).__name__}")
    unknown = set(raw) - _CONFIG_FIELDS
    if unknown:
        raise ConfigError(f"{p}: unknown config key(s): {sorted(unknown)}")

    overrides: dict = {}
    if "judges" in raw:
        if not isinstance(raw["judges"], list) or not raw["judges"]:
            raise ConfigError(f"{p}: 'judges' must be a non-empty list")
        overrides["judges"] = tuple(
            _spec(j, kind="judge", allowed=_JUDGE_FIELDS, providers=_JUDGE_PROVIDERS,
                  default_provider=None, where=f"{p} judges[{i}]")
            for i, j in enumerate(raw["judges"])
        )
    if "subjects" in raw:
        if not isinstance(raw["subjects"], list) or not raw["subjects"]:
            raise ConfigError(f"{p}: 'subjects' must be a non-empty list")
        overrides["subjects"] = tuple(
            _spec(s, kind="subject", allowed=_SUBJECT_FIELDS, providers=_SUBJECT_PROVIDERS,
                  default_provider="anthropic", where=f"{p} subjects[{i}]")
            for i, s in enumerate(raw["subjects"])
        )
    if "framings" in raw:
        overrides["framings"] = _str_tuple(raw, "framings", FRAMINGS, str(p))
    if "pressures" in raw:
        overrides["pressures"] = _str_tuple(raw, "pressures", PRESSURES, str(p))
    if "scopes" in raw:
        overrides["scopes"] = _str_tuple(raw, "scopes", SCOPES, str(p))
    if "concurrency" in raw:
        overrides["concurrency"] = _opt_pos_int(raw, "concurrency", Config.concurrency, str(p))
    if "retries" in raw:
        v = raw["retries"]  # retries may be 0 (no retry); non-negative int
        if not isinstance(v, int) or isinstance(v, bool) or v < 0:
            raise ConfigError(f"{p}: 'retries' must be a non-negative integer")
        overrides["retries"] = v
    if "results_dir" in raw:
        overrides["results_dir"] = _require_str(raw, "results_dir", str(p))

    return replace(default_config(), **overrides)
