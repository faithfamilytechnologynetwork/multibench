"""Loader + validation tests (spec T1/T2): fail-fast on every §4.1 error condition;
tolerate the documented benign ones; v2 overrides win by identity key.
"""

import json
import shutil
from pathlib import Path

import pytest

from analysis.loaders import (
    AnalysisInputError,
    is_valid_score,
    load_corpus,
    load_run_dir,
)

FIX = Path(__file__).resolve().parent / "fixtures"


def _copy_fixture(src_name: str, dst: Path) -> Path:
    run = dst / src_name
    shutil.copytree(FIX / src_name, run)
    return run


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


# --- happy path ---------------------------------------------------------------

def test_load_run_dir_ok():
    run = load_run_dir(FIX / "buddhism")
    assert run.tradition == "buddhism"
    assert run.subjects == ["claude-opus-4-8", "claude-sonnet-4-6"]
    assert len(run.judgments) == 216  # v2 overrides by key, never adds a row


def test_load_corpus_two_traditions():
    runs = load_corpus([FIX / "buddhism", FIX / "taoism"])
    assert [r.tradition for r in runs] == ["buddhism", "taoism"]


# --- is_valid_score -----------------------------------------------------------

@pytest.mark.parametrize("v", [-1.0, -0.5, 0.0, 0.5, 1.0, 1, 0])
def test_valid_scores(v):
    assert is_valid_score(v)


@pytest.mark.parametrize("v", ["1.0", 0.25, 2.0, True, False, None, "x"])
def test_invalid_scores(v):
    # A string score (as it appears inside `raw`) and off-grid/bool values are rejected.
    assert not is_valid_score(v)


# --- v2 overlay (T2) ----------------------------------------------------------

def test_v2_overrides_by_key_without_changing_count(tmp_path):
    run = _copy_fixture("buddhism", tmp_path)
    v2 = _read_jsonl(run / "judgments_v2.jsonl")
    override = v2[0]
    key = (override["subject"], override["scenario_id"], override["pressure"],
           override["framing"], override["judge"], override["scope"])

    loaded = load_run_dir(run)
    assert len(loaded.judgments) == 216
    got = [
        j for j in loaded.judgments
        if (j["subject"], j["scenario_id"], j["pressure"], j["framing"],
            j["judge"], j["scope"]) == key
    ]
    assert len(got) == 1
    assert got[0]["score"] == override["score"]  # v2 wins


def test_empty_and_absent_v2_are_valid(tmp_path):
    run = _copy_fixture("buddhism", tmp_path)
    (run / "judgments_v2.jsonl").write_text("", encoding="utf-8")  # empty -> no-op
    assert len(load_run_dir(run).judgments) == 216
    (run / "judgments_v2.jsonl").unlink()  # absent -> no-op
    assert len(load_run_dir(run).judgments) == 216


def test_extra_files_are_ignored(tmp_path):
    run = _copy_fixture("buddhism", tmp_path)
    (run / "batch_state.json").write_text("{}", encoding="utf-8")
    (run / "config.yaml").write_text("concurrency: 16\n", encoding="utf-8")
    # report.md already present in the fixture; none of these should raise.
    assert load_run_dir(run).tradition == "buddhism"


# --- fail-fast (T1) -----------------------------------------------------------

def test_missing_report_raises(tmp_path):
    run = _copy_fixture("buddhism", tmp_path)
    (run / "report.json").unlink()
    with pytest.raises(AnalysisInputError, match="report.json"):
        load_run_dir(run)


def test_missing_judgments_raises(tmp_path):
    run = _copy_fixture("buddhism", tmp_path)
    (run / "judgments.jsonl").unlink()
    with pytest.raises(AnalysisInputError, match="judgments.jsonl"):
        load_run_dir(run)


def test_missing_key_raises(tmp_path):
    run = _copy_fixture("buddhism", tmp_path)
    rows = _read_jsonl(run / "judgments.jsonl")
    del rows[0]["score"]
    _write_jsonl(run / "judgments.jsonl", rows)
    with pytest.raises(AnalysisInputError, match="missing required key 'score'"):
        load_run_dir(run)


def test_off_grid_score_raises(tmp_path):
    run = _copy_fixture("buddhism", tmp_path)
    rows = _read_jsonl(run / "judgments.jsonl")
    rows[0]["score"] = 0.3
    _write_jsonl(run / "judgments.jsonl", rows)
    with pytest.raises(AnalysisInputError, match="invalid score"):
        load_run_dir(run)


def test_string_score_from_raw_raises(tmp_path):
    run = _copy_fixture("buddhism", tmp_path)
    rows = _read_jsonl(run / "judgments.jsonl")
    rows[0]["score"] = "1.0"  # the string form inside `raw` — must not be accepted
    _write_jsonl(run / "judgments.jsonl", rows)
    with pytest.raises(AnalysisInputError, match="invalid score"):
        load_run_dir(run)


def test_cross_metadata_mismatch_raises(tmp_path):
    run = _copy_fixture("buddhism", tmp_path)
    rows = _read_jsonl(run / "judgments.jsonl")
    rows[0]["tradition"] = "taoism"  # disagrees with report.json tradition
    _write_jsonl(run / "judgments.jsonl", rows)
    with pytest.raises(AnalysisInputError, match="cross-metadata mismatch"):
        load_run_dir(run)


def test_unknown_subject_raises(tmp_path):
    run = _copy_fixture("buddhism", tmp_path)
    rows = _read_jsonl(run / "judgments.jsonl")
    rows[0]["subject"] = "some-other-model"
    _write_jsonl(run / "judgments.jsonl", rows)
    with pytest.raises(AnalysisInputError, match="cross-metadata mismatch"):
        load_run_dir(run)


def test_duplicate_base_identity_raises(tmp_path):
    run = _copy_fixture("buddhism", tmp_path)
    rows = _read_jsonl(run / "judgments.jsonl")
    rows.append(dict(rows[0]))  # exact-identity duplicate
    _write_jsonl(run / "judgments.jsonl", rows)
    with pytest.raises(AnalysisInputError, match="duplicate base identity"):
        load_run_dir(run)


def test_duplicate_tradition_id_raises(tmp_path):
    run_a = _copy_fixture("buddhism", tmp_path)
    run_b = tmp_path / "buddhism-copy"
    shutil.copytree(FIX / "buddhism", run_b)
    with pytest.raises(AnalysisInputError, match="duplicate tradition id"):
        load_corpus([run_a, run_b])


def test_empty_paths_raises():
    with pytest.raises(AnalysisInputError, match="no run-dirs"):
        load_corpus([])
