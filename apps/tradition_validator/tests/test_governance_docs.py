"""Governance-doc consistency: keep the hot/cold tier docs honest (issue #4).

Guards the two-tier model (Spec 987) the `update-arch-docs` skill polices:

- the always-on HOT files carry no leftover ``<placeholder>`` template lines;
- the HOT files stay within their cap (so they remain cheap to inject everywhere);
- every HOT "Map of <cold doc>" topic names a *real* top-level section in its cold
  doc (map accuracy, both directions);
- ``codev/projects/`` consult artifacts are gitignored while porch's ``status.yaml`` stays
  tracked (porch commits it on every phase transition).

Repo-root reads, skipping when a file is absent — same convention as ``test_docs.py``.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
RESOURCES = REPO_ROOT / "codev" / "resources"

# (hot file, cold file it maps) pairs.
TIER_PAIRS = (
    ("arch-critical.md", "arch.md"),
    ("lessons-critical.md", "lessons-learned.md"),
)

# Files carrying the generated always-on mirror of the hot tier.
MIRROR_FILES = ("CLAUDE.md", "AGENTS.md")
HOT_FILES = ("arch-critical.md", "lessons-critical.md")
HOT_CONTEXT_RE = re.compile(
    r"<!-- BEGIN CODEV HOT CONTEXT.*?-->(.*?)<!-- END CODEV HOT CONTEXT -->", re.DOTALL
)

# Hot-file cap from the update-arch-docs skill: <=10 entries, <=12 map topics, <=35 lines.
MAX_HOT_LINES = 35
MAX_HOT_ENTRIES = 10
MAX_MAP_TOPICS = 12

# A leftover template placeholder is an angle-bracket span with an internal space
# ("<Top-level arch.md section>"); real content tokens like "<id>" or "<pressure>"
# have no internal space, so they are not flagged.
PLACEHOLDER_RE = re.compile(r"<[^>\n]* [^>\n]*>")
COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


def _strip_comments(text: str) -> str:
    return COMMENT_RE.sub("", text)


def _top_level_sections(text: str) -> list[str]:
    """Exact heading text of every ``## `` (level-2) section in a cold doc."""
    return [m.group(1).strip() for m in re.finditer(r"^## (.+)$", text, re.MULTILINE)]


def _map_topics(hot_text: str) -> list[str]:
    """Topics from the 'Map of …' bullets — the text before ' — consult when'.

    Split on the ' — consult when' marker (not on the em dash) so a topic that itself
    contains an em dash, e.g. 'Universal core — framings & pressures', survives intact.
    """
    topics: list[str] = []
    in_map = False
    for line in hot_text.splitlines():
        if line.startswith("## Map of"):
            in_map = True
            continue
        if in_map and line.startswith("## "):
            break
        if in_map and line.lstrip().startswith("- "):
            head = re.split(r"\s+—\s+consult when", line.lstrip()[2:], maxsplit=1)[0]
            topics.append(head.strip())
    return topics


@pytest.mark.parametrize("hot_name", [h for h, _ in TIER_PAIRS])
def test_hot_file_has_no_template_placeholders(hot_name: str):
    path = RESOURCES / hot_name
    if not path.is_file():
        pytest.skip(f"{hot_name} not present")
    body = _strip_comments(path.read_text(encoding="utf-8"))
    leftovers = PLACEHOLDER_RE.findall(body)
    assert not leftovers, f"{hot_name} still has template placeholders: {leftovers}"


@pytest.mark.parametrize("hot_name", [h for h, _ in TIER_PAIRS])
def test_hot_file_within_cap(hot_name: str):
    path = RESOURCES / hot_name
    if not path.is_file():
        pytest.skip(f"{hot_name} not present")
    text = path.read_text(encoding="utf-8")
    n_lines = len(text.splitlines())
    assert n_lines <= MAX_HOT_LINES, f"{hot_name}: {n_lines} lines > cap {MAX_HOT_LINES}"

    # Count the "Critical …" entries (bullets before the Map section).
    entries = 0
    in_entries = False
    for line in text.splitlines():
        if line.startswith("## Critical"):
            in_entries = True
            continue
        if in_entries and line.startswith("## "):
            break
        if in_entries and line.lstrip().startswith("- "):
            entries += 1
    assert entries <= MAX_HOT_ENTRIES, f"{hot_name}: {entries} entries > cap {MAX_HOT_ENTRIES}"
    assert len(_map_topics(text)) <= MAX_MAP_TOPICS, f"{hot_name}: map over {MAX_MAP_TOPICS} topics"


@pytest.mark.parametrize("hot_name,cold_name", TIER_PAIRS)
def test_hot_map_matches_real_cold_sections(hot_name: str, cold_name: str):
    hot = RESOURCES / hot_name
    cold = RESOURCES / cold_name
    if not hot.is_file() or not cold.is_file():
        pytest.skip(f"{hot_name}/{cold_name} not present")

    sections = _top_level_sections(cold.read_text(encoding="utf-8"))
    topics = _map_topics(hot.read_text(encoding="utf-8"))

    assert topics, f"{hot_name} has no map topics"
    # The cold doc must carry real content, not the empty STARTER.
    assert "No architecture documented yet." not in cold.read_text(encoding="utf-8")
    assert "No lessons captured yet." not in cold.read_text(encoding="utf-8")

    missing = [t for t in topics if t not in sections]
    assert not missing, f"{hot_name} map topics with no matching {cold_name} section: {missing}"
    unmapped = [s for s in sections if s not in topics]
    assert not unmapped, f"{cold_name} sections missing from {hot_name} map: {unmapped}"


@pytest.mark.parametrize("mirror_name", MIRROR_FILES)
def test_hot_context_mirror_in_sync(mirror_name: str):
    """CLAUDE.md / AGENTS.md must mirror the *current* hot files verbatim (no stale drift)."""
    mirror = REPO_ROOT / mirror_name
    if not mirror.is_file():
        pytest.skip(f"{mirror_name} not present")
    m = HOT_CONTEXT_RE.search(mirror.read_text(encoding="utf-8"))
    assert m, f"{mirror_name}: no CODEV HOT CONTEXT block"
    block = m.group(1)

    for hot_name in HOT_FILES:
        hot = RESOURCES / hot_name
        if not hot.is_file():
            continue
        # The hot file is inlined verbatim into the mirror; assert it is present in full.
        assert hot.read_text(encoding="utf-8").strip() in block, (
            f"{mirror_name} mirror is stale vs {hot_name} — regenerate the HOT CONTEXT block"
        )
    # And no template placeholders survive inside the mirror.
    assert not PLACEHOLDER_RE.findall(_strip_comments(block)), f"{mirror_name} mirror has placeholders"


def test_projects_consult_artifacts_gitignored_but_status_kept():
    gitignore = REPO_ROOT / ".gitignore"
    if not gitignore.is_file():
        pytest.skip(".gitignore not present")
    lines = {ln.strip() for ln in gitignore.read_text(encoding="utf-8").splitlines()}
    # Consult artifacts (rebuttals/context/briefs) under each project dir are ignored …
    assert "codev/projects/*/*" in lines, "porch consult artifacts must be gitignored (issue #4)"
    # … but porch's own state file must stay tracked — porch commits it on every transition.
    assert "!codev/projects/*/status.yaml" in lines, "status.yaml must remain tracked for porch"
