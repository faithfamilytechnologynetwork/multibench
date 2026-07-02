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


def test_batch_request_constructs_via_real_anthropic_batch_request_type(sunni):
    # Real-client construction (M21, anti-mock, batch path): the FULL batch request (incl the
    # load-bearing output_config schema field + cache_control blocks) validates through the real
    # anthropic SDK batch-request model, and that validation bites (a bad request is rejected).
    import pydantic
    from anthropic.types.messages import batch_create_params as bcp

    trad = load_tradition(sunni)
    scen = load_scenario(sunni, "JLS-001")
    req = batch_request(
        trad, scen, _sitting(), JudgeSpec("claude-opus-4-8", "anthropic"), "full", "a000000",
        verdict_schema(),
    )
    assert req["custom_id"] == "a000000"
    assert "output_config" in req["params"]  # the load-bearing schema field IS validated below
    ta = pydantic.TypeAdapter(bcp.Request)
    ta.validate_python(req)  # constructs against the real SDK batch-request type (incl output_config)
    with pytest.raises(pydantic.ValidationError):  # and it bites
        ta.validate_python({"custom_id": "x", "params": {"model": "m"}})  # missing max_tokens/messages


def test_collect_live_fallback_judges_pending_cells(sunni, tmp_path):
    # M14/T20: a cell the batch errors on is picked up by the LIVE judge via collect(fallback=True).
    sp = _write_sittings(tmp_path, _sitting())
    submit_batches = _FakeBatches()
    submit(str(sp), sunni, tmp_path, config=_cfg(), client=_client(submit_batches))
    manifest = json.loads((tmp_path / "batch_state.json").read_text())["anthropic"][0]["manifest"]
    err_cid = sorted(manifest)[0]
    batches = _FakeBatches(outcomes={err_cid: ("errored", None)})
    batches.created = submit_batches.created

    def live_judge(judge, parts):  # the injected live judge fills what the batch left pending
        v = {"score": -0.5, "direction": "d", "rationale": "r", "techniques_used": []}
        return (v, json.dumps(v), {})  # (verdict, raw_text, usage)

    c = collect(
        sunni, tmp_path, config=_cfg(), client=_client(batches),
        sittings_path=str(sp), judge_fn=live_judge, fallback=True,
    )
    assert c["errored"] == 1 and c["live"]["written"] == 1  # the errored cell judged live
    rows = [json.loads(l) for l in (tmp_path / "judgments.jsonl").read_text().splitlines()]
    keys = {judgment_key(r) for r in rows}
    assert manifest[err_cid] in keys  # now resolved (by the live fallback)
    assert len(rows) == 2  # one batch-priced + one live


def test_batch_judge_cli_lifecycle(sunni, tmp_path, monkeypatch):
    # CLI-level (M14): submit + collect through the actual Typer commands drive batch_state.json's
    # lifecycle + idempotent re-collect. The Anthropic client is injected via the client factory;
    # --no-fallback avoids a live judge call in this offline test.
    import judging.batching as batching

    sp = _write_sittings(tmp_path, _sitting())
    batches = _FakeBatches()
    monkeypatch.setattr(batching, "_anthropic_client", lambda client: _client(batches))

    r = runner.invoke(app, ["batch-judge", "submit", str(sp), str(sunni), "--results-dir", str(tmp_path)])
    assert r.exit_code == 0, r.output
    assert (tmp_path / "batch_state.json").exists()
    assert json.loads(r.output)["submitted"] == 2

    r = runner.invoke(
        app, ["batch-judge", "collect", str(sp), str(sunni), "--results-dir", str(tmp_path), "--no-fallback"]
    )
    assert r.exit_code == 0, r.output
    assert json.loads(r.output)["written"] == 2
    state = json.loads((tmp_path / "batch_state.json").read_text())
    assert state["anthropic"][0]["done"] is True  # manifest lifecycle: batch marked done
    # Idempotent re-collect: nothing new written.
    r2 = runner.invoke(
        app, ["batch-judge", "collect", str(sp), str(sunni), "--results-dir", str(tmp_path), "--no-fallback"]
    )
    assert json.loads(r2.output)["written"] == 0
    assert len((tmp_path / "judgments.jsonl").read_text().splitlines()) == 2
