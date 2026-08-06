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
import re
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
            try:
                yield lineno, json.loads(line)
            except json.JSONDecodeError as e:
                raise AnalysisInputError(f"{path}:{lineno}: malformed JSON ({e})") from e


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
        # Validate the dimension vocab: an out-of-vocab framing/pressure/scope would be silently
        # excluded from every aggregate (build_tradition_export iterates the known vocab) while
        # still counted in the manifest — so fail loudly instead (fail-fast).
        if row["framing"] not in FRAMINGS:
            raise AnalysisInputError(f"{where}: unknown framing {row['framing']!r} (not in {FRAMINGS})")
        if row["pressure"] not in PRESSURES:
            raise AnalysisInputError(f"{where}: unknown pressure {row['pressure']!r} (not in {sorted(PRESSURES)})")
        if row["scope"] not in SCOPES:
            raise AnalysisInputError(f"{where}: unknown scope {row['scope']!r} (not in {SCOPES})")
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

    Winner rules:
    * **Base** rows: for a normalized identity present under both Opus aliases (the real
      cross-alias collision), the later ``ts`` wins — the architect-specified dedup.
    * **v2** rows: a ``judgments_v2.jsonl`` row always overrides the base for its identity,
      and among v2 rows for one identity the **last in file order** wins — matching the
      canonical loader's last-wins (independent of ``ts``, which may be missing/non-
      monotonic on a correction file).
    A v2 row whose identity has no base judgment is rejected — v2 is an override that
    **never adds a vote** (the loader's invariant, preserved after normalization).
    Returns rows with ``subject``/``judge`` rewritten to their canonical ids.
    """
    base_rows = [r for t in raws for r in t.base]
    v2_rows = [r for t in raws for r in t.v2]  # preserves per-file line order
    winners: dict[tuple, dict] = {}  # normalized id → winning (canonical) row

    # Base: later-ts wins on a cross-alias collision.
    base_ts: dict[tuple, str] = {}
    for row in base_rows:
        key = _normalized_id(row)
        ts = str(row.get("ts", ""))
        if key not in winners or ts >= base_ts[key]:
            winners[key] = _canon_row(row, key)
            base_ts[key] = ts
    base_keys = set(winners)

    # v2: file-order last-wins, always overriding base (loader parity).
    for row in v2_rows:
        key = _normalized_id(row)
        if key not in base_keys:
            raise AnalysisInputError(
                f"v2 override {dict(zip(_NORM_FIELDS, key))} references no base judgment "
                f"(v2 overrides only — it never adds a vote)"
            )
        winners[key] = _canon_row(row, key)  # later v2 line overrides earlier
    return list(winners.values())


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
    n_judgments: dict[str, int]  # judge → deduped judgment count (manifest counts)
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
    n_judgments = {jg: sum(1 for j in judgments if j["judge"] == jg) for jg in judges}
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
        n_judgments=n_judgments,
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


# ── Serialization (Phase 2): manifest + per-tradition shards ──────────────────────
# The committed, versioned dataset the SPA reads at runtime. Compact: nested dicts,
# means as ``[mean, n_judged, n_expected]`` and steadfastness as ``[value, matched_n]``;
# zero-coverage slices are simply absent (the SPA derives ``n_expected`` from
# ``n_scenarios``). ``json.dumps(sort_keys=True)`` makes the output byte-stable.

SCHEMA_VERSION = 1
MAX_TOTAL_BYTES = 8 * 1024 * 1024   # ≤ 8 MB per run (spec size ceiling)
MAX_SHARD_BYTES = 1 * 1024 * 1024   # ≤ 1 MB per tradition shard

_MANIFEST = "manifest.json"

# A safe single path segment — no separators, no `..`, no leading dot/dash. Guards the
# destructive parts of write_dataset (mkdir + unlink of stale shards) against a run-id or
# tradition name that would escape the output dir via path traversal.
_SAFE_SEGMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def _require_safe_segment(name: str, kind: str) -> None:
    if not _SAFE_SEGMENT.match(name) or ".." in name:
        raise AnalysisInputError(
            f"unsafe {kind} {name!r} — must be a single path segment matching "
            f"[A-Za-z0-9][A-Za-z0-9._-]* (no separators or '..')"
        )


def _nested_set(d: dict, path: tuple, value) -> None:
    for k in path[:-1]:
        d = d.setdefault(k, {})
    d[path[-1]] = value


def serialize_tradition(exp: TraditionExport) -> dict:
    """One tradition's shard document."""
    means: dict = {}
    for (judge, subject, framing, scope, pressure), sl in exp.means.items():
        _nested_set(means, (judge, subject, framing, scope, pressure),
                    [sl.mean, sl.n_judged, sl.n_expected])
    steadfast: dict = {}
    for (judge, subject, framing, pressure), st in exp.steadfastness.items():
        _nested_set(steadfast, (judge, subject, framing, pressure),
                    [st.value, st.matched_n])
    return {
        "tradition": exp.tradition,
        "n_scenarios": exp.n_scenarios,
        "judges": exp.judges,
        "means": means,
        "steadfastness": steadfast,
    }


def _coverage_summary(exports: dict[str, TraditionExport]) -> dict:
    """Per (judge, framing) coverage pooled over traditions+subjects at scope=full,
    pressure=all — a headline honesty signal (Gemini full-grid; Opus stated/guided sample).

    NOTE: this is a *summary* only. The SPA must badge each view from the per-slice
    ``n_judged/n_expected`` in the shards, not from this roll-up (Opus *unstated* is full
    while stated/guided is a sample — a single per-judge flag would misrepresent that).
    """
    cov: dict[str, dict[str, dict[str, int]]] = {}
    for exp in exports.values():
        for (judge, _subject, framing, scope, pressure), sl in exp.means.items():
            if scope != "full" or pressure != PRESSURE_ALL:
                continue
            cell = cov.setdefault(judge, {}).setdefault(framing, {"n_judged": 0, "n_expected": 0})
            cell["n_judged"] += sl.n_judged
            cell["n_expected"] += sl.n_expected
    return cov


def _assert_full_grid(exports: dict[str, TraditionExport], judge_model: str) -> None:
    """Fail-fast unless *judge_model* covered the COMPLETE grid — every tradition × subject ×
    framing × scope × pressure. The UI trusts ``full_grid: true`` to rank on this judge, so the
    flag must be earned at export time, not asserted statically. Coverage is checked per specific
    pressure (n_judged == n_scenarios) across every subject/framing/scope, for every tradition.
    """
    for tradition, exp in exports.items():
        for subject in CANONICAL_SUBJECTS:
            for framing in FRAMINGS:
                for scope in SCOPES:
                    for pressure in PRESSURES:
                        sl = exp.means.get((judge_model, subject, framing, scope, pressure))
                        if sl is None or sl.n_judged != sl.n_expected:
                            got = "missing" if sl is None else f"{sl.n_judged}/{sl.n_expected}"
                            raise AnalysisInputError(
                                f"full_grid judge {judge_model!r} has incomplete coverage at "
                                f"{tradition}/{subject}/{framing}/{scope}/{pressure} ({got}) — "
                                f"cannot write full_grid:true"
                            )


def build_manifest(exports: dict[str, TraditionExport], run_id: str,
                   generated_at: str) -> dict:
    """The run-level manifest (subjects, judges, framings, pressures, scopes, counts)."""
    all_judges = sorted({j for exp in exports.values() for j in exp.judges})
    judges_meta = []
    for model in all_judges:
        if model not in JUDGE_UI:  # fail-fast — a normalized judge is always known here
            raise AnalysisInputError(f"no UI metadata for judge {model!r}")
        ui = JUDGE_UI[model]
        if ui["full_grid"]:
            _assert_full_grid(exports, model)  # earn the flag, don't assert it statically
        aliases = sorted({model, *_JUDGE_VARIANTS.get(model, ())})
        judges_meta.append({
            "key": ui["key"], "model": model, "aliases": aliases,
            # full_grid = guaranteed full across ALL framings (Gemini yes; Opus no —
            # its stated/guided layer is a sample). Per-view sampling is read per-slice.
            "full_grid": ui["full_grid"],
        })
    counts: dict[str, int] = {}
    for exp in exports.values():
        for jg, n in exp.n_judgments.items():
            counts[jg] = counts.get(jg, 0) + n
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "generated_at": generated_at,
        "subjects": list(CANONICAL_SUBJECTS),
        "judges": judges_meta,
        "framings": list(FRAMINGS),
        "pressures": list(PRESSURES),
        "pressure_all": PRESSURE_ALL,
        "scopes": list(SCOPES),
        "metrics": ["turn1", "full", "steadfastness"],
        "traditions": [
            {"id": t, "n_scenarios": exports[t].n_scenarios, "shard": f"{t}.json"}
            for t in sorted(exports)
        ],
        "counts": {"judgments": counts, "coverage": _coverage_summary(exports)},
    }


def _dump(obj: dict) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def write_dataset(exports: dict[str, TraditionExport], out_root: str | Path,
                  run_id: str, generated_at: str) -> list[Path]:
    """Write ``<out_root>/<run_id>/{manifest.json, <tradition>.json}``; enforce size ceilings.

    Serializes and **validates all sizes before writing anything**, so a size violation
    never leaves a partial dataset, and the total is computed over the full new set (not
    just newly-written files). Stale ``*.json`` from a prior export of the same run-id are
    pruned, so regeneration does not depend on prior directory contents. Returns the
    written paths.
    """
    # 0. Path-safety: run_id + tradition names must be safe segments (write_dataset unlinks).
    _require_safe_segment(run_id, "run-id")
    for tradition in exports:
        _require_safe_segment(tradition, "tradition")

    # 1. Serialize everything in memory.
    docs: dict[str, bytes] = {
        _MANIFEST: _dump(build_manifest(exports, run_id, generated_at)).encode("utf-8")
    }
    for tradition in sorted(exports):
        docs[f"{tradition}.json"] = _dump(serialize_tradition(exports[tradition])).encode("utf-8")

    # 2. Validate sizes BEFORE any write.
    total = 0
    for name, payload in docs.items():
        if name != _MANIFEST and len(payload) > MAX_SHARD_BYTES:
            raise AnalysisInputError(
                f"{name} is {len(payload)} bytes (> {MAX_SHARD_BYTES} shard ceiling)"
            )
        total += len(payload)
    if total > MAX_TOTAL_BYTES:
        raise AnalysisInputError(f"dataset total {total} bytes (> {MAX_TOTAL_BYTES} ceiling)")

    # 3. Write, pruning any stale *.json not in the new set.
    run_dir = Path(out_root) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    for old in run_dir.glob("*.json"):
        if old.name not in docs:
            old.unlink()
    written: list[Path] = []
    for name, payload in docs.items():
        path = run_dir / name
        path.write_bytes(payload)
        written.append(path)
    return sorted(written)


def export_dataset(roots: list[str | Path], out_root: str | Path, run_id: str,
                   generated_at: str) -> list[Path]:
    """End-to-end: read run roots → build exports → write the committed dataset."""
    return write_dataset(build_corpus_export(roots), out_root, run_id, generated_at)
