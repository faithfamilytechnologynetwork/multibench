"""Raw-results export core — per-scenario transcripts + judge verdicts (#51, Phase 1).

Sibling to :mod:`analysis.export_results` (#49). Where that module aggregates judging runs
into *scores-and-metadata* slice tables, this one produces the **raw** tier the multibrowser
raw-results viewer reads: per-scenario shards carrying each subject×framing×pressure cell's
**transcript** plus its per-(judge, scope) **verdicts** (score, direction summary, rationale).

Agreement with the score tier is by construction: verdicts come from the **same** loaders
(``read_run_root`` + ``resolve_judgments`` + the alias maps), and both tiers stamp the same
:func:`source_fingerprint` over the resolved-judgments stream (Phase 2 wires it into
``export_results``). Transcripts are read **only** from the full-grid (``report.json``-bearing)
run; every other run root contributes verdicts only, never transcripts.

The contract is **catalog-generic** (issue #54): the catalog declares the score scale + color
ramp, subjects, judges, condition axes, grouping axis, and items — nothing MultiBench-specific
(``tradition``/``scenario``/framing/pressure) is hardcoded in the *shape*. A non-MultiBench
catalog (AFB 0–4) rides the same viewer unchanged.

Phase 1 (this module) is the **pure transform** — it reads run roots and returns in-memory
documents. The deterministic writer, the ``export-raw`` CLI, and presets are Phase 2/3.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from analysis.colors import STOPS as RAMP_STOPS
from analysis.core_imports import FRAMINGS, PRESSURES
from analysis.export_results import (
    CANONICAL_SUBJECTS,
    JUDGE_UI,
    SCOPES,
    RawTradition,
    _scenario_universe,
    normalize_subject,
    read_run_root,
    resolve_judgments,
)
from analysis.loaders import AnalysisInputError

SCHEMA_VERSION = 1

# The dataset block for the MultiBench catalog. License is CC-BY-4.0 (spec Decision 7).
_DATASET = {
    "title": "MultiBench raw results",
    "description": (
        "Per-scenario model transcripts and judge verdicts from the MultiBench "
        "multi-tradition benchmark."
    ),
    "language": "en",
    "license": "CC-BY-4.0",
}

# The −1…+1 numeric scale + the score colormap, shipped as catalog DATA (no band names). The
# ramp stops are the single-source colormap in analysis.colors (scoreColor.ts is its TS port).
_SCALE = {"min": -1.0, "center": 0.0, "max": 1.0}

_SITTINGS = "sittings.jsonl"


def _humanize(value: str) -> str:
    """`false_authority` -> `False Authority`; `unstated` -> `Unstated`."""
    return value.replace("_", " ").title()


# ── Fingerprint (shared with export_results in Phase 2) ────────────────────────────
# A deterministic hash over the resolved-judgments stream. Both tiers compute it from the
# SAME input shape so a per-run equality check upgrades "same loaders" to a checkable
# invariant (spec Decision 2). Field order is fixed here and must never change silently.


def _fingerprint_tuple(row: dict) -> list:
    """One resolved judgment reduced to its fingerprinted fields (canonical order)."""
    return [
        row["subject"], row["scenario_id"], row["pressure"], row["framing"],
        row["judge"], row["scope"],
        # score as a JSON number; direction/rationale as "" when absent (stable).
        row["score"],
        row.get("direction") or "",
        row.get("rationale") or "",
    ]


def source_fingerprint(resolved: list[dict]) -> str:
    """`sha256:<hex>` over the sorted resolved-judgments stream.

    ``resolved`` is the **global** list of canonical (normalized) resolved judgments across
    all traditions — exactly what ``resolve_judgments`` returns, concatenated. Each row is
    serialized to its canonical JSON form and the stream is sorted on that exact serialization
    (so the sort key and the hashed bytes agree), making the hash order-independent and
    byte-stable. export_results must call THIS function on the same global stream (Phase 2)
    for the tiers to agree.
    """
    lines = sorted(
        json.dumps(_fingerprint_tuple(r), ensure_ascii=False, separators=(",", ":"))
        for r in resolved
    )
    blob = "\n".join(lines)
    return "sha256:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()


# ── Reading full-grid transcripts ──────────────────────────────────────────────────
# The full-grid run (the one whose tradition dirs carry report.json) is the SOLE transcript
# source. Its sittings.jsonl rows are keyed by NORMALIZED subject so they join to the
# normalized verdicts even though subject id spellings differ across run roots.

# Normalized transcript identity — subject normalized, tradition excluded (one dir = one trad).
SittingKey = tuple  # (norm_subject, scenario_id, pressure, framing)


@dataclass(frozen=True)
class Sitting:
    """One transcript cell: allowlisted turns + the optional context-prefix text."""

    turns: list[dict]          # [{"role": "user"|"assistant", "content": str}, …]
    context_prefix: str | None  # stated/guided framing text; None for unstated


def _sitting_key(subject_norm: str, row: dict) -> SittingKey:
    return (subject_norm, row["scenario_id"], row["pressure"], row["framing"])


def read_full_grid_sittings(sittings_path: Path, tradition: str) -> dict[SittingKey, Sitting]:
    """Read + validate one tradition's sittings from the full-grid run.

    Keys by **normalized** subject. Rejects a duplicate sitting identity and a conflicting
    ``context_prefix`` for the same identity (both signal an inconsistent run). Only the
    allowlisted fields (turns' role/content, context_prefix) are retained — attempts/usage/
    ts/model never leave here.
    """
    out: dict[SittingKey, Sitting] = {}
    for lineno, row in _iter_jsonl(sittings_path):
        where = f"{sittings_path}:{lineno}"
        for k in ("subject", "tradition", "scenario_id", "pressure", "framing", "turns"):
            if k not in row:
                raise AnalysisInputError(f"{where}: sitting missing required key {k!r}")
        if row["tradition"] != tradition:
            raise AnalysisInputError(
                f"{where}: sitting tradition {row['tradition']!r} != dir tradition {tradition!r}"
            )
        if row["framing"] not in FRAMINGS:
            raise AnalysisInputError(f"{where}: unknown framing {row['framing']!r}")
        if row["pressure"] not in PRESSURES:
            raise AnalysisInputError(f"{where}: unknown pressure {row['pressure']!r}")
        key = _sitting_key(normalize_subject(row["subject"]), row)
        turns = _clean_turns(row["turns"], where)
        prefix = _clean_prefix(row.get("context_prefix"), where)
        # The unstated framing is context-free by contract — a prefix on it is an anomaly.
        if row["framing"] == "unstated" and prefix is not None:
            raise AnalysisInputError(
                f"{where}: unstated cell carries a context_prefix (unstated is context-free)"
            )
        sitting = Sitting(turns=turns, context_prefix=prefix)
        if key in out:
            prev = out[key]
            if prev.context_prefix != sitting.context_prefix:
                raise AnalysisInputError(
                    f"{where}: conflicting context_prefix for {dict(zip(_SITTING_FIELDS, key))}"
                )
            raise AnalysisInputError(
                f"{where}: duplicate sitting identity {dict(zip(_SITTING_FIELDS, key))}"
            )
        out[key] = sitting
    return out


_SITTING_FIELDS: tuple[str, ...] = ("subject", "scenario_id", "pressure", "framing")


def _clean_turns(turns, where: str) -> list[dict]:
    """Keep only ``{role, content}`` (drop any harness-only per-turn fields); validate roles.

    Validates the container and element types so malformed input fails as an
    ``AnalysisInputError`` (fail-loud) rather than an ``AttributeError``/``TypeError``.
    """
    if not isinstance(turns, list):
        raise AnalysisInputError(f"{where}: 'turns' is not a list")
    cleaned: list[dict] = []
    for t in turns:
        if not isinstance(t, dict):
            raise AnalysisInputError(f"{where}: turn is not an object")
        role, content = t.get("role"), t.get("content")
        if role not in ("user", "assistant"):
            raise AnalysisInputError(f"{where}: unexpected turn role {role!r}")
        if not isinstance(content, str):
            raise AnalysisInputError(f"{where}: turn content is not a string")
        cleaned.append({"role": role, "content": content})
    return cleaned


def _clean_prefix(prefix, where: str) -> str | None:
    """Normalize the context prefix: JSON null / empty → None; a non-empty string → itself."""
    if prefix is None or (isinstance(prefix, str) and prefix.strip() == ""):
        return None
    if not isinstance(prefix, str):
        raise AnalysisInputError(f"{where}: context_prefix is not a string: {prefix!r}")
    return prefix


def _iter_jsonl(path: Path):
    """Yield (lineno, obj) for non-blank JSONL lines; fail loud on malformed JSON."""
    if not path.is_file():
        raise AnalysisInputError(f"expected sittings file not found: {path}")
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if line.strip():
            try:
                yield lineno, json.loads(line)
            except json.JSONDecodeError as e:
                raise AnalysisInputError(f"{path}:{lineno}: malformed JSON ({e})") from e


# ── Building the raw corpus (per tradition) ────────────────────────────────────────


@dataclass(frozen=True)
class RawScenario:
    """One scenario's cells (in-memory), before serialization."""

    scenario_id: str
    group: str                      # the grouping-axis value (tradition, for MultiBench)
    contexts: dict[str, str]        # framing → prefix text (only framings with a prefix)
    cells: list[dict]               # serialized-ready cell dicts (sorted)


@dataclass(frozen=True)
class RawTraditionExport:
    """One tradition's raw scenarios (sorted by scenario_id)."""

    tradition: str
    scenarios: list[RawScenario]


@dataclass(frozen=True)
class RawCorpus:
    """The whole raw export, in memory: per-tradition scenarios + the global resolved stream."""

    per_tradition: dict[str, RawTraditionExport]   # keyed by tradition, sorted keys
    subjects: list[str]                            # canonical subjects present (catalog order)
    judges: list[str]                              # canonical judge model-ids present (sorted)
    resolved: list[dict]                           # global resolved-judgments stream (fingerprint)


def _full_grid_root_for(tradition: str, per_root: list[tuple[Path, dict[str, RawTradition]]]) -> Path:
    """The single run-root path whose ``<root>/<tradition>/`` provided ``report.json``.

    That run is the transcript source. More than one report-bearing root would be ambiguous;
    ``_scenario_universe`` separately enforces the universes agree, but the transcript source
    must be exactly one directory, so we require a single report-bearing root here.
    """
    roots = [root for root, parsed in per_root
             if tradition in parsed and parsed[tradition].report is not None]
    if not roots:
        raise AnalysisInputError(
            f"{tradition}: no run root provides report.json — cannot source transcripts "
            f"(the full-grid run must supply it)"
        )
    if len(roots) > 1:
        raise AnalysisInputError(
            f"{tradition}: {len(roots)} run roots provide report.json — ambiguous transcript "
            f"source; exactly one full-grid run is expected"
        )
    return roots[0]


def _verdict(row: dict, tradition: str) -> dict:
    """One resolved judgment → a slimmed, allowlisted verdict on the display scale.

    Only the shipped fields: UI judge key, scope, numeric score, the direction ``summary``
    (always present — the judging contract carries a direction on every verdict), and the
    rationale when present. Harness-only fields (raw/usage/ts/sitting_key) are dropped.
    """
    model = row["judge"]
    ui = JUDGE_UI.get(model)
    if ui is None:  # fail-fast — a normalized judge is always known here
        raise AnalysisInputError(f"no UI metadata for judge {model!r}")
    direction = row.get("direction")
    if not (isinstance(direction, str) and direction.strip()):
        raise AnalysisInputError(
            f"{tradition}: verdict for {row['subject']}/{row['scenario_id']}/"
            f"{row['pressure']}/{row['framing']}/{ui['key']}/{row['scope']} has no direction "
            f"summary (the verdict contract requires one)"
        )
    verdict = {"judge": ui["key"], "scope": row["scope"], "score": row["score"],
               "summary": direction}
    if row.get("rationale"):
        verdict["rationale"] = row["rationale"]
    return verdict


# Canonical orderings so shards/catalog are stable regardless of source row order.
_FRAMING_ORDER = {f: i for i, f in enumerate(FRAMINGS)}
_PRESSURE_ORDER = {p: i for i, p in enumerate(PRESSURES)}
_SCOPE_ORDER = {s: i for i, s in enumerate(SCOPES)}
_SUBJECT_ORDER = {s: i for i, s in enumerate(CANONICAL_SUBJECTS)}


def _build_scenario(scenario_id: str, tradition: str,
                    sittings: dict[SittingKey, Sitting],
                    verdicts_by_cell: dict[tuple, list[dict]]) -> RawScenario:
    """Assemble one scenario's shard-ready cells + contexts pool."""
    contexts: dict[str, str] = {}
    cells: list[dict] = []
    # Iterate the sittings for this scenario (transcript is the anchor; a cell exists iff a
    # transcript exists — verdicts without a transcript are caught by the orphan guard).
    for (subj, sc, pr, fr), sitting in sittings.items():
        if sc != scenario_id:
            continue
        cell = {
            "subject": subj,
            "conditions": {"framing": fr, "pressure": pr},
            "transcript": sitting.turns,
            "verdicts": sorted(
                verdicts_by_cell.get((subj, sc, pr, fr), []),
                key=lambda v: (v["judge"], _SCOPE_ORDER.get(v["scope"], 99)),
            ),
        }
        if sitting.context_prefix is not None:
            # Pool by framing; a differing prefix for the same framing within a scenario is a
            # run inconsistency (never silently first-wins — the pool must be unambiguous).
            existing = contexts.get(fr)
            if existing is not None and existing != sitting.context_prefix:
                raise AnalysisInputError(
                    f"{scenario_id}: conflicting context_prefix for framing {fr!r} "
                    f"(the per-shard contexts pool is keyed by framing and must be unambiguous)"
                )
            contexts[fr] = sitting.context_prefix
            cell["contextKey"] = fr  # opaque key into the shard's contexts pool
        cells.append(cell)
    cells.sort(key=lambda c: (
        _SUBJECT_ORDER.get(c["subject"], 99),
        _FRAMING_ORDER.get(c["conditions"]["framing"], 99),
        _PRESSURE_ORDER.get(c["conditions"]["pressure"], 99),
    ))
    return RawScenario(scenario_id=scenario_id, group=tradition, contexts=contexts, cells=cells)


def build_tradition_raw(tradition: str, raws: list[RawTradition],
                        full_grid_sittings: dict[SittingKey, Sitting],
                        resolved: list[dict]) -> RawTraditionExport:
    """Join one tradition's resolved verdicts to transcripts and build its scenarios.

    ``resolved`` is ``resolve_judgments(raws)`` (passed in so the caller resolves once and
    reuses the same rows for the global fingerprint stream). Fail-fast on the two
    run-consistency hazards: a resolved verdict whose cell has no full-grid transcript
    (orphan — a half-copied run root), and a sitting scenario outside the report universe
    (an inconsistent run).
    """
    universe = set(_scenario_universe(raws, tradition))  # reuse #49's helper (no fork)

    sitting_scenarios = {sc for (_su, sc, _pr, _fr) in full_grid_sittings}
    stray = sitting_scenarios - universe
    if stray:
        raise AnalysisInputError(
            f"{tradition}: full-grid sittings reference scenarios {sorted(stray)} outside the "
            f"report universe ({len(universe)} scenarios) — inconsistent run"
        )
    missing = universe - sitting_scenarios
    if missing:
        raise AnalysisInputError(
            f"{tradition}: report universe scenarios {sorted(missing)} have no full-grid "
            f"sittings — a partial full-grid run must not produce a partial public tier"
        )

    # Per-scenario cell-grid completeness: every scenario must carry the full expected grid
    # (report subjects × framings × pressures), so a partially-copied sittings file can't
    # silently ship a thin shard. (Verified complete across all traditions on the real run.)
    expected_subjects = _report_subjects(raws) or {su for (su, _sc, _pr, _fr) in full_grid_sittings}
    expected_cells = {(su, fr, pr)
                      for su in expected_subjects for fr in FRAMINGS for pr in PRESSURES}
    cells_by_scenario: dict[str, set] = defaultdict(set)
    for (su, sc, pr, fr) in full_grid_sittings:
        cells_by_scenario[sc].add((su, fr, pr))
    for sc in sorted(sitting_scenarios):
        got = cells_by_scenario[sc]
        if got != expected_cells:
            lack, extra = expected_cells - got, got - expected_cells
            raise AnalysisInputError(
                f"{tradition}/{sc}: incomplete cell grid — missing {len(lack)}, extra "
                f"{len(extra)} of {len(expected_cells)} expected (subject×framing×pressure); "
                f"a partial full-grid run must not produce a partial shard"
            )

    verdicts_by_cell: dict[tuple, list[dict]] = {}
    for row in resolved:
        key = (row["subject"], row["scenario_id"], row["pressure"], row["framing"])
        if key not in full_grid_sittings:
            raise AnalysisInputError(
                f"{tradition}: resolved verdict {dict(zip(_SITTING_FIELDS, key))} has no "
                f"full-grid transcript (orphan) — refusing to ship a verdict without a transcript"
            )
        verdicts_by_cell.setdefault(key, []).append(_verdict(row, tradition))

    scenarios = [
        _build_scenario(sc, tradition, full_grid_sittings, verdicts_by_cell)
        for sc in sorted(sitting_scenarios)
    ]
    return RawTraditionExport(tradition=tradition, scenarios=scenarios)


def _report_subjects(raws: list[RawTradition]) -> set[str]:
    """The normalized subject set declared by the full-grid report (empty if undeclared)."""
    for r in raws:
        if r.report is not None:
            return {normalize_subject(s) for s in (r.report.get("subjects") or [])}
    return set()


def iter_tradition_raw(
    roots: list[str | Path],
) -> Iterator[tuple[str, RawTraditionExport, list[dict]]]:
    """Yield ``(tradition, RawTraditionExport, resolved_rows)`` one tradition at a time.

    The **streaming** entry point (Phase 2's writer consumes this so only ONE tradition's
    transcripts are live at a time — the whole corpus is ~430 MB of source sittings). The
    resolved rows are small (no transcripts) and are what the caller accumulates for the
    global :func:`source_fingerprint`.
    """
    per_root: list[tuple[Path, dict[str, RawTradition]]] = [
        (Path(r), read_run_root(r)) for r in roots
    ]
    for tradition in sorted({t for _root, parsed in per_root for t in parsed}):
        raws = [parsed[tradition] for _root, parsed in per_root if tradition in parsed]
        fg_root = _full_grid_root_for(tradition, per_root)
        sittings = read_full_grid_sittings(fg_root / tradition / _SITTINGS, tradition)
        resolved = resolve_judgments(raws)  # resolve once; reused for export + fingerprint
        export = build_tradition_raw(tradition, raws, sittings, resolved)
        yield tradition, export, resolved


def build_raw_corpus(roots: list[str | Path]) -> RawCorpus:
    """Read all run roots and build the whole in-memory raw corpus (transform only, no writes).

    Convenience wrapper over :func:`iter_tradition_raw` that materializes every tradition —
    fine for tests and small runs. Phase 2's writer uses the generator directly for the real
    (large) export so it never holds all transcripts at once.
    """
    per_tradition: dict[str, RawTraditionExport] = {}
    global_resolved: list[dict] = []
    subjects_present: set[str] = set()
    judges_present: set[str] = set()

    for tradition, export, resolved in iter_tradition_raw(roots):
        per_tradition[tradition] = export
        global_resolved.extend(resolved)
        subjects_present.update(row["subject"] for row in resolved)
        for scenario in export.scenarios:
            subjects_present.update(c["subject"] for c in scenario.cells)
        judges_present.update(row["judge"] for row in resolved)

    subjects = [s for s in CANONICAL_SUBJECTS if s in subjects_present]
    judges = sorted(judges_present)
    return RawCorpus(
        per_tradition=per_tradition, subjects=subjects, judges=judges, resolved=global_resolved,
    )


# ── Catalog + shard documents (generic; serialization-ready) ───────────────────────


def build_shard(scenario: RawScenario) -> dict:
    """One scenario's self-contained shard document (schema-versioned, contexts + cells)."""
    doc: dict = {"schema_version": SCHEMA_VERSION, "cells": scenario.cells}
    if scenario.contexts:
        doc["contexts"] = scenario.contexts
    return doc


def _shard_path(tradition: str, scenario_id: str) -> str:
    """Manifest-declared shard path, relative to the run dir: `<group>/<item>.json.gz`."""
    return f"{tradition}/{scenario_id}.json.gz"


def build_catalog(corpus: RawCorpus) -> dict:
    """The generic run catalog (manifest): scale/ramp, subjects, judges, axes, items, fingerprint.

    Nothing MultiBench-specific is baked into the *shape* — a non-MultiBench catalog (AFB 0–4)
    uses the identical structure with different values.
    """
    items = []
    for tradition in sorted(corpus.per_tradition):
        export = corpus.per_tradition[tradition]
        for scenario in export.scenarios:
            items.append({
                "id": scenario.scenario_id,
                "label": scenario.scenario_id,
                "group": tradition,
                "shard": _shard_path(tradition, scenario.scenario_id),
            })

    judges = []
    for model in corpus.judges:
        ui = JUDGE_UI.get(model)
        if ui is None:
            raise AnalysisInputError(f"no UI metadata for judge {model!r}")
        judges.append({"key": ui["key"], "label": ui["key"], "fullGrid": ui["full_grid"]})

    return {
        "schema_version": SCHEMA_VERSION,
        "dataset": dict(_DATASET),
        "scale": dict(_SCALE),
        "ramp": list(RAMP_STOPS),
        "subjects": [{"id": s, "label": s} for s in corpus.subjects],
        "judges": judges,
        "conditionAxes": [
            {"key": "framing", "label": "Framing",
             "values": [{"id": f, "label": _humanize(f)} for f in FRAMINGS]},
            {"key": "pressure", "label": "Pressure",
             "values": [{"id": p, "label": _humanize(p)} for p in PRESSURES]},
        ],
        "groupBy": {"key": "tradition", "label": "Tradition"},
        "scopes": [{"id": s, "label": s} for s in SCOPES],
        "items": items,
        "fingerprint": source_fingerprint(corpus.resolved),
    }
