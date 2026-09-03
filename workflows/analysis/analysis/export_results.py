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
from analysis.fingerprint import combine_fingerprint, fingerprint_line
from analysis.loaders import (
    AnalysisInputError,
    _REQUIRED_JUDGMENT_KEYS,
    _require_safe_segment,  # noqa: F401 — moved here (neutral home); re-exported for callers/tests
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

# canonical judge model-id → source variants. The two Opus aliases collapse to one; the Gemini
# judge run via OpenRouter (issue #43 funded path) records the provider-prefixed slug
# ``google/gemini-3.6-flash``, which collapses to the canonical ``gemini-3.6-flash`` — same
# slug-normalization the Opus judge and every subject already get (a #89 OpenRouter-slug run).
_JUDGE_VARIANTS: dict[str, tuple[str, ...]] = {
    "gemini-3.6-flash": ("google/gemini-3.6-flash",),
    "claude-opus-4-8": ("anthropic/claude-opus-4.8",),
}
_JUDGE_ALIAS: dict[str, str] = {
    variant: canon for canon, variants in _JUDGE_VARIANTS.items() for variant in variants
}
_JUDGE_ALIAS.update({canon: canon for canon in _JUDGE_VARIANTS})

# Short UI keys the SPA uses in deep-links / the judge selector, and whether the judge is
# **rankable** — the leaderboard ranks on the single rankable judge (Gemini). `rankable` is a
# STATIC property of the judge's ROLE and is deliberately decoupled from `full_grid` (#96): a
# validation judge that reaches full-grid coverage earns the `full_grid` *badge* but must NEVER
# become rankable. `full_grid` itself is no longer stored here — it is EARNED per run from actual
# coverage (see `earns_full_grid`); this dict carries only the stable key + ranking role.
JUDGE_UI: dict[str, dict] = {
    "gemini-3.6-flash": {"key": "gemini", "rankable": True},
    "claude-opus-4-8": {"key": "opus", "rankable": False},
}

# A judge earns the `full_grid` badge when it covered every framing at full-grid scale. Coverage
# is never a clean 100% (judges persistently refuse / emit unparseable verdicts on a few cells),
# so the badge is TOLERANT: all three framings present with per-framing coverage >= this floor.
# It cleanly separates a designed sub-sample (~0.14) from a full-grid layer (~0.999). Ranking
# eligibility stays strict — a `rankable` judge must be strictly complete (`_assert_full_grid`).
FULL_GRID_MIN_COVERAGE = 0.95


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


def resolve_judgments(raws: list[RawTradition],
                      priorities: list[int] | None = None) -> list[dict]:
    """Normalize, overlay v2, and dedup one tradition's rows across run roots.

    Winner rules:
    * **Base** rows: the winner for a normalized identity is chosen by ``(priority, ts)`` —
      a higher-``priority`` source wins outright, ties broken by later ``ts``. ``priorities`` is
      parallel to ``raws`` (one per run root); the default (all 0) reduces to the original
      later-``ts`` rule, so every run whose caller does not set priorities is byte-identical.
      Root-order priority lets a full-grid layer deterministically outrank a sample layer for
      the SAME judge across roots, while a WITHIN-root cross-alias collision (e.g. the two Opus
      aliases in one file — equal priority) still resolves by the architect-specified later-``ts``.
    * **v2** rows: a ``judgments_v2.jsonl`` row always overrides the base for its identity,
      and among v2 rows for one identity the **last in file order** wins — matching the
      canonical loader's last-wins (independent of ``ts``, which may be missing/non-
      monotonic on a correction file).
    A v2 row whose identity has no base judgment is rejected — v2 is an override that
    **never adds a vote** (the loader's invariant, preserved after normalization).
    Returns rows with ``subject``/``judge`` rewritten to their canonical ids.
    """
    if priorities is None:
        priorities = [0] * len(raws)
    if len(priorities) != len(raws):
        raise AnalysisInputError(
            f"priorities length {len(priorities)} != raws length {len(raws)}")
    base_rows = [(prio, r) for prio, t in zip(priorities, raws) for r in t.base]
    v2_rows = [(prio, r) for prio, t in zip(priorities, raws) for r in t.v2]  # per-file line order
    winners: dict[tuple, dict] = {}  # normalized id → winning (canonical) row

    # Base: higher (priority, ts) wins; ">=" keeps last-in-iteration on an exact tie.
    best: dict[tuple, int] = {}  # winning priority per identity (v2 must respect it)
    best_pt: dict[tuple, tuple[int, str]] = {}
    for prio, row in base_rows:
        key = _normalized_id(row)
        cand = (prio, str(row.get("ts", "")))
        if key not in winners or cand >= best_pt[key]:
            winners[key] = _canon_row(row, key)
            best_pt[key] = cand
            best[key] = prio
    base_keys = set(winners)

    # v2 overrides base, but MUST respect source priority: a lower-priority v2 (e.g. a sample
    # correction) never displaces a higher-priority verdict (the full-grid layer). Among v2 at
    # the winner's priority, file-order last-wins (loader parity).
    for prio, row in v2_rows:
        key = _normalized_id(row)
        if key not in base_keys:
            raise AnalysisInputError(
                f"v2 override {dict(zip(_NORM_FIELDS, key))} references no base judgment "
                f"(v2 overrides only — it never adds a vote)"
            )
        if prio >= best[key]:
            winners[key] = _canon_row(row, key)  # later same-or-higher-priority v2 overrides
            best[key] = prio
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
    # per-row fingerprint LINES for this tradition — retained (instead of the full resolved
    # dicts) so build_manifest computes the cross-tier source fingerprint (#51) from the SAME
    # rows the aggregates were built from, without holding every judgment dict live. Required
    # (no default) so a manifest can never be stamped with a silently-empty fingerprint.
    fingerprint_lines: list[str]
    # the report-DECLARED subject universe (normalized), pinned to the full-grid grid like
    # n_scenarios — the coverage denominator uses this (not observed subjects), so a wholly
    # unjudged subject reads as a coverage gap rather than shrinking the denominator.
    subjects: tuple[str, ...]


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


def _subject_universe(raws: list[RawTradition], tradition: str) -> tuple[str, ...]:
    """The report-declared subject set (normalized), pinned to the full-grid grid like scenarios.

    Using the DECLARED universe (not observed rows) as the coverage denominator keeps the badge
    honest: a judge that never scored a whole subject reads as a gap, not ~full coverage.
    """
    for r in raws:
        if r.report is not None:
            declared = r.report.get("subjects") or []
            if not declared:
                raise AnalysisInputError(
                    f"{tradition}: report.json declares no subjects — cannot pin the subject grid")
            return tuple(sorted({normalize_subject(s) for s in declared}))
    raise AnalysisInputError(
        f"{tradition}: no run root provides report.json — cannot pin the subject universe")


def build_tradition_export(tradition: str, raws: list[RawTradition],
                           priorities: list[int] | None = None) -> TraditionExport:
    """Aggregate one tradition's merged rows into slice tables + steadfastness."""
    judgments = resolve_judgments(raws, priorities)
    universe = set(_scenario_universe(raws, tradition))
    subjects = _subject_universe(raws, tradition)
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
        fingerprint_lines=[fingerprint_line(r) for r in judgments],
        subjects=subjects,
    )


def build_corpus_export(roots: list[str | Path]) -> dict[str, TraditionExport]:
    """Read all run roots and build per-tradition exports (keyed by tradition).

    A row's dedup priority is its **run-root position** (later root wins ties): the resolved
    ``raws``/``priorities`` for a tradition preserve the ``roots`` order, so passing a full-grid
    layer AFTER a sample layer makes the full-grid verdict win any same-judge overlap while a
    tradition absent from an earlier root keeps its relative (still-higher) position.
    """
    per_root = [read_run_root(r) for r in roots]
    traditions = sorted({t for root in per_root for t in root})
    out: dict[str, TraditionExport] = {}
    for tradition in traditions:
        present = [(i, root[tradition]) for i, root in enumerate(per_root) if tradition in root]
        raws = [rt for _i, rt in present]
        priorities = [i for i, _rt in present]
        out[tradition] = build_tradition_export(tradition, raws, priorities)
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

# `_require_safe_segment` (the path-traversal guard) now lives in `analysis.loaders` (a neutral
# module) so the generic raw writer can share it without importing this MB-specific exporter (#54).
# Imported at the top of this file; re-exported here for the existing callers/tests.


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


# ── Coverage contract (single source for counts.coverage, the earned full_grid badge, and the
# per-judge coverage fraction — so the three can never disagree) ────────────────────────────────
# Coverage is keyed per (judge, framing) at scope=full, pressure=all — the same slicing the
# manifest already displayed. ``n_expected`` is pinned to the FULL grid (total scenarios ×
# subjects × pressures) for EVERY framing, so a framing a judge never touched reads honestly as
# 0/full rather than being silently omitted. The raw tier (export_raw) computes the identical
# shape from resolved rows via ``coverage_counts_from_judged`` — the tiers agree by construction.

Coverage = dict[str, dict[str, dict[str, int]]]  # judge -> framing -> {n_judged, n_expected}


def coverage_counts_from_judged(judged: dict[tuple[str, str], int], judges: set[str],
                                total_scenarios: int, n_subjects: int) -> Coverage:
    """Build the coverage table from per-(judge, framing) judged counts + the grid size.

    ``judged[(judge, framing)]`` is the number of judged full-scope cells (pooled over subjects,
    scenarios, pressures). ``n_expected`` per framing is the full grid ``total_scenarios ×
    n_subjects × |pressures|``, where ``n_subjects`` is the run's actual subject universe (the
    distinct subjects that appear across all judges — 5 on the real run, fewer on small fixtures),
    so the denominator matches the grid the run actually spans. Every framing is present for every
    listed judge (an untouched framing reads honestly as 0/full).
    """
    ne = total_scenarios * n_subjects * len(PRESSURES)
    return {
        judge: {fr: {"n_judged": judged.get((judge, fr), 0), "n_expected": ne} for fr in FRAMINGS}
        for judge in sorted(judges)
    }


def _coverage_from_exports(exports: dict[str, TraditionExport]) -> Coverage:
    """Score-tier coverage: judged full-scope cells summed from the slice tables.

    The denominator's subject count is the report-DECLARED universe (``exp.subjects``), so a
    wholly-unjudged subject is an honest coverage gap, not a shrunk denominator.
    """
    total_scenarios = sum(exp.n_scenarios for exp in exports.values())
    subjects: set[str] = set()
    judged: dict[tuple[str, str], int] = {}
    judges: set[str] = set()
    for exp in exports.values():
        subjects.update(exp.subjects)
        for (judge, _subject, framing, scope, pressure), sl in exp.means.items():
            if scope == "full" and pressure == PRESSURE_ALL:
                judged[(judge, framing)] = judged.get((judge, framing), 0) + sl.n_judged
                judges.add(judge)
    return coverage_counts_from_judged(judged, judges, total_scenarios, len(subjects))


def earns_full_grid(coverage: Coverage, judge: str,
                    threshold: float = FULL_GRID_MIN_COVERAGE) -> bool:
    """True iff *judge* covered ALL three framings with per-framing coverage >= *threshold*.

    The tolerant `full_grid` badge (#96): a judge earns it from real coverage, not static config.
    A designed sub-sample (one framing ~0.14) fails; a full-grid layer (~0.999) passes.
    """
    framings = coverage.get(judge)
    if not framings:
        return False
    for framing in FRAMINGS:
        cell = framings.get(framing)
        if not cell or cell["n_expected"] == 0:
            return False
        if cell["n_judged"] / cell["n_expected"] < threshold:
            return False
    return True


def judge_coverage(coverage: Coverage, judge: str) -> float:
    """The judge's overall coverage fraction (pooled n_judged / n_expected across framings)."""
    framings = coverage.get(judge, {})
    n_judged = sum(c["n_judged"] for c in framings.values())
    n_expected = sum(c["n_expected"] for c in framings.values())
    return n_judged / n_expected if n_expected else 0.0


def _assert_full_grid(exports: dict[str, TraditionExport], judge_model: str) -> None:
    """Fail-fast unless *judge_model* covered the COMPLETE grid — every tradition × subject ×
    framing × scope × pressure. This is the STRICT gate for a **rankable** judge (Gemini): the
    leaderboard ranks on it, so its grid must have no gaps. (The tolerant `full_grid` *badge* for
    validation judges is a separate, earned signal — see ``earns_full_grid``.) Coverage is checked
    per specific pressure (n_judged == n_scenarios) across every subject/framing/scope, per tradition.
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
    for model in all_judges:  # validate UI metadata first, so an unknown judge is the reported error
        if model not in JUDGE_UI:  # fail-fast — a normalized judge is always known here
            raise AnalysisInputError(f"no UI metadata for judge {model!r}")
    coverage = _coverage_from_exports(exports)
    rankable = [m for m in all_judges if JUDGE_UI[m]["rankable"]]
    if len(rankable) != 1:  # the leaderboard ranks on exactly one judge (Gemini)
        raise AnalysisInputError(
            f"exactly one rankable judge required, found {rankable} among {all_judges}")
    judges_meta = []
    for model in all_judges:
        ui = JUDGE_UI[model]
        if ui["rankable"]:
            # A rankable judge MUST be strictly complete — ranking cannot rest on a gappy grid.
            _assert_full_grid(exports, model)
        aliases = sorted({model, *_JUDGE_VARIANTS.get(model, ())})
        judges_meta.append({
            "key": ui["key"], "model": model, "aliases": aliases,
            # full_grid = the EARNED coverage badge (tolerant; #96). rankable = the STATIC ranking
            # role (Gemini only). coverage = the actual pooled fraction for display/citation.
            # Earning full_grid never makes a judge rankable.
            "full_grid": earns_full_grid(coverage, model),
            "rankable": ui["rankable"],
            "coverage": round(judge_coverage(coverage, model), 6),
        })
    counts: dict[str, int] = {}
    for exp in exports.values():
        for jg, n in exp.n_judgments.items():
            counts[jg] = counts.get(jg, 0) + n
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "generated_at": generated_at,
        # Cross-tier source fingerprint (#51): computed from the SAME resolved-judgments stream
        # the aggregates were built from, so the raw tier's manifest fingerprint must match this
        # for the same run-id. (The raw tier omits generated_at entirely — this is the stable
        # provenance both tiers share.)
        "fingerprint": combine_fingerprint(
            line for exp in exports.values() for line in exp.fingerprint_lines),
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
        "counts": {"judgments": counts, "coverage": coverage},
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
