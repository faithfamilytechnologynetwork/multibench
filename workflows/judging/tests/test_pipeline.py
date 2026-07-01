"""End-to-end pipeline (spec S1, M12): collect → judge → report, fully mocked.

The provider seams are injected (no live API). Covers the happy path (report artifacts land
on partial data), the --limit bound (S4), and the M12 non-zero-exit contract when cells fail.
"""

import json

from judging.config import Config, JudgeSpec, SubjectSpec
from judging.pipeline import run_pipeline


def _cfg():
    # One subject, two judges (neither == the subject, so nothing self-skips), one framing +
    # one pressure -> a small but complete grid to exercise the whole pipeline.
    return Config(
        subjects=(SubjectSpec("claude-opus-4-8"),),
        # provider is irrelevant here — the injected judge_fn bypasses the provider layer.
        judges=(JudgeSpec("judge-a", "anthropic"), JudgeSpec("judge-b", "anthropic")),
        framings=("unstated",),
        pressures=("secularize",),
    )


def _subject_fn(reply="REPLY"):
    def fn(subject, ctx, msgs):
        return (reply, {"in": 1, "out": 1}, 1)

    return fn


def _judge_fn(score=1.0):
    def fn(judge, parts):
        verdict = {
            "score": score,
            "direction": "held the line",
            "rationale": "anchored to the guidance",
            "techniques_used": [],
        }
        return (verdict, {"in": 2, "out": 2})

    return fn


def test_pipeline_end_to_end_writes_all_artifacts(sunni, tmp_path):
    summary = run_pipeline(
        sunni,
        tmp_path,
        config=_cfg(),
        subject_fn=_subject_fn(),
        judge_fn=_judge_fn(),
        limit=1,
    )
    assert summary["failed"] == 0
    assert summary["collect"]["written"] == 1
    assert summary["judge"]["written"] == 4  # 2 judges x 2 scopes (turn1 + full) over one cell
    # The three stage artifacts + the report all exist.
    for name in ("sittings.jsonl", "judgments.jsonl", "report.md", "report.json"):
        assert (tmp_path / name).exists(), name
    rep = json.loads((tmp_path / "report.json").read_text())
    assert rep["tradition"] == "sunni-islam"
    assert rep["scorecard"]["claude-opus-4-8"]["headline"] == 1.0


def test_pipeline_limit_bounds_collection(sunni, tmp_path):
    summary = run_pipeline(
        sunni, tmp_path, config=_cfg(), subject_fn=_subject_fn(), judge_fn=_judge_fn(), limit=2
    )
    assert summary["collect"]["written"] == 2  # S4: --limit caps the grid cheaply


def test_pipeline_collect_failure_propagates_nonzero_but_report_still_runs(sunni, tmp_path):
    # M12: a failed collection cell -> summary.failed > 0 (CLI exits non-zero), yet report
    # is still written from whatever partial data exists (never hard-fails).
    def boom(subject, ctx, msgs):
        raise RuntimeError("subject api down")

    summary = run_pipeline(
        sunni, tmp_path, config=_cfg(), subject_fn=boom, judge_fn=_judge_fn(), limit=1
    )
    assert summary["failed"] > 0
    assert summary["collect"]["failed"] == 1
    assert (tmp_path / "report.md").exists()  # partial data still produces a report


def test_pipeline_judge_failure_counts_toward_failed(sunni, tmp_path):
    def bad_judge(judge, parts):
        raise RuntimeError("judge api down")

    summary = run_pipeline(
        sunni, tmp_path, config=_cfg(), subject_fn=_subject_fn(), judge_fn=bad_judge, limit=1
    )
    assert summary["collect"]["failed"] == 0
    assert summary["judge"]["failed"] > 0
    assert summary["failed"] == summary["judge"]["failed"]
