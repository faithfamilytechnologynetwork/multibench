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
    import json as _json
    from pathlib import Path

    from analysis.aggregate import aggregate_tradition
    from analysis.html_report import render_report
    from analysis.loaders import AnalysisInputError, load_corpus
    from analysis.stats import compute_tradition_stats, stats_to_dict

    try:
        runs = load_corpus(list(run_dirs))
    except AnalysisInputError as e:  # fail-fast, spec M7
        typer.echo(f"input error: {e}", err=True)
        raise typer.Exit(code=2) from e

    aggregates = [aggregate_tradition(r) for r in runs]
    all_stats = [compute_tradition_stats(a, n_boot=n_boot, seed=seed) for a in aggregates]

    out_dir = Path(out)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "report.html"
    stats_path = out_dir / "analysis_stats.json"
    report_path.write_text(render_report(aggregates, all_stats), encoding="utf-8")
    stats_path.write_text(_json.dumps(stats_to_dict(all_stats), indent=2) + "\n", encoding="utf-8")

    if figures:
        _emit_figures(aggregates, all_stats, out_dir, fig_format)

    typer.echo(
        _json.dumps(
            {
                "out": str(out_dir),
                "traditions": [a.tradition for a in aggregates],
                "report": str(report_path),
                "stats": str(stats_path),
            }
        )
    )


def _emit_figures(aggregates, all_stats, out_dir, fig_format) -> None:
    """Matplotlib PNG/PDF figures are wired in the figures phase (deferred import there)."""
    typer.echo(
        "note: --figures (matplotlib PNG/PDF) is added in a later phase; "
        "wrote HTML + stats only.",
        err=True,
    )
