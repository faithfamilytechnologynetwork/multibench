"""Bootstrap-stats tests (spec T4): paired draw-sharing (F2), percentile CI,
determinism, and agreement of the CI point with the aggregate point estimate.
"""

import json
from pathlib import Path

import numpy as np
import pytest

from analysis.aggregate import aggregate_tradition
from analysis.core_imports import PRESSURES
from analysis.loaders import load_run_dir
from analysis.stats import (
    N_BOOT,
    SEED,
    _est,
    _sumcount,
    compute_tradition_stats,
    diff_ci,
    make_resamples,
    point_and_ci,
    stats_to_dict,
)

FIX = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture(scope="module")
def buddhism_agg():
    return aggregate_tradition(load_run_dir(FIX / "buddhism"))


def _index(agg):
    return {sid: i for i, sid in enumerate(agg.scenario_ids)}


# --- paired-point identity (F2) ----------------------------------------------

def test_diff_point_equals_difference_of_points(buddhism_agg):
    agg = buddhism_agg
    idx = _index(agg)
    s = agg.subjects[1]
    resamples = make_resamples(len(idx), n_boot=200, seed=SEED)
    a = _sumcount(agg, idx, s, framing="stated", scope="full")
    b = _sumcount(agg, idx, s, framing="unstated", scope="full")
    dpoint = diff_ci(a, b, resamples)[0]
    pa = point_and_ci(a, resamples)[0]
    pb = point_and_ci(b, resamples)[0]
    assert dpoint == pytest.approx(pa - pb, abs=1e-12)


# --- shared draws reduce difference variance (the load-bearing F2 property) ---

def test_shared_draws_reduce_diff_variance(buddhism_agg):
    agg = buddhism_agg
    idx = _index(agg)
    s = agg.subjects[1]
    n = len(idx)
    a = _sumcount(agg, idx, s, framing="stated", scope="full")
    b = _sumcount(agg, idx, s, framing="unstated", scope="full")

    shared = make_resamples(n, n_boot=2000, seed=SEED)
    paired = np.array([_est(a, r) - _est(b, r) for r in shared])

    # Independent draws for a and b (different seeds) — breaks the pairing.
    ra = make_resamples(n, n_boot=2000, seed=1)
    rb = make_resamples(n, n_boot=2000, seed=2)
    independent = np.array([_est(a, r1) - _est(b, r2) for r1, r2 in zip(ra, rb)])

    # a and b are positively correlated (same scenarios), so pairing cancels shared
    # scenario variance — the paired difference CI is tighter.
    assert paired.var() < independent.var()


# --- percentile method + ordering --------------------------------------------

def test_ci_is_percentile_and_ordered(buddhism_agg):
    agg = buddhism_agg
    idx = _index(agg)
    s = agg.subjects[1]
    resamples = make_resamples(len(idx), n_boot=1000, seed=SEED)
    sc = _sumcount(agg, idx, s, framing="unstated", scope="full")
    point, lo, hi = point_and_ci(sc, resamples)
    boots = np.array([_est(sc, r) for r in resamples])
    exp_lo, exp_hi = np.percentile(boots, [2.5, 97.5])
    assert lo == pytest.approx(exp_lo)
    assert hi == pytest.approx(exp_hi)
    assert lo <= point <= hi


# --- CI point agrees with the aggregate point estimate -----------------------

def test_headline_ci_point_matches_aggregate(buddhism_agg):
    agg = buddhism_agg
    stats = compute_tradition_stats(agg, n_boot=200, seed=SEED)
    for s in agg.subjects:
        assert stats.per_subject[s].headline[0] == pytest.approx(
            agg.scorecard[s]["headline"], abs=1e-9
        )


# --- determinism / byte-stability --------------------------------------------

def test_compute_is_reproducible(buddhism_agg):
    a = compute_tradition_stats(buddhism_agg, n_boot=300, seed=SEED)
    b = compute_tradition_stats(buddhism_agg, n_boot=300, seed=SEED)
    assert a.per_subject == b.per_subject


def test_stats_to_dict_is_byte_stable(buddhism_agg):
    stats = [compute_tradition_stats(buddhism_agg, n_boot=300, seed=SEED)]
    d1 = json.dumps(stats_to_dict(stats), indent=2)
    d2 = json.dumps(stats_to_dict(stats), indent=2)
    assert d1 == d2


def test_stats_to_dict_shape(buddhism_agg):
    stats = [compute_tradition_stats(buddhism_agg, n_boot=200, seed=SEED)]
    d = stats_to_dict(stats)
    assert d["meta"]["n_boot"] == 200
    assert d["meta"]["resample_unit"] == "scenario cluster"
    bud = d["traditions"]["buddhism"]
    assert set(bud["subjects"]) == set(buddhism_agg.subjects)
    for s in buddhism_agg.subjects:
        sub = bud["subjects"][s]
        assert len(sub["headline"]) == 3  # [point, lo, hi]
        assert set(sub["steadfastness_by_pressure"]) == set(PRESSURES)


def test_default_constants():
    assert N_BOOT == 5000
    assert SEED == 12345
