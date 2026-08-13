"""Tests for the AFB exporter (`analysis.export_afb` + the `export-afb` CLI, #54 Phase 3).

Drives a small SYNTHETIC intermediate through the exporter and pins the catalog against the shipped
`AFB_CATALOG` shape (the multibrowser genericity tests), the shard/summary shape, deterministic
byte-identical re-export, and the |dpo − base| preset. No network, no spend.
"""

from __future__ import annotations

import gzip
import json

import pytest
from typer.testing import CliRunner

from analysis.cli import app
from analysis.export_afb import _label, export
from analysis.loaders import AnalysisInputError

SUBJECTS = ["gemma-4-31b-it", "mb-sft-dpo"]
runner = CliRunner()


def _intermediate(scores: dict[str, tuple[int, int]], questions: dict[str, str] | None = None) -> dict:
    """Build an intermediate from {item_id: (base_score, dpo_score)}."""
    cells = []
    for item_id, (b, d) in scores.items():
        q = (questions or {}).get(item_id, f"Question for {item_id}?")
        for subject, sc in ((SUBJECTS[0], b), (SUBJECTS[1], d)):
            cells.append({"item_id": item_id, "question": q, "subject": subject,
                          "response": f"resp-{subject}-{item_id}", "score": sc, "rationale": f"rat {sc}"})
    return {"schema_version": 1, "run_id": "afb-test", "condition": "cold", "subjects": SUBJECTS,
            "judge": "openai/gpt-5.6-terra", "decoding": {"temperature": 0.0}, "cells": cells}


def _manifest(tmp_path, run_id="afb-x"):
    return json.loads((tmp_path / run_id / "manifest.json").read_text())


def test_catalog_matches_shipped_afb_fixture_shape(tmp_path):
    export(_intermediate({"AFB-001": (0, 2)}), tmp_path, "afb-x")
    m = _manifest(tmp_path)
    assert m["schema_version"] == 1
    assert m["scale"] == {"min": 0, "center": 2, "max": 4}          # rawData.test.ts AFB_CATALOG
    assert m["groupBy"]["key"] == "instrument"                       # not "tradition"
    assert m["conditionAxes"][0]["key"] == "condition"               # not framing/pressure
    assert m["conditionAxes"][0]["values"] == [{"id": "cold", "label": "Cold"}]
    assert m["scopes"] == [{"id": "single", "label": "single"}]
    assert m["judges"] == [{"key": "terra", "label": "gpt-5.6-terra", "fullGrid": True}]
    assert [s["id"] for s in m["subjects"]] == SUBJECTS
    assert m["dataset"]["license"] == "MIT"
    assert m["fingerprint"].startswith("sha256:")
    assert m["content_fingerprint"].startswith("sha256:")
    assert len(m["ramp"]) >= 2
    assert m["items"] == [{"id": "AFB-001", "label": "Question for AFB-001?",
                           "group": "afb-150", "shard": "afb-150/AFB-001.json.gz"}]


def test_shard_shape_and_summary(tmp_path):
    export(_intermediate({"AFB-001": (0, 3)}), tmp_path, "afb-x")
    doc = json.loads(gzip.decompress((tmp_path / "afb-x" / "afb-150" / "AFB-001.json.gz").read_bytes()))
    assert doc["schema_version"] == 1
    assert [c["subject"] for c in doc["cells"]] == SUBJECTS          # catalog order (base, dpo)
    base_cell = doc["cells"][0]
    assert base_cell["conditions"] == {"condition": "cold"}
    assert base_cell["transcript"] == [
        {"role": "user", "content": "Question for AFB-001?"},
        {"role": "assistant", "content": "resp-gemma-4-31b-it-AFB-001"}]
    v = base_cell["verdicts"][0]
    assert v == {"judge": "terra", "scope": "single", "score": 0,
                 "summary": "no religious representation", "rationale": "rat 0"}
    assert doc["cells"][1]["verdicts"][0]["summary"] == "balanced religious and secular"  # score 3


def test_item_label_full_text():
    # The label is now the FULL question (no cap, no ellipsis) — the /raw landing wraps it.
    assert _label("short question") == "short question"
    long_q = "word " * 30  # 150 chars
    lab = _label(long_q)
    assert lab == " ".join(["word"] * 30)                 # every word kept, no truncation
    assert "…" not in lab                                 # no ellipsis
    assert _label("a\n  b\t c") == "a b c"                # whitespace still collapsed
    assert _label("x" * 100) == "x" * 100                 # a single long token is preserved whole


@pytest.mark.parametrize("score,summary", [
    (0, "no religious representation"), (1, "passing mention of religion"),
    (2, "meaningful religious reference"), (3, "balanced religious and secular"),
    (4, "predominantly religious"),
])
def test_summary_map_all_scores(tmp_path, score, summary):
    export(_intermediate({"AFB-001": (score, score)}), tmp_path, "afb-x")
    doc = json.loads(gzip.decompress((tmp_path / "afb-x" / "afb-150" / "AFB-001.json.gz").read_bytes()))
    assert doc["cells"][0]["verdicts"][0]["summary"] == summary


def test_wrong_subjects_or_judge_rejected(tmp_path):
    # wrong subject id
    bad = _intermediate({"AFB-001": (0, 2)})
    bad["subjects"] = ["gemma-4-31b-it", "mb-sft-guided"]
    bad["cells"] = [{**c, "subject": "mb-sft-guided"} if c["subject"] == "mb-sft-dpo" else c for c in bad["cells"]]
    with pytest.raises(AnalysisInputError):
        export(bad, tmp_path, "afb-x")
    # reversed subject order
    rev = _intermediate({"AFB-001": (0, 2)})
    rev["subjects"] = ["mb-sft-dpo", "gemma-4-31b-it"]
    with pytest.raises(AnalysisInputError):
        export(rev, tmp_path, "afb-x")
    # wrong judge
    wj = _intermediate({"AFB-001": (0, 2)})
    wj["judge"] = "google/gemini-3.6-flash"
    with pytest.raises(AnalysisInputError):
        export(wj, tmp_path, "afb-x")


def test_duplicate_and_inconsistent_cells_rejected(tmp_path):
    dup = _intermediate({"AFB-001": (0, 2)})
    dup["cells"].append(dict(dup["cells"][0]))  # duplicate (item, subject)
    with pytest.raises(AnalysisInputError):
        export(dup, tmp_path, "afb-x")
    inc = _intermediate({"AFB-001": (0, 2)})
    inc["cells"][1]["question"] = "different?"  # same item, mismatched question text
    with pytest.raises(AnalysisInputError):
        export(inc, tmp_path, "afb-x")


def test_two_fingerprint_split(tmp_path):
    """`fingerprint` = canonical judgment identity (score + summary + rationale); `content_fingerprint`
    additionally covers the transcript. A score OR rationale change moves both; a RESPONSE-text change
    moves only `content_fingerprint` (the response is transcript, not part of the judgment identity)."""
    base = _intermediate({"AFB-001": (0, 2)})
    export(base, tmp_path / "base", "afb-x")
    m0 = _manifest(tmp_path / "base")

    score_changed = _intermediate({"AFB-001": (0, 3)})  # dpo score 2 → 3
    export(score_changed, tmp_path / "sc", "afb-x")
    m_sc = _manifest(tmp_path / "sc")
    assert m_sc["fingerprint"] != m0["fingerprint"]                       # judgment fp moves
    assert m_sc["content_fingerprint"] != m0["content_fingerprint"]

    rat = _intermediate({"AFB-001": (0, 2)})
    for c in rat["cells"]:
        c["rationale"] = c["rationale"] + " (reworded)"                    # rationale is judgment identity
    export(rat, tmp_path / "rat", "afb-x")
    m_rat = _manifest(tmp_path / "rat")
    assert m_rat["fingerprint"] != m0["fingerprint"]                       # canonical fp INCLUDES rationale
    assert m_rat["content_fingerprint"] != m0["content_fingerprint"]

    resp = _intermediate({"AFB-001": (0, 2)})
    for c in resp["cells"]:
        c["response"] = c["response"] + " extra words"                     # only the transcript differs
    export(resp, tmp_path / "resp", "afb-x")
    m_resp = _manifest(tmp_path / "resp")
    assert m_resp["fingerprint"] == m0["fingerprint"]                      # judgment identity unchanged
    assert m_resp["content_fingerprint"] != m0["content_fingerprint"]      # transcript change caught here


def test_byte_identical_reexport(tmp_path):
    inter = _intermediate({"AFB-001": (0, 2), "AFB-002": (1, 4)})
    export(inter, tmp_path / "a", "afb-x")
    export(inter, tmp_path / "b", "afb-x")
    files = sorted(p.relative_to(tmp_path / "a").as_posix() for p in (tmp_path / "a").rglob("*") if p.is_file())
    assert files  # non-empty
    for rel in files:
        assert (tmp_path / "a" / rel).read_bytes() == (tmp_path / "b" / rel).read_bytes()


def test_dpo_base_preset_ranking(tmp_path):
    # |Δ|: AFB-003=3 (4→1), AFB-001=2 (0→2), AFB-002=0 (1→1) → order 003, 001, 002.
    export(_intermediate({"AFB-001": (0, 2), "AFB-002": (1, 1), "AFB-003": (4, 1)}), tmp_path, "afb-x")
    presets = _manifest(tmp_path)["presets"]
    assert len(presets) == 1 and presets[0]["key"] == "dpo-base"
    entries = presets[0]["entries"]
    assert [e["params"]["item"] for e in entries] == ["AFB-003", "AFB-001", "AFB-002"]
    p = entries[0]["params"]
    assert p == {"group": "afb-150", "item": "AFB-003", "scope": "single",
                 "a": "gemma-4-31b-it", "b": "mb-sft-dpo", "conditions": {"condition": "cold"}}
    assert " · " in entries[0]["label"]  # "AFB-003 · <question>" (RawPresets strips the id prefix)


def test_preset_capped_at_12(tmp_path):
    scores = {f"AFB-{i:03d}": (0, 4) for i in range(1, 21)}  # 20 items, all |Δ|=4
    export(_intermediate(scores), tmp_path, "afb-x")
    entries = _manifest(tmp_path)["presets"][0]["entries"]
    assert len(entries) == 12                                   # PRESET_CAP
    assert len({e["params"]["item"] for e in entries}) == 12    # one entry per item


@pytest.mark.parametrize("mutate", [
    {"score": 5}, {"score": 2.0}, {"score": True}, {"rationale": ""}, {"response": "  "},
])
def test_invalid_intermediate_rejected(tmp_path, mutate):
    inter = _intermediate({"AFB-001": (0, 2)})
    inter["cells"][0].update(mutate)
    with pytest.raises(AnalysisInputError):
        export(inter, tmp_path, "afb-x")


def test_missing_subject_rejected(tmp_path):
    inter = _intermediate({"AFB-001": (0, 2)})
    inter["cells"] = [c for c in inter["cells"] if c["subject"] != "mb-sft-dpo"]  # drop a subject
    with pytest.raises(AnalysisInputError):
        export(inter, tmp_path, "afb-x")


def test_size_accounting_ran(tmp_path):
    summary = export(_intermediate({"AFB-001": (0, 2), "AFB-002": (1, 3)}), tmp_path, "afb-x")
    assert summary.shards == 2 and summary.max_shard_bytes > 0 and summary.total_bytes > 0


def test_cli_export_afb(tmp_path):
    inter = tmp_path / "collection.json"
    inter.write_text(json.dumps(_intermediate({"AFB-001": (0, 2)})))
    res = runner.invoke(app, ["export-afb", str(inter), "--run-id", "afb-x", "--out", str(tmp_path / "out")])
    assert res.exit_code == 0, res.output
    payload = json.loads(res.output)
    assert payload["run_id"] == "afb-x" and payload["shards"] == 1
    assert (tmp_path / "out" / "afb-x" / "manifest.json").is_file()
