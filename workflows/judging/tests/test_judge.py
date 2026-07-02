"""Judge orchestration (spec §5.5/§5.9): parse/validate, self-judge skip, resume,
re-judge override, failure handling. The provider boundary is injected (no live API)."""

import json

import pytest

from judging.config import Config, JudgeSpec, SubjectSpec
from judging.judge import (
    JudgeInputError,
    judge_all,
    load_judgments,
    load_skips,
    parse_verdict,
    should_skip,
)


def _sitting(subject, scenario_id="JLS-001", pressure="secularize", framing="unstated"):
    return {
        "subject": subject,
        "tradition": "sunni-islam",
        "scenario_id": scenario_id,
        "pressure": pressure,
        "framing": framing,
        "turns": [
            {"role": "user", "content": "u1"},
            {"role": "assistant", "content": "a1"},
            {"role": "user", "content": "u2"},
            {"role": "assistant", "content": "a2"},
        ],
    }


def _write_sittings(tmp_path, *sittings):
    p = tmp_path / "sittings.jsonl"
    p.write_text("".join(json.dumps(s) + "\n" for s in sittings), encoding="utf-8")
    return p


def _fixed_fn(score=1.0):
    def fn(judge, parts):
        v = {"score": score, "direction": "d", "rationale": "r", "techniques_used": ["open_door"]}
        return (v, json.dumps(v), {"in": 1, "out": 1})  # (verdict, raw_text, usage)

    return fn


# --- parse_verdict (T1/T2) --------------------------------------------------


def test_parse_verdict_valid():
    v = parse_verdict(
        {"score": 0.5, "direction": "dir", "rationale": "because X", "techniques_used": ["open_door", "gradualism"]}
    )
    assert v == {
        "score": 0.5,
        "direction": "dir",
        "rationale": "because X",
        "techniques_used": ["open_door", "gradualism"],
    }


@pytest.mark.parametrize(
    "raw",
    [
        {"score": 0.7, "direction": "d", "rationale": "r"},  # off-grid score (T2)
        {"score": 3, "direction": "d", "rationale": "r"},  # out of range
        {"score": 1.0, "direction": "d", "rationale": ""},  # empty rationale
        {"score": 1.0, "direction": "", "rationale": "r"},  # empty direction
        {"score": 1.0, "direction": "d", "rationale": "r", "techniques_used": ["nope"]},  # unknown
        {"score": 1.0, "direction": "d", "rationale": "r", "techniques_used": "open_door"},  # not list
        "not-a-dict",
    ],
)
def test_parse_verdict_rejects(raw):
    with pytest.raises(ValueError):
        parse_verdict(raw)


# --- self-judge skip (T5) ---------------------------------------------------


def test_should_skip_exact_model_match():
    assert should_skip("claude-opus-4-8", "claude-opus-4-8") is True
    assert should_skip("claude-opus-4-8", "claude-sonnet-4-6") is False


def test_self_judgments_are_skipped(sunni, tmp_path):
    # Subject == the Opus judge -> Opus skips; Gemini judges both scopes.
    sp = _write_sittings(tmp_path, _sitting("claude-opus-4-8"))
    summary = judge_all(sp, sunni, tmp_path, judge_fn=_fixed_fn())
    assert summary["written"] == 2  # gemini x {turn1, full}
    assert summary["skipped_self"] == 2  # opus x {turn1, full}
    assert {j["judge"] for j in load_judgments(tmp_path)} == {"gemini-3.5-flash"}
    # ...and the skipped self-judgments are durably recorded (T5/M3 audit trail).
    skips = load_skips(tmp_path)
    assert len(skips) == 2
    assert all(sk["reason"] == "self_judge" and sk["judge"] == "claude-opus-4-8" for sk in skips)


# --- full panel x scope + keying (M3) --------------------------------------


def test_judge_all_writes_panel_times_scope(sunni, tmp_path):
    sp = _write_sittings(tmp_path, _sitting("claude-sonnet-4-6"))  # not a judge -> no skip
    summary = judge_all(sp, sunni, tmp_path, judge_fn=_fixed_fn(1.0))
    assert summary["written"] == 4  # 2 judges x 2 scopes
    js = load_judgments(tmp_path)
    assert len(js) == 4
    assert {j["scope"] for j in js} == {"turn1", "full"}
    assert all(j["score"] == 1.0 for j in js)
    assert all(j["sitting_key"] == "claude-sonnet-4-6|JLS-001|secularize|unstated" for j in js)


# --- idempotent resume (T9) -------------------------------------------------


def test_resume_skips_completed_cells(sunni, tmp_path):
    sp = _write_sittings(tmp_path, _sitting("claude-sonnet-4-6"))
    judge_all(sp, sunni, tmp_path, judge_fn=_fixed_fn())
    summary2 = judge_all(sp, sunni, tmp_path, judge_fn=_fixed_fn())
    assert summary2["written"] == 0  # all four already done
    assert len(load_judgments(tmp_path)) == 4


# --- failures left pending + counted (M12) ----------------------------------


def test_failure_is_counted_and_nothing_written(sunni, tmp_path):
    def boom(judge, parts):
        raise RuntimeError("api down")

    sp = _write_sittings(tmp_path, _sitting("claude-sonnet-4-6"))
    summary = judge_all(sp, sunni, tmp_path, judge_fn=boom)
    assert summary["failed"] >= 1
    assert summary["written"] == 0
    assert load_judgments(tmp_path) == []  # never written as a score


# --- re-judge on >=2-level disagreement (T4/T16/M10) ------------------------


def test_rejudge_pass_on_disagreement(sunni, tmp_path):
    # Opus -> +1.0, Gemini -> 0.0  =>  gap 1.0 (>= 2 levels) -> re-judge.
    def split(judge, parts):
        score = 1.0 if judge.model == "claude-opus-4-8" else 0.0
        _v = {"score": score, "direction": "d", "rationale": "r", "techniques_used": []}
        return (_v, json.dumps(_v), {})

    sp = _write_sittings(tmp_path, _sitting("claude-sonnet-4-6"))
    summary = judge_all(sp, sunni, tmp_path, judge_fn=split)
    assert summary["rejudge_cells"] >= 1
    assert summary["rejudged"] >= 1
    assert (tmp_path / "judgments_v2.jsonl").exists()
    # Overlay: load_judgments returns one record per (cell, judge) — v2 overrides base.
    keys = [
        (j["subject"], j["scenario_id"], j["pressure"], j["framing"], j["judge"], j["scope"])
        for j in load_judgments(tmp_path)
    ]
    assert len(keys) == len(set(keys))  # no duplicates after overlay


def test_no_rejudge_when_judges_agree(sunni, tmp_path):
    sp = _write_sittings(tmp_path, _sitting("claude-sonnet-4-6"))
    summary = judge_all(sp, sunni, tmp_path, judge_fn=_fixed_fn(0.5))  # both judges 0.5
    assert summary["rejudge_cells"] == 0
    assert not (tmp_path / "judgments_v2.jsonl").exists()


# --- fail-loud on missing / malformed sittings input (spec N2) --------------


def test_missing_sittings_file_fails_loud(sunni, tmp_path):
    with pytest.raises(JudgeInputError):
        judge_all(tmp_path / "does-not-exist.jsonl", sunni, tmp_path, judge_fn=_fixed_fn())


def test_malformed_sitting_row_fails_loud(sunni, tmp_path):
    sp = tmp_path / "sittings.jsonl"
    # second row is missing required fields
    sp.write_text(
        json.dumps(_sitting("claude-sonnet-4-6")) + "\n" + json.dumps({"subject": "x"}) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(JudgeInputError):
        judge_all(sp, sunni, tmp_path, judge_fn=_fixed_fn())


def test_invalid_json_row_fails_loud(sunni, tmp_path):
    sp = tmp_path / "sittings.jsonl"
    sp.write_text(json.dumps(_sitting("claude-sonnet-4-6")) + "\n{ not json\n", encoding="utf-8")
    with pytest.raises(JudgeInputError):
        judge_all(sp, sunni, tmp_path, judge_fn=_fixed_fn())


@pytest.mark.parametrize("bad", [{"subject": None}, {"pressure": 3}, {"framing": ""}])
def test_non_string_required_field_fails_loud(sunni, tmp_path, bad):
    s = _sitting("claude-sonnet-4-6")
    s.update(bad)
    sp = _write_sittings(tmp_path, s)
    with pytest.raises(JudgeInputError):
        judge_all(sp, sunni, tmp_path, judge_fn=_fixed_fn())


def test_judgment_tradition_is_authoritative(sunni, tmp_path):
    # `tradition` on each judgment row is the tradition being judged, even if the sitting
    # omits the optional self-report field (§5.8 requires it on every row).
    s = _sitting("claude-sonnet-4-6")
    del s["tradition"]
    sp = _write_sittings(tmp_path, s)
    judge_all(sp, sunni, tmp_path, judge_fn=_fixed_fn())
    js = load_judgments(tmp_path)
    assert js and all(j["tradition"] == "sunni-islam" for j in js)


def test_judgment_carries_raw_text(sunni, tmp_path):
    # M19: every judgment retains the judge's raw response text for audit/debug.
    sp = _write_sittings(tmp_path, _sitting("claude-sonnet-4-6"))
    judge_all(sp, sunni, tmp_path, judge_fn=_fixed_fn())
    js = load_judgments(tmp_path)
    assert js and all(j["raw"] and json.loads(j["raw"])["score"] == 1.0 for j in js)


def test_judge_concurrency_is_honored(sunni, tmp_path):
    # M15/T19: the base judge pass fans out under config.concurrency (overlap bounded).
    import threading
    import time

    sittings = [
        _sitting("subj", pressure=p, framing=f)
        for p in ("secularize", "insistence")
        for f in ("unstated", "stated")
    ]
    sp = _write_sittings(tmp_path, *sittings)
    cfg = Config(
        judges=(JudgeSpec("jA", "anthropic"), JudgeSpec("jB", "anthropic")),
        subjects=(SubjectSpec("subj"),),
        concurrency=4,
    )
    state, lock = {"in": 0, "max": 0}, threading.Lock()

    def fn(judge, parts):
        with lock:
            state["in"] += 1
            state["max"] = max(state["max"], state["in"])
        time.sleep(0.02)
        with lock:
            state["in"] -= 1
        _v = {"score": 1.0, "direction": "d", "rationale": "r", "techniques_used": []}
        return (_v, json.dumps(_v), {})

    judge_all(str(sp), sunni, tmp_path, config=cfg, judge_fn=fn)
    assert state["max"] > 1  # ran concurrently (4 sittings x 2 judges x 2 scopes = 16 cells)
    assert state["max"] <= 4  # bounded by config.concurrency


def _judgment_keys(results_dir):
    return {
        (j["subject"], j["scenario_id"], j["pressure"], j["framing"], j["judge"], j["scope"], j["score"])
        for j in load_judgments(results_dir)
    }


def test_judge_parallel_output_set_equivalent_to_serial(sunni, tmp_path):
    # Same SET of judgments regardless of concurrency (M15); line order may differ.
    sittings = [
        _sitting("subj", pressure=p, framing=f)
        for p in ("secularize", "insistence")
        for f in ("unstated", "stated")
    ]
    judges = (JudgeSpec("jA", "anthropic"), JudgeSpec("jB", "anthropic"))
    subs = (SubjectSpec("subj"),)
    serial_dir, par_dir = tmp_path / "serial", tmp_path / "par"
    serial_dir.mkdir()
    par_dir.mkdir()
    judge_all(
        str(_write_sittings(serial_dir, *sittings)), sunni, serial_dir,
        config=Config(judges=judges, subjects=subs, concurrency=1), judge_fn=_fixed_fn(),
    )
    judge_all(
        str(_write_sittings(par_dir, *sittings)), sunni, par_dir,
        config=Config(judges=judges, subjects=subs, concurrency=6), judge_fn=_fixed_fn(),
    )
    assert _judgment_keys(serial_dir) == _judgment_keys(par_dir)


def test_judge_rejudge_runs_under_concurrency_and_counts_cells(sunni, tmp_path):
    # M15 + rejudge_cells fix: a >=2-level disagreement re-judges under concurrency; the count is
    # over the FULL cell key (both scopes disagree -> 2 distinct cells, not collapsed to 1).
    sp = _write_sittings(tmp_path, _sitting("subj"))
    cfg = Config(
        judges=(JudgeSpec("jA", "anthropic"), JudgeSpec("jB", "anthropic")),
        subjects=(SubjectSpec("subj"),),
        concurrency=4,
    )

    def fn(judge, parts):
        score = 1.0 if judge.model == "jA" else -1.0  # gap 2.0 >= 1.0 -> re-judge
        _v = {"score": score, "direction": "d", "rationale": "r", "techniques_used": []}
        return (_v, json.dumps(_v), {})

    summary = judge_all(str(sp), sunni, tmp_path, config=cfg, judge_fn=fn)
    assert summary["rejudge_cells"] == 2  # turn1 + full, each a distinct cell
    assert summary["rejudged"] >= 1
    assert (tmp_path / "judgments_v2.jsonl").exists()
