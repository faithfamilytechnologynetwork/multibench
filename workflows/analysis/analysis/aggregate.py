"""Cross-tradition aggregation — the cell reducer + report aggregates (spec §4.2).

Faithfully reproduces ``judging.report.build_report``'s numeric semantics so every
recomputed aggregate matches the upstream ``report.json`` to ≤1e−9 (spec M3): a
*cell* score is the **mean of its present judges' scores** (v2 already overlaid by
the loader), and a breakdown *mean* is the **unweighted mean of the in-scope cell
scores** (uncovered cells excluded — never counted as 0.0; an empty set is
``None``). This is the port's deliberate deviation from JaleesBench's raw-judgment
pooling (spec §4.7 D5): cell-level averaging keeps subjects comparable whenever
coverage is uneven (a pre-#28 self-judge-skipped run, or any partial run).

``check_parity`` is the self-check backing the M3 acceptance criterion.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from analysis.core_imports import FRAMINGS, PRESSURES
from analysis.loaders import SCORES

# Aggregate scorecard/by_scenario are taken at the headline condition: unstated framing,
# after-pressure (full) scope — matching judging.report.
_HEADLINE_FRAMING = "unstated"
_FULL = "full"
_TURN1 = "turn1"

Cell = tuple  # (subject, scenario_id, pressure, framing, scope)


def mean(values) -> float | None:
    """Unweighted mean on the −1…+1 scale, or ``None`` if empty (never 0.0; spec §5.9)."""
    vals = list(values)
    return sum(vals) / len(vals) if vals else None


def _cell(j: dict) -> Cell:
    return (j["subject"], j["scenario_id"], j["pressure"], j["framing"], j["scope"])


def cell_scores(judgments: list[dict]) -> dict[Cell, float]:
    """Mean of each cell's present-judge scores — the canonical reducer (spec §4.2)."""
    by: dict[Cell, list[float]] = defaultdict(list)
    for j in judgments:
        by[_cell(j)].append(j["score"])
    return {c: mean(v) for c, v in by.items()}  # a cell exists iff it has ≥1 score


def _mean_over(
    cs: dict[Cell, float],
    subject: str,
    *,
    framing: str | None = None,
    scope: str | None = None,
    pressure: str | None = None,
    scenarios: set[str] | None = None,
) -> float | None:
    """Unweighted mean of in-scope cell scores; ``None`` if none match (never 0.0)."""
    vals: list[float] = []
    for (su, sc, pr, fr, scp), val in cs.items():
        if su != subject:
            continue
        if framing is not None and fr != framing:
            continue
        if scope is not None and scp != scope:
            continue
        if pressure is not None and pr != pressure:
            continue
        if scenarios is not None and sc not in scenarios:
            continue
        vals.append(val)
    return mean(vals)


@dataclass(frozen=True)
class TraditionAggregate:
    """The recomputed cross-tradition-comparable aggregates for one tradition.

    Field shapes mirror ``report.json`` so the parity self-check is a direct
    comparison. ``report`` retains the raw upstream doc for display-only fields
    (cost, counts, taxonomies) that are read through rather than recomputed.
    """

    tradition: str
    subjects: list[str]
    judges: list[str]
    scenario_ids: list[str]
    cell_scores: dict[Cell, float]
    scorecard: dict[str, dict]
    score_distribution: dict[str, dict[str, int]]
    agreement: dict
    scenario_agreement: dict[str, float]
    by_scenario: dict[str, dict[str, float | None]]
    report: dict


def aggregate_tradition(run) -> TraditionAggregate:
    """Compute one tradition's aggregates from its overlaid judgments (spec §4.2)."""
    judgments = run.judgments
    subjects = run.subjects
    cs = cell_scores(judgments)
    # Scenario universe = the bootstrap cluster set. Derive it from the run's `by_scenario`
    # (upstream keys it by judgments ∪ sittings — the full *expected* coverage), unioned with
    # judged scenarios. A scenario that was collected but produced ZERO judgments (a partial
    # run) must NOT silently vanish, or the scenario-cluster bootstrap resamples over too few
    # clusters and understates every CI (CMAP finding, PR #27). Such a scenario carries no
    # cells, so it dilutes resamples (widening CIs) exactly as it should.
    scenario_ids = sorted(
        set(run.report.get("by_scenario", {})) | {j["scenario_id"] for j in judgments}
    )

    # 1. Scorecard — headline (unstated, full), steadfastness (full − turn1), per-framing.
    scorecard: dict[str, dict] = {}
    for s in subjects:
        full = _mean_over(cs, s, framing=_HEADLINE_FRAMING, scope=_FULL)
        t1 = _mean_over(cs, s, framing=_HEADLINE_FRAMING, scope=_TURN1)
        steadfast = None if (full is None or t1 is None) else full - t1
        by_pressure: dict[str, float | None] = {}
        for pr in PRESSURES:
            pf = _mean_over(cs, s, framing=_HEADLINE_FRAMING, scope=_FULL, pressure=pr)
            pt = _mean_over(cs, s, framing=_HEADLINE_FRAMING, scope=_TURN1, pressure=pr)
            by_pressure[pr] = None if (pf is None or pt is None) else pf - pt
        scorecard[s] = {
            "headline": full,
            "steadfastness": steadfast,
            "steadfastness_by_pressure": by_pressure,
            "by_framing": {fr: _mean_over(cs, s, framing=fr, scope=_FULL) for fr in FRAMINGS},
        }

    # 2. Score distribution over per-judge verdicts (string keys, matching report.json).
    distribution: dict[str, dict[str, int]] = {
        s: {str(sc): 0 for sc in SCORES} for s in subjects
    }
    for j in judgments:
        key = str(float(j["score"]))
        if key in distribution[j["subject"]]:
            distribution[j["subject"]][key] += 1

    # 3. Inter-judge agreement (cells with ≥2 present judgments).
    by_cell: dict[Cell, list[float]] = defaultdict(list)
    for j in judgments:
        by_cell[_cell(j)].append(j["score"])
    multi = [v for v in by_cell.values() if len(v) >= 2]
    exact = sum(1 for v in multi if max(v) == min(v))
    within_one = sum(1 for v in multi if (max(v) - min(v)) <= 0.5)
    agreement = {
        "cells": len(multi),
        "exact_pct": (exact / len(multi)) if multi else None,
        "within_one_pct": (within_one / len(multi)) if multi else None,
    }

    # Per-scenario agreement, scoped to the headline (unstated, full) condition so it
    # annotates the by_scenario table (matches judging.report).
    scen_cells: dict[str, list[list[float]]] = defaultdict(list)
    for cell, scores in by_cell.items():
        if cell[3] == _HEADLINE_FRAMING and cell[4] == _FULL and len(scores) >= 2:
            scen_cells[cell[1]].append(scores)
    scenario_agreement = {
        sid: sum(1 for v in cl if max(v) == min(v)) / len(cl) for sid, cl in scen_cells.items()
    }
    worst = min(scenario_agreement, key=lambda s: scenario_agreement[s], default=None)
    agreement["worst_scenario"] = worst
    agreement["worst_scenario_exact_pct"] = scenario_agreement.get(worst) if worst else None

    # 4. Per-scenario results (unstated, full).
    by_scenario = {
        sid: {
            s: _mean_over(cs, s, framing=_HEADLINE_FRAMING, scope=_FULL, scenarios={sid})
            for s in subjects
        }
        for sid in scenario_ids
    }

    return TraditionAggregate(
        tradition=run.tradition,
        subjects=subjects,
        judges=run.judges,
        scenario_ids=scenario_ids,
        cell_scores=cs,
        scorecard=scorecard,
        score_distribution=distribution,
        agreement=agreement,
        scenario_agreement=scenario_agreement,
        by_scenario=by_scenario,
        report=run.report,
    )


def _num_eq(a: float | None, b: float | None, tol: float) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return abs(a - b) <= tol


def check_parity(agg: TraditionAggregate, tol: float = 1e-9) -> list[str]:
    """Return human-readable mismatches between recomputed aggregates and the upstream
    ``report.json`` (empty list = full ≤``tol`` parity). Backs the M3 self-check (spec §4.2).

    Compares the recomputed fields the spec names — headline, by_framing, steadfastness
    (+ by_pressure), and inter-judge agreement (exact/within-one) — plus
    score_distribution / by_scenario / scenario_agreement. Display-only fields (cost,
    counts, taxonomies) are read through, not recomputed, so they are not compared.
    A pre-#28 report.json's ``techniques`` block is ignored (no longer recomputed).
    """
    rep = agg.report
    diffs: list[str] = []

    def cmp(label: str, a, b):
        if not _num_eq(a, b, tol):
            diffs.append(f"{agg.tradition}: {label}: recomputed {a!r} != report.json {b!r}")

    for s in agg.subjects:
        rsc = rep["scorecard"][s]
        asc = agg.scorecard[s]
        cmp(f"scorecard[{s}].headline", asc["headline"], rsc["headline"])
        cmp(f"scorecard[{s}].steadfastness", asc["steadfastness"], rsc["steadfastness"])
        for fr in FRAMINGS:
            cmp(f"scorecard[{s}].by_framing[{fr}]",
                asc["by_framing"].get(fr), rsc["by_framing"].get(fr))
        for pr in PRESSURES:
            cmp(f"scorecard[{s}].steadfastness_by_pressure[{pr}]",
                asc["steadfastness_by_pressure"].get(pr),
                rsc["steadfastness_by_pressure"].get(pr))
        for k, v in agg.score_distribution[s].items():
            cmp(f"score_distribution[{s}][{k}]", v, rep["score_distribution"][s].get(k))
        for sid in agg.scenario_ids:
            cmp(f"by_scenario[{sid}][{s}]",
                agg.by_scenario[sid].get(s), rep["by_scenario"][sid].get(s))

    for k in ("cells", "exact_pct", "within_one_pct"):
        cmp(f"agreement[{k}]", agg.agreement[k], rep["agreement"][k])
    cmp("agreement[worst_scenario_exact_pct]",
        agg.agreement["worst_scenario_exact_pct"],
        rep["agreement"].get("worst_scenario_exact_pct"))
    if agg.agreement["worst_scenario"] != rep["agreement"].get("worst_scenario"):
        diffs.append(
            f"{agg.tradition}: agreement[worst_scenario]: recomputed "
            f"{agg.agreement['worst_scenario']!r} != report.json "
            f"{rep['agreement'].get('worst_scenario')!r}"
        )
    for sid, v in agg.scenario_agreement.items():
        cmp(f"scenario_agreement[{sid}]", v, rep["scenario_agreement"].get(sid))

    return diffs
