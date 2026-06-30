"""Typer CLI for the judging workflow: ``collect`` | ``judge`` | ``report`` | ``run``.

Phase 1 wires the command surface (so ``--help`` lists everything and the package
is runnable); each command is implemented in the phase that owns it: ``judge`` →
Phase 3, ``collect`` → Phase 4, ``report`` → Phase 5, ``run`` → Phase 6. Until
then, invoking a command fails loudly with a non-zero exit (no silent no-op).
"""

from __future__ import annotations

import typer

app = typer.Typer(
    name="judging",
    help=(
        "Score assistant responses against each scenario's judge-guidance.md "
        "on the canonical -1..+1 scale."
    ),
    no_args_is_help=True,
    add_completion=False,
)


def _not_yet(command: str, phase: str) -> None:
    """Fail loudly for a not-yet-implemented command (no silent degrade, spec N2)."""
    typer.echo(f"judging {command}: not yet implemented (lands in {phase}).", err=True)
    raise typer.Exit(code=1)


@app.command()
def collect(
    tradition: str = typer.Argument(..., help="Path to a tradition directory."),
) -> None:
    """Run subject models over the framing x pressure x scenario grid -> sittings.jsonl."""
    _not_yet("collect", "Phase 4")


@app.command()
def judge(
    sittings: str = typer.Argument(..., help="Path to a sittings.jsonl file."),
    tradition: str = typer.Argument(..., help="Path to the tradition directory."),
) -> None:
    """Score each sitting with the judge panel -> judgments.jsonl."""
    _not_yet("judge", "Phase 3")


@app.command()
def report(
    sittings: str = typer.Argument(..., help="Path to a sittings.jsonl file."),
    judgments: str = typer.Argument(..., help="Path to a judgments.jsonl file."),
    tradition: str = typer.Argument(..., help="Path to the tradition directory."),
) -> None:
    """Aggregate judgments -> per-scenario results + report.md / report.json."""
    _not_yet("report", "Phase 5")


@app.command()
def run(
    tradition: str = typer.Argument(..., help="Path to a tradition directory."),
) -> None:
    """End-to-end: collect -> judge -> report for a tradition."""
    _not_yet("run", "Phase 6")
