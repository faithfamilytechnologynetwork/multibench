"""Shared fixtures. Integration tests read the real traditions (spec N3): the
repo's `sunni-islam` plus a real second tradition `taoism` for generalizability (M7).
"""

from pathlib import Path

import pytest

# workflows/judging/tests/conftest.py -> repo root
_REPO_ROOT = Path(__file__).resolve().parents[3]


def pytest_addoption(parser: pytest.Parser) -> None:
    # Opt-in live tests (M8b anchoring, S3 cache-hit) call real provider APIs and cost money;
    # they are excluded from the default (mocked) suite / CI and only run with --live (spec N3).
    parser.addoption(
        "--live",
        action="store_true",
        default=False,
        help="Run opt-in tests that call real provider APIs (needs credentials).",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", "live: opt-in test that calls a real provider API (needs --live + creds)."
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list) -> None:
    if config.getoption("--live"):
        return
    skip_live = pytest.mark.skip(reason="opt-in: pass --live to run (calls real provider APIs)")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip_live)


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
