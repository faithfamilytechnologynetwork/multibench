"""Tradition validation engine.

Covers (spec §5, §8.2): directory structure; the ``tradition.yaml`` manifest +
taxonomies; ``scenarios/index.json`` ⟺ scenario-folder drift; tradition-level prose
non-emptiness; per-scenario folders (``scenario.yaml`` schema + taxonomy membership,
``turn1.md``, the ``judge-guidance.md`` seam, and ``pressures.md`` coverage);
plus robustness guards (UTF-8 / safe-load / size cap via loaders, symlink-escape
rejection here).
"""

from __future__ import annotations

import re
from pathlib import Path

from pydantic import ValidationError

from tradition_validator import core
from tradition_validator.findings import Finding, Report
from tradition_validator.loaders import load_json, load_text, load_yaml
from tradition_validator.models import ScenarioMeta, ScenariosIndex, TraditionManifest


def _pydantic_findings(exc: ValidationError, file: str) -> list[Finding]:
    """Turn a Pydantic ValidationError into one located Finding per error."""
    findings: list[Finding] = []
    for err in exc.errors():
        loc = ".".join(str(p) for p in err["loc"]) or "(root)"
        findings.append(Finding("error", file, err["msg"], loc))
    return findings


def _within_root(path: Path, root: Path) -> bool:
    """True if ``path`` resolves inside ``root`` (rejects symlink/.. escapes)."""
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except (ValueError, OSError):
        return False


def _guard_within(path: Path, root: Path, report: Report) -> bool:
    """Report + return False if ``path`` escapes ``root`` (applied before every read)."""
    if not _within_root(path, root):
        report.error(str(path), "Path escapes the tradition directory (symlink/.. not allowed).")
        return False
    return True


def list_scenario_folders(scenarios_dir: Path) -> list[str]:
    """Scenario folder names under scenarios/, ignoring dot/system entries (spec §8.2)."""
    if not scenarios_dir.is_dir():
        return []
    return sorted(
        p.name for p in scenarios_dir.iterdir() if p.is_dir() and not p.name.startswith(".")
    )


def _nonempty_text(path: Path, root: Path, report: Report, *, seam: bool = False) -> None:
    """Require a file to exist, be readable, and be non-blank."""
    if not _within_root(path, root):
        report.error(str(path), "Path escapes the tradition directory (symlink/.. not allowed).")
        return
    if not path.is_file():
        report.error(str(path), f"Required file missing: {path.name}")
        return
    text, err = load_text(path)
    if err:
        report.extend([err])
        return
    if not text or not text.strip():
        msg = f"{path.name} must be non-empty"
        if seam:
            msg += " (it is the judge's binding ground truth)"
        report.error(str(path), msg + ".")


def parse_pressure_sections(text: str) -> list[tuple[str, str, str]]:
    """Split ``pressures.md`` into ``[(normalized_id, raw_heading, body)]``.

    Only ``## `` (level-2) headings start a section; content before the first such
    heading is preamble and is ignored (spec §5.6).
    """
    sections: list[tuple[str, str, str]] = []
    raw: str | None = None
    norm: str | None = None
    buf: list[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            if norm is not None:
                sections.append((norm, raw or "", "\n".join(buf).strip()))
            raw = line[3:].strip()
            norm = core.normalize_heading(raw)
            buf = []
        elif norm is not None:
            buf.append(line)
    if norm is not None:
        sections.append((norm, raw or "", "\n".join(buf).strip()))
    return sections


def _validate_pressures_md(path: Path, root: Path, report: Report) -> None:
    if not _within_root(path, root):
        report.error(str(path), "Path escapes the tradition directory.")
        return
    if not path.is_file():
        report.error(str(path), "Required scenario file missing: pressures.md")
        return
    text, err = load_text(path)
    if err:
        report.extend([err])
        return

    seen: dict[str, list[str]] = {}
    for norm, raw, body in parse_pressure_sections(text):
        seen.setdefault(norm, []).append(body)
        if norm not in core.PRESSURES:
            report.error(
                str(path),
                f"unknown pressure section '## {raw}' (normalizes to '{norm}'); "
                f"expected one of {list(core.PRESSURES)}.",
                f"## {raw}",
            )
    for pressure in core.PRESSURES:
        bodies = seen.get(pressure)
        if not bodies:
            report.error(str(path), f"missing section for core pressure '{pressure}'.", "pressures")
            continue
        if len(bodies) > 1:
            report.error(
                str(path), f"duplicate section for pressure '{pressure}' ({len(bodies)} found).",
                f"## {pressure}",
            )
        for body in bodies:
            if not body:
                report.error(str(path), f"pressure section '{pressure}' is empty.", f"## {pressure}")


def _validate_scenario_folder(
    folder: Path,
    root: Path,
    manifest: TraditionManifest | None,
    report: Report,
    seen_ids: dict[str, str],
) -> None:
    if not _within_root(folder, root):
        report.error(str(folder), "Scenario folder escapes the tradition directory (symlink not allowed).")
        return

    # Required files present; unexpected non-dot files -> warning (typo catch).
    expected = set(core.REQUIRED_SCENARIO_FILES)
    for fname in core.REQUIRED_SCENARIO_FILES:
        if not (folder / fname).is_file():
            report.error(str(folder / fname), f"Required scenario file missing: {fname}")
    for child in folder.iterdir():
        if child.name.startswith("."):
            continue
        if child.is_file() and child.name not in expected:
            report.warning(str(child), f"unexpected file in scenario folder: {child.name}")

    # scenario.yaml
    scenario_path = folder / "scenario.yaml"
    meta: ScenarioMeta | None = None
    if scenario_path.is_file() and _guard_within(scenario_path, root, report):
        data, err = load_yaml(scenario_path)
        if err:
            report.extend([err])
        elif data is None:
            report.error(str(scenario_path), "scenario.yaml is empty (no fields).")
        elif not isinstance(data, dict):
            report.error(str(scenario_path), "scenario.yaml must be a YAML mapping.")
        else:
            try:
                meta = ScenarioMeta.model_validate(data)
            except ValidationError as e:
                report.extend(_pydantic_findings(e, str(scenario_path)))
    if meta is not None:
        if meta.id != folder.name:
            report.error(
                str(scenario_path),
                f"scenario id '{meta.id}' must equal its folder name '{folder.name}'.",
                "id",
            )
        if meta.id in seen_ids:
            first = seen_ids[meta.id]
            # Name BOTH conflicting locations (spec T13): a finding on each file.
            report.error(
                str(scenario_path),
                f"duplicate scenario id '{meta.id}' (also declared in {first}).",
                "id",
            )
            report.error(
                first,
                f"duplicate scenario id '{meta.id}' (also declared in {scenario_path}).",
                "id",
            )
        else:
            seen_ids[meta.id] = str(scenario_path)
        if manifest is not None:
            # fullmatch so an unanchored scenario_id_pattern still requires the whole id.
            if not re.compile(manifest.scenario_id_pattern).fullmatch(meta.id):
                report.error(
                    str(scenario_path),
                    f"scenario id '{meta.id}' does not match scenario_id_pattern "
                    f"'{manifest.scenario_id_pattern}'.",
                    "id",
                )
            _validate_tags(scenario_path, meta, manifest, report)

    # Prose files (the turn-1 opening, the judge seam) must be present + non-empty.
    _nonempty_text(folder / "turn1.md", root, report)
    _nonempty_text(folder / "judge-guidance.md", root, report, seam=True)
    _validate_pressures_md(folder / "pressures.md", root, report)


def _validate_tags(
    scenario_path: Path, meta: ScenarioMeta, manifest: TraditionManifest, report: Report
) -> None:
    declared = set(manifest.taxonomies.keys())
    present = set(meta.tags.keys())
    for missing in sorted(declared - present):
        report.error(str(scenario_path), f"missing required taxonomy axis '{missing}' in tags.", "tags")
    for extra in sorted(present - declared):
        report.error(str(scenario_path), f"unknown taxonomy axis '{extra}' in tags.", f"tags.{extra}")
    for axis in sorted(present & declared):
        values = meta.tags[axis]
        if not values:
            report.error(str(scenario_path), f"tags.{axis} must be non-empty.", f"tags.{axis}")
        if len(set(values)) != len(values):
            report.error(str(scenario_path), f"duplicate values in tags.{axis}.", f"tags.{axis}")
        allowed = set(manifest.taxonomies[axis].values)
        for v in values:
            if v not in allowed:
                report.error(
                    str(scenario_path),
                    f"unknown taxonomy value '{v}' for axis '{axis}'. "
                    f"Declared: {sorted(allowed)}.",
                    f"tags.{axis}",
                )


def _validate_manifest(tradition_dir: Path, report: Report) -> TraditionManifest | None:
    manifest_path = tradition_dir / "tradition.yaml"
    if not manifest_path.is_file():
        return None  # missing-file already reported by the structure check
    if not _guard_within(manifest_path, tradition_dir, report):
        return None
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
    index_path = tradition_dir / core.SCENARIOS_INDEX
    folders = list_scenario_folders(tradition_dir / "scenarios")
    if not folders:
        report.error(
            str(tradition_dir / "scenarios"),
            "No scenario folders found under scenarios/ (need at least one).",
        )

    if not index_path.is_file():
        return  # missing-file already reported by the structure check
    if not _guard_within(index_path, tradition_dir, report):
        return
    data, err = load_json(index_path)
    if err:
        report.extend([err])
        return
    if not isinstance(data, dict):
        report.error(str(index_path), "index.json must be a JSON object.")
        return
    try:
        index = ScenariosIndex.model_validate(data)
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

    if len(set(index.scenarios)) != len(index.scenarios):
        dupes = sorted({s for s in index.scenarios if index.scenarios.count(s) > 1})
        report.error(str(index_path), f"duplicate entries in scenarios list: {dupes}.", "scenarios")

    idx_set, fld_set = set(index.scenarios), set(folders)
    for missing in sorted(idx_set - fld_set):
        report.error(
            str(index_path),
            f"index lists scenario '{missing}' but no scenarios/{missing}/ folder exists (drift).",
            "scenarios",
        )
    for extra in sorted(fld_set - idx_set):
        report.error(
            str(index_path),
            f"scenario folder '{extra}' is on disk but not listed in index.json (drift).",
            "scenarios",
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
    if not (tradition_dir / core.SCENARIOS_INDEX).is_file():
        report.error(
            str(tradition_dir / core.SCENARIOS_INDEX),
            f"Required file missing: {core.SCENARIOS_INDEX}",
        )

    # Tradition-level prose must be non-empty (spec §8.2 checks 6/9). guide.md is
    # required because the Guided framing is universal core.
    for name in ("README.md", "source.md", "guide.md"):
        if (tradition_dir / name).is_file():
            _nonempty_text(tradition_dir / name, tradition_dir, report)

    manifest = _validate_manifest(tradition_dir, report)
    _validate_index_and_drift(tradition_dir, report)

    seen_ids: dict[str, str] = {}  # scenario id -> first file that declared it
    for folder_name in list_scenario_folders(tradition_dir / "scenarios"):
        _validate_scenario_folder(
            tradition_dir / "scenarios" / folder_name, tradition_dir, manifest, report, seen_ids
        )

    return report
