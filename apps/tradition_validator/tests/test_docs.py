"""Doc-consistency: the format doc must mention every file/pressure the validator enforces.

Guards against the format doc (`traditions/README.md`) drifting from the actual contract
(plan Phase 5 risk mitigation). Skips if the doc isn't present.
"""

from pathlib import Path

import pytest

from tradition_validator import core

REPO_ROOT = Path(__file__).resolve().parents[3]
FORMAT_DOC = REPO_ROOT / "traditions" / "README.md"


@pytest.mark.skipif(not FORMAT_DOC.is_file(), reason="traditions/README.md not present")
def test_format_doc_covers_required_files_and_pressures():
    text = FORMAT_DOC.read_text(encoding="utf-8")
    for name in (*core.REQUIRED_TRADITION_FILES, "index.json", *core.REQUIRED_PROBE_FILES):
        assert name in text, f"format doc does not mention required file: {name}"
    for pressure in core.PRESSURES:
        assert pressure in text, f"format doc does not mention core pressure: {pressure}"
    # The doc must show how to run the validator.
    assert "tradition_validator validate" in text
