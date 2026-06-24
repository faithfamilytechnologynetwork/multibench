"""Smoke tests for the CLI surface and exit codes (validate / validate-all)."""

import json
from pathlib import Path

from typer.testing import CliRunner

from tradition_validator.cli import app

runner = CliRunner()


def test_help_runs():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "validate" in result.output


def test_validate_empty_dir_fails_loudly(tmp_path: Path):
    empty = tmp_path / "empty"
    empty.mkdir()
    result = runner.invoke(app, ["validate", str(empty)])
    assert result.exit_code == 1
    assert "tradition.yaml" in result.output
    assert "FAIL" in result.output


def test_validate_valid_tradition_passes(valid_tradition: Path):
    result = runner.invoke(app, ["validate", str(valid_tradition)])
    assert result.exit_code == 0, result.output
    assert "PASS" in result.output


def test_validate_json_shape(valid_tradition: Path):
    result = runner.invoke(app, ["validate", str(valid_tradition), "--format", "json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["tradition"].endswith("sunni-islam")
    assert payload["findings"] == []


def test_bad_format_rejected(tmp_path: Path):
    result = runner.invoke(app, ["validate", str(tmp_path), "--format", "xml"])
    assert result.exit_code == 2


def test_validate_all_text(make_tradition, tmp_path: Path):
    make_tradition(tmp_path, "sunni-islam")
    # A second, broken tradition (manifest present so it's discovered, but invalid).
    broken = tmp_path / "broken"
    (broken / "probes").mkdir(parents=True)
    (broken / "tradition.yaml").write_text("not: a valid manifest\n", encoding="utf-8")
    result = runner.invoke(app, ["validate-all", str(tmp_path)])
    assert result.exit_code == 1
    assert "SOME FAILED" in result.output


def test_validate_all_json_single_document(make_tradition, tmp_path: Path):
    make_tradition(tmp_path, "sunni-islam")
    broken = tmp_path / "broken"
    (broken / "probes").mkdir(parents=True)
    (broken / "tradition.yaml").write_text("not: a valid manifest\n", encoding="utf-8")
    result = runner.invoke(app, ["validate-all", str(tmp_path), "--format", "json"])
    payload = json.loads(result.output)  # must be ONE valid document
    assert payload["ok"] is False
    assert len(payload["traditions"]) == 2
    by_ok = {t["tradition"].split("/")[-1]: t["ok"] for t in payload["traditions"]}
    assert by_ok["sunni-islam"] is True
    assert by_ok["broken"] is False


def test_validate_all_all_pass(make_tradition, tmp_path: Path):
    make_tradition(tmp_path, "sunni-islam")
    result = runner.invoke(app, ["validate-all", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert "ALL PASS" in result.output


def test_validate_all_no_traditions(tmp_path: Path):
    result = runner.invoke(app, ["validate-all", str(tmp_path)])
    assert result.exit_code == 2
    assert "No traditions found" in result.output
