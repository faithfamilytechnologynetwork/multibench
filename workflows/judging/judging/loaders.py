"""Read a tradition's judge inputs by composing ``tradition_validator``'s generic
loaders + strict Pydantic models (spec N5: single-source format parsing — no fork).

There are no tradition-specific loaders in the validator; we build accessors from
its generic ``load_text`` / ``load_yaml`` / ``load_json`` (each returning
``(data, Finding|None)``) and its models (``TraditionManifest``, ``ScenariosIndex``,
``ScenarioMeta``). Fail loud: a missing or malformed file raises :class:`LoadError`
with a located message (spec N2) — never a silent default.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tradition_validator import loaders as tv_loaders
from tradition_validator.findings import Finding
from tradition_validator.models import (
    ScenarioMeta,
    ScenariosIndex,
    TraditionManifest,
)

from judging.core_imports import PRESSURES, normalize_heading


class LoadError(Exception):
    """A tradition/scenario file is missing or malformed (fail-loud, spec N2)."""


def _fail(err: Finding) -> None:
    loc = err.file + (f" [{err.path}]" if err.path else "")
    raise LoadError(f"{loc}: {err.message}")


def _text(path: Path) -> str:
    data, err = tv_loaders.load_text(path)
    if err is not None:
        _fail(err)
    if data is None or not data.strip():
        raise LoadError(f"{path}: file is empty")
    return data


def _yaml_model(path: Path, model: type):
    data, err = tv_loaders.load_yaml(path)
    if err is not None:
        _fail(err)
    try:
        return model.model_validate(data)
    except Exception as e:  # pydantic ValidationError, etc. -> located error
        raise LoadError(f"{path}: {e}") from e


def _json_model(path: Path, model: type):
    data, err = tv_loaders.load_json(path)
    if err is not None:
        _fail(err)
    try:
        return model.model_validate(data)
    except Exception as e:
        raise LoadError(f"{path}: {e}") from e


@dataclass(frozen=True)
class Scenario:
    """One scenario's judge inputs."""

    id: str
    meta: ScenarioMeta
    turn1: str  # turn1.md — the opening (turn-1 user message)
    judge_guidance: str  # judge-guidance.md — the binding ground truth
    pressures: dict[str, str]  # canonical pressure id -> turn-2 push


@dataclass(frozen=True)
class Tradition:
    """A tradition's construct + manifest + the scenario bank."""

    id: str
    path: Path
    manifest: TraditionManifest
    guide: str  # guide.md — the construct ("good company" for this tradition)
    scenario_ids: tuple[str, ...]


def _parse_pressures(path: Path) -> dict[str, str]:
    """Parse ``pressures.md`` into ``{canonical_pressure_id: body}``.

    One ``## <pressure>`` section per core pressure; headings normalize via the
    universal-core rule (``core.normalize_heading``). Content before the first
    heading is allowed and ignored (spec §5.6). All six present, none unknown,
    none duplicated, each non-empty — else :class:`LoadError`.
    """
    text = _text(path)
    sections: dict[str, str] = {}
    order: list[str] = []
    current: str | None = None
    buf: list[str] = []

    def flush() -> None:
        if current is not None:
            sections[current] = "\n".join(buf).strip()

    for line in text.splitlines():
        if line.startswith("## "):
            flush()
            current = normalize_heading(line[3:])
            order.append(current)
            buf = []
        elif current is not None:
            buf.append(line)
    flush()

    dupes = sorted({h for h in order if order.count(h) > 1})
    if dupes:
        raise LoadError(f"{path}: duplicate pressure section(s): {dupes}")
    missing = [p for p in PRESSURES if p not in sections]
    unknown = sorted(h for h in sections if h not in PRESSURES)
    if missing or unknown:
        raise LoadError(
            f"{path}: pressure sections must be exactly the six core pressures "
            f"(missing={missing}, unknown={unknown})"
        )
    empty = [p for p in PRESSURES if not sections[p]]
    if empty:
        raise LoadError(f"{path}: empty pressure section(s): {empty}")
    return sections


def load_tradition(tradition_dir: str | Path) -> Tradition:
    """Load a tradition's construct (guide), manifest, and scenario bank."""
    d = Path(tradition_dir)
    manifest = _yaml_model(d / "tradition.yaml", TraditionManifest)
    guide = _text(d / "guide.md")
    index = _json_model(d / "scenarios" / "index.json", ScenariosIndex)
    return Tradition(
        id=manifest.id,
        path=d,
        manifest=manifest,
        guide=guide,
        scenario_ids=tuple(index.scenarios),
    )


def load_scenario(tradition_dir: str | Path, scenario_id: str) -> Scenario:
    """Load one scenario's turn-1, ground truth, pressures, and metadata."""
    sdir = Path(tradition_dir) / "scenarios" / scenario_id
    meta = _yaml_model(sdir / "scenario.yaml", ScenarioMeta)
    if meta.id != scenario_id:
        raise LoadError(
            f"{sdir / 'scenario.yaml'}: scenario id mismatch — folder/requested "
            f"{scenario_id!r} != scenario.yaml id {meta.id!r} (would corrupt keying)"
        )
    turn1 = _text(sdir / "turn1.md")
    judge_guidance = _text(sdir / "judge-guidance.md")
    pressures = _parse_pressures(sdir / "pressures.md")
    return Scenario(
        id=scenario_id,
        meta=meta,
        turn1=turn1,
        judge_guidance=judge_guidance,
        pressures=pressures,
    )
