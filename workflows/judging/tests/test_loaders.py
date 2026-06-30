"""Tradition/scenario loading (spec N5, T6; generalizes to a real 2nd tradition, M7)."""

import pytest

from judging.core_imports import PRESSURES
from judging.loaders import LoadError, _parse_pressures, load_scenario, load_tradition


def test_load_real_sunni_islam(sunni):
    trad = load_tradition(sunni)
    assert trad.id == "sunni-islam"
    assert trad.guide.strip()
    assert "JLS-001" in trad.scenario_ids
    assert trad.manifest.adherent_noun  # feeds the Stated framing


def test_load_real_scenario(sunni):
    sc = load_scenario(sunni, "JLS-001")
    assert sc.turn1.strip()
    assert sc.judge_guidance.strip()  # the binding ground truth (must be non-empty)
    assert set(sc.pressures) == set(PRESSURES)
    assert all(sc.pressures[p].strip() for p in PRESSURES)


def test_generalizes_to_taoism(taoism):
    # M7: a real second tradition with different taxonomy axes — no code change.
    trad = load_tradition(taoism)
    assert trad.id == "taoism"
    assert set(trad.manifest.taxonomies) == {"departures", "te", "pivot", "register"}
    first = trad.scenario_ids[0]
    sc = load_scenario(taoism, first)
    assert set(sc.pressures) == set(PRESSURES)
    assert sc.judge_guidance.strip()


def test_pressures_heading_normalization(tmp_path):
    # T6: varied heading forms all normalize to the six canonical ids.
    p = tmp_path / "pressures.md"
    p.write_text(
        "Author preamble before the first heading is ignored.\n\n"
        "## Secularize\nbody1\n"
        "## insistence\nbody2\n"
        "## False authority\nbody3\n"
        "## good-cause\nbody4\n"
        "## flattery\nbody5\n"
        "## Personal Appeal\nbody6\n",
        encoding="utf-8",
    )
    sections = _parse_pressures(p)
    assert set(sections) == set(PRESSURES)
    assert sections["false_authority"] == "body3"
    assert sections["personal_appeal"] == "body6"


def test_pressures_missing_one_fails_loud(tmp_path):
    p = tmp_path / "pressures.md"
    p.write_text("## secularize\nb\n## insistence\nb\n", encoding="utf-8")
    with pytest.raises(LoadError):
        _parse_pressures(p)


def test_pressures_unknown_heading_fails_loud(tmp_path):
    p = tmp_path / "pressures.md"
    body = "".join(f"## {x}\nbody\n" for x in PRESSURES) + "## bananas\nbody\n"
    p.write_text(body, encoding="utf-8")
    with pytest.raises(LoadError):
        _parse_pressures(p)


def test_missing_scenario_fails_loud(sunni):
    with pytest.raises(LoadError):
        load_scenario(sunni, "JLS-000-does-not-exist")


def _write_min_scenario(root, folder, meta_id):
    sdir = root / "scenarios" / folder
    sdir.mkdir(parents=True)
    (sdir / "scenario.yaml").write_text(
        f"id: {meta_id}\n"
        "tags:\n  pillars:\n  - courage\n"
        "source_locus: 1\n"
        "locus_label: x\n"
        "identity_signal: clean\n",
        encoding="utf-8",
    )
    (sdir / "turn1.md").write_text("opening\n", encoding="utf-8")
    (sdir / "judge-guidance.md").write_text("ground truth\n", encoding="utf-8")
    (sdir / "pressures.md").write_text(
        "".join(f"## {p}\nbody\n" for p in PRESSURES), encoding="utf-8"
    )


def test_scenario_id_must_match_folder(tmp_path):
    # Matching id loads fine...
    _write_min_scenario(tmp_path, "GOOD-1", meta_id="GOOD-1")
    sc = load_scenario(tmp_path, "GOOD-1")
    assert sc.id == sc.meta.id == "GOOD-1"
    # ...a mismatch between folder/requested id and scenario.yaml id fails loud
    # (would corrupt downstream keying).
    _write_min_scenario(tmp_path, "MISMATCH", meta_id="OTHER-2")
    with pytest.raises(LoadError):
        load_scenario(tmp_path, "MISMATCH")
