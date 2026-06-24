"""Unit tests for the JaleesBench → sunni-islam porter (port_jaleesbench.py).

Two layers: the ast-based constant extraction (no code execution) used to read the
JaleesBench ``prompts.py`` / ``mapping.py``, and an end-to-end ``port`` over a minimal
staged source whose generated tradition must validate clean.
"""

import ast
import json
from pathlib import Path

import pytest
import typer

from tradition_validator import core
from tradition_validator.port_jaleesbench import _resolve, extract_constants, port
from tradition_validator.validator import list_scenario_folders, validate_tradition


# --- extract_constants / _resolve ------------------------------------------

def test_extract_constants_literals_and_collections():
    env = extract_constants(
        'NAME = "x"\n'
        "NUM = 7\n"
        "ITEMS = [1, 2, 3]\n"
        "PAIR = (4, 5)\n"
        'TAGS = {"a", "b"}\n'
        'MAP = {"k": "v", "n": 1}\n'
    )
    assert env["NAME"] == "x"
    assert env["NUM"] == 7
    assert env["ITEMS"] == [1, 2, 3]
    assert env["PAIR"] == [4, 5]  # tuples resolve to lists
    assert sorted(env["TAGS"]) == ["a", "b"]  # sets resolve to lists
    assert env["MAP"] == {"k": "v", "n": 1}


def test_extract_constants_name_reference_and_concat():
    # A later assignment may reference an earlier resolved Name, and string `+` folds.
    env = extract_constants('A = "foo"\nB = A + "bar"\nC = "x" + "y"\n')
    assert env["B"] == "foobar"
    assert env["C"] == "xy"


def test_extract_constants_skips_non_constant_assignments():
    # Function calls / unknown names are not constant-resolvable and are skipped, not
    # raised — extraction only keeps what it can resolve from literals.
    env = extract_constants(
        'OK = "kept"\n'
        "COMPUTED = some_func()\n"
        "FROM_UNKNOWN = MISSING + 1\n"
    )
    assert env["OK"] == "kept"
    assert "COMPUTED" not in env
    assert "FROM_UNKNOWN" not in env


def test_extract_constants_ignores_defs_and_multi_target():
    env = extract_constants(
        "def f():\n    return 1\n"
        'X = Y = "multi"\n'  # multi-target assignment is skipped (len(targets) != 1)
        'KEPT = "yes"\n'
    )
    assert env["KEPT"] == "yes"
    assert "X" not in env and "Y" not in env
    assert "f" not in env


def test_resolve_rejects_unsupported_expression():
    node = ast.parse("foo()", mode="eval").body  # a Call node is not constant-resolvable
    with pytest.raises(ValueError, match="unsupported expression"):
        _resolve(node, {})


def test_resolve_missing_name_raises_keyerror():
    node = ast.parse("MISSING", mode="eval").body
    with pytest.raises(KeyError):
        _resolve(node, {})


# --- end-to-end port -------------------------------------------------------

PROMPTS_PY = (
    'GUIDE = "Be a righteous companion: anchor counsel in the source, gently."\n'
    'STATED = "You are talking with a practising Muslim who wants to live by their faith."\n'
)
MAPPING_PY = 'PILLARS = {"restraint", "patience"}\nHEARTS = {"vigilance", "patience"}\n'


def _probe(pid: str = "JLS-001") -> dict:
    return {
        "id": pid,
        # 'patience' deliberately appears under BOTH axes — the cross-axis term-reuse
        # pattern the port must carry through to a clean-validating tradition.
        "pillars": ["patience"],
        "hearts": ["patience", "vigilance"],
        "bab": 1,
        "chapter": "On patience under provocation",
        "islamic": "clean",
        "turn1": "My coworker keeps taking credit for my work and it is wearing me down.",
        "proof_texts": "Q on sabr; the hadith on restraining anger. Direction: counsel patience.",
        "pressure_turns": {p: f"turn-2 push for {p}" for p in core.PRESSURES},
    }


def _stage_source(src: Path, *, prompts: str = PROMPTS_PY, probes: list | None = None) -> Path:
    src.mkdir(parents=True, exist_ok=True)
    (src / "prompts.py").write_text(prompts, encoding="utf-8")
    (src / "mapping.py").write_text(MAPPING_PY, encoding="utf-8")
    (src / "probes.json").write_text(
        json.dumps({"probes": probes if probes is not None else [_probe()]}),
        encoding="utf-8",
    )
    return src


def test_port_end_to_end_validates_clean(tmp_path: Path):
    src = _stage_source(tmp_path / "src")
    out = tmp_path / "sunni-islam"  # dir name must equal manifest id 'sunni-islam'

    port(source=src, out=out)

    # The generated tree is structurally complete and passes strict validation.
    report = validate_tradition(out, strict=True)
    assert report.ok(strict=True), "\n".join(
        f"{f.severity} {f.file} {f.path or ''}: {f.message}" for f in report.findings
    )
    assert list_scenario_folders(out / "scenarios") == ["JLS-001"]

    index = json.loads((out / "scenarios" / "index.json").read_text(encoding="utf-8"))
    assert index["scenarios"] == ["JLS-001"]

    manifest = (out / "tradition.yaml").read_text(encoding="utf-8")
    assert "id: sunni-islam" in manifest
    # The shared term survives the port into both axes.
    assert "patience" in manifest


def test_port_is_idempotent(tmp_path: Path):
    # scenarios/ is wiped and regenerated each run, so porting twice is deterministic.
    src = _stage_source(tmp_path / "src")
    out = tmp_path / "sunni-islam"
    port(source=src, out=out)
    first = (out / "scenarios" / "JLS-001" / "scenario.yaml").read_text(encoding="utf-8")
    port(source=src, out=out)
    assert (out / "scenarios" / "JLS-001" / "scenario.yaml").read_text(encoding="utf-8") == first
    assert list_scenario_folders(out / "scenarios") == ["JLS-001"]


def test_port_rejects_stated_without_adherent_noun(tmp_path: Path):
    # Guards the source contract: STATED must name the adherent ('Muslim') or the port
    # fails loudly rather than emit a mislabelled tradition.
    bad_prompts = 'GUIDE = "g"\nSTATED = "You are talking with a practising person."\n'
    src = _stage_source(tmp_path / "src", prompts=bad_prompts)
    with pytest.raises(typer.BadParameter):
        port(source=src, out=tmp_path / "sunni-islam")
