"""Scenario-cluster bootstrap 95% CIs — the port of JaleesBench ``paper_stats.py``.

The load-bearing statistics piece the pilot report lacks (spec §4.3). Faithful to
the source in the ways that matter (spec §4.7):

- **N_BOOT = 5000, SEED = 12345** (port defaults; overridable).
- **One shared ``RESAMPLES`` list per tradition** (F2): built once and reused by
  every ``point_and_ci`` and ``diff_ci`` of that tradition, so paired quantities
  (recognition/instruction gaps, steadfastness) are computed on the *same*
  resampled scenarios per draw — the CI on a difference absorbs the correlation.
- **Percentile method**: 95% CI = ``np.percentile(boots, [2.5, 97.5])``.

Deviations from the source (spec §4.7 D3/D5):

- **Resampling unit = the scenario cluster** (5 per tradition), not 140 probes; each
  bootstrap draw resamples the tradition's scenario indices with replacement.
- The resampled quantity is the **cell-mean** aggregate (present-judge cell scores),
  expressed as ``sum(cell values) / count(cells)`` per scenario — the same
  ``(sum, count)`` form as the source, but over **cells** (not raw judgments), so the
  asymmetric judge panel is not double-weighted.

Every required CI is **per-(tradition, subject)** over that tradition's own cluster
set — no pooled / cross-tradition CI (IQ3 resolved, spec §4.3).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from analysis.aggregate import TraditionAggregate
from analysis.core_imports import FRAMINGS, PRESSURES

N_BOOT = 5000
SEED = 12345

_UNSTATED, _STATED, _GUIDED = "unstated", "stated", "guided"
_FULL, _TURN1 = "full", "turn1"

# A per-scenario (sum, count) pair for one filtered slice of cells.
SumCount = tuple[np.ndarray, np.ndarray]
CI = list  # [point, lo, hi]


def make_resamples(n_scenarios: int, n_boot: int = N_BOOT, seed: int = SEED) -> list[np.ndarray]:
    """One shared list of resample index arrays for a tradition (F2).

    Generated **once** and reused for every estimate of that tradition so paired
    quantities use identical scenario draws. Each element resamples the tradition's
    ``n_scenarios`` scenario indices with replacement (the cluster bootstrap).
    """
    rng = np.random.default_rng(seed)
    return [rng.integers(0, n_scenarios, n_scenarios) for _ in range(n_boot)]


def _sumcount(
    agg: TraditionAggregate,
    scenario_index: dict[str, int],
    subject: str,
    *,
    framing: str | None = None,
    scope: str | None = None,
    pressure: str | None = None,
) -> SumCount:
    """Per-scenario (sum-of-cell-values, count-of-cells) arrays for one filtered slice.

    ``sum(sum_arr)/sum(count_arr)`` is exactly the cell-mean aggregate (``_mean_over``);
    resampling scenario indices over these arrays is the cluster bootstrap of it.
    """
    n = len(scenario_index)
    s = np.zeros(n)
    c = np.zeros(n)
    for (su, sc, pr, fr, scp), val in agg.cell_scores.items():
        if su != subject:
            continue
        if framing is not None and fr != framing:
            continue
        if scope is not None and scp != scope:
            continue
        if pressure is not None and pr != pressure:
            continue
        i = scenario_index[sc]
        s[i] += val
        c[i] += 1
    return s, c


def _point(sc: SumCount) -> float | None:
    s, c = sc
    tot = c.sum()
    return None if tot == 0 else float(s.sum() / tot)


def _est(sc: SumCount, idx: np.ndarray) -> float:
    s, c = sc
    return s[idx].sum() / c[idx].sum()


def point_and_ci(sc: SumCount, resamples: list[np.ndarray]) -> CI | None:
    """(point, lo, hi) for one cell-mean slice; ``None`` if the slice has no cells."""
    p = _point(sc)
    if p is None:
        return None
    boots = np.array([_est(sc, idx) for idx in resamples])
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return [p, float(lo), float(hi)]


def diff_ci(sc_a: SumCount, sc_b: SumCount, resamples: list[np.ndarray]) -> CI | None:
    """(point, lo, hi) for (mean_a − mean_b), **paired** on the same resampled scenarios.

    Uses the shared ``resamples`` for both terms per draw so the difference's CI
    reflects the correlation between a and b (F2). ``None`` if either slice is empty.
    """
    pa, pb = _point(sc_a), _point(sc_b)
    if pa is None or pb is None:
        return None
    boots = np.array([_est(sc_a, idx) - _est(sc_b, idx) for idx in resamples])
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return [pa - pb, float(lo), float(hi)]


@dataclass(frozen=True)
class SubjectStats:
    """Bootstrap CIs for one subject within one tradition (spec §4.3)."""

    headline: CI | None
    recognition_gap: CI | None  # stated − unstated (full)
    instruction_gap: CI | None  # guided − stated (full)
    steadfastness: CI | None  # unstated: full − turn1
    steadfastness_by_pressure: dict[str, CI | None]


@dataclass(frozen=True)
class TraditionStats:
    tradition: str
    subjects: list[str]
    scenario_ids: list[str]
    n_boot: int
    seed: int
    per_subject: dict[str, SubjectStats]


def compute_tradition_stats(
    agg: TraditionAggregate, *, n_boot: int = N_BOOT, seed: int = SEED
) -> TraditionStats:
    """Bootstrap CIs for every subject of one tradition, over its scenario clusters."""
    scenario_index = {sid: i for i, sid in enumerate(agg.scenario_ids)}
    resamples = make_resamples(len(scenario_index), n_boot=n_boot, seed=seed)  # shared (F2)

    per_subject: dict[str, SubjectStats] = {}
    for s in agg.subjects:
        def sc(**kw):
            return _sumcount(agg, scenario_index, s, **kw)

        headline = point_and_ci(sc(framing=_UNSTATED, scope=_FULL), resamples)
        recognition = diff_ci(
            sc(framing=_STATED, scope=_FULL), sc(framing=_UNSTATED, scope=_FULL), resamples
        )
        instruction = diff_ci(
            sc(framing=_GUIDED, scope=_FULL), sc(framing=_STATED, scope=_FULL), resamples
        )
        steadfast = diff_ci(
            sc(framing=_UNSTATED, scope=_FULL), sc(framing=_UNSTATED, scope=_TURN1), resamples
        )
        by_pressure = {
            pr: diff_ci(
                sc(framing=_UNSTATED, scope=_FULL, pressure=pr),
                sc(framing=_UNSTATED, scope=_TURN1, pressure=pr),
                resamples,
            )
            for pr in PRESSURES
        }
        per_subject[s] = SubjectStats(
            headline=headline,
            recognition_gap=recognition,
            instruction_gap=instruction,
            steadfastness=steadfast,
            steadfastness_by_pressure=by_pressure,
        )

    return TraditionStats(
        tradition=agg.tradition,
        subjects=list(agg.subjects),
        scenario_ids=list(agg.scenario_ids),
        n_boot=n_boot,
        seed=seed,
        per_subject=per_subject,
    )


_RND = 4  # fixed serialization precision → byte-stable analysis_stats.json


def _round_ci(ci: CI | None) -> list | None:
    return None if ci is None else [round(x, _RND) for x in ci]


def stats_to_dict(stats: list[TraditionStats]) -> dict:
    """Deterministic ``analysis_stats.json`` payload (the ``paper_stats.json`` analogue).

    Ordering is fixed (traditions in input order; subjects in report order; framings/
    pressures in canonical core order) and CI floats are rounded to a fixed precision,
    so ``json.dumps(indent=2)`` is byte-stable across runs (spec §4.3 / §7.3). In-memory
    only — the on-disk write is Phase 4's ``cli.report``.
    """
    if not stats:
        return {"meta": _meta(N_BOOT, SEED), "traditions": {}}

    traditions: dict[str, dict] = {}
    for ts in stats:
        subjects: dict[str, dict] = {}
        for s in ts.subjects:
            ss = ts.per_subject[s]
            subjects[s] = {
                "headline": _round_ci(ss.headline),
                "recognition_gap": _round_ci(ss.recognition_gap),
                "instruction_gap": _round_ci(ss.instruction_gap),
                "steadfastness": _round_ci(ss.steadfastness),
                "steadfastness_by_pressure": {
                    pr: _round_ci(ss.steadfastness_by_pressure.get(pr)) for pr in PRESSURES
                },
            }
        traditions[ts.tradition] = {
            "scenario_ids": list(ts.scenario_ids),
            "subjects": subjects,
        }

    return {"meta": _meta(stats[0].n_boot, stats[0].seed), "traditions": traditions}


def _meta(n_boot: int, seed: int) -> dict:
    return {
        "n_boot": n_boot,
        "seed": seed,
        "ci": "95% percentile [2.5, 97.5]",
        "resample_unit": "scenario cluster",
        "framings": list(FRAMINGS),
        "pressures": list(PRESSURES),
    }
