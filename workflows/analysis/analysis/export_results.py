"""Results export — normalize + aggregate judging runs into browsable slice tables (#49).

This is the correctness heart of the multibrowser results explorer. It reads the raw
judging run roots (the full-grid **Gemini** run plus the report-less **Opus** judge
layers), collapses the model-id spelling differences across runs, resolves the Opus
alias collision + the ``judgments_v2.jsonl`` overlay, and produces per-tradition
**slice tables** the SPA reads at runtime:

* per (subject, framing, scope, pressure-incl-``"all"``, judge) → the breakdown **mean**
  + coverage (``n_judged`` / ``n_expected``), and
* per (subject, framing, pressure-incl-``"all"``, judge) → a matched-cell **steadfastness**
  (``mean(full) − mean(turn1)`` over cells present in *both* scopes) + ``matched_n``.

Aggregation reuses the canonical semantics in :mod:`analysis.aggregate`
(``cell_scores`` + ``breakdown_mean``): a breakdown is the unweighted mean of the
in-scope cells, uncovered cells excluded (never 0). Because the leaderboard ranks on
Gemini (a full grid), the SPA's only cross-tradition statistic is an equal-weight mean
of these per-tradition means — which reconciles with the paper's ``subj_overall`` by
construction (see the parity self-check in the tests).

Phase 1 (this module) is the pure transform: no dataset is written to disk here — the
writer, manifest, and CLI live in Phase 2.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from analysis.aggregate import Cell, breakdown_mean, cell_scores, mean
from analysis.core_imports import FRAMINGS, PRESSURES
from analysis.loaders import (
    AnalysisInputError,
    _REQUIRED_JUDGMENT_KEYS,
    is_valid_score,
)

# ── Canonical vocabularies ────────────────────────────────────────────────────────
# Subjects and judges are spelled differently across the source runs (the OpenRouter
# tail-fill uses provider-prefixed, lowercased ids; Qwen even drops the ``-Instruct``
# segment). Normalization is an EXPLICIT map, not an algorithm — a "strip prefix +
# lowercase" rule silently mis-merges Qwen. An unmapped id fails loudly (fail-fast).

SCOPES: tuple[str, ...] = ("turn1", "full")
PRESSURE_ALL = "all"

# canonical subject id → every source variant that means the same subject
_SUBJECT_VARIANTS: dict[str, tuple[str, ...]] = {
    "Qwen/Qwen3-235B-A22B-Instruct-2507": ("qwen/qwen3-235b-a22b-2507",),
    "claude-sonnet-5": ("anthropic/claude-sonnet-5",),
    "gemini-3.6-flash": ("google/gemini-3.6-flash",),
    "gpt-5.6-terra": ("openai/gpt-5.6-terra",),
    "thinkingmachines/Inkling": ("thinkingmachines/inkling",),
}
CANONICAL_SUBJECTS: tuple[str, ...] = tuple(_SUBJECT_VARIANTS)
_SUBJECT_ALIAS: dict[str, str] = {
    variant: canon for canon, variants in _SUBJECT_VARIANTS.items() for variant in variants
}
_SUBJECT_ALIAS.update({canon: canon for canon in _SUBJECT_VARIANTS})

# canonical judge model-id → source variants. The two Opus aliases collapse to one.
_JUDGE_VARIANTS: dict[str, tuple[str, ...]] = {
    "gemini-3.6-flash": (),
    "claude-opus-4-8": ("anthropic/claude-opus-4.8",),
}
_JUDGE_ALIAS: dict[str, str] = {
    variant: canon for canon, variants in _JUDGE_VARIANTS.items() for variant in variants
}
_JUDGE_ALIAS.update({canon: canon for canon in _JUDGE_VARIANTS})

# Short UI keys the SPA uses in deep-links / the judge selector, and whether the judge
# is a full-grid ranking judge (Gemini) or a validation layer (Opus).
JUDGE_UI: dict[str, dict] = {
    "gemini-3.6-flash": {"key": "gemini", "full_grid": True},
    "claude-opus-4-8": {"key": "opus", "full_grid": False},
}


def normalize_subject(subject: str) -> str:
    """Map a source subject id to its canonical spelling; raise on an unmapped id."""
    try:
        return _SUBJECT_ALIAS[subject]
    except KeyError:
        raise AnalysisInputError(
            f"unmapped subject id {subject!r} — add it to _SUBJECT_VARIANTS "
            f"(known: {sorted(_SUBJECT_ALIAS)})"
        ) from None


def normalize_judge(judge: str) -> str:
    """Map a source judge id to its canonical model id; raise on an unmapped id."""
    try:
        return _JUDGE_ALIAS[judge]
    except KeyError:
        raise AnalysisInputError(
            f"unmapped judge id {judge!r} — add it to _JUDGE_VARIANTS "
            f"(known: {sorted(_JUDGE_ALIAS)})"
        ) from None


# ── Reading raw run roots ─────────────────────────────────────────────────────────
# A run *root* is a directory of per-tradition subdirs (``<root>/<tradition>/``), each
# with ``judgments.jsonl`` (required), ``judgments_v2.jsonl`` (optional override), and
# ``report.json`` (present only for the full-grid Gemini run). We deliberately do NOT
# use ``loaders.load_run_dir`` — it requires ``report.json`` (the Opus layers have
# none) and ``load_corpus`` rejects the same tradition appearing in more than one run.

_JUDGMENTS = "judgments.jsonl"
_JUDGMENTS_V2 = "judgments_v2.jsonl"
_REPORT = "report.json"


@dataclass(frozen=True)
class RawTradition:
    """One tradition's rows read from ONE run root (unnormalized), plus optional report."""

    tradition: str
    base: list[dict]
    v2: list[dict]
    report: dict | None


def _iter_jsonl(path: Path):
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if line.strip():
            yield lineno, json.loads(line)


# Raw identity within a single file — matches the loader's ``_JKEY`` (raw judge alias),
# used to reject same-file duplicate base identities exactly as ``load_run_dir`` does.
_RAW_JKEY: tuple[str, ...] = ("subject", "scenario_id", "pressure", "framing", "judge", "scope")


def _read_rows(path: Path, tradition: str, *, reject_dupes: bool) -> list[dict]:
    """Read + minimally validate judgment rows (reuses the loader's row contract).

    With ``reject_dupes`` (base files), a repeated raw identity in one file is a hard
    error — matching ``load_run_dir``. The expected Opus *alias* collision is a
    *cross-alias* case (different raw judge) resolved later in ``resolve_judgments``,
    not a same-file duplicate, so this stays strict without rejecting the collision.
    """
    rows: list[dict] = []
    seen: set[tuple] = set()
    for lineno, row in _iter_jsonl(path):
        where = f"{path}:{lineno}"
        for k in _REQUIRED_JUDGMENT_KEYS:
            if k not in row:
                raise AnalysisInputError(f"{where}: judgment missing required key {k!r}")
        if not is_valid_score(row["score"]):
            raise AnalysisInputError(
                f"{where}: invalid score {row['score']!r} "
                f"(parse the numeric top-level 'score', not 'raw')"
            )
        if row["tradition"] != tradition:
            raise AnalysisInputError(
                f"{where}: judgment tradition {row['tradition']!r} != dir tradition {tradition!r}"
            )
        if reject_dupes:
            rk = tuple(row[k] for k in _RAW_JKEY)
            if rk in seen:
                raise AnalysisInputError(
                    f"{where}: duplicate base identity {dict(zip(_RAW_JKEY, rk))} "
                    f"(each raw identity must be unique within a file)"
                )
            seen.add(rk)
        rows.append(row)
    return rows


def read_run_root(root: str | Path) -> dict[str, RawTradition]:
    """Read every ``<root>/<tradition>/`` subdir that has a ``judgments.jsonl``."""
    p = Path(root)
    if not p.is_dir():
        raise AnalysisInputError(f"run root not found: {p}")
    out: dict[str, RawTradition] = {}
    for sub in sorted(x for x in p.iterdir() if x.is_dir()):
        jpath = sub / _JUDGMENTS
        if not jpath.is_file():
            continue  # not a tradition dir (e.g. analysis-out/)
        tradition = sub.name
        base = _read_rows(jpath, tradition, reject_dupes=True)
        v2_path = sub / _JUDGMENTS_V2
        # v2 tolerates repeated keys (last wins, per the loader), so no dup-rejection.
        v2 = _read_rows(v2_path, tradition, reject_dupes=False) if v2_path.is_file() else []
        report_path = sub / _REPORT
        report = (
            json.loads(report_path.read_text(encoding="utf-8"))
            if report_path.is_file()
            else None
        )
        out[tradition] = RawTradition(tradition=tradition, base=base, v2=v2, report=report)
    if not out:
        raise AnalysisInputError(f"no tradition subdirs with {_JUDGMENTS} under {p}")
    return out


# ── Normalize + overlay + dedup ───────────────────────────────────────────────────
# Normalized identity — includes judge, excludes tradition (matches the loader's
# ``_JKEY``). Judge MUST be normalized before keying, so the two Opus aliases collide
# onto one identity and the later-``ts`` winner is chosen (the collision is real:
# ~1,800 sunni-islam cells appear under both aliases). Field order is shared with
# ``_canon_row`` below so the two never drift.
_NORM_FIELDS: tuple[str, ...] = ("subject", "scenario_id", "pressure", "framing", "judge", "scope")


def _normalized_id(row: dict) -> tuple:
    return (
        normalize_subject(row["subject"]),
        row["scenario_id"],
        row["pressure"],
        row["framing"],
        normalize_judge(row["judge"]),
        row["scope"],
    )


def _canon_row(row: dict, key: tuple) -> dict:
    """Row copy with ``subject``/``judge`` rewritten to their canonical ids."""
    out = dict(row)
    out["subject"], out["judge"] = key[0], key[4]
    return out


def resolve_judgments(raws: list[RawTradition]) -> list[dict]:
    """Normalize, overlay v2, and dedup one tradition's rows across run roots.

    Winner rule (``v2-then-dedupe``): a ``judgments_v2.jsonl`` row (tier 1) beats a base
    row (tier 0) for the same normalized identity; within a tier the later ``ts`` wins.
    A v2 row whose identity has no base judgment is rejected — v2 is an override that
    **never adds a vote** (the loader's invariant, preserved after normalization).
    Returns rows with ``subject``/``judge`` rewritten to their canonical ids.
    """
    base_rows = [r for t in raws for r in t.base]
    v2_rows = [r for t in raws for r in t.v2]
    winners: dict[tuple, tuple[int, str, dict]] = {}  # id → (tier, ts, normalized_row)

    for row in base_rows:
        key = _normalized_id(row)
        ts = str(row.get("ts", ""))
        cur = winners.get(key)
        if cur is None or (0, ts) >= (cur[0], cur[1]):
            winners[key] = (0, ts, _canon_row(row, key))
    base_keys = set(winners)

    for row in v2_rows:
        key = _normalized_id(row)
        if key not in base_keys:
            raise AnalysisInputError(
                f"v2 override {dict(zip(_NORM_FIELDS, key))} references no base judgment "
                f"(v2 overrides only — it never adds a vote)"
            )
        ts = str(row.get("ts", ""))
        cur = winners.get(key)
        if cur is None or (1, ts) >= (cur[0], cur[1]):
            winners[key] = (1, ts, _canon_row(row, key))
    return [w[2] for w in winners.values()]


# ── Per-tradition slice tables ────────────────────────────────────────────────────


@dataclass(frozen=True)
class Slice:
    """One breakdown cell of the shard: a mean over judged cells + coverage."""

    mean: float
    n_judged: int
    n_expected: int


@dataclass(frozen=True)
class Steadfastness:
    """Matched-cell full − turn1 for one (subject, framing, pressure, judge) slice."""

    value: float
    matched_n: int


@dataclass(frozen=True)
class TraditionExport:
    """One tradition's export payload (in-memory; Phase 2 serializes it)."""

    tradition: str
    n_scenarios: int
    judges: list[str]
    # keyed by (judge, subject, framing, scope, pressure_or_"all")
    means: dict[tuple, Slice]
    # keyed by (judge, subject, framing, pressure_or_"all")
    steadfastness: dict[tuple, Steadfastness]


def _count_cells(cs: dict[Cell, float], subject: str, framing: str, scope: str,
                 pressure: str | None) -> int:
    """Number of judged cells in a slice — the coverage numerator (``n_judged``)."""
    return sum(
        1
        for (su, _sc, pr, fr, scp) in cs
        if su == subject and fr == framing and scp == scope and (pressure is None or pr == pressure)
    )


def _matched_steadfastness(cs: dict[Cell, float], subject: str, framing: str,
                           pressure: str | None) -> Steadfastness | None:
    """mean(full) − mean(turn1) over (scenario,pressure) cells present in BOTH scopes."""
    full_by: dict[tuple, float] = {}
    turn1_by: dict[tuple, float] = {}
    for (su, sc, pr, fr, scp), val in cs.items():
        if su != subject or fr != framing:
            continue
        if pressure is not None and pr != pressure:
            continue
        if scp == "full":
            full_by[(sc, pr)] = val
        elif scp == "turn1":
            turn1_by[(sc, pr)] = val
    matched = full_by.keys() & turn1_by.keys()
    if not matched:
        return None
    f = mean(full_by[k] for k in matched)
    t = mean(turn1_by[k] for k in matched)
    return Steadfastness(value=f - t, matched_n=len(matched))


def _scenario_universe(raws: list[RawTradition], tradition: str) -> list[str]:
    """The judge-independent full-grid scenario set — from the run bearing report.json.

    Pinning ``n_scenarios`` to the Gemini full grid (not to observed rows) is what keeps
    coverage honest: a 2-cell Opus panel must read as low coverage, not ~100%.
    """
    reports = [r.report for r in raws if r.report is not None]
    if not reports:
        raise AnalysisInputError(
            f"{tradition}: no run root provides report.json — cannot pin the full-grid "
            f"scenario universe (the Gemini run must supply it)"
        )
    universe = set(reports[0].get("by_scenario", {}))
    if not universe:
        raise AnalysisInputError(f"{tradition}: report.json has an empty by_scenario universe")
    # If more than one run supplies a report, they must agree on the universe.
    for other in reports[1:]:
        if set(other.get("by_scenario", {})) != universe:
            raise AnalysisInputError(
                f"{tradition}: run roots disagree on the full-grid scenario universe"
            )
    return sorted(universe)


def build_tradition_export(tradition: str, raws: list[RawTradition]) -> TraditionExport:
    """Aggregate one tradition's merged rows into slice tables + steadfastness."""
    judgments = resolve_judgments(raws)
    universe = set(_scenario_universe(raws, tradition))
    n_scenarios = len(universe)

    # Every judged scenario must be within the full-grid universe (else the universe is
    # wrong / runs are inconsistent).
    stray = {j["scenario_id"] for j in judgments} - universe
    if stray:
        raise AnalysisInputError(
            f"{tradition}: judged scenarios {sorted(stray)} not in the full-grid "
            f"universe ({n_scenarios} scenarios) — inconsistent runs"
        )

    judges = sorted({j["judge"] for j in judgments})
    means: dict[tuple, Slice] = {}
    steadfast: dict[tuple, Steadfastness] = {}

    for judge in judges:
        cs = cell_scores([j for j in judgments if j["judge"] == judge])
        for subject in CANONICAL_SUBJECTS:
            for framing in FRAMINGS:
                # steadfastness (scope-collapsing) per pressure incl. "all"
                for pressure in (*PRESSURES, PRESSURE_ALL):
                    pr = None if pressure == PRESSURE_ALL else pressure
                    st = _matched_steadfastness(cs, subject, framing, pr)
                    if st is not None:
                        steadfast[(judge, subject, framing, pressure)] = st
                for scope in SCOPES:
                    for pressure in (*PRESSURES, PRESSURE_ALL):
                        pr = None if pressure == PRESSURE_ALL else pressure
                        m = breakdown_mean(cs, subject, framing=framing, scope=scope, pressure=pr)
                        if m is None:
                            continue  # zero coverage → omit; SPA derives n_expected
                        n_expected = n_scenarios * (len(PRESSURES) if pr is None else 1)
                        means[(judge, subject, framing, scope, pressure)] = Slice(
                            mean=m,
                            n_judged=_count_cells(cs, subject, framing, scope, pr),
                            n_expected=n_expected,
                        )

    return TraditionExport(
        tradition=tradition,
        n_scenarios=n_scenarios,
        judges=judges,
        means=means,
        steadfastness=steadfast,
    )


def build_corpus_export(roots: list[str | Path]) -> dict[str, TraditionExport]:
    """Read all run roots and build per-tradition exports (keyed by tradition)."""
    per_root = [read_run_root(r) for r in roots]
    traditions = sorted({t for root in per_root for t in root})
    out: dict[str, TraditionExport] = {}
    for tradition in traditions:
        raws = [root[tradition] for root in per_root if tradition in root]
        out[tradition] = build_tradition_export(tradition, raws)
    return out


# ── Parity helper (used by the real-data parity test) ─────────────────────────────


def leaderboard_mean_of_means(
    exports: dict[str, TraditionExport], judge: str, subject: str, framing: str,
    scope: str, pressure: str = PRESSURE_ALL,
) -> float | None:
    """Equal-weight mean across traditions of the per-tradition slice means.

    This is exactly what the SPA computes for the leaderboard; the parity test asserts
    it equals the paper's ``subj_overall`` for judge=Gemini, scope=full, pressure=all.
    """
    vals = [
        exp.means[(judge, subject, framing, scope, pressure)].mean
        for exp in exports.values()
        if (judge, subject, framing, scope, pressure) in exp.means
    ]
    return sum(vals) / len(vals) if vals else None
