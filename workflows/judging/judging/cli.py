"""Typer CLI for the judging workflow: ``collect`` | ``judge`` | ``report`` | ``run``.

``collect`` runs subjects over the grid → ``sittings.jsonl``; ``judge`` scores those with the
panel → ``judgments.jsonl``; ``report`` aggregates → ``report.md`` / ``report.json``; ``run``
is the end-to-end pipeline (collect → judge → report). Failed cells are resumable and make the
command exit non-zero (M12).

Every command takes ``--config <file.yaml>`` (spec §5.7): the run configuration — judge panel,
subjects, framings, pressures, scopes, retries — overridable from a YAML file (defaults in
``config.py``). Pass the SAME ``--config`` to ``report`` that produced the artifacts so its
coverage is computed against the right panel/scopes.
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

_CONFIG_OPT = typer.Option(
    None, "--config", help="YAML run-config file overriding defaults (judges, subjects, framings, …)."
)


def _load(config: str | None):
    """Load a Config from --config, or None to use defaults. Fails loud on a bad file (N2)."""
    if config is None:
        return None
    from judging.config import ConfigError, load_config

    try:
        return load_config(config)
    except ConfigError as e:
        typer.echo(f"config error: {e}", err=True)
        raise typer.Exit(code=2) from e


@app.command()
def collect(
    tradition: str = typer.Argument(..., help="Path to a tradition directory."),
    results_dir: str = typer.Option("results", help="Directory for sittings output."),
    limit: int = typer.Option(None, help="Cap the number of grid cells (smoke runs)."),
    config: str = _CONFIG_OPT,
) -> None:
    """Run subject models over the framing x pressure x scenario grid -> sittings.jsonl."""
    import json as _json

    from judging.collect import collect as run_collect

    summary = run_collect(tradition, results_dir, config=_load(config), limit=limit)
    typer.echo(_json.dumps(summary))
    if summary["failed"]:
        raise typer.Exit(code=1)  # failed cells are resumable; signal non-zero (M12)


@app.command()
def judge(
    sittings: str = typer.Argument(..., help="Path to a sittings.jsonl file."),
    tradition: str = typer.Argument(..., help="Path to the tradition directory."),
    results_dir: str = typer.Option("results", help="Directory for judgments output."),
    config: str = _CONFIG_OPT,
) -> None:
    """Score each sitting with the judge panel -> judgments.jsonl (+ re-judge overrides)."""
    import json as _json

    from judging.judge import judge_all

    summary = judge_all(sittings, tradition, results_dir, config=_load(config))
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
    config: str = _CONFIG_OPT,
) -> None:
    """Aggregate judgments -> per-scenario results + report.md / report.json.

    Reads everything from --results-dir (where collect/judge wrote their outputs); computable
    from partial data (never hard-fails). Pass the SAME --config used for collect/judge so the
    coverage counts match the panel/scopes that produced the artifacts.
    """
    import json as _json

    from judging.report import write_report

    summary = write_report(results_dir, tradition, config=_load(config))
    typer.echo(_json.dumps(summary))


@app.command()
def run(
    tradition: str = typer.Argument(..., help="Path to a tradition directory."),
    results_dir: str = typer.Option("results", help="Directory for all pipeline outputs."),
    limit: int = typer.Option(None, help="Cap the number of grid cells (smoke runs)."),
    config: str = _CONFIG_OPT,
) -> None:
    """End-to-end: collect -> judge -> report for a tradition.

    Runs the three stages against --results-dir (one shared --config). ``report`` always runs
    (never hard-fails), so partial results + coverage are written even if some cells failed;
    exits non-zero when collect or judge left failed (resumable) cells (M12).
    """
    import json as _json

    from judging.pipeline import run_pipeline

    summary = run_pipeline(tradition, results_dir, config=_load(config), limit=limit)
    typer.echo(_json.dumps(summary))
    if summary["failed"]:
        raise typer.Exit(code=1)  # failed cells are resumable; signal non-zero (M12)
