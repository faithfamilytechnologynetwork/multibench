"""Collector (spec §4.5/§5.6, T11): framing-blinded 4-turn sittings, resume, limit, failures.
The provider boundary is injected (no live API)."""

import json

from judging.collect import collect
from judging.config import Config, SubjectSpec
from judging.loaders import load_scenario, load_tradition
from judging.prompts import framing_context


def _fake(reply="REPLY"):
    def fn(subject, ctx, msgs):
        return (reply, {"in": 1, "out": 1})

    return fn


def _cfg(framings=("unstated",), pressures=("secularize",)):
    return Config(
        subjects=(SubjectSpec("claude-opus-4-8"),), framings=framings, pressures=pressures
    )


def _first_sitting(tmp_path):
    return json.loads((tmp_path / "sittings.jsonl").read_text().splitlines()[0])


def test_collect_one_cell_is_clean_and_blinded(sunni, tmp_path):
    summary = collect(sunni, tmp_path, config=_cfg(), subject_fn=_fake(), limit=1)
    assert summary["written"] == 1
    s = _first_sitting(tmp_path)
    assert s["framing"] == "unstated"
    assert s["context_prefix"] is None  # unstated carries no prefix
    assert [t["role"] for t in s["turns"]] == ["user", "assistant", "user", "assistant"]
    sc = load_scenario(sunni, s["scenario_id"])
    assert s["turns"][0]["content"] == sc.turn1  # clean scenario text
    assert s["turns"][2]["content"] == sc.pressures["secularize"]
    assert s["turns"][1]["content"] == s["turns"][3]["content"] == "REPLY"
    assert s["subject"] == "claude-opus-4-8" and s["tradition"] == "sunni-islam"


def test_framing_goes_to_subject_and_into_prefix_but_not_turns(sunni, tmp_path):
    # Stated framing: handed to the subject layer (as ctx) + recorded in context_prefix,
    # but NEVER leaked into the stored (judged) turns (T11 blinding).
    seen_ctx = []

    def fake(subject, ctx, msgs):
        seen_ctx.append(ctx)
        return ("R", {})

    collect(sunni, tmp_path, config=_cfg(framings=("stated",)), subject_fn=fake, limit=1)
    s = _first_sitting(tmp_path)
    trad = load_tradition(sunni)
    stated = framing_context("stated", trad)  # the Stated sentence (with adherent_noun)

    assert all(c == stated for c in seen_ctx)  # framing handed to the subject layer
    assert stated in s["context_prefix"]  # recorded for audit
    assert all(stated not in t["content"] for t in s["turns"])  # not in judged turns


def test_collect_resume_does_not_rewrite_done_cells(sunni, tmp_path):
    collect(sunni, tmp_path, config=_cfg(), subject_fn=_fake(), limit=1)
    summary2 = collect(sunni, tmp_path, config=_cfg(), subject_fn=_fake(), limit=1)
    assert summary2["written"] == 1  # a *different* cell
    lines = (tmp_path / "sittings.jsonl").read_text().splitlines()
    scen_ids = [json.loads(l)["scenario_id"] for l in lines]
    assert len(scen_ids) == len(set(scen_ids)) == 2  # two distinct cells, no duplicate


def test_collect_limit_caps_written(sunni, tmp_path):
    summary = collect(sunni, tmp_path, config=_cfg(), subject_fn=_fake(), limit=3)
    assert summary["written"] == 3
    assert summary["todo"] == 3


def test_collect_failure_is_counted(sunni, tmp_path):
    def boom(subject, ctx, msgs):
        raise RuntimeError("api down")

    summary = collect(sunni, tmp_path, config=_cfg(), subject_fn=boom, limit=2)
    assert summary["failed"] == 2
    assert summary["written"] == 0
