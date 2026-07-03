"""Load judging run-dirs (read-only) with fail-fast validation and the v2 overlay.

Each ``<run-dir>`` is one tradition's judging ``--results-dir``. This module reads
``report.json`` (required) and ``judgments.jsonl`` (required), overlays
``judgments_v2.jsonl`` (optional) by identity key ``(subject, scenario_id,
pressure, framing, judge, scope)`` — v2 wins, exactly as ``judging.judge.
load_judgments`` does so our aggregates match the upstream ``report.json`` — and
applies the spec §4.1 validation table. Everything is untrusted, model-produced
data; validation fails loudly (spec M7), never silently substitutes a default.

Constants (`SCORES`, `_JKEY`) mirror the judging **output contract** (spec §4.1);
they are the input contract this consumer reads, owned here so ``analysis`` need
not depend on the ``judging`` package.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

# The canonical five-value scale (spec §4.1 / §5.3) — bare numbers, no band names.
SCORES: tuple[float, ...] = (-1.0, -0.5, 0.0, 0.5, 1.0)
_ALLOWED: frozenset[float] = frozenset(SCORES)

# Identity key for the v2 overlay and duplicate detection (matches judging's _JKEY).
_JKEY: tuple[str, ...] = ("subject", "scenario_id", "pressure", "framing", "judge", "scope")

# Judgment fields analysis depends on. `raw`/`direction`/`rationale`/`usage`/`ts`
# are part of the judging contract but not consumed here (rationale is used only in
# the Phase 4 report), so they are not required — keeping fixtures lean.
_REQUIRED_JUDGMENT_KEYS: tuple[str, ...] = (
    "subject", "tradition", "scenario_id", "pressure", "framing",
    "judge", "scope", "score", "techniques_used",
)

_REPORT = "report.json"
_JUDGMENTS = "judgments.jsonl"
_JUDGMENTS_V2 = "judgments_v2.jsonl"
_SKIPPED = "skipped.jsonl"


class AnalysisInputError(Exception):
    """A run-dir artifact is missing, malformed, or internally inconsistent (fail-fast)."""


def is_valid_score(value: object) -> bool:
    """True iff *value* is exactly one of the five canonical scores.

    ``bool`` is rejected (not a score) and a *string* score (e.g. the ``"1.0"``
    inside a judge's ``raw`` blob) is rejected — callers must parse the top-level
    numeric ``score``, never ``raw`` (spec §4.1).
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return float(value) in _ALLOWED


@dataclass(frozen=True)
class TraditionRun:
    """One tradition's loaded run-dir: raw report + the overlaid, validated judgments."""

    path: Path
    tradition: str
    subjects: list[str]
    judges: list[str]
    report: dict
    judgments: list[dict]  # base overlaid with v2 (v2 wins by _JKEY)
    skips: list[dict]  # recorded self-judgment skips (expected absences, M5); audit-only


def _key(row: dict) -> tuple:
    return tuple(row[k] for k in _JKEY)


def _iter_jsonl(path: Path):
    """Yield ``(lineno, obj)`` for each non-blank line; 1-indexed for error messages."""
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if line.strip():
            yield lineno, json.loads(line)


def _validate_row(row: dict, tradition: str, subjects: list[str], where: str) -> None:
    """Fail-fast checks for one judgment row (spec §4.1)."""
    for k in _REQUIRED_JUDGMENT_KEYS:
        if k not in row:
            raise AnalysisInputError(f"{where}: judgment missing required key {k!r}")
    if not is_valid_score(row["score"]):
        raise AnalysisInputError(
            f"{where}: invalid score {row['score']!r} — must be one of "
            f"{sorted(_ALLOWED)} (parse the numeric top-level 'score', not 'raw')"
        )
    if row["tradition"] != tradition:
        raise AnalysisInputError(
            f"{where}: judgment tradition {row['tradition']!r} != report.json "
            f"tradition {tradition!r} (cross-metadata mismatch)"
        )
    if row["subject"] not in subjects:
        raise AnalysisInputError(
            f"{where}: judgment subject {row['subject']!r} not in report.json "
            f"subjects {subjects} (cross-metadata mismatch)"
        )


def load_run_dir(path: str | Path) -> TraditionRun:
    """Load one tradition run-dir with validation + v2 overlay (spec §4.1)."""
    p = Path(path)
    if not p.is_dir():
        raise AnalysisInputError(f"run-dir not found: {p}")

    report_path = p / _REPORT
    judgments_path = p / _JUDGMENTS
    if not report_path.is_file():
        raise AnalysisInputError(f"missing required artifact {_REPORT} in {p}")
    if not judgments_path.is_file():
        raise AnalysisInputError(f"missing required artifact {_JUDGMENTS} in {p}")

    report = json.loads(report_path.read_text(encoding="utf-8"))
    tradition = report["tradition"]
    subjects = list(report["subjects"])
    judges = list(report["judges"])

    # Base judgments — validated; duplicate base identity is a hard error (stricter than
    # judging's silent last-wins, per spec §4.1: the upstream should never emit two verdicts
    # for one identity).
    by_key: dict[tuple, dict] = {}
    for lineno, row in _iter_jsonl(judgments_path):
        where = f"{judgments_path}:{lineno}"
        _validate_row(row, tradition, subjects, where)
        k = _key(row)
        if k in by_key:
            raise AnalysisInputError(
                f"{where}: duplicate base identity {dict(zip(_JKEY, k))} "
                f"(each (subject,scenario,pressure,framing,judge,scope) must be unique)"
            )
        by_key[k] = row

    # v2 overrides (optional) — v2 is an **override only**: a v2 row must reference an
    # existing base judgment (it "never adds a vote", spec §4.1 / M5); duplicate v2 keys
    # are tolerated (last wins); an absent/empty file is a valid no-op overlay.
    v2_path = p / _JUDGMENTS_V2
    if v2_path.is_file():
        for lineno, row in _iter_jsonl(v2_path):
            where = f"{v2_path}:{lineno}"
            _validate_row(row, tradition, subjects, where)
            k = _key(row)
            if k not in by_key:
                raise AnalysisInputError(
                    f"{where}: v2 override {dict(zip(_JKEY, k))} references no base "
                    f"judgment (v2 overrides only — it never adds a vote)"
                )
            by_key[k] = row  # override; dup-v2 last-wins, tolerated

    # Self-judgment skips (optional): parsed and represented as expected absences (M5),
    # not aggregated. An absent/empty file is valid (a run with no skips).
    skip_path = p / _SKIPPED
    skips: list[dict] = []
    if skip_path.is_file():
        for lineno, row in _iter_jsonl(skip_path):
            if not isinstance(row, dict):
                raise AnalysisInputError(f"{skip_path}:{lineno}: skip row is not a JSON object")
            skips.append(row)

    return TraditionRun(
        path=p,
        tradition=tradition,
        subjects=subjects,
        judges=judges,
        report=report,
        judgments=list(by_key.values()),
        skips=skips,
    )


def load_corpus(paths: list[str | Path]) -> list[TraditionRun]:
    """Load N run-dirs (one per tradition); duplicate tradition ids are a hard error."""
    if not paths:
        raise AnalysisInputError("no run-dirs given")
    runs: list[TraditionRun] = []
    seen: dict[str, Path] = {}
    for path in paths:
        run = load_run_dir(path)
        if run.tradition in seen:
            raise AnalysisInputError(
                f"duplicate tradition id {run.tradition!r} in run-dirs "
                f"{seen[run.tradition]} and {run.path} (each run-dir must be a distinct tradition)"
            )
        seen[run.tradition] = run.path
        runs.append(run)
    return runs
