"""Typer CLI for the analysis workflow: ``report``.

``report`` turns N per-tradition judging ``--results-dir``s into a self-contained
cross-tradition HTML report + scenario-cluster bootstrap CIs (and, under
``--figures``, matplotlib PNG/PDF figures). Run from the repo root:

    uv --project workflows/analysis run python -m analysis report <run-dir>...

Heavy imports (loaders, aggregation, stats, rendering, matplotlib) are deferred
inside the command body so ``--help`` stays import-light and the HTML-only path
never imports matplotlib (spec §4.6 / §7.3).
"""

from __future__ import annotations

import typer

app = typer.Typer(
    name="analysis",
    help=(
        "Turn judging-run outputs into a cross-tradition HTML report, "
        "scenario-cluster bootstrap CIs, and optional matplotlib figures."
    ),
    no_args_is_help=True,
    add_completion=False,
)


@app.callback()
def _main() -> None:
    """Cross-tradition analysis for MultiBench judging runs.

    A callback is defined so ``report`` stays a *named* subcommand
    (``analysis report <run-dir>...``, per spec §4.6) rather than collapsing into a
    single-command app when it is the only command.
    """


@app.command()
def report(
    run_dirs: list[str] = typer.Argument(
        ...,
        metavar="RUN_DIR...",
        help="One judging --results-dir per tradition (each holds report.json + *.jsonl).",
    ),
    out: str = typer.Option(
        "analysis-out",
        "--out",
        help="Output directory (created if absent); writes report.html + analysis_stats.json.",
    ),
    figures: bool = typer.Option(
        False,
        "--figures/--no-figures",
        help="Also emit matplotlib PNG/PDF figures (requires the 'figures' extra).",
    ),
    n_boot: int = typer.Option(
        5000, "--n-boot", help="Bootstrap resamples for the scenario-cluster CIs."
    ),
    seed: int = typer.Option(
        12345, "--seed", help="Bootstrap RNG seed (determinism)."
    ),
    fig_format: str = typer.Option(
        "pdf,png",
        "--fig-format",
        help="Comma list of matplotlib output formats, from {pdf, png} (with --figures).",
    ),
) -> None:
    """Render a cross-tradition analysis report from N judging run-dirs."""
    # Scaffold phase (phase_1): the report pipeline is wired in later phases
    # (loaders/aggregation → stats → HTML → figures). Fail loudly rather than
    # emit a misleading empty report.
    typer.echo(
        "analysis report: not implemented yet — the loaders/aggregation, "
        "bootstrap, and HTML rendering land in subsequent phases.",
        err=True,
    )
    raise typer.Exit(code=1)
