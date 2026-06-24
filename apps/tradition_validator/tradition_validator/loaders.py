"""Safe, fail-loud loaders for YAML / JSON (spec §8.2 check 10 / robustness).

Each loader reads UTF-8, parses with a safe parser, and returns ``(data, error)``
where ``error`` is a located :class:`Finding` (and ``data`` is None) on any failure
— never a raw traceback. YAML uses ``safe_load`` (no arbitrary object construction).
The full symlink-escape guard and ``MAX_FILE_BYTES`` size cap land in Phase 3.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from tradition_validator.findings import Finding


def _read_text(path: Path) -> tuple[str | None, Finding | None]:
    try:
        return path.read_text(encoding="utf-8"), None
    except FileNotFoundError:
        return None, Finding("error", str(path), "File not found.")
    except UnicodeDecodeError:
        return None, Finding("error", str(path), "File is not valid UTF-8.")
    except OSError as e:  # pragma: no cover - unusual fs errors
        return None, Finding("error", str(path), f"Could not read file: {e}")


def load_yaml(path: Path) -> tuple[object | None, Finding | None]:
    """Load a YAML file with ``safe_load``. Returns ``(data, error)``."""
    text, err = _read_text(path)
    if err:
        return None, err
    try:
        return yaml.safe_load(text), None
    except yaml.YAMLError as e:
        detail = str(e).replace("\n", " ")
        return None, Finding("error", str(path), f"Invalid YAML: {detail}")


def load_json(path: Path) -> tuple[object | None, Finding | None]:
    """Load a JSON file. Returns ``(data, error)``."""
    text, err = _read_text(path)
    if err:
        return None, err
    try:
        return json.loads(text), None
    except json.JSONDecodeError as e:
        return None, Finding("error", str(path), f"Invalid JSON: {e}")
