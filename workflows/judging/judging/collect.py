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
from collections.abc import Callable
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
    grid = [
        (subject, sid, pressure, framing)
        for subject in config.subjects
        for sid in scenario_ids
        for pressure in config.pressures
        for framing in config.framings
    ]
    todo = [g for g in grid if sitting_key(g[0].model, g[1], g[2], g[3]) not in done]
    if limit is not None:
        todo = todo[:limit]

    scenarios: dict[str, Scenario] = {}
    written = failed = 0
    with out.open("a") as fh:
        for subject, sid, pressure, framing in todo:
            key = sitting_key(subject.model, sid, pressure, framing)
            try:
                scen = scenarios.get(sid)
                if scen is None:
                    scen = load_scenario(tradition_dir, sid)
                    scenarios[sid] = scen
                rec = run_sitting(subject, tradition, scen, pressure, framing, subject_fn)
            except Exception as e:  # noqa: BLE001 — report, leave pending (resumable)
                failed += 1
                print(f"  FAILED {key}: {e}")
                continue
            fh.write(json.dumps(rec) + "\n")
            fh.flush()
            done.add(key)
            written += 1

    return {"grid": len(grid), "todo": len(todo), "written": written, "failed": failed}
