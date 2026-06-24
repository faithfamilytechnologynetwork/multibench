"""Tradition validation engine.

Phase 2 covers: directory structure, the ``tradition.yaml`` manifest (incl.
taxonomies), and ``probes/index.json`` ⟺ probe-folder drift. Per-probe-folder
validation (probe.yaml / scenario.md / judge-guidance.md / pressures.md / the judge
seam) and the safety guards land in Phase 3.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import ValidationError

from tradition_validator import core
from tradition_validator.findings import Finding, Report
from tradition_validator.loaders import load_json, load_yaml
from tradition_validator.models import ProbesIndex, TraditionManifest


def _pydantic_findings(exc: ValidationError, file: str) -> list[Finding]:
    """Turn a Pydantic ValidationError into one located Finding per error."""
    findings: list[Finding] = []
    for err in exc.errors():
        loc = ".".join(str(p) for p in err["loc"]) or "(root)"
        findings.append(Finding("error", file, err["msg"], loc))
    return findings


def list_probe_folders(probes_dir: Path) -> list[str]:
    """Probe folder names under probes/, ignoring dot/system entries (spec §8.2)."""
    if not probes_dir.is_dir():
        return []
    return sorted(
        p.name for p in probes_dir.iterdir() if p.is_dir() and not p.name.startswith(".")
    )


def _validate_manifest(tradition_dir: Path, report: Report) -> TraditionManifest | None:
    manifest_path = tradition_dir / "tradition.yaml"
    if not manifest_path.is_file():
        return None  # missing-file already reported by the structure check
    data, err = load_yaml(manifest_path)
    if err:
        report.extend([err])
        return None
    if data is None:
        report.error(str(manifest_path), "tradition.yaml is empty (no fields).")
        return None
    if not isinstance(data, dict):
        report.error(str(manifest_path), "tradition.yaml must be a YAML mapping.")
        return None
    try:
        manifest = TraditionManifest.model_validate(data)
    except ValidationError as e:
        report.extend(_pydantic_findings(e, str(manifest_path)))
        return None
    if manifest.id != tradition_dir.name:
        report.error(
            str(manifest_path),
            f"manifest id '{manifest.id}' must equal the directory name "
            f"'{tradition_dir.name}'.",
            "id",
        )
    if manifest.schema_version not in core.SUPPORTED_MODULE_SCHEMA_VERSIONS:
        report.error(
            str(manifest_path),
            f"unsupported module schema_version {manifest.schema_version} "
            f"(supported: {sorted(core.SUPPORTED_MODULE_SCHEMA_VERSIONS)}).",
            "schema_version",
        )
    return manifest


def _validate_index_and_drift(tradition_dir: Path, report: Report) -> None:
    index_path = tradition_dir / core.PROBES_INDEX
    folders = list_probe_folders(tradition_dir / "probes")
    if not folders:
        report.error(
            str(tradition_dir / "probes"),
            "No probe folders found under probes/ (need at least one).",
        )

    if not index_path.is_file():
        return  # missing-file already reported by the structure check
    data, err = load_json(index_path)
    if err:
        report.extend([err])
        return
    if not isinstance(data, dict):
        report.error(str(index_path), "index.json must be a JSON object.")
        return
    try:
        index = ProbesIndex.model_validate(data)
    except ValidationError as e:
        report.extend(_pydantic_findings(e, str(index_path)))
        return

    if index.schema_version not in core.SUPPORTED_BANK_SCHEMA_VERSIONS:
        report.error(
            str(index_path),
            f"unsupported bank schema_version {index.schema_version} "
            f"(supported: {sorted(core.SUPPORTED_BANK_SCHEMA_VERSIONS)}).",
            "schema_version",
        )

    if len(set(index.probes)) != len(index.probes):
        dupes = sorted({p for p in index.probes if index.probes.count(p) > 1})
        report.error(str(index_path), f"duplicate entries in probes list: {dupes}", "probes")

    idx_set, fld_set = set(index.probes), set(folders)
    for missing in sorted(idx_set - fld_set):
        report.error(
            str(index_path),
            f"index lists probe '{missing}' but no probes/{missing}/ folder exists (drift).",
            "probes",
        )
    for extra in sorted(fld_set - idx_set):
        report.error(
            str(tradition_dir / "probes" / extra),
            f"probe folder '{extra}' is on disk but not listed in index.json (drift).",
        )


def validate_tradition(tradition_dir: Path, strict: bool = False) -> Report:
    """Validate one tradition directory and return its :class:`Report`.

    ``strict`` only affects pass/fail rendering (warnings → failing); the checks
    themselves are unconditional.
    """
    report = Report(tradition=str(tradition_dir))

    if not tradition_dir.is_dir():
        report.error(str(tradition_dir), "Tradition path is not a directory.")
        return report

    # Structure: required tradition-level files present (spec §5.1).
    for name in core.REQUIRED_TRADITION_FILES:
        if not (tradition_dir / name).is_file():
            report.error(str(tradition_dir / name), f"Required file missing: {name}")
    if not (tradition_dir / core.PROBES_INDEX).is_file():
        report.error(
            str(tradition_dir / core.PROBES_INDEX),
            f"Required file missing: {core.PROBES_INDEX}",
        )

    _validate_manifest(tradition_dir, report)
    _validate_index_and_drift(tradition_dir, report)
    return report
