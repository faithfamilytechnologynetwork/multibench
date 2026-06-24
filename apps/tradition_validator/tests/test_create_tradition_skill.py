"""Conformance tests for the create-tradition skill (Phase 6).

The skill is author-facing instructions, so its "tests" are: (1) its frontmatter and body
match the repo skill convention + the actual format/validator contract; and (2) an
end-to-end check that the structure it prescribes actually validates clean. The skill file
is located CWD-independently from the repo root.
"""

from pathlib import Path

import pytest

from tradition_validator import core
from tradition_validator.validator import validate_tradition

REPO_ROOT = Path(__file__).resolve().parents[3]
SKILL = REPO_ROOT / ".claude" / "skills" / "create-tradition" / "SKILL.md"


def _frontmatter(text: str) -> dict:
    """Parse the leading ``--- ... ---`` YAML frontmatter block."""
    import yaml

    assert text.startswith("---\n"), "SKILL.md must start with a --- frontmatter block"
    end = text.index("\n---", 4)
    return yaml.safe_load(text[4:end])


@pytest.mark.skipif(not SKILL.is_file(), reason="create-tradition skill not present")
def test_frontmatter_matches_convention():
    fm = _frontmatter(SKILL.read_text(encoding="utf-8"))
    assert fm["name"] == "create-tradition"
    assert fm["name"] == SKILL.parent.name  # name matches its directory
    assert isinstance(fm.get("description"), str) and len(fm["description"]) > 30


@pytest.mark.skipif(not SKILL.is_file(), reason="create-tradition skill not present")
def test_body_covers_every_required_file_and_pressure():
    text = SKILL.read_text(encoding="utf-8")
    for name in (*core.REQUIRED_TRADITION_FILES, "index.json", *core.REQUIRED_SCENARIO_FILES):
        assert name in text, f"skill does not mention required file: {name}"
    for pressure in core.PRESSURES:
        assert pressure in text, f"skill does not mention core pressure: {pressure}"


@pytest.mark.skipif(not SKILL.is_file(), reason="create-tradition skill not present")
def test_body_ends_by_running_the_validator():
    text = SKILL.read_text(encoding="utf-8")
    assert "tradition_validator validate" in text
    assert "traditions/<id>" in text  # run from repo root, against the new tradition


def test_skill_prescribed_structure_validates(make_tradition, tmp_path: Path):
    """End-to-end: a tradition built as the skill prescribes validates clean (exit 0)."""
    t = make_tradition(tmp_path, "test-faith")  # canonical structure, the skill's shape
    report = validate_tradition(t, strict=True)
    assert report.ok(strict=True), "\n".join(f.message for f in report.findings)
