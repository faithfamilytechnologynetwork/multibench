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
    results_dir: str = typer.Option("results", help="Directory for sittings output."),
    limit: int = typer.Option(None, help="Cap the number of grid cells (smoke runs)."),
) -> None:
    """Run subject models over the framing x pressure x scenario grid -> sittings.jsonl."""
    import json as _json

    from judging.collect import collect as run_collect

    summary = run_collect(tradition, results_dir, limit=limit)
    typer.echo(_json.dumps(summary))
    if summary["failed"]:
        raise typer.Exit(code=1)  # failed cells are resumable; signal non-zero (M12)


@app.command()
def judge(
    sittings: str = typer.Argument(..., help="Path to a sittings.jsonl file."),
    tradition: str = typer.Argument(..., help="Path to the tradition directory."),
    results_dir: str = typer.Option("results", help="Directory for judgments output."),
) -> None:
    """Score each sitting with the judge panel -> judgments.jsonl (+ re-judge overrides)."""
    import json as _json

    from judging.judge import judge_all

    summary = judge_all(sittings, tradition, results_dir)
    typer.echo(_json.dumps(summary))
    if summary["failed"]:
        # Failed cells are left pending (resumable) but the run signals non-zero (M12).
        raise typer.Exit(code=1)


@app.command()
def report(
    tradition: str = typer.Argument(..., help="Path to the tradition directory."),
    results_dir: str = typer.Option(
        "results", help="Directory holding sittings.jsonl / judgments.jsonl (+ v2/skipped)."
    ),
) -> None:
    """Aggregate judgments -> per-scenario results + report.md / report.json.

    Reads everything from --results-dir (where collect/judge wrote their outputs); computable
    from partial data (never hard-fails).
    """
    import json as _json

    from judging.report import write_report

    summary = write_report(results_dir, tradition)
    typer.echo(_json.dumps(summary))


@app.command()
def run(
    tradition: str = typer.Argument(..., help="Path to a tradition directory."),
) -> None:
    """End-to-end: collect -> judge -> report for a tradition."""
    _not_yet("run", "Phase 6")
