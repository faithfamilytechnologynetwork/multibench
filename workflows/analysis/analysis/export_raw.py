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

This module is the **MultiBench binding** of the raw tier: the pure transform (sitting reader +
verdict join + MB shard/catalog builders) and the MB export-computed presets. The generic,
catalog-agnostic pieces live alongside it — the byte-stable writer + size guards in
:mod:`analysis.raw_writer`, and the preset cap + dedup in :mod:`analysis.raw_presets` — so a
second catalog type (the AFB explorer, #54) reuses them without forking. The ``export-raw`` CLI
wraps :func:`write_dataset`.
"""

from __future__ import annotations

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
    RANKING_RULE,
    SCOPES,
    Coverage,
    RawTradition,
    _JUDGMENTS,
    _JUDGMENTS_V2,
    _REPORT,
    _read_rows,
    _scenario_universe,
    assert_uniform_subject_roster,
    coverage_counts_from_judged,
    earns_full_grid,
    judge_coverage,
    normalize_subject,
    resolve_judgments,
)
from analysis.fingerprint import (
    combine_fingerprint,
    content_fingerprint_line,
    fingerprint_line,
    source_fingerprint,
)
from analysis.loaders import AnalysisInputError, _require_safe_segment
from analysis.raw_presets import (  # generic preset cap + per-item/round-robin dedup (#54 reuse)
    PRESET_CAP,  # noqa: F401 — re-exported for tests + Phase-3 reuse
    dedup_per_item as _dedup_per_item,
)
from analysis.raw_writer import (  # generic byte-stable writer, extracted for AFB reuse (#54)
    MAX_SHARD_BYTES,
    MAX_TOTAL_BYTES,
    RawTierWriter,
    WriteSummary,
    json_bytes,
    _require_safe_relpath,  # noqa: F401 — re-exported for tests (add_shard validates internally)
)

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
    """Yield (lineno, obj) for non-blank JSONL lines; fail loud on malformed JSON.

    Streams the file line by line (``sittings.jsonl`` is ~100 MB/tradition) rather than
    reading it whole.
    """
    if not path.is_file():
        raise AnalysisInputError(f"expected sittings file not found: {path}")
    with path.open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
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
    subjects: tuple[str, ...] = ()  # report-declared subject universe (coverage denominator)


@dataclass(frozen=True)
class RawCorpus:
    """The whole raw export, in memory: per-tradition scenarios + the global resolved stream."""

    per_tradition: dict[str, RawTraditionExport]   # keyed by tradition, sorted keys
    subjects: list[str]                            # canonical subjects present (catalog order)
    judges: list[str]                              # canonical judge model-ids present (sorted)
    resolved: list[dict]                           # global resolved-judgments stream (fingerprint)


# Judgment fields the raw tier never ships and never needs downstream (dedup uses `ts`; the
# aggregate/verdict paths use score/direction/rationale) — dropped at read to bound memory.
_HEAVY_JUDGMENT_FIELDS = ("raw", "usage")


def _tradition_dirs(root: Path) -> set[str]:
    """Names of ``<root>/<tradition>/`` subdirs that carry a ``judgments.jsonl`` (no parsing).

    Fails loudly if the root exists but contains no such subdir (matching #49's
    ``read_run_root``) — a mis-mounted/empty run root must not be silently skipped.
    """
    if not root.is_dir():
        raise AnalysisInputError(f"run root not found: {root}")
    trads = {sub.name for sub in root.iterdir()
             if sub.is_dir() and (sub / _JUDGMENTS).is_file()}
    if not trads:
        raise AnalysisInputError(f"no tradition subdirs with {_JUDGMENTS} under {root}")
    return trads


def _read_tradition_dir(sub: Path, tradition: str) -> RawTradition:
    """Read ONE ``<root>/<tradition>/`` into a ``RawTradition``, dropping heavy judgment fields.

    Reuses the #49 row reader/validator (``_read_rows``) so the raw and score tiers share the
    same row contract; then strips ``raw``/``usage`` (never shipped, never needed) so streaming
    one tradition at a time keeps peak memory bounded.
    """
    base = _read_rows(sub / _JUDGMENTS, tradition, reject_dupes=True)
    v2_path = sub / _JUDGMENTS_V2
    v2 = _read_rows(v2_path, tradition, reject_dupes=False) if v2_path.is_file() else []
    for rows in (base, v2):
        for row in rows:
            for f in _HEAVY_JUDGMENT_FIELDS:
                row.pop(f, None)
    report_path = sub / _REPORT
    report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.is_file() else None
    return RawTradition(tradition=tradition, base=base, v2=v2, report=report)


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
# Newcomer-friendly scope labels (id stays the stable key; a generic viewer just shows `label`).
_SCOPE_LABELS = {"turn1": "First response", "full": "After the pressure"}
_SUBJECT_ORDER = {s: i for i, s in enumerate(CANONICAL_SUBJECTS)}


def _build_scenario(scenario_id: str, tradition: str,
                    scenario_sittings: dict[SittingKey, Sitting],
                    verdicts_by_cell: dict[tuple, list[dict]]) -> RawScenario:
    """Assemble one scenario's shard-ready cells + contexts pool.

    ``scenario_sittings`` is already filtered to this scenario (the caller pre-groups, so this
    is linear in the scenario's cells rather than rescanning the whole tradition per scenario).
    """
    contexts: dict[str, str] = {}
    cells: list[dict] = []
    # The transcript is the anchor; a cell exists iff a transcript exists — verdicts without a
    # transcript are caught by the orphan guard.
    for (subj, sc, pr, fr), sitting in scenario_sittings.items():
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

    # Pre-group sittings by scenario once (linear), so each _build_scenario is linear in its
    # own cells rather than rescanning the whole tradition.
    sittings_by_scenario: dict[str, dict[SittingKey, Sitting]] = defaultdict(dict)
    for skey, sitting in full_grid_sittings.items():
        sittings_by_scenario[skey[1]][skey] = sitting

    scenarios = [
        _build_scenario(sc, tradition, sittings_by_scenario[sc], verdicts_by_cell)
        for sc in sorted(sitting_scenarios)
    ]
    return RawTraditionExport(tradition=tradition, scenarios=scenarios,
                              subjects=tuple(sorted(expected_subjects)))


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
    judgments + transcripts are live at a time — the whole corpus is ~430 MB of source
    sittings and the judgment files are large too). Judgments are read **per tradition** (not
    whole-root) with ``raw``/``usage`` dropped; the resolved rows are small (no transcripts)
    and are what the caller accumulates for the global :func:`source_fingerprint`.
    """
    roots = [Path(r) for r in roots]
    per_root_trads = {root: _tradition_dirs(root) for root in roots}
    all_traditions = sorted(set().union(*per_root_trads.values())) if per_root_trads else []
    if not all_traditions:
        raise AnalysisInputError("no tradition subdirs with judgments.jsonl under any run root")

    for tradition in all_traditions:
        pairs = [(root, _read_tradition_dir(root / tradition, tradition))
                 for root in roots if tradition in per_root_trads[root]]
        raws = [rt for _root, rt in pairs]
        # The full-grid (report.json-bearing) run is the SOLE transcript source; exactly one.
        fg_roots = [root for root, rt in pairs if rt.report is not None]
        if not fg_roots:
            raise AnalysisInputError(
                f"{tradition}: no run root provides report.json — cannot source transcripts "
                f"(the full-grid run must supply it)"
            )
        if len(fg_roots) > 1:
            raise AnalysisInputError(
                f"{tradition}: {len(fg_roots)} run roots provide report.json — ambiguous "
                f"transcript source; exactly one full-grid run is expected"
            )
        sittings = read_full_grid_sittings(fg_roots[0] / tradition / _SITTINGS, tradition)
        # Root-order dedup priority (later root wins ties), matching the score tier so a full-grid
        # layer passed AFTER a sample layer wins any same-judge overlap.
        priorities = list(range(len(raws)))
        resolved = resolve_judgments(raws, priorities)  # resolve once; reused for export + fingerprint
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


def accumulate_full_scope_judged(judged: dict[tuple[str, str], int], resolved: list[dict]) -> None:
    """Fold one tradition's resolved rows into a running per-(judge, framing) full-scope count.

    Streaming-safe (tiny counters; the caller keeps freeing the per-tradition rows). Counts the
    **full** resolved rows only — a `--limit` fixture still reports true judge coverage because
    coverage is over the resolved judgments, not the written shard subset.
    """
    for row in resolved:
        if row["scope"] == "full":
            key = (row["judge"], row["framing"])
            judged[key] = judged.get(key, 0) + 1


def _strict_grid_size(total_scenarios: int, n_subjects: int) -> int:
    """The complete both-scope grid: scenarios × subjects × pressures × framings × scopes."""
    return total_scenarios * n_subjects * len(PRESSURES) * len(FRAMINGS) * len(SCOPES)


def _catalog_doc(items: list[dict], subjects: list[str], judge_models: list[str],
                 fingerprint: str, content_fingerprint: str, coverage: Coverage,
                 strict_judged: dict[str, int], strict_expected: int,
                 presets: list[dict] | None = None) -> dict:
    """The generic run catalog (manifest) from lightweight pieces — no transcripts held.

    Nothing MultiBench-specific is baked into the *shape* — a non-MultiBench catalog (AFB 0–4)
    uses the identical structure with different values. ``items`` are sorted by (group, id) for
    a deterministic manifest.

    Two fingerprints, two jobs: ``fingerprint`` (the resolved-judgment stream) is shared with
    the ``results/`` score tier for cross-tier reconciliation; ``content_fingerprint`` (the
    shard byte stream — transcripts+contexts+verdicts) is raw-tier-only and drives baked-vs-GitHub
    coherence, catching transcript/context corrections the judgment fingerprint misses.

    ``coverage`` is the shared coverage table (per judge, per framing) built from the SAME resolved
    rows the score tier uses, so the raw catalog's earned ``fullGrid``/``coverage`` and the score
    manifest's agree by construction; ``rankable`` is the static ranking role.
    """
    judges = []
    for model in judge_models:
        ui = JUDGE_UI.get(model)
        if ui is None:
            raise AnalysisInputError(f"no UI metadata for judge {model!r}")
        judges.append({
            "key": ui["key"], "label": ui["key"],
            "fullGrid": earns_full_grid(coverage, model),
            "rankable": ui["rankable"],
            "coverage": round(judge_coverage(coverage, model), 6),
        })
    # Ranking-integrity guard (#120 re-shape) — the MultiBench raw catalog carries the same invariant
    # as the score manifest (this builder is MB-specific; the AFB tier bypasses it via RawTierWriter).
    # The score tier ranks on the COMBINED two-judge mean, well-defined as long as AT LEAST ONE real
    # judge is STRICTLY complete across the WHOLE both-scope grid (was: exactly one `rankable` judge).
    # Strict completeness is a pooled count: resolved rows are unique per cell and confined to the
    # declared grid, so judged == grid ⟺ every cell covered.
    complete_models = [m for m in judge_models if strict_judged.get(m, 0) == strict_expected]
    if not complete_models:
        got = {m: f"{strict_judged.get(m, 0)}/{strict_expected}" for m in judge_models}
        raise AnalysisInputError(
            f"raw catalog needs at least one strictly-complete judge for the combined ranking; "
            f"none complete ({got})")
    # The combined-mean ranking declaration (mirrors the score manifest; raw shards carry per-judge
    # verdicts, so there is no combined per-cell block here — only the rule + the judges averaged).
    ranking = {"rule": RANKING_RULE, "judges": list(judge_models)}

    return {
        "schema_version": SCHEMA_VERSION,
        "dataset": dict(_DATASET),
        "scale": dict(_SCALE),
        "ramp": list(RAMP_STOPS),
        "subjects": [{"id": s, "label": s} for s in subjects],
        "judges": judges,
        "ranking": ranking,
        "conditionAxes": [
            {"key": "framing", "label": "Framing",
             "values": [{"id": f, "label": _humanize(f)} for f in FRAMINGS]},
            {"key": "pressure", "label": "Pressure",
             "values": [{"id": p, "label": _humanize(p)} for p in PRESSURES]},
        ],
        "groupBy": {"key": "tradition", "label": "Tradition"},
        # Newcomer-facing scope labels (the internal id stays the stable key). "turn1" is the
        # assistant's FIRST answer; "full" is its answer AFTER the pressure push.
        "scopes": [{"id": s, "label": _SCOPE_LABELS.get(s, s)} for s in SCOPES],
        "items": sorted(items, key=lambda it: (it["group"], it["id"])),
        "presets": presets or [],
        "fingerprint": fingerprint,
        "content_fingerprint": content_fingerprint,
    }


# ── Presets (export-computed deep-links) ───────────────────────────────────────────
# Curated navigation, computed at export from fixed thresholds: deterministic, capped, one
# entry per item (a dramatic scenario can't flood a preset), stable-keyed, sparse-safe (a
# candidate that lacks the required judge/scope is simply skipped). Entries are deep-link
# param maps the viewer feeds into the raw-view route (group/item + a/b/framing/pressure/scope).

_GEMINI = JUDGE_UI["gemini-3.6-flash"]["key"]  # "gemini"
_OPUS = JUDGE_UI["claude-opus-4-8"]["key"]     # "opus"

# A cell's per-judge scores, keyed by (tradition, scenario, subject, pressure, framing, scope).
PresetCell = tuple


def accumulate_cell_scores(resolved: list[dict], into: dict[PresetCell, dict[str, float]]) -> None:
    """Fold one tradition's resolved rows into the compact per-cell judge-score map (numbers only)."""
    for r in resolved:
        ui = JUDGE_UI.get(r["judge"])
        if ui is None:
            raise AnalysisInputError(f"no UI metadata for judge {r['judge']!r}")
        key = (r["tradition"], r["scenario_id"], r["subject"], r["pressure"], r["framing"], r["scope"])
        into.setdefault(key, {})[ui["key"]] = r["score"]


def _entry(preset_key: str, group: str, item: str, *, framing: str, pressure: str, scope: str,
           a: str, b: str | None, label: str) -> dict:
    # Condition-axis values are nested under `conditions` (matching the cell shape and keeping
    # the viewer generic over axes), not flattened into the reserved param namespace.
    params = {"group": group, "item": item, "scope": scope, "a": a,
              "conditions": {"framing": framing, "pressure": pressure}}
    if b is not None:
        params["b"] = b
    # Stable key includes group+item (the item identity is (group, id); item ids need not be
    # globally unique across future catalogs).
    return {"key": f"{preset_key}:{group}:{item}", "label": label, "params": params}


# `PRESET_CAP` + `_dedup_per_item` (one entry per (group,item), round-robin across groups up to
# the cap) live in `analysis.raw_presets` — generic over the entry shape, so the AFB tier (#54
# Phase 3) reuses them without importing this MB module. Re-imported here (top of file) so the
# MB preset builders + existing tests keep the same names.


def _top_gemini_subject(group_scores: dict[str, float], exclude: str) -> str | None:
    """The highest-gemini-score subject in a (scenario,pressure,framing) group, != ``exclude``."""
    others = {s: v for s, v in group_scores.items() if s != exclude}
    if not others:
        return None
    return max(others, key=lambda s: (others[s], s))


def _models_split(cells: dict[PresetCell, dict[str, float]]) -> dict | None:
    """Widest cross-subject Gemini spread at turn-1 (pre-pressure)."""
    groups: dict[tuple, dict[str, float]] = defaultdict(dict)
    for (trad, scen, subj, pr, fr, scope), js in cells.items():
        if scope == "turn1" and _GEMINI in js:
            groups[(trad, scen, pr, fr)][subj] = js[_GEMINI]
    cands = []
    for (trad, scen, pr, fr), subs in groups.items():
        if len(subs) < 2:
            continue
        hi = max(subs, key=lambda s: (subs[s], s))
        lo = min(subs, key=lambda s: (subs[s], s))
        spread = subs[hi] - subs[lo]
        if spread <= 0:
            continue
        cands.append((spread, trad, scen, pr, fr, hi, lo))
    cands.sort(key=lambda e: (-e[0], e[1], e[2], _PRESSURE_ORDER[e[3]], _FRAMING_ORDER[e[4]]))
    entries = _dedup_per_item(
        _entry("models-split", trad, scen, framing=fr, pressure=pr, scope="turn1",
               a=hi, b=lo, label=f"{scen} · {hi} vs {lo}")
        for (_spread, trad, scen, pr, fr, hi, lo) in cands
    )
    if not entries:
        return None
    return {"key": "models-split", "label": "Models split",
            "description": "widest turn-1 spread across models", "entries": entries}


def _judges_differed(cells: dict[PresetCell, dict[str, float]]) -> dict | None:
    """Cells (post-pressure) where the two judges' scores differ by ≥ 1.0 on the −1…+1 scale."""
    full_gemini: dict[tuple, dict[str, float]] = defaultdict(dict)
    for (trad, scen, subj, pr, fr, scope), js in cells.items():
        if scope == "full" and _GEMINI in js:
            full_gemini[(trad, scen, pr, fr)][subj] = js[_GEMINI]
    cands = []
    for (trad, scen, subj, pr, fr, scope), js in cells.items():
        if scope == "full" and _GEMINI in js and _OPUS in js and abs(js[_GEMINI] - js[_OPUS]) >= 1.0:
            cands.append((abs(js[_GEMINI] - js[_OPUS]), trad, scen, pr, fr, subj))
    cands.sort(key=lambda e: (-e[0], e[1], e[2], _PRESSURE_ORDER[e[3]], _FRAMING_ORDER[e[4]], e[5]))
    entries = _dedup_per_item(
        _entry("judges-differed", trad, scen, framing=fr, pressure=pr, scope="full",
               a=subj, b=_top_gemini_subject(full_gemini[(trad, scen, pr, fr)], subj),
               label=f"{scen} · judges split on {subj}")
        for (_diff, trad, scen, pr, fr, subj) in cands
    )
    if not entries:
        return None
    return {"key": "judges-differed", "label": "Judges differed",
            "description": "the two judges ≥1 point apart", "entries": entries}


def _steadfastness_cliff(cells: dict[PresetCell, dict[str, float]]) -> dict | None:
    """Largest post-pressure Gemini drop (full − turn1 most negative)."""
    by_cell: dict[tuple, dict[str, float]] = defaultdict(dict)
    for (trad, scen, subj, pr, fr, scope), js in cells.items():
        if _GEMINI in js:
            by_cell[(trad, scen, subj, pr, fr)][scope] = js[_GEMINI]
    cands = []
    for (trad, scen, subj, pr, fr), sc in by_cell.items():
        if "turn1" in sc and "full" in sc:
            drop = sc["full"] - sc["turn1"]
            if drop < 0:
                cands.append((drop, trad, scen, pr, fr, subj))
    # most negative first; then group + canonical condition order + subject (deterministic)
    cands.sort(key=lambda e: (e[0], e[1], e[2], _PRESSURE_ORDER[e[3]], _FRAMING_ORDER[e[4]], e[5]))
    entries = _dedup_per_item(
        _entry("steadfastness-cliff", trad, scen, framing=fr, pressure=pr, scope="full",
               a=subj, b=None, label=f"{scen} · {subj} buckled under pressure")
        for (_drop, trad, scen, pr, fr, subj) in cands
    )
    if not entries:
        return None
    return {"key": "steadfastness-cliff", "label": "Steadfastness cliff",
            "description": "biggest post-pressure drop (Gemini)", "entries": entries}


def compute_presets(cells: dict[PresetCell, dict[str, float]]) -> list[dict]:
    """The three export-computed presets (a preset with no qualifying entries is omitted)."""
    return [p for p in (_models_split(cells), _judges_differed(cells),
                        _steadfastness_cliff(cells)) if p is not None]


def _item_ref(scenario: RawScenario) -> dict:
    return {
        "id": scenario.scenario_id,
        "label": scenario.scenario_id,
        "group": scenario.group,
        "shard": _shard_path(scenario.group, scenario.scenario_id),
    }


def build_catalog(corpus: RawCorpus) -> dict:
    """Build the catalog from a whole in-memory corpus (test/small-run convenience)."""
    items = [_item_ref(s) for export in corpus.per_tradition.values() for s in export.scenarios]
    cells: dict[PresetCell, dict[str, float]] = {}
    accumulate_cell_scores(corpus.resolved, cells)
    # Coverage over the whole corpus's resolved rows (same slicing as the score tier); the
    # denominator's subject count is the report-DECLARED universe, not observed rows.
    judged: dict[tuple[str, str], int] = {}
    accumulate_full_scope_judged(judged, corpus.resolved)
    assert_uniform_subject_roster(e.subjects for e in corpus.per_tradition.values())
    total_scenarios = sum(len(e.scenarios) for e in corpus.per_tradition.values())
    n_subjects = len({s for e in corpus.per_tradition.values() for s in e.subjects})
    coverage = coverage_counts_from_judged(judged, set(corpus.judges), total_scenarios, n_subjects)
    strict_judged: dict[str, int] = {}
    for r in corpus.resolved:
        strict_judged[r["judge"]] = strict_judged.get(r["judge"], 0) + 1
    # Content fingerprint over the same canonical shard bytes the writer would emit (order-independent).
    content_lines = [
        content_fingerprint_line(_shard_path(s.group, s.scenario_id), json_bytes(build_shard(s)))
        for export in corpus.per_tradition.values() for s in export.scenarios
    ]
    return _catalog_doc(items, corpus.subjects, corpus.judges,
                        source_fingerprint(corpus.resolved), combine_fingerprint(content_lines),
                        coverage, strict_judged, _strict_grid_size(total_scenarios, n_subjects),
                        compute_presets(cells))


# ── Deterministic streaming writer ─────────────────────────────────────────────────
# The generic byte-stable writer (gzip mtime=0, size ceilings, content fingerprint, stale-file
# prune) lives in `analysis.raw_writer` (`RawTierWriter`), extracted so the AFB tier (#54) reuses
# it verbatim. `write_dataset` below is the MultiBench binding: it reads the run roots, builds the
# MB catalog + presets, and streams shards through the writer. `MAX_SHARD_BYTES`/`MAX_TOTAL_BYTES`
# are re-exported here (from raw_writer) so they stay monkeypatchable at `export_raw` scope and are
# passed into `writer.write(...)` at call time.


def write_dataset(roots: list[str | Path], out_root: str | Path, run_id: str,
                  limit: int | None = None) -> WriteSummary:
    """Stream the raw tier to ``<out_root>/<run_id>/`` deterministically; enforce size ceilings.

    Serializes everything (validating sizes) BEFORE writing anything, so a violation never
    leaves a partial tier. Stale files from a prior export of the same run-id are pruned.
    ``limit`` caps the number of scenarios written (a small dev fixture); the manifest
    fingerprint then covers exactly the **written** scenarios (self-consistent, but — being a
    subset — it will NOT match the full ``results/`` fingerprint; tests inject an expected one).
    """
    if limit is not None and limit < 1:
        raise AnalysisInputError(f"--limit must be >= 1 (got {limit})")

    writer = RawTierWriter(out_root, run_id, prune=(limit is None))  # validates run_id
    items: list[dict] = []
    subjects_present: set[str] = set()
    judges_present: set[str] = set()
    fp_lines: list[str] = []             # small serialized lines, not full resolved dicts
    cells: dict[PresetCell, dict[str, float]] = {}  # per-cell judge scores (numbers only) for presets
    judged_full: dict[tuple[str, str], int] = {}  # per (judge, framing) full-scope coverage counter
    strict_judged: dict[str, int] = {}   # per-judge ALL-scope cell count (strict completeness)
    subjects_all: set[str] = set()       # the run's subject universe (limit-independent denominator)
    rosters: list[tuple[str, ...]] = []  # each tradition's declared roster (must be uniform)
    total_scenarios = 0                  # full-grid scenario count (limit-independent)
    n_scenarios = 0

    for tradition, export, resolved in iter_tradition_raw(roots):
        _require_safe_segment(tradition, "tradition")
        # Coverage over the FULL resolved rows of this tradition (limit-independent), before the
        # shard-write limit truncates anything.
        # Coverage/judges are accumulated over the FULL resolved rows of EVERY tradition — never
        # truncated by --limit — so a limited dev fixture still reports true judge coverage. The
        # subject count is the report-DECLARED universe (not observed rows).
        accumulate_full_scope_judged(judged_full, resolved)
        for r in resolved:
            strict_judged[r["judge"]] = strict_judged.get(r["judge"], 0) + 1
        subjects_all.update(export.subjects)
        rosters.append(export.subjects)
        judges_present.update(r["judge"] for r in resolved)
        total_scenarios += len(export.scenarios)
        written_here: set[str] = set()
        for scenario in export.scenarios:
            if limit is not None and n_scenarios >= limit:
                break
            _require_safe_segment(scenario.scenario_id, "scenario")
            subjects_present.update(c["subject"] for c in scenario.cells)
            relpath = _shard_path(scenario.group, scenario.scenario_id)
            writer.add_shard(relpath, json_bytes(build_shard(scenario)))  # validates + gz + content fp
            items.append(_item_ref(scenario))
            written_here.add(scenario.scenario_id)
            n_scenarios += 1
        # Fingerprint over exactly the WRITTEN scenarios of this tradition (for a full export that
        # is every row → matches the results/ tier; for a --limit fixture, the written subset).
        # The full `resolved` dicts are freed as the loop moves on. NOTE: no outer break — later
        # traditions still contribute coverage even once the shard limit is reached.
        written_rows = [r for r in resolved if r["scenario_id"] in written_here]
        fp_lines.extend(fingerprint_line(r) for r in written_rows)
        accumulate_cell_scores(written_rows, cells)  # for presets (numbers only)

    assert_uniform_subject_roster(rosters)  # one uniform subject grid across traditions
    subjects = [s for s in CANONICAL_SUBJECTS if s in subjects_present]
    coverage = coverage_counts_from_judged(
        judged_full, set(judges_present), total_scenarios, len(subjects_all))
    catalog = _catalog_doc(items, subjects, sorted(judges_present),
                           combine_fingerprint(fp_lines), writer.content_fingerprint,
                           coverage, strict_judged, _strict_grid_size(total_scenarios, len(subjects_all)),
                           compute_presets(cells))
    return writer.write(catalog, max_shard_bytes=MAX_SHARD_BYTES, max_total_bytes=MAX_TOTAL_BYTES)
