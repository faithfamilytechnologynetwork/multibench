"""Batch judging (spec §4.6 / M14): submit -> manifest, collect -> verdicts (batch-priced),
idempotency, and errored-cell -> live fallback. The Anthropic batch client is injected (no API).
Gemini is intentionally not batched (JaleesBench fidelity) — those cells go to the live judge.
"""

import json
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from judging.batching import batch_request, collect, submit
from judging.cli import app
from judging.config import Config, JudgeSpec, SubjectSpec
from judging.judge import judgment_key
from judging.loaders import load_scenario, load_tradition
from judging.rubric import verdict_schema

runner = CliRunner()

_VERDICT = '{"score": 1.0, "direction": "held", "rationale": "anchored", "techniques_used": []}'
_USAGE = SimpleNamespace(
    input_tokens=1000, output_tokens=500,
    cache_creation_input_tokens=200, cache_read_input_tokens=800,
)


class _FakeBatches:
    """Records created batches; replays canned results keyed by custom_id."""

    def __init__(self, outcomes=None, status="ended"):
        self.created = []
        self._outcomes = outcomes or {}  # custom_id -> ("succeeded", text) | ("errored", None)
        self._status = status

    def create(self, requests):
        bid = f"batch_{len(self.created)}"
        self.created.append({"id": bid, "requests": requests})
        return SimpleNamespace(id=bid)

    def retrieve(self, batch_id):
        return SimpleNamespace(processing_status=self._status)

    def results(self, batch_id):
        reqs = next(b["requests"] for b in self.created if b["id"] == batch_id)
        for r in reqs:
            cid = r["custom_id"]
            kind, text = self._outcomes.get(cid, ("succeeded", _VERDICT))
            if kind == "succeeded":
                msg = SimpleNamespace(content=[SimpleNamespace(type="text", text=text)], usage=_USAGE)
                yield SimpleNamespace(custom_id=cid, result=SimpleNamespace(type="succeeded", message=msg))
            else:
                yield SimpleNamespace(custom_id=cid, result=SimpleNamespace(type="errored", message=None))


def _client(batches):
    return SimpleNamespace(messages=SimpleNamespace(batches=batches))


def _sitting(subject="subjX", scenario_id="JLS-001", pressure="secularize", framing="unstated"):
    return {
        "subject": subject, "tradition": "sunni-islam", "scenario_id": scenario_id,
        "pressure": pressure, "framing": framing,
        "turns": [
            {"role": "user", "content": "u1"}, {"role": "assistant", "content": "a1"},
            {"role": "user", "content": "u2"}, {"role": "assistant", "content": "a2"},
        ],
    }


def _write_sittings(rd, *sittings):
    rd.mkdir(parents=True, exist_ok=True)
    p = rd / "sittings.jsonl"
    p.write_text("".join(json.dumps(s) + "\n" for s in sittings), encoding="utf-8")
    return p


def _cfg():
    # One Anthropic judge (!= the subject, so no self-skip) + no Gemini -> 1 sitting x 1 judge x 2
    # scopes = 2 batched cells.
    return Config(judges=(JudgeSpec("claude-opus-4-8", "anthropic"),), subjects=(SubjectSpec("subjX"),))


def test_submit_records_manifest_then_collect_writes_batch_priced_verdicts(sunni, tmp_path):
    sp = _write_sittings(tmp_path, _sitting())
    batches = _FakeBatches()
    s = submit(str(sp), sunni, tmp_path, config=_cfg(), client=_client(batches))
    assert s["submitted"] == 2 and s["batches"] == 1 and s["gemini_pending"] == 0
    state = json.loads((tmp_path / "batch_state.json").read_text())
    assert len(state["anthropic"][0]["manifest"]) == 2  # turn1 + full

    c = collect(sunni, tmp_path, config=_cfg(), client=_client(batches))
    assert c["written"] == 2 and c["errored"] == 0
    rows = [json.loads(l) for l in (tmp_path / "judgments.jsonl").read_text().splitlines()]
    assert len(rows) == 2
    assert all(r["usage"]["batch"] is True for r in rows)  # priced 0.5x by the report (M14)
    assert all(r["score"] == 1.0 and r["tradition"] == "sunni-islam" for r in rows)
    assert {r["scope"] for r in rows} == {"turn1", "full"}


def test_submit_is_idempotent_across_manifest(sunni, tmp_path):
    sp = _write_sittings(tmp_path, _sitting())
    batches = _FakeBatches()
    submit(str(sp), sunni, tmp_path, config=_cfg(), client=_client(batches))
    # Second submit: the in-flight manifest excludes those cells -> nothing new.
    again = submit(str(sp), sunni, tmp_path, config=_cfg(), client=_client(batches))
    assert again["submitted"] == 0


def test_collect_is_idempotent(sunni, tmp_path):
    sp = _write_sittings(tmp_path, _sitting())
    batches = _FakeBatches()
    submit(str(sp), sunni, tmp_path, config=_cfg(), client=_client(batches))
    collect(sunni, tmp_path, config=_cfg(), client=_client(batches))
    # Re-collect: batch already marked done -> no new rows.
    c2 = collect(sunni, tmp_path, config=_cfg(), client=_client(batches))
    assert c2["written"] == 0
    rows = (tmp_path / "judgments.jsonl").read_text().splitlines()
    assert len(rows) == 2  # not duplicated


def test_errored_cell_is_left_pending_for_live_fallback(sunni, tmp_path):
    sp = _write_sittings(tmp_path, _sitting())
    submit_batches = _FakeBatches()
    submit(str(sp), sunni, tmp_path, config=_cfg(), client=_client(submit_batches))
    manifest = json.loads((tmp_path / "batch_state.json").read_text())["anthropic"][0]["manifest"]
    a_cid = sorted(manifest)[0]  # error out the first cell
    batches = _FakeBatches(outcomes={a_cid: ("errored", None)})
    batches.created = submit_batches.created  # same submitted requests
    c = collect(sunni, tmp_path, config=_cfg(), client=_client(batches))
    assert c["written"] == 1 and c["errored"] == 1
    written_keys = {
        judgment_key(json.loads(l)) for l in (tmp_path / "judgments.jsonl").read_text().splitlines()
    }
    assert manifest[a_cid] not in written_keys  # left pending -> the live `judge` picks it up


def test_gemini_cells_are_not_batched(sunni, tmp_path):
    sp = _write_sittings(tmp_path, _sitting())
    cfg = Config(
        judges=(JudgeSpec("claude-opus-4-8", "anthropic"), JudgeSpec("gemini-3.5-flash", "gemini")),
        subjects=(SubjectSpec("subjX"),),
    )
    batches = _FakeBatches()
    s = submit(str(sp), sunni, tmp_path, config=cfg, client=_client(batches))
    assert s["submitted"] == 2  # only the Anthropic judge x 2 scopes
    assert s["gemini_pending"] == 2  # the Gemini cells go to the live judge, not the batch


def test_batch_request_constructs_via_real_anthropic_params(sunni):
    # Real-client construction (M21, anti-mock, batch path): the batch request's params validate
    # through the real anthropic SDK request model.
    import pydantic
    from anthropic import types as atypes

    trad = load_tradition(sunni)
    scen = load_scenario(sunni, "JLS-001")
    req = batch_request(
        trad, scen, _sitting(), JudgeSpec("claude-opus-4-8", "anthropic"), "full", "a000000",
        verdict_schema(),
    )
    assert req["custom_id"] == "a000000"
    params = {k: v for k, v in req["params"].items() if k != "output_config"}  # newer field, not in the TypedDict
    pydantic.TypeAdapter(atypes.MessageCreateParams).validate_python(params)


def test_batch_judge_cli_wiring(sunni, tmp_path):
    # CLI-level: the batch-judge sub-app + its subcommands are wired and load.
    assert runner.invoke(app, ["batch-judge", "--help"]).exit_code == 0
    for sub in ("submit", "collect"):
        r = runner.invoke(app, ["batch-judge", sub, "--help"])
        assert r.exit_code == 0, f"batch-judge {sub} --help failed"
        assert "results-dir" in r.output
