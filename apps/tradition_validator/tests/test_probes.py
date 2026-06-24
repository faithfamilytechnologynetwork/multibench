"""Per-probe validation: probe.yaml, tags, the judge seam, pressures.md, safety.

(spec §5.4/§5.5/§5.6, §8.2 checks 5/8/10.)
"""

import os
from pathlib import Path

import yaml
from conftest import CORE_PRESSURES, find_finding, write_probe

from tradition_validator.validator import (
    parse_pressure_sections,
    validate_tradition,
)


def _probe(t: Path, pid: str = "JLS-001") -> Path:
    return t / "probes" / pid


def _load_probe(t: Path, pid: str = "JLS-001") -> dict:
    return yaml.safe_load((_probe(t, pid) / "probe.yaml").read_text(encoding="utf-8"))


def _write_probe_yaml(t: Path, m: dict, pid: str = "JLS-001") -> None:
    (_probe(t, pid) / "probe.yaml").write_text(yaml.safe_dump(m, sort_keys=False), encoding="utf-8")


# --- baseline ---------------------------------------------------------------

def test_valid_probe_passes(valid_tradition: Path):
    report = validate_tradition(valid_tradition)
    assert report.ok(strict=True), " | ".join(f.message for f in report.findings)


# --- probe.yaml schema + identity ------------------------------------------

def test_probe_id_must_equal_folder_name(valid_tradition: Path):
    m = _load_probe(valid_tradition)
    m["id"] = "JLS-999"
    _write_probe_yaml(valid_tradition, m)
    report = validate_tradition(valid_tradition)
    f = find_finding(report, contains="must equal its folder name", severity="error")
    assert f is not None and f.file.endswith("JLS-001/probe.yaml") and f.path == "id"


def test_probe_id_pattern_enforced(valid_tradition: Path):
    # A probe folder named outside the declared probe_id_pattern (^JLS-\d{3}$).
    import json

    write_probe(valid_tradition / "probes" / "BAD-1", "BAD-1")
    (valid_tradition / "probes" / "index.json").write_text(
        json.dumps({"schema_version": 1, "probes": ["JLS-001", "BAD-1"]}), encoding="utf-8"
    )
    report = validate_tradition(valid_tradition)
    assert find_finding(report, contains="probe_id_pattern", severity="error") is not None


def test_bad_identity_signal(valid_tradition: Path):
    m = _load_probe(valid_tradition)
    m["identity_signal"] = "sideways"
    _write_probe_yaml(valid_tradition, m)
    report = validate_tradition(valid_tradition)
    assert find_finding(report, contains="identity_signal", severity="error") is not None


def test_probe_unknown_key_rejected(valid_tradition: Path):
    m = _load_probe(valid_tradition)
    m["extra"] = 1
    _write_probe_yaml(valid_tradition, m)
    assert not validate_tradition(valid_tradition).ok(strict=False)


# --- tags vs declared taxonomy ---------------------------------------------

def test_tag_value_not_in_axis(valid_tradition: Path):
    m = _load_probe(valid_tradition)
    m["tags"]["hearts"] = ["not_a_heart"]
    _write_probe_yaml(valid_tradition, m)
    report = validate_tradition(valid_tradition)
    f = find_finding(report, contains="unknown taxonomy value", severity="error")
    assert f is not None and f.path == "tags.hearts"


def test_missing_declared_axis(valid_tradition: Path):
    m = _load_probe(valid_tradition)
    del m["tags"]["hearts"]  # manifest declares pillars + hearts
    _write_probe_yaml(valid_tradition, m)
    report = validate_tradition(valid_tradition)
    assert find_finding(report, contains="missing required taxonomy axis", severity="error") is not None


def test_unknown_axis(valid_tradition: Path):
    m = _load_probe(valid_tradition)
    m["tags"]["invented"] = ["x"]
    _write_probe_yaml(valid_tradition, m)
    report = validate_tradition(valid_tradition)
    assert find_finding(report, contains="unknown taxonomy axis", severity="error") is not None


def test_duplicate_tag_values(valid_tradition: Path):
    m = _load_probe(valid_tradition)
    m["tags"]["pillars"] = ["justice", "justice"]
    _write_probe_yaml(valid_tradition, m)
    report = validate_tradition(valid_tradition)
    assert find_finding(report, contains="duplicate values in tags.pillars", severity="error") is not None


# --- required files + the judge seam ---------------------------------------

def test_missing_scenario_md(valid_tradition: Path):
    (_probe(valid_tradition) / "scenario.md").unlink()
    report = validate_tradition(valid_tradition)
    assert find_finding(report, contains="scenario.md", severity="error") is not None


def test_empty_judge_guidance_is_error(valid_tradition: Path):
    (_probe(valid_tradition) / "judge-guidance.md").write_text("   \n", encoding="utf-8")
    report = validate_tradition(valid_tradition)
    f = find_finding(report, contains="judge-guidance.md must be non-empty", severity="error")
    assert f is not None and "binding ground truth" in f.message  # the seam


def test_unexpected_file_warns(valid_tradition: Path):
    (_probe(valid_tradition) / "notes.txt").write_text("scratch\n", encoding="utf-8")
    report = validate_tradition(valid_tradition)
    f = find_finding(report, contains="unexpected file", severity="warning")
    assert f is not None
    assert report.ok(strict=False)  # warning only
    assert not report.ok(strict=True)  # escalated under --strict


# --- pressures.md -----------------------------------------------------------

def test_pressures_missing_one(valid_tradition: Path):
    body = "\n".join(f"## {p}\n\ntext\n" for p in CORE_PRESSURES if p != "flattery")
    (_probe(valid_tradition) / "pressures.md").write_text(body, encoding="utf-8")
    report = validate_tradition(valid_tradition)
    assert find_finding(report, contains="missing section for core pressure 'flattery'", severity="error") is not None


def test_pressures_unknown_heading(valid_tradition: Path):
    body = "\n".join(f"## {p}\n\ntext\n" for p in CORE_PRESSURES)
    body += "\n## bribery\n\nnot a real pressure\n"
    (_probe(valid_tradition) / "pressures.md").write_text(body, encoding="utf-8")
    report = validate_tradition(valid_tradition)
    assert find_finding(report, contains="unknown pressure section", severity="error") is not None


def test_pressures_heading_normalization_accepts_variants(valid_tradition: Path):
    # 'False Authority' and 'personal-appeal' must normalize to the canonical ids.
    variants = {
        "secularize": "Secularize",
        "insistence": "Insistence",
        "false_authority": "False Authority",
        "good_cause": "Good cause",
        "flattery": "Flattery",
        "personal_appeal": "personal-appeal",
    }
    body = "\n".join(f"## {variants[p]}\n\ntext for {p}\n" for p in CORE_PRESSURES)
    (_probe(valid_tradition) / "pressures.md").write_text(body, encoding="utf-8")
    assert validate_tradition(valid_tradition).ok(strict=True)


def test_pressures_empty_section(valid_tradition: Path):
    body = ""
    for p in CORE_PRESSURES:
        body += f"## {p}\n\n{'text' if p != 'flattery' else ''}\n"
    (_probe(valid_tradition) / "pressures.md").write_text(body, encoding="utf-8")
    report = validate_tradition(valid_tradition)
    assert find_finding(report, contains="pressure section 'flattery' is empty", severity="error") is not None


def test_pressures_preamble_ignored(valid_tradition: Path):
    body = "Author notes here, before any heading.\n\n"
    body += "\n".join(f"## {p}\n\ntext\n" for p in CORE_PRESSURES)
    (_probe(valid_tradition) / "pressures.md").write_text(body, encoding="utf-8")
    assert validate_tradition(valid_tradition).ok(strict=True)


def test_parse_pressure_sections_unit():
    text = "preamble\n## Secularize\nbody1\n## flattery\nbody2\n"
    secs = parse_pressure_sections(text)
    assert secs == [("secularize", "Secularize", "body1"), ("flattery", "flattery", "body2")]


# --- safety -----------------------------------------------------------------

def test_symlink_escape_rejected(valid_tradition: Path, tmp_path: Path):
    outside = tmp_path / "outside_probe"
    write_probe(outside, "JLS-002")
    link = valid_tradition / "probes" / "JLS-002"
    try:
        os.symlink(outside, link, target_is_directory=True)
    except (OSError, NotImplementedError):
        import pytest
        pytest.skip("symlinks not supported on this platform")
    import json
    (valid_tradition / "probes" / "index.json").write_text(
        json.dumps({"schema_version": 1, "probes": ["JLS-001", "JLS-002"]}), encoding="utf-8"
    )
    report = validate_tradition(valid_tradition)
    assert find_finding(report, contains="escapes the tradition directory", severity="error") is not None


def test_oversized_file_rejected(valid_tradition: Path, monkeypatch):
    from tradition_validator import core
    monkeypatch.setattr(core, "MAX_FILE_BYTES", 10)  # tiny cap
    report = validate_tradition(valid_tradition)
    assert find_finding(report, contains="too large", severity="error") is not None


def test_duplicate_probe_id(valid_tradition: Path):
    # T13: a second folder whose probe.yaml claims an already-used id.
    import json

    write_probe(valid_tradition / "probes" / "JLS-002", "JLS-002")
    # Point JLS-002's probe.yaml id at JLS-001 (duplicate).
    p2 = valid_tradition / "probes" / "JLS-002" / "probe.yaml"
    m = yaml.safe_load(p2.read_text(encoding="utf-8"))
    m["id"] = "JLS-001"
    p2.write_text(yaml.safe_dump(m, sort_keys=False), encoding="utf-8")
    (valid_tradition / "probes" / "index.json").write_text(
        json.dumps({"schema_version": 1, "probes": ["JLS-001", "JLS-002"]}), encoding="utf-8"
    )
    report = validate_tradition(valid_tradition)
    assert find_finding(report, contains="duplicate probe id", severity="error") is not None


def test_symlinked_machine_file_escape_rejected(valid_tradition: Path, tmp_path: Path):
    # A symlinked probe.yaml pointing outside the tradition must be rejected (N4),
    # not silently parsed.
    outside = tmp_path / "evil.yaml"
    outside.write_text("id: JLS-001\n", encoding="utf-8")
    target = valid_tradition / "probes" / "JLS-001" / "probe.yaml"
    target.unlink()
    try:
        os.symlink(outside, target)
    except (OSError, NotImplementedError):
        import pytest
        pytest.skip("symlinks not supported on this platform")
    report = validate_tradition(valid_tradition)
    assert find_finding(report, contains="escapes the tradition directory", severity="error") is not None
