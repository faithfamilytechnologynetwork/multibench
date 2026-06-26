"""Regression guard for issue #17: no tradition-specific scoring band NAMES remain.

Each tradition once invented its own evocative names for the five scoring levels —
eastern-christianity Myrrh/Fragrance/Idle word/Smoke/Stench, judaism Apples of
gold/.../a stumbling block, buddhism Fragrance of virtue/.../the wheel and the hoof,
taoism Like water/.../Not the Way — embedded as **bolded** scoring labels in each
README band table and across every ``judge-guidance.md``. They were normalized to
bare numbers on the canonical scale (−1, −0.5, 0, +0.5, +1). This test fails if any
band-name scoring label reappears in a tradition's ``README.md`` or any
``judge-guidance.md``.

Genuine teaching imagery — the ``construct:`` in ``tradition.yaml``, ``guide.md`` ("be
like water", the perfume-seller, the myrrh), ``source.md``, ``turn1.md``,
``pressures.md`` — is out of scope and deliberately NOT scanned: there the same images
are the tradition's actual counsel, not scoring labels. For the same reason, a README is
scanned only within its ``## The five bands`` section (the band table and its intro), not
its construct/overview bullets, where e.g. buddhism keeps "the **fragrance of virtue**
that travels even against the wind" as the construct's own image.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
TRADITIONS = REPO_ROOT / "traditions"

# Band names once used as bolded scoring labels (any tradition). Matching is
# case-insensitive and whitespace between words is collapsed (``\s+``) so labels that
# wrap across a line break — e.g. ``**Apples\nof gold**`` — are still caught.
BAND_NAMES = (
    # eastern-christianity
    "Myrrh", "Fragrance", "Idle word", "Smoke", "Stench",
    # judaism
    "Apples of gold", "Light", "Idle words", "Dust", "a stumbling block", "stumbling block",
    # buddhism
    "Fragrance of virtue", "Wholesome", "Unwholesome", "the wheel and the hoof",
    # taoism
    "Like water", "the soft and living", "Many words", "the hard and stiff", "Not the Way",
)


def _band_label_pattern() -> re.Pattern[str]:
    """A regex matching any band name as a **bolded** token (the scoring-label syntax)."""
    alts = "|".join(re.escape(n).replace(r"\ ", r"\s+") for n in BAND_NAMES)
    return re.compile(rf"\*\*\s*(?:{alts})\s*\*\*", re.IGNORECASE)


PATTERN = _band_label_pattern()


_BANDS_SECTION = re.compile(r"^##\s+The five bands\b.*?(?=^##\s|\Z)", re.MULTILINE | re.DOTALL)


def _band_section(readme_text: str) -> str:
    """The ``## The five bands`` section (table + intro), or "" if the README has none."""
    m = _BANDS_SECTION.search(readme_text)
    return m.group(0) if m else ""


def _scanned_files() -> list[Path]:
    if not TRADITIONS.is_dir():
        return []
    files = list(TRADITIONS.glob("*/README.md"))
    files += list(TRADITIONS.glob("*/scenarios/*/judge-guidance.md"))
    return sorted(files)


def _scan_text(f: Path) -> str:
    """Text to scan: a README contributes only its band-table section; a judge-guidance
    file contributes its whole body."""
    text = f.read_text(encoding="utf-8")
    return _band_section(text) if f.name == "README.md" else text


@pytest.mark.skipif(not TRADITIONS.is_dir(), reason="traditions/ not present")
def test_no_band_name_scoring_labels_remain():
    violations: list[str] = []
    for f in _scanned_files():
        for m in PATTERN.finditer(_scan_text(f)):
            rel = f.relative_to(REPO_ROOT)
            snippet = re.sub(r"\s+", " ", m.group(0))
            violations.append(f"{rel}: {snippet}")
    assert not violations, (
        "Tradition-specific band NAMES used as scoring labels must be bare numbers "
        f"(−1, −0.5, 0, +0.5, +1). Found {len(violations)}:\n  "
        + "\n  ".join(violations[:40])
        + ("\n  ..." if len(violations) > 40 else "")
    )


@pytest.mark.skipif(not TRADITIONS.is_dir(), reason="traditions/ not present")
def test_scanner_actually_finds_files():
    # Guard against the glob silently matching nothing (which would make the band-name
    # assertion vacuously pass).
    assert len(_scanned_files()) >= 5
