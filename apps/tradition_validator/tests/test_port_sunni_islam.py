"""Acceptance test (M3): the real ported Sunni Islam tradition validates clean.

This is the single highest-value test — it proves both the port and the format. It
locates the repo-root tradition CWD-independently and skips cleanly if it hasn't been
generated yet (so the suite stays hermetic).
"""

from pathlib import Path

import pytest

from tradition_validator.validator import list_scenario_folders, validate_tradition

REPO_ROOT = Path(__file__).resolve().parents[3]
TRADITION = REPO_ROOT / "traditions" / "sunni-islam"


@pytest.mark.skipif(
    not (TRADITION / "tradition.yaml").is_file(),
    reason="traditions/sunni-islam not generated (run port_jaleesbench)",
)
def test_sunni_islam_validates_clean():
    report = validate_tradition(TRADITION, strict=True)
    assert report.ok(strict=True), "\n".join(
        f"{f.severity} {f.file} {f.path or ''}: {f.message}" for f in report.findings
    )


@pytest.mark.skipif(
    not (TRADITION / "tradition.yaml").is_file(),
    reason="traditions/sunni-islam not generated",
)
def test_sunni_islam_has_full_bank():
    # The port is complete: all 140 scenarios (from the JaleesBench bank), listed and on disk.
    folders = list_scenario_folders(TRADITION / "scenarios")
    assert len(folders) == 140
