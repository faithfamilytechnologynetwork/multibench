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


@app.command()
def export(
    run_roots: list[str] = typer.Argument(
        ...,
        metavar="RUN_ROOT...",
        help="Judging run ROOTS (each a dir of per-tradition subdirs). The full-grid "
             "Gemini run must carry report.json; report-less Opus layers merge in.",
    ),
    run_id: str = typer.Option(
        ..., "--run-id", help="Dataset id — the results/<run-id>/ directory name."
    ),
    out: str = typer.Option(
        "results", "--out",
        help="Root output dir; writes <out>/<run-id>/manifest.json + <tradition>.json.",
    ),
    single_judge_attempts: int = typer.Option(
        None, "--single-judge-attempts",
        help="Re-judge attempts made on residual single-judge cells; recorded in "
             "ranking.single_judge_cells.attempts (provenance not derivable from the data).",
    ),
) -> None:
    """Export judging runs into a compact, browsable results/<run-id>/ dataset (#49).

    Normalizes subject/judge ids across runs, resolves the Opus alias collision + v2
    overlay, aggregates via the canonical semantics, and writes per-tradition shards +
    a manifest (scores + metadata only — no transcripts).
    """
    import json as _json
    from datetime import datetime, timezone
    from pathlib import Path

    from analysis.export_results import export_dataset
    from analysis.loaders import AnalysisInputError

    generated_at = datetime.now(timezone.utc).isoformat()
    try:
        written = export_dataset(list(run_roots), out, run_id, generated_at, single_judge_attempts)
    except AnalysisInputError as e:  # fail-fast, spec M7
        typer.echo(f"input error: {e}", err=True)
        raise typer.Exit(code=2) from e

    total = sum(p.stat().st_size for p in written)
    manifest = _json.loads((Path(out) / run_id / "manifest.json").read_text())
    typer.echo(
        _json.dumps({
            "run_id": run_id,
            "out": str(Path(out) / run_id),
            "files": len(written),
            "total_bytes": total,
            "traditions": [t["id"] for t in manifest["traditions"]],
            "counts": manifest["counts"],
        })
    )


@app.command(name="export-raw")
def export_raw(
    run_roots: list[str] = typer.Argument(
        ...,
        metavar="RUN_ROOT...",
        help="Judging run ROOTS. The full-grid Gemini run (report.json + sittings.jsonl) is "
             "the sole transcript source; report-less Opus layers contribute verdicts only.",
    ),
    run_id: str = typer.Option(
        ..., "--run-id", help="Dataset id — the results-raw/<run-id>/ directory name."
    ),
    out: str = typer.Option(
        "results-raw", "--out",
        help="Root output dir; writes <out>/<run-id>/manifest.json + <tradition>/<scenario>.json.gz.",
    ),
    limit: int = typer.Option(
        None, "--limit",
        help="Write at most N scenarios — a small dev fixture (fingerprint is over the subset).",
    ),
) -> None:
    """Export judging runs into the browsable results-raw/<run-id>/ tier (#51).

    Per-scenario gzip shards of transcripts + judge verdicts, plus a generic catalog. Reuses
    the #49 loaders (normalization, v2 overlay, Opus-alias dedup) so the raw tier and the
    results/ score tier share one source fingerprint. Deterministic (no wall-clock; gzip
    mtime=0) → byte-identical re-exports.
    """
    import json as _json
    from pathlib import Path

    from analysis.export_raw import write_dataset
    from analysis.loaders import AnalysisInputError

    try:
        summary = write_dataset(list(run_roots), out, run_id, limit=limit)
    except AnalysisInputError as e:  # fail-fast, spec M7
        typer.echo(f"input error: {e}", err=True)
        raise typer.Exit(code=2) from e

    typer.echo(
        _json.dumps({
            "run_id": run_id,
            "out": str(Path(out) / run_id),
            "shards": summary.shards,
            "shard_bytes": summary.shard_bytes,
            "shard_uncompressed_bytes": summary.shard_uncompressed_bytes,
            "compression_ratio": round(summary.compression_ratio, 2),
            "max_shard_bytes": summary.max_shard_bytes,
            "manifest_bytes": summary.manifest_bytes,
            "total_bytes": summary.total_bytes,
        })
    )


@app.command(name="export-afb")
def export_afb(
    intermediate: str = typer.Argument(
        ..., metavar="INTERMEDIATE",
        help="The Phase-2 collection intermediate JSON (responses + Terra 0–4 verdicts).",
    ),
    run_id: str = typer.Option(
        ..., "--run-id", help="Dataset id — the results-raw/<run-id>/ directory name (e.g. afb-20260808)."
    ),
    out: str = typer.Option(
        "results-raw", "--out",
        help="Root output dir; writes <out>/<run-id>/manifest.json + afb-150/<item>.json.gz.",
    ),
) -> None:
    """Export the AFB collection intermediate into a drop-in results-raw/<run-id>/ catalog (#54).

    The AFB before/after explorer as a SECOND catalog type on the Spec 51 raw viewer: 0–4 scale,
    two checkpoint subjects, the Terra judge, a single cold condition. Reuses the byte-stable writer
    (deterministic, gzip mtime=0) → byte-identical re-exports.
    """
    import json as _json
    from pathlib import Path

    from analysis.export_afb import export
    from analysis.loaders import AnalysisInputError

    try:
        doc = _json.loads(Path(intermediate).read_text(encoding="utf-8"))
        summary = export(doc, out, run_id)
    except (AnalysisInputError, OSError, _json.JSONDecodeError) as e:  # fail-fast, spec M7
        typer.echo(f"input error: {e}", err=True)
        raise typer.Exit(code=2) from e

    typer.echo(
        _json.dumps({
            "run_id": run_id,
            "out": str(Path(out) / run_id),
            "shards": summary.shards,
            "shard_bytes": summary.shard_bytes,
            "shard_uncompressed_bytes": summary.shard_uncompressed_bytes,
            "compression_ratio": round(summary.compression_ratio, 2),
            "max_shard_bytes": summary.max_shard_bytes,
            "manifest_bytes": summary.manifest_bytes,
            "total_bytes": summary.total_bytes,
        })
    )


def _emit_figures(aggregates, all_stats, out_dir, fig_format) -> None:
    """Render matplotlib PNG/PDF figures under ``<out>/figures``.

    matplotlib is imported **only here** (lazily), so the default HTML path never loads
    it (spec §7.3). Missing matplotlib fails loud with a clear install hint (fail-fast).
    """
    from pathlib import Path

    try:
        from analysis.figures import emit_figures
    except ImportError as e:  # the optional 'figures' extra is not installed
        typer.echo(
            "--figures needs matplotlib; install the 'figures' extra, e.g. "
            "`uv --project workflows/analysis sync --extra figures`.",
            err=True,
        )
        raise typer.Exit(code=3) from e

    formats = [f.strip() for f in fig_format.split(",") if f.strip()]
    try:
        written = emit_figures(aggregates, all_stats, Path(out_dir) / "figures", formats)
    except ValueError as e:  # bad --fig-format
        typer.echo(f"figure error: {e}", err=True)
        raise typer.Exit(code=2) from e
    typer.echo(f"wrote {len(written)} figure files to {Path(out_dir) / 'figures'}", err=True)
