"""Batch judging at ~50% batch pricing (spec §4.6 / M14) — ports JaleesBench ``batching.py``.

- ``submit``: enumerate pending judgments (the SAME identity keys as the live judge, excluding
  ones already recorded and ones in an in-flight batch manifest), submit **Anthropic Message
  Batches** whose per-request params mirror the live judge exactly (the two cached prompt blocks
  + the schema-constrained ``output_config`` + thinking), and record a ``batch_state.json``
  manifest for idempotency.
- ``collect``: poll each open batch; parse **succeeded** results into ``judgments.jsonl`` with the
  same record shape as the live judge, marking ``usage["batch"] = True`` so the report prices them
  at 0.5x. Anything a batch **errors** on (or that fails to parse) is left **pending** — the live
  ``judge`` command is the fallback, and the identity keys make the two paths idempotent.

**Fidelity note (matches JaleesBench):** Gemini is **not** batched — Google's batch API is Vertex
GCS/BigQuery-based (there is no developer file-batch), so Gemini judge cells are left pending for
the live ``judge`` fallback. Anthropic (the Opus judge) batches at 50%.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from judging import providers
from judging.config import Config, JudgeSpec, default_config
from judging.judge import _read_jsonl, _read_sittings, judgment_key, parse_verdict, should_skip
from judging.loaders import load_scenario, load_tradition
from judging.prompts import judge_prompt_parts
from judging.rubric import verdict_schema

STATE_FILE = "batch_state.json"
ANTHROPIC_CHUNK = 10_000  # stay well under the batch size cap


def _state_path(rd: Path) -> Path:
    return rd / STATE_FILE


def _load_state(rd: Path) -> dict:
    p = _state_path(rd)
    return json.loads(p.read_text()) if p.exists() else {"anthropic": []}


def _save_state(rd: Path, state: dict) -> None:
    _state_path(rd).write_text(json.dumps(state, indent=1))


def _cell_key(s: dict, judge_model: str, scope: str) -> str:
    return "|".join(
        [s["subject"], s["scenario_id"], s["pressure"], s["framing"], judge_model, scope]
    )


def _anthropic_pending(sittings: list[dict], rd: Path, config: Config) -> list[tuple]:
    """(sitting, judge, scope, key) for anthropic-judge cells not recorded and not in an in-flight
    manifest. Self-judgments are skipped (the live path records those)."""
    done = {judgment_key(j) for j in _read_jsonl(rd / "judgments.jsonl")}
    for b in _load_state(rd)["anthropic"]:
        if not b["done"]:
            done.update(b["manifest"].values())  # in-flight cells are not re-eligible
    jobs: list[tuple] = []
    for s in sittings:
        for judge in config.judges:
            if judge.provider != "anthropic":  # Gemini -> live fallback (not batched)
                continue
            for scope in config.scopes:
                if should_skip(judge.model, s["subject"]):
                    continue
                key = _cell_key(s, judge.model, scope)
                if key not in done:
                    jobs.append((s, judge, scope, key))
    return jobs


def _gemini_pending(sittings: list[dict], config: Config) -> int:
    """Count of Gemini judge cells (they are judged live, not batched) — an operator hint."""
    return sum(
        1
        for s in sittings
        for judge in config.judges
        if judge.provider == "gemini"
        for scope in config.scopes
        if not should_skip(judge.model, s["subject"])
    )


def batch_request(tradition: Any, scenario: Any, s: dict, judge: JudgeSpec, scope: str,
                  custom_id: str, schema: dict) -> dict:
    """One Anthropic batch request that mirrors the live judge request exactly (the two cached
    prompt blocks + the schema-constrained ``output_config`` + thinking)."""
    rubric, anchor, tail = judge_prompt_parts(tradition, scenario, s["turns"], scope)
    params: dict[str, Any] = {
        "model": judge.model,
        "max_tokens": judge.max_tokens,
        "output_config": {"format": {"type": "json_schema", "schema": schema}},
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": rubric, "cache_control": {"type": "ephemeral", "ttl": "1h"}},
                    {"type": "text", "text": anchor, "cache_control": {"type": "ephemeral", "ttl": "1h"}},
                    {"type": "text", "text": tail},
                ],
            }
        ],
    }
    if judge.thinking:
        params["thinking"] = {"type": "adaptive"}
    return {"custom_id": custom_id, "params": params}


def _anthropic_client(client: Any) -> Any:
    if client is not None:
        return client
    providers._require_env("ANTHROPIC_API_KEY")
    import anthropic

    return anthropic.Anthropic()


def submit(
    sittings_path: str | Path,
    tradition_dir: str | Path,
    results_dir: str | Path,
    config: Config | None = None,
    client: Any = None,
    limit: int | None = None,
) -> dict:
    """Submit pending anthropic-judge cells as Anthropic Message Batches; record the manifest."""
    config = config or default_config()
    rd = Path(results_dir)
    rd.mkdir(parents=True, exist_ok=True)
    sittings = _read_sittings(Path(sittings_path))
    jobs = _anthropic_pending(sittings, rd, config)
    if limit is not None:
        jobs = jobs[:limit]

    summary = {"submitted": 0, "batches": 0, "gemini_pending": _gemini_pending(sittings, config)}
    if not jobs:
        return summary

    client = _anthropic_client(client)
    tradition = load_tradition(tradition_dir)
    schema = verdict_schema()
    scen_cache: dict[str, Any] = {}
    state = _load_state(rd)
    for c0 in range(0, len(jobs), ANTHROPIC_CHUNK):
        chunk = jobs[c0 : c0 + ANTHROPIC_CHUNK]
        manifest: dict[str, str] = {}
        requests: list[dict] = []
        for i, (s, judge, scope, key) in enumerate(chunk):
            sid = s["scenario_id"]
            scen = scen_cache.get(sid)
            if scen is None:
                scen = load_scenario(tradition_dir, sid)
                scen_cache[sid] = scen
            cid = f"a{c0 + i:06d}"
            manifest[cid] = key
            requests.append(batch_request(tradition, scen, s, judge, scope, cid, schema))
        batch = client.messages.batches.create(requests=requests)
        state["anthropic"].append({"batch_id": batch.id, "manifest": manifest, "done": False})
        summary["submitted"] += len(requests)
        summary["batches"] += 1
    _save_state(rd, state)
    return summary


def _rec_from_key(key: str, verdict: dict, usage: dict, tradition_id: str) -> dict:
    subject, scenario_id, pressure, framing, judge, scope = key.split("|")
    return {
        "sitting_key": f"{subject}|{scenario_id}|{pressure}|{framing}",
        "subject": subject,
        "tradition": tradition_id,
        "scenario_id": scenario_id,
        "pressure": pressure,
        "framing": framing,
        "judge": judge,
        "scope": scope,
        **verdict,
        "usage": usage,
        "ts": datetime.now(timezone.utc).isoformat(),
    }


def _append_new(jpath: Path, recs: list[dict]) -> int:
    done = {judgment_key(j) for j in _read_jsonl(jpath)}
    written = 0
    with jpath.open("a") as fh:
        for r in recs:
            if judgment_key(r) not in done:
                fh.write(json.dumps(r) + "\n")
                done.add(judgment_key(r))
                written += 1
    return written


def _batch_usage(u: Any) -> dict:
    return {
        "in": getattr(u, "input_tokens", 0) or 0,
        "out": getattr(u, "output_tokens", 0) or 0,
        "cache_write": getattr(u, "cache_creation_input_tokens", 0) or 0,
        "cache_read": getattr(u, "cache_read_input_tokens", 0) or 0,
        "batch": True,  # priced at 0.5x by the report (M14)
    }


def collect(
    tradition_dir: str | Path,
    results_dir: str | Path,
    config: Config | None = None,
    client: Any = None,
) -> dict:
    """Poll open batches; write succeeded verdicts (batch-priced); leave errors to live fallback."""
    config = config or default_config()
    rd = Path(results_dir)
    state = _load_state(rd)
    tradition = load_tradition(tradition_dir)
    jpath = rd / "judgments.jsonl"
    written = errored = open_batches = 0

    if any(not b["done"] for b in state["anthropic"]):
        client = _anthropic_client(client)

    for b in state["anthropic"]:
        if b["done"]:
            continue
        batch = client.messages.batches.retrieve(b["batch_id"])
        if getattr(batch, "processing_status", None) != "ended":
            open_batches += 1
            continue
        recs: list[dict] = []
        for result in client.messages.batches.results(b["batch_id"]):
            key = b["manifest"].get(result.custom_id)
            if key is None:
                continue
            if result.result.type != "succeeded":
                errored += 1  # left pending -> live `judge` fallback
                continue
            msg = result.result.message
            text = "".join(x.text for x in msg.content if getattr(x, "type", None) == "text")
            try:
                verdict = parse_verdict(json.loads(text))
            except (ValueError, json.JSONDecodeError):
                errored += 1  # unparseable -> left pending for the live fallback
                continue
            recs.append(_rec_from_key(key, verdict, _batch_usage(msg.usage), tradition.id))
        written += _append_new(jpath, recs)
        b["done"] = True
    _save_state(rd, state)
    return {"written": written, "errored": errored, "open_batches": open_batches}
