"""Tradition-level prose non-emptiness: README.md / source.md / guide.md (§8.2 6/9)."""

from pathlib import Path

from conftest import find_finding

from tradition_validator.validator import validate_tradition


def test_empty_readme_is_error(valid_tradition: Path):
    (valid_tradition / "README.md").write_text("   \n", encoding="utf-8")
    report = validate_tradition(valid_tradition)
    f = find_finding(report, contains="README.md must be non-empty", severity="error")
    assert f is not None and f.file.endswith("README.md")


def test_empty_source_is_error(valid_tradition: Path):
    (valid_tradition / "source.md").write_text("", encoding="utf-8")
    report = validate_tradition(valid_tradition)
    assert find_finding(report, contains="source.md must be non-empty", severity="error") is not None


def test_missing_guide_is_error(valid_tradition: Path):
    # T5: guide.md is required because the Guided framing is universal core.
    (valid_tradition / "guide.md").unlink()
    report = validate_tradition(valid_tradition)
    assert find_finding(report, contains="guide.md", severity="error") is not None
    assert not report.ok(strict=False)


def test_empty_guide_is_error(valid_tradition: Path):
    (valid_tradition / "guide.md").write_text("\n\n", encoding="utf-8")
    report = validate_tradition(valid_tradition)
    assert find_finding(report, contains="guide.md must be non-empty", severity="error") is not None
