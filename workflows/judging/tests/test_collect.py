"""Collector (spec §4.5/§5.6, T11): framing-blinded 4-turn sittings, resume, limit, failures.
The provider boundary is injected (no live API)."""

import json

from judging.collect import collect
from judging.config import Config, SubjectSpec
from judging.loaders import load_scenario, load_tradition
from judging.prompts import framing_context


def _fake(reply="REPLY"):
    def fn(subject, ctx, msgs):
        return (reply, {"in": 1, "out": 1}, 1)  # (text, usage, attempts)

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
    assert s["attempts"] == [1, 1]  # §5.6 audit field populated
    assert s["usage"] == [{"in": 1, "out": 1}, {"in": 1, "out": 1}]


def test_framing_goes_to_subject_and_into_prefix_but_not_turns(sunni, tmp_path):
    # Stated framing: handed to the subject layer (as ctx) + recorded in context_prefix,
    # but NEVER leaked into the stored (judged) turns (T11 blinding).
    seen_ctx = []

    def fake(subject, ctx, msgs):
        seen_ctx.append(ctx)
        return ("R", {}, 1)

    collect(sunni, tmp_path, config=_cfg(framings=("stated",)), subject_fn=fake, limit=1)
    s = _first_sitting(tmp_path)
    trad = load_tradition(sunni)
    stated = framing_context("stated", trad)  # the Stated sentence (with adherent_noun)

    assert all(c == stated for c in seen_ctx)  # framing handed to the subject layer
    assert stated in s["context_prefix"]  # recorded for audit
    assert all(stated not in t["content"] for t in s["turns"])  # not in judged turns


def test_collect_guided_framing_in_prefix_not_turns(sunni, tmp_path):
    # The guided framing (the full guide) is the longest context_prefix; verify the same
    # blinding property holds for it.
    collect(sunni, tmp_path, config=_cfg(framings=("guided",)), subject_fn=_fake(), limit=1)
    s = _first_sitting(tmp_path)
    guide_ctx = framing_context("guided", load_tradition(sunni))
    assert s["framing"] == "guided"
    assert guide_ctx in s["context_prefix"]
    assert all(guide_ctx not in t["content"] for t in s["turns"])


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


def test_collect_scenarios_caps_to_first_n_full_grid_all_subjects(sunni, tmp_path):
    # --scenarios N: the first N scenario ids x the FULL framing x pressure x subject grid
    # (every subject present) — unlike --limit, which caps raw cells (subject-outer, so a small
    # --limit would only ever reach the first subject). This was the live-run smoke selector.
    cfg = Config(
        subjects=(SubjectSpec("claude-opus-4-8"), SubjectSpec("claude-sonnet-4-6")),
        framings=("unstated", "stated"),
        pressures=("secularize", "insistence"),
    )
    collect(sunni, tmp_path, config=cfg, subject_fn=_fake(), scenarios=2)
    lines = [json.loads(l) for l in (tmp_path / "sittings.jsonl").read_text().splitlines()]

    first_two = list(load_tradition(sunni).scenario_ids[:2])
    assert {s["scenario_id"] for s in lines} == set(first_two)  # exactly the first 2 scenarios
    assert {s["subject"] for s in lines} == {"claude-opus-4-8", "claude-sonnet-4-6"}  # both subjects
    # 2 scenarios x 2 subjects x 2 framings x 2 pressures = the full grid over the first 2.
    assert len(lines) == 2 * 2 * 2 * 2
    assert summary_grid_full(lines)  # every (scenario, subject) has all 4 framing x pressure cells


def summary_grid_full(lines) -> bool:
    from collections import Counter

    per_pair = Counter((s["scenario_id"], s["subject"]) for s in lines)
    return all(n == 4 for n in per_pair.values()) and len(per_pair) == 4
