"""The ``tradition_validator`` Typer CLI.

Thin command surface over :mod:`tradition_validator.validator`. As of Phase 2 it
validates structure + the ``tradition.yaml`` manifest (incl. taxonomies) +
``scenarios/index.json`` ⟺ folder drift. Per-scenario-folder checks land in Phase 3.
"""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path

import typer

from tradition_validator.findings import render_all_json
from tradition_validator.validator import validate_tradition

app = typer.Typer(
    add_completion=False,
    help="Validate a MultiBench tradition module against the canonical format.",
    no_args_is_help=True,
)


class OutputFormat(str, Enum):
    """Choices for ``--format``. Typer validates the value natively (an invalid choice
    is a usage error, exit 2) and lists the choices in ``--help``."""

    text = "text"
    json = "json"


@app.command()
def validate(
    path: Path = typer.Argument(..., help="Path to a tradition directory."),
    strict: bool = typer.Option(False, "--strict", help="Escalate warnings to errors."),
    fmt: OutputFormat = typer.Option(
        OutputFormat.text, "--format", help="Output format.", case_sensitive=False
    ),
) -> None:
    """Validate a single tradition directory."""
    report = validate_tradition(path, strict)
    if fmt is OutputFormat.json:
        typer.echo(json.dumps(report.to_dict(strict), ensure_ascii=False, indent=2))
    else:
        typer.echo(report.render_text(strict))
    raise typer.Exit(0 if report.ok(strict) else 1)


@app.command("validate-all")
def validate_all(
    traditions_dir: Path = typer.Argument(
        ..., help="Directory containing tradition subdirectories."
    ),
    strict: bool = typer.Option(False, "--strict", help="Escalate warnings to errors."),
    fmt: OutputFormat = typer.Option(
        OutputFormat.text, "--format", help="Output format.", case_sensitive=False
    ),
) -> None:
    """Discover (``*/tradition.yaml``) and validate every tradition."""
    if not traditions_dir.is_dir():
        typer.echo(f"Error: not a directory: {traditions_dir}", err=True)
        raise typer.Exit(2)

    manifests = sorted(traditions_dir.glob("*/tradition.yaml"))
    if not manifests:
        typer.echo(f"No traditions found under {traditions_dir} (no */tradition.yaml).", err=True)
        raise typer.Exit(2)

    reports = [validate_tradition(m.parent, strict) for m in manifests]
    all_ok = all(r.ok(strict) for r in reports)

    if fmt is OutputFormat.json:
        typer.echo(render_all_json(reports, strict))
    else:
        for r in reports:
            typer.echo(r.render_text(strict))
            typer.echo("")
        typer.echo(f"{'ALL PASS' if all_ok else 'SOME FAILED'}  ({len(reports)} tradition(s))")

    raise typer.Exit(0 if all_ok else 1)


if __name__ == "__main__":  # pragma: no cover
    app()
