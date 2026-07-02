"""Minimal Claude-only subject collector (spec §4.5 / §5.6).

Run each subject over the grid ``subjects × scenarios × pressures × framings``, producing
4-turn sittings (turn1 -> reply1 -> pressure-turn-2 -> reply2). Framing is delivered as a
**context prefix on every user turn** (never a system prompt; §4.5) — the stored turns are
CLEAN scenario text only, so judges stay framing-blinded. Idempotent/resumable (keyed
``subject|scenario|pressure|framing``); ``--limit`` for cheap smoke runs. Failures are left
pending (resumable) and counted -> non-zero exit (M12).
"""

from __future__ import annotations

import json
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from judging import providers
from judging.config import Config, SubjectSpec, default_config
from judging.loaders import Scenario, Tradition, load_scenario, load_tradition
from judging.prompts import framing_context

# A subject_fn returns (text, usage, attempts) for (subject, context_prefix, clean messages).
SubjectFn = Callable[[SubjectSpec, str | None, list[dict]], tuple[str, dict, int]]


def sitting_key(subject: str, scenario_id: str, pressure: str, framing: str) -> str:
    return f"{subject}|{scenario_id}|{pressure}|{framing}"


def run_sitting(
    subject: SubjectSpec,
    tradition: Tradition,
    scenario: Scenario,
    pressure: str,
    framing: str,
    subject_fn: SubjectFn,
) -> dict:
    """Produce one 4-turn sitting. Turns store clean scenario text (no framing leaked)."""
    ctx = framing_context(framing, tradition)  # None | stated sentence | guide
    turn1 = scenario.turn1
    push = scenario.pressures[pressure]

    reply1, usage1, att1 = subject_fn(subject, ctx, [{"role": "user", "content": turn1}])
    second = [
        {"role": "user", "content": turn1},
        {"role": "assistant", "content": reply1},
        {"role": "user", "content": push},
    ]
    reply2, usage2, att2 = subject_fn(subject, ctx, second)

    return {
        "subject": subject.model,
        "tradition": tradition.id,
        "scenario_id": scenario.id,
        "pressure": pressure,
        "framing": framing,
        # Audit only — the framing the subject saw as a prefix; NOT part of the judged turns.
        "context_prefix": providers.ctx_block(ctx) if ctx else None,
        "model": subject.model,
        "ts": datetime.now(timezone.utc).isoformat(),
        "attempts": [att1, att2],
        "usage": [usage1, usage2],
        "turns": [
            {"role": "user", "content": turn1},
            {"role": "assistant", "content": reply1},
            {"role": "user", "content": push},
            {"role": "assistant", "content": reply2},
        ],
    }


def collect(
    tradition_dir: str | Path,
    results_dir: str | Path,
    config: Config | None = None,
    subject_fn: SubjectFn | None = None,
    limit: int | None = None,
    scenarios: int | None = None,
) -> dict:
    """Collect sittings over the grid into ``sittings.jsonl``. Returns a summary;
    ``failed > 0`` means the caller should exit non-zero (M12).

    ``scenarios`` caps the grid to the first N scenario ids (the full framing x pressure x
    subject grid for each) — for cheap-but-representative smoke runs across every subject,
    unlike ``limit`` which caps raw cells (subject-outer, so it would only reach one subject)."""
    config = config or default_config()
    if subject_fn is None:
        def subject_fn(subject, ctx, msgs):  # noqa: ANN001 — default provider seam
            return providers.subject_complete(subject, ctx, msgs, config.retries)

    rd = Path(results_dir)
    rd.mkdir(parents=True, exist_ok=True)
    out = rd / "sittings.jsonl"

    done: set[str] = set()
    if out.exists():
        for line in out.read_text().splitlines():
            if line.strip():
                s = json.loads(line)
                done.add(sitting_key(s["subject"], s["scenario_id"], s["pressure"], s["framing"]))

    tradition = load_tradition(tradition_dir)
    scenario_ids = tradition.scenario_ids
    if scenarios is not None:
        scenario_ids = scenario_ids[:scenarios]
    # Cell-major interleave (JaleesBench collect.py:269): (scenario, pressure, framing) OUTER,
    # subject INNER, so consecutive cells hit different subjects — concurrency spreads across
    # providers rather than hammering one, and a small --limit reaches every subject.
    grid = [
        (subject, sid, pressure, framing)
        for sid in scenario_ids
        for pressure in config.pressures
        for framing in config.framings
        for subject in config.subjects
    ]
    todo = [g for g in grid if sitting_key(g[0].model, g[1], g[2], g[3]) not in done]
    if limit is not None:
        todo = todo[:limit]

    # Concurrency-bounded fan-out (M13): a bounded ThreadPoolExecutor over the per-cell provider
    # calls, bounded by config.concurrency, with one lock around the JSONL append (thread-safe)
    # and one around the scenario cache. Output is set-equivalent to serial — line ORDER is
    # non-deterministic under concurrency; the SET of records is identical.
    scen_cache: dict[str, Scenario] = {}
    scen_lock = threading.Lock()
    write_lock = threading.Lock()
    counters = {"written": 0, "failed": 0}

    def _scenario(sid: str) -> Scenario:
        with scen_lock:
            scen = scen_cache.get(sid)
            if scen is None:
                scen = load_scenario(tradition_dir, sid)
                scen_cache[sid] = scen
            return scen

    with out.open("a") as fh:

        def _run_one(cell: tuple) -> None:
            subject, sid, pressure, framing = cell
            key = sitting_key(subject.model, sid, pressure, framing)
            try:
                rec = run_sitting(subject, tradition, _scenario(sid), pressure, framing, subject_fn)
            except Exception as e:  # noqa: BLE001 — report, leave pending (resumable), count -> exit≠0
                with write_lock:
                    counters["failed"] += 1
                print(f"  FAILED {key}: {e}")
                return
            with write_lock:
                fh.write(json.dumps(rec) + "\n")
                fh.flush()
                counters["written"] += 1

        workers = max(1, config.concurrency)
        if workers == 1 or len(todo) <= 1:
            for cell in todo:
                _run_one(cell)
        else:
            with ThreadPoolExecutor(max_workers=workers) as ex:
                list(ex.map(_run_one, todo))  # consume so all cells finish before fh closes

    return {
        "grid": len(grid),
        "todo": len(todo),
        "written": counters["written"],
        "failed": counters["failed"],
    }
