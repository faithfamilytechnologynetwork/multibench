"""Tests for the export-computed presets (#51, Phase 3).

Each preset is deterministic, capped at 12, deduped to one entry per scenario, stable-keyed,
and sparse-safe (a candidate lacking the required judge/scope is skipped). Tested on the
compact per-cell score map directly (fast, exhaustive) and end-to-end through the catalog.
"""

from __future__ import annotations

from analysis.export_raw import (
    PRESET_CAP,
    accumulate_cell_scores,
    build_catalog,
    build_raw_corpus,
    compute_presets,
)
from tests.test_export_raw import _full_grid, _grid


def _cell(trad, scen, subj, pr, fr, scope, gemini=None, opus=None):
    js = {}
    if gemini is not None:
        js["gemini"] = gemini
    if opus is not None:
        js["opus"] = opus
    return (trad, scen, subj, pr, fr, scope), js


def _cells(*entries):
    return dict(entries)


def _preset(presets, key):
    return next((p for p in presets if p["key"] == key), None)


# ── Models split ────────────────────────────────────────────────────────────────────


def test_models_split_picks_widest_turn1_gemini_spread():
    cells = _cells(
        _cell("buddhism", "BUD-001", "A", "secularize", "unstated", "turn1", gemini=1.0),
        _cell("buddhism", "BUD-001", "B", "secularize", "unstated", "turn1", gemini=-1.0),
        _cell("buddhism", "BUD-002", "A", "secularize", "unstated", "turn1", gemini=0.5),
        _cell("buddhism", "BUD-002", "B", "secularize", "unstated", "turn1", gemini=0.0),
    )
    ms = _preset(compute_presets(cells), "models-split")
    assert [e["params"]["item"] for e in ms["entries"]] == ["BUD-001", "BUD-002"]  # widest first
    top = ms["entries"][0]["params"]
    assert top == {"group": "buddhism", "item": "BUD-001", "scope": "turn1", "a": "A", "b": "B",
                   "conditions": {"framing": "unstated", "pressure": "secularize"}}
    assert ms["entries"][0]["key"] == "models-split:buddhism:BUD-001"


def test_models_split_skips_zero_spread_and_single_subject():
    cells = _cells(
        _cell("buddhism", "BUD-001", "A", "secularize", "unstated", "turn1", gemini=1.0),
        _cell("buddhism", "BUD-001", "B", "secularize", "unstated", "turn1", gemini=1.0),  # tie
        _cell("buddhism", "BUD-002", "A", "secularize", "unstated", "turn1", gemini=0.5),  # 1 subj
    )
    assert _preset(compute_presets(cells), "models-split") is None


# ── Judges differed ───────────────────────────────────────────────────────────────────


def test_judges_differed_threshold_and_contrast():
    cells = _cells(
        _cell("buddhism", "BUD-001", "A", "secularize", "unstated", "full", gemini=1.0, opus=-0.5),
        _cell("buddhism", "BUD-001", "B", "secularize", "unstated", "full", gemini=1.0, opus=1.0),
        _cell("buddhism", "BUD-002", "A", "secularize", "unstated", "full", gemini=0.5, opus=0.0),  # <1
    )
    jd = _preset(compute_presets(cells), "judges-differed")
    assert [e["params"]["item"] for e in jd["entries"]] == ["BUD-001"]  # only the ≥1 gap
    p = jd["entries"][0]["params"]
    assert p["a"] == "A" and p["b"] == "B" and p["scope"] == "full"  # contrast vs top gemini


def test_judges_differed_exact_1_0_boundary_included():
    cells = _cells(
        _cell("buddhism", "BUD-001", "A", "secularize", "unstated", "full", gemini=0.5, opus=-0.5),  # =1.0
        _cell("buddhism", "BUD-002", "A", "secularize", "unstated", "full", gemini=0.5, opus=0.0),   # =0.5
    )
    jd = _preset(compute_presets(cells), "judges-differed")
    assert [e["params"]["item"] for e in jd["entries"]] == ["BUD-001"]  # 1.0 in, 0.5 out


def test_judges_differed_skips_sparse_opus():
    # a full cell with Gemini but no Opus (sparse honest-sample) must not produce an entry
    cells = _cells(
        _cell("buddhism", "BUD-001", "A", "secularize", "unstated", "full", gemini=1.0),  # opus missing
    )
    assert _preset(compute_presets(cells), "judges-differed") is None


def test_judges_differed_b_absent_when_only_one_subject():
    # only subject A in the (scenario, pressure, framing) group → no contrast subject → b omitted
    cells = _cells(
        _cell("buddhism", "BUD-001", "A", "secularize", "unstated", "full", gemini=1.0, opus=-0.5),
    )
    jd = _preset(compute_presets(cells), "judges-differed")
    p = jd["entries"][0]["params"]
    assert p["a"] == "A" and "b" not in p


def test_steadfastness_skips_missing_scope():
    # only turn1 present (no full) → no drop can be computed → skipped
    cells = _cells(
        _cell("buddhism", "BUD-001", "A", "secularize", "unstated", "turn1", gemini=1.0),
    )
    assert _preset(compute_presets(cells), "steadfastness-cliff") is None


def test_models_split_tie_break_by_scenario_pressure_framing():
    # two candidates with identical spread → ordered by (scenario, pressure, framing)
    cells = _cells(
        _cell("buddhism", "BUD-002", "A", "secularize", "unstated", "turn1", gemini=1.0),
        _cell("buddhism", "BUD-002", "B", "secularize", "unstated", "turn1", gemini=-1.0),
        _cell("buddhism", "BUD-001", "A", "insistence", "stated", "turn1", gemini=1.0),
        _cell("buddhism", "BUD-001", "B", "insistence", "stated", "turn1", gemini=-1.0),
    )
    ms = _preset(compute_presets(cells), "models-split")
    assert [e["params"]["item"] for e in ms["entries"]] == ["BUD-001", "BUD-002"]  # scenario asc


# ── Steadfastness cliff ───────────────────────────────────────────────────────────────


def test_steadfastness_cliff_largest_negative_drop():
    cells = _cells(
        _cell("buddhism", "BUD-001", "A", "secularize", "unstated", "turn1", gemini=1.0),
        _cell("buddhism", "BUD-001", "A", "secularize", "unstated", "full", gemini=-1.0),   # drop -2
        _cell("buddhism", "BUD-002", "A", "secularize", "unstated", "turn1", gemini=1.0),
        _cell("buddhism", "BUD-002", "A", "secularize", "unstated", "full", gemini=0.5),    # drop -0.5
        _cell("buddhism", "BUD-003", "A", "secularize", "unstated", "turn1", gemini=0.0),
        _cell("buddhism", "BUD-003", "A", "secularize", "unstated", "full", gemini=1.0),    # rose (skip)
    )
    sc = _preset(compute_presets(cells), "steadfastness-cliff")
    assert [e["params"]["item"] for e in sc["entries"]] == ["BUD-001", "BUD-002"]  # steepest first
    assert sc["entries"][0]["params"]["a"] == "A" and "b" not in sc["entries"][0]["params"]


# ── Dedup, cap, determinism ───────────────────────────────────────────────────────────


def test_one_entry_per_scenario_and_cap():
    # one scenario, many pressures with spread → must collapse to a single entry
    cells = {}
    for i, pr in enumerate(["secularize", "insistence", "false_authority"]):
        cells.update(_cells(
            _cell("buddhism", "BUD-001", "A", pr, "unstated", "turn1", gemini=1.0),
            _cell("buddhism", "BUD-001", "B", pr, "unstated", "turn1", gemini=-1.0 + i * 0.1),
        ))
    ms = _preset(compute_presets(cells), "models-split")
    assert len(ms["entries"]) == 1  # deduped to one per scenario


def test_cap_at_preset_cap():
    cells = {}
    for n in range(PRESET_CAP + 5):
        cells.update(_cells(
            _cell("buddhism", f"BUD-{n:03d}", "A", "secularize", "unstated", "turn1", gemini=1.0),
            _cell("buddhism", f"BUD-{n:03d}", "B", "secularize", "unstated", "turn1", gemini=-1.0),
        ))
    ms = _preset(compute_presets(cells), "models-split")
    assert len(ms["entries"]) == PRESET_CAP


def test_presets_deterministic_order_independent():
    items = [
        _cell("buddhism", "BUD-001", "A", "secularize", "unstated", "turn1", gemini=1.0),
        _cell("buddhism", "BUD-001", "B", "secularize", "unstated", "turn1", gemini=-1.0),
        _cell("buddhism", "BUD-002", "A", "insistence", "stated", "turn1", gemini=0.5),
        _cell("buddhism", "BUD-002", "B", "insistence", "stated", "turn1", gemini=-0.5),
    ]
    assert compute_presets(dict(items)) == compute_presets(dict(reversed(items)))


# ── End-to-end through the catalog ────────────────────────────────────────────────────


def test_catalog_carries_presets(tmp_path):
    # a 2-subject grid with divergent turn-1 scores yields a Models-split preset
    def score_fn(su, fr, pr, scope):
        if scope == "turn1":
            return 1.0 if su == "gpt-5.6-terra" else -1.0
        return 0.0
    base, sittings = _grid(["gpt-5.6-terra", "claude-sonnet-5"], score_fn=score_fn)
    root = _full_grid(tmp_path / "fg", base=base, sittings=sittings,
                      subjects=["gpt-5.6-terra", "claude-sonnet-5"], judges=["gemini-3.6-flash"])
    catalog = build_catalog(build_raw_corpus([root]))
    ms = _preset(catalog["presets"], "models-split")
    assert ms is not None and ms["entries"]
    assert ms["entries"][0]["params"]["item"] == "BUD-001"


def test_presets_round_robin_across_groups_for_diverse_curation():
    """When many scenarios across groups tie at max magnitude, entries span groups (round-robin)
    rather than filling the cap from the alphabetically-first group."""
    cells = {}
    for g in ("buddhism", "taoism", "judaism"):
        for n in range(6):  # 6 max-spread scenarios per group
            cells.update(_cells(
                _cell(g, f"{g[:3].upper()}-{n:03d}", "A", "secularize", "unstated", "turn1", gemini=1.0),
                _cell(g, f"{g[:3].upper()}-{n:03d}", "B", "secularize", "unstated", "turn1", gemini=-1.0),
            ))
    ms = _preset(compute_presets(cells), "models-split")
    groups = [e["params"]["group"] for e in ms["entries"]]
    assert len(ms["entries"]) == 12
    # every group represented (round-robin), not 12 from one
    assert set(groups) == {"buddhism", "judaism", "taoism"}
    assert groups[:3] == ["buddhism", "judaism", "taoism"]  # first round, sorted group order


def test_presets_deterministic_across_groups_under_shuffle():
    items = []
    for g in ("buddhism", "taoism"):
        items += [
            _cell(g, f"{g[:3].upper()}-001", "A", "secularize", "unstated", "turn1", gemini=1.0),
            _cell(g, f"{g[:3].upper()}-001", "B", "secularize", "unstated", "turn1", gemini=-1.0),
        ]
    assert compute_presets(dict(items)) == compute_presets(dict(reversed(items)))


def test_write_dataset_emits_presets_into_manifest(tmp_path):
    from analysis.export_raw import write_dataset
    import json
    def score_fn(su, fr, pr, scope):
        return (1.0 if su == "gpt-5.6-terra" else -1.0) if scope == "turn1" else 0.0
    base, sittings = _grid(["gpt-5.6-terra", "claude-sonnet-5"], score_fn=score_fn)
    root = _full_grid(tmp_path / "fg", base=base, sittings=sittings,
                      subjects=["gpt-5.6-terra", "claude-sonnet-5"], judges=["gemini-3.6-flash"])
    write_dataset([root], tmp_path / "out", "run1")
    manifest = json.loads((tmp_path / "out" / "run1" / "manifest.json").read_text())
    keys = {p["key"] for p in manifest["presets"]}
    assert "models-split" in keys


def test_limit_confines_preset_entries_to_written_items(tmp_path):
    from analysis.export_raw import write_dataset
    import json
    base, sittings = [], []
    for sc in ("BUD-001", "BUD-002", "BUD-003"):
        b, s = _grid(["gpt-5.6-terra", "claude-sonnet-5"],
                     scenario=sc,
                     score_fn=lambda su, fr, pr, scope: (1.0 if su == "gpt-5.6-terra" else -1.0)
                     if scope == "turn1" else 0.0)
        base += b
        sittings += s
    root = _full_grid(tmp_path / "fg", base=base, sittings=sittings,
                      subjects=["gpt-5.6-terra", "claude-sonnet-5"], judges=["gemini-3.6-flash"],
                      scenarios=("BUD-001", "BUD-002", "BUD-003"))
    write_dataset([root], tmp_path / "out", "run1", limit=2)
    manifest = json.loads((tmp_path / "out" / "run1" / "manifest.json").read_text())
    ms = _preset(manifest["presets"], "models-split")
    assert {e["params"]["item"] for e in ms["entries"]} <= {"BUD-001", "BUD-002"}  # no BUD-003


def test_accumulate_cell_scores_maps_judge_keys():
    cells: dict = {}
    accumulate_cell_scores(
        [{"tradition": "buddhism", "scenario_id": "BUD-001", "subject": "A",
          "pressure": "secularize", "framing": "unstated", "scope": "turn1",
          "judge": "gemini-3.6-flash", "score": 1.0}],
        cells,
    )
    assert cells[("buddhism", "BUD-001", "A", "secularize", "unstated", "turn1")] == {"gemini": 1.0}
