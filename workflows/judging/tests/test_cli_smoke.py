"""CLI smoke tests (spec M1): the app loads and exposes the four commands."""

from typer.testing import CliRunner

from judging.cli import app

runner = CliRunner()

COMMANDS = ("collect", "judge", "report", "run")


def test_top_level_help_lists_all_commands():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for command in COMMANDS:
        assert command in result.output


def test_each_subcommand_has_help():
    for command in COMMANDS:
        result = runner.invoke(app, [command, "--help"])
        assert result.exit_code == 0, f"{command} --help failed"


def test_unimplemented_command_fails_loudly():
    # A stub must not silently succeed — it exits non-zero (spec N2).
    result = runner.invoke(app, ["judge", "sittings.jsonl", "traditions/x"])
    assert result.exit_code != 0
