"""Shared fixtures. Integration tests read the real traditions (spec N3): the
repo's `sunni-islam` plus a real second tradition `taoism` for generalizability (M7).
"""

from pathlib import Path

import pytest

# workflows/judging/tests/conftest.py -> repo root
_REPO_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="session")
def traditions_dir() -> Path:
    d = _REPO_ROOT / "traditions"
    assert d.is_dir(), f"traditions dir not found at {d}"
    return d


@pytest.fixture(scope="session")
def sunni(traditions_dir: Path) -> Path:
    return traditions_dir / "sunni-islam"


@pytest.fixture(scope="session")
def taoism(traditions_dir: Path) -> Path:
    return traditions_dir / "taoism"
