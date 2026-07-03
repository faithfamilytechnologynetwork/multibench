"""Shared fixtures for the analysis workflow tests.

The analysis tool consumes judging **run artifacts**, which are git-ignored
(`tmp/`) and not available to CI. Tests therefore rely on committed miniature
fixture run-dirs under `tests/fixtures/` (added in Phase 2), never on
`tmp/judging-runs/`. This conftest only wires the repo-root path for now.
"""

from pathlib import Path

import pytest

# workflows/analysis/tests/conftest.py -> repo root (mirrors workflows/judging).
_REPO_ROOT = Path(__file__).resolve().parents[3]
_FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture(scope="session")
def repo_root() -> Path:
    assert _REPO_ROOT.is_dir(), f"repo root not found at {_REPO_ROOT}"
    return _REPO_ROOT


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    """Directory of committed miniature run-dirs (populated in Phase 2)."""
    return _FIXTURES
