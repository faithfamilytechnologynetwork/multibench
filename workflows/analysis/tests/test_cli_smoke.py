"""CLI smoke tests (spec T8): the app loads, exposes ``report`` with its flags,
and importing the CLI does not drag in matplotlib (the HTML path must stay
matplotlib-free; spec §7.3 / D7).
"""

import sys

from typer.testing import CliRunner

runner = CliRunner()


def test_importing_cli_does_not_import_matplotlib():
    # Import in a way that reflects the real entry point, then assert matplotlib
    # was not imported as a side effect (deferred-import discipline).
    import analysis.cli  # noqa: F401

    assert "matplotlib" not in sys.modules, (
        "importing analysis.cli must not import matplotlib (deferred-import rule)"
    )


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
