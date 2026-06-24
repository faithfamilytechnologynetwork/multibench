"""Findings model and report rendering (spec §8.3).

A ``Finding`` is one located, actionable result; a ``Report`` collects them for a
single tradition and decides pass/fail and the rendered output (text or json).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class Finding:
    """One validation finding.

    ``path`` is a field path / JSON pointer / heading when applicable (else None).
    """

    severity: str  # "error" | "warning"
    file: str
    message: str
    path: str | None = None


@dataclass
class Report:
    """Findings for one tradition, plus pass/fail rendering."""

    tradition: str
    findings: list[Finding] = field(default_factory=list)

    def error(self, file: str, message: str, path: str | None = None) -> None:
        self.findings.append(Finding("error", file, message, path))

    def warning(self, file: str, message: str, path: str | None = None) -> None:
        self.findings.append(Finding("warning", file, message, path))

    def extend(self, findings: list[Finding]) -> None:
        self.findings.extend(findings)

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == "error"]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == "warning"]

    def ok(self, strict: bool) -> bool:
        """Pass when there are no errors and (no warnings, or not strict)."""
        return not self.errors and not (strict and self.warnings)

    def to_dict(self, strict: bool) -> dict:
        return {
            "tradition": self.tradition,
            "ok": self.ok(strict),
            "findings": [asdict(f) for f in self.findings],
        }

    def render_text(self, strict: bool) -> str:
        lines = []
        for f in self.findings:
            loc = f"  {f.path}" if f.path else ""
            lines.append(f"{f.severity.upper():7} {f.file}{loc}\n        {f.message}")
        status = "PASS" if self.ok(strict) else "FAIL"
        lines.append(
            f"\n{status}  {self.tradition}  "
            f"({len(self.errors)} error(s), {len(self.warnings)} warning(s))"
        )
        return "\n".join(lines)


def render_all_json(reports: list[Report], strict: bool) -> str:
    """One valid JSON document covering many traditions (for validate-all)."""
    payload = {
        "ok": all(r.ok(strict) for r in reports),
        "traditions": [r.to_dict(strict) for r in reports],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)
