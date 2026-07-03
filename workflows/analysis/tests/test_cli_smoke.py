"""CLI smoke tests (spec T8): the app loads, exposes ``report`` with its flags,
and importing the CLI does not drag in matplotlib (the HTML path must stay
matplotlib-free; spec §7.3 / D7).
"""

import subprocess
import sys

from typer.testing import CliRunner

runner = CliRunner()


def test_importing_cli_does_not_import_matplotlib():
    # Deferred-import discipline: importing analysis.cli must not pull in matplotlib.
    # Checked in a fresh subprocess so the result is independent of what other test
    # modules imported into this process (spec §7.3 / D7).
    code = (
        "import sys, analysis.cli;"
        "assert 'matplotlib' not in sys.modules, 'analysis.cli must not import matplotlib';"
        "print('ok')"
    )
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert "ok" in proc.stdout


def test_top_level_help_lists_report():
    from analysis.cli import app

    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "report" in result.output


def test_report_help_lists_all_flags():
    from analysis.cli import app

    result = runner.invoke(app, ["report", "--help"])
    assert result.exit_code == 0
    for flag in ("--out", "--figures", "--n-boot", "--seed", "--fig-format"):
        assert flag in result.output, f"{flag} missing from `report --help`"


def test_report_without_args_fails_loudly():
    # No silent success: `report` with no run-dirs must exit non-zero.
    from analysis.cli import app

    result = runner.invoke(app, ["report"])
    assert result.exit_code != 0


def test_core_imports_reexport_universal_core():
    # core_imports single-sources the universal core from tradition_validator.
    from analysis.core_imports import FRAMINGS, PRESSURES

    assert tuple(FRAMINGS) == ("unstated", "stated", "guided")
    assert len(PRESSURES) == 6
