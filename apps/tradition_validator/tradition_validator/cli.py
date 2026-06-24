"""The ``tradition_validator`` Typer CLI.

Phase 1 implements the command surface and a **structure-only** check (required
top-level files/dirs present). Later phases replace ``_structure_findings`` with
the full schema/probe/seam validation engine and a richer findings model.
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import typer

from tradition_validator import core

app = typer.Typer(
    add_completion=False,
    help="Validate a MultiBench tradition module against the canonical format.",
    no_args_is_help=True,
)


@dataclass(frozen=True)
class Finding:
    """One validation finding. ``path`` is a field path/heading when applicable."""

    severity: str  # "error" | "warning"
    file: str
    message: str
    path: str | None = None


def _structure_findings(tradition_dir: Path) -> list[Finding]:
    """Phase-1 structure-only check: required files/dirs exist (spec §5.1).

    Schema/content validation arrives in later phases; this only proves the
    skeleton is present.
    """
    findings: list[Finding] = []

    if not tradition_dir.is_dir():
        findings.append(
            Finding("error", str(tradition_dir), "Tradition path is not a directory.")
        )
        return findings

    for name in core.REQUIRED_TRADITION_FILES:
        if not (tradition_dir / name).is_file():
            findings.append(
                Finding("error", str(tradition_dir / name), f"Required file missing: {name}")
            )

    index = tradition_dir / core.PROBES_INDEX
    if not index.is_file():
        findings.append(
            Finding("error", str(index), f"Required file missing: {core.PROBES_INDEX}")
        )

    probes_dir = tradition_dir / "probes"
    probe_folders = (
        [p for p in probes_dir.iterdir() if p.is_dir() and not p.name.startswith(".")]
        if probes_dir.is_dir()
        else []
    )
    if not probe_folders:
        findings.append(
            Finding(
                "error",
                str(probes_dir),
                "No probe folders found under probes/ (need at least one).",
            )
        )

    return findings


def _report(tradition_dir: Path, findings: list[Finding], fmt: str, strict: bool) -> int:
    """Render findings and return the process exit code (0 == ok)."""
    errors = [f for f in findings if f.severity == "error"]
    warnings = [f for f in findings if f.severity == "warning"]
    ok = not errors and (not warnings or not strict)

    if fmt == "json":
        payload = {
            "tradition": str(tradition_dir),
            "ok": ok,
            "findings": [asdict(f) for f in findings],
        }
        typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for f in findings:
            loc = f"  {f.path}" if f.path else ""
            typer.echo(f"{f.severity.upper():7} {f.file}{loc}\n        {f.message}")
        status = "PASS" if ok else "FAIL"
        typer.echo(
            f"\n{status}  {tradition_dir}  "
            f"({len(errors)} error(s), {len(warnings)} warning(s))"
        )

    return 0 if ok else 1


@app.command()
def validate(
    path: Path = typer.Argument(..., help="Path to a tradition directory."),
    strict: bool = typer.Option(False, "--strict", help="Escalate warnings to errors."),
    fmt: str = typer.Option("text", "--format", help="Output format: text | json."),
) -> None:
    """Validate a single tradition directory."""
    if fmt not in ("text", "json"):
        typer.echo("Error: --format must be 'text' or 'json'.", err=True)
        raise typer.Exit(2)
    findings = _structure_findings(path)
    raise typer.Exit(_report(path, findings, fmt, strict))


@app.command("validate-all")
def validate_all(
    traditions_dir: Path = typer.Argument(
        ..., help="Directory containing tradition subdirectories."
    ),
    strict: bool = typer.Option(False, "--strict", help="Escalate warnings to errors."),
    fmt: str = typer.Option("text", "--format", help="Output format: text | json."),
) -> None:
    """Discover (``*/tradition.yaml``) and validate every tradition."""
    if fmt not in ("text", "json"):
        typer.echo("Error: --format must be 'text' or 'json'.", err=True)
        raise typer.Exit(2)
    if not traditions_dir.is_dir():
        typer.echo(f"Error: not a directory: {traditions_dir}", err=True)
        raise typer.Exit(2)

    manifests = sorted(traditions_dir.glob("*/tradition.yaml"))
    if not manifests:
        typer.echo(f"No traditions found under {traditions_dir} (no */tradition.yaml).", err=True)
        raise typer.Exit(2)

    worst = 0
    for manifest in manifests:
        tradition_dir = manifest.parent
        findings = _structure_findings(tradition_dir)
        worst = max(worst, _report(tradition_dir, findings, fmt, strict))
    raise typer.Exit(worst)


if __name__ == "__main__":  # pragma: no cover
    app()
