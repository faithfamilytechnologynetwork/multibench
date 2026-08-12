"""Experiment 76 — fading collector.

Variant of ``judging.collect`` for the prompt-fading design. The one structural departure from the
benchmark collector: the ``guided`` framing is delivered **once, early** (not re-prefixed onto every
user turn), with value-neutral fluff separating it from the dilemma at four ramp levels. Everything
else — the clean turn1/reply1/push/reply2 turns that get stored and judged, the −1…+1 judge seam —
is unchanged, so the stock ``judging judge`` scores these sittings as-is.

Arms (encoded in the sitting KEY so they survive into judgments.jsonl):
  subject = arm ∈ {A1 (guide as SYSTEM msg), A2 (guide as one FIRST-USER-TURN prefix), B (weights,
            no guide)};  framing = level ∈ {L0,L1,L2,L3}.
The judge keys on subject|scenario|pressure|framing, so (arm, level, scenario, pressure) is unique.

Model per arm is the SERVED name on the Modal endpoint: A1/A2 -> base google/gemma-4-31B-it,
B -> "dpo" (mb-sft-dpo). (Conditional arm C -> base, no guide — added later only if triggered.)

Run (endpoint from EVAL_BASE_URL or --base-url):
  uv --project workflows/judging run python experiments/76_prompt_fading/collect_fading.py \
      --base-url https://<modal-url>/v1
Smoke: add --scenarios-limit 2 --pressures secularize,insistence  (a cheap slice across all arms/levels).
"""

from __future__ import annotations

import json
import os
import re
import threading
import time
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import typer

from judging.core_imports import PRESSURES
from judging.loaders import Scenario, Tradition, load_scenario, load_tradition
from judging.providers import ctx_block

app = typer.Typer(add_completion=False)

REPO_ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent

# Arm -> (served model name, delivery channel, guide included?)
ARMS: dict[str, dict] = {
    "A1": {"model": "google/gemma-4-31B-it", "channel": "system", "framed": True},
    "A2": {"model": "google/gemma-4-31B-it", "channel": "prefix", "framed": True},
    "B": {"model": "dpo", "channel": None, "framed": False},
    # Conditional arm C (base, no guide) — enable via --arms C only if the pre-registered trigger fires.
    "C": {"model": "google/gemma-4-31B-it", "channel": None, "framed": False},
}

# Fluff-token targets per level (approx tokens = chars/4; the judge never sees fluff, so this only
# affects the subject's context distance — the pre-registered separation ramp).
LEVELS: dict[str, int] = {"L0": 0, "L1": 1000, "L2": 4000, "L3": 12000}


def approx_tokens(text: str) -> int:
    """Dependency-free token estimate (chars/4). Used only to size the separation ramp and as the
    log-token robustness x-axis; the pre-registered primary regressor is the ordinal level."""
    return (len(text) + 3) // 4


def parse_fluff_bank(path: Path) -> list[tuple[str, str]]:
    """Parse fluff_bank.md into ordered (user, assistant) pairs."""
    text = path.read_text()
    pairs: list[tuple[str, str]] = []
    for block in text.split("### exchange")[1:]:
        um = re.search(r"USER:\s*(.*?)\s*(?=\nASSISTANT:)", block, re.S)
        am = re.search(r"ASSISTANT:\s*(.*)", block, re.S)
        if not um or not am:
            continue
        pairs.append((um.group(1).strip(), am.group(1).strip()))
    if not pairs:
        raise ValueError(f"no exchanges parsed from {path}")
    return pairs


def build_fluff(pairs: list[tuple[str, str]], target_tokens: int) -> tuple[list[dict], int]:
    """Greedily append whole (user,assistant) exchanges in bank order, CYCLING the bank if needed,
    until cumulative approx tokens >= target. Deterministic. Returns (turns, actual_approx_tokens)."""
    if target_tokens <= 0:
        return [], 0
    turns: list[dict] = []
    total = 0
    i = 0
    while total < target_tokens:
        u, a = pairs[i % len(pairs)]
        turns.append({"role": "user", "content": u})
        turns.append({"role": "assistant", "content": a})
        total += approx_tokens(u) + approx_tokens(a)
        i += 1
    return turns, total


def _apply_prefix(messages: list[dict], guide: str) -> None:
    """A2 channel: prepend the guide as a context prefix onto the FIRST user turn only (in place)."""
    for m in messages:
        if m["role"] == "user":
            m["content"] = f"{ctx_block(guide)}\n\n{m['content']}"
            return
    raise ValueError("no user turn to attach the guide prefix to")


def build_messages(
    arm: str, guide: str, fluff: list[dict], tail: list[dict]
) -> list[dict]:
    """Assemble the full message list for one model call.
    tail = the clean dilemma turns so far ([user turn1] for reply1; [user turn1, assistant reply1,
    user push] for reply2)."""
    spec = ARMS[arm]
    msgs: list[dict] = []
    if spec["channel"] == "system":
        msgs.append({"role": "system", "content": guide})
    msgs += deepcopy(fluff)
    msgs += deepcopy(tail)
    if spec["channel"] == "prefix":
        _apply_prefix(msgs, guide)
    return msgs


def make_caller(base_url: str, max_tokens: int, temperature: float, retries: int):
    from openai import OpenAI

    client = OpenAI(api_key="EMPTY", base_url=base_url, timeout=600)

    def call(model: str, messages: list[dict]) -> tuple[str, dict]:
        last: Exception | None = None
        for attempt in range(retries + 1):
            try:
                r = client.chat.completions.create(
                    model=model, messages=messages, max_tokens=max_tokens, temperature=temperature
                )
                t = (r.choices[0].message.content or "").strip()
                if not t:
                    raise RuntimeError("empty subject response")
                u = r.usage
                usage = {
                    "input_tokens": getattr(u, "prompt_tokens", None),
                    "output_tokens": getattr(u, "completion_tokens", None),
                } if u else {}
                return t, usage
            except Exception as e:  # noqa: BLE001 — transient; retry then fail loud
                last = e
                if attempt < retries:
                    time.sleep(2 * (attempt + 1))
        raise RuntimeError(f"subject call failed after {retries + 1} attempts: {last}")

    return call


def cell_key(arm: str, scenario_id: str, pressure: str, level: str) -> str:
    return f"{arm}|{scenario_id}|{pressure}|{level}"


def run_cell(
    arm: str,
    level: str,
    tradition: Tradition,
    scenario: Scenario,
    pressure: str,
    fluff: list[dict],
    sep_tokens: int,
    caller,
) -> dict:
    spec = ARMS[arm]
    guide = tradition.guide if spec["framed"] else ""
    turn1 = scenario.turn1
    push = scenario.pressures[pressure]

    msgs1 = build_messages(arm, guide, fluff, [{"role": "user", "content": turn1}])
    reply1, usage1 = caller(spec["model"], msgs1)

    tail2 = [
        {"role": "user", "content": turn1},
        {"role": "assistant", "content": reply1},
        {"role": "user", "content": push},
    ]
    msgs2 = build_messages(arm, guide, fluff, tail2)
    reply2, usage2 = caller(spec["model"], msgs2)

    return {
        # --- fields the stock judge keys on / reads (subject=arm, framing=level) ---
        "subject": arm,
        "framing": level,
        "tradition": tradition.id,
        "scenario_id": scenario.id,
        "pressure": pressure,
        "turns": [
            {"role": "user", "content": turn1},
            {"role": "assistant", "content": reply1},
            {"role": "user", "content": push},
            {"role": "assistant", "content": reply2},
        ],
        # --- experiment audit (ignored by the judge) ---
        "arm": arm,
        "level": level,
        "channel": spec["channel"],
        "model": spec["model"],
        "guide_included": spec["framed"],
        "sep_approx_tokens": sep_tokens,
        "context_prefix": guide if spec["framed"] else None,
        "ts": datetime.now(timezone.utc).isoformat(),
        "usage": [usage1, usage2],
    }


@app.command()
def main(
    base_url: str = typer.Option(
        None, help="OpenAI-compatible endpoint (Modal serve). Falls back to $EVAL_BASE_URL."
    ),
    manifest: Path = typer.Option(HERE / "data" / "output" / "scenarios.json"),
    results_dir: Path = typer.Option(HERE / "data" / "output"),
    fluff_bank: Path = typer.Option(HERE / "fluff_bank.md"),
    traditions_dir: Path = typer.Option(REPO_ROOT / "traditions"),
    arms: str = typer.Option("A1,A2,B", help="comma list of arms to run"),
    levels: str = typer.Option("L0,L1,L2,L3", help="comma list of levels to run"),
    pressures: str = typer.Option("", help="comma list of pressures (default: all six core)"),
    traditions: str = typer.Option("", help="comma list of tradition ids (default: all in manifest)"),
    scenarios_limit: int = typer.Option(0, help="if >0, first N scenarios per tradition (smoke)"),
    concurrency: int = typer.Option(16),
    max_tokens: int = typer.Option(1024),
    temperature: float = typer.Option(0.0, help="0 = deterministic/reproducible counsel"),
    retries: int = typer.Option(3),
) -> None:
    url = base_url or os.environ.get("EVAL_BASE_URL")
    if not url:
        raise typer.Exit("no endpoint: pass --base-url or set EVAL_BASE_URL")

    arm_list = [a.strip() for a in arms.split(",") if a.strip()]
    level_list = [l.strip() for l in levels.split(",") if l.strip()]
    pressure_list = [p.strip() for p in pressures.split(",") if p.strip()] or list(PRESSURES)
    for a in arm_list:
        if a not in ARMS:
            raise typer.Exit(f"unknown arm {a!r} (known: {list(ARMS)})")
    for l in level_list:
        if l not in LEVELS:
            raise typer.Exit(f"unknown level {l!r} (known: {list(LEVELS)})")
    for p in pressure_list:
        if p not in PRESSURES:
            raise typer.Exit(f"unknown pressure {p!r} (core: {list(PRESSURES)})")

    sel = json.loads(manifest.read_text())["scenarios"]
    trad_ids = [t.strip() for t in traditions.split(",") if t.strip()] or sorted(sel)

    pairs = parse_fluff_bank(fluff_bank)
    fluff_by_level = {lv: build_fluff(pairs, LEVELS[lv]) for lv in level_list}
    for lv in level_list:
        _, tok = fluff_by_level[lv]
        print(f"  fluff {lv}: target {LEVELS[lv]} -> {tok} approx tokens ({len(fluff_by_level[lv][0])} turns)")

    caller = make_caller(url, max_tokens, temperature, retries)
    write_lock = threading.Lock()
    counters = {"written": 0, "failed": 0, "skipped": 0}

    for tid in trad_ids:
        tradition = load_tradition(traditions_dir / tid)
        scen_ids = list(sel[tid])
        if scenarios_limit > 0:
            scen_ids = scen_ids[:scenarios_limit]
        scen_cache = {sid: load_scenario(traditions_dir / tid, sid) for sid in scen_ids}

        out_dir = results_dir / tid
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / "sittings.jsonl"
        done: set[str] = set()
        if out.exists():
            for line in out.read_text().splitlines():
                if line.strip():
                    s = json.loads(line)
                    done.add(cell_key(s["subject"], s["scenario_id"], s["pressure"], s["framing"]))

        cells = [
            (arm, lv, sid, pr)
            for sid in scen_ids
            for pr in pressure_list
            for lv in level_list
            for arm in arm_list
            if cell_key(arm, sid, pr, lv) not in done
        ]
        print(f"[{tid}] {len(scen_ids)} scenarios, {len(cells)} cells to run (skipping {len(done)} done)")

        fh = out.open("a")

        def _run(cell: tuple) -> None:
            arm, lv, sid, pr = cell
            fluff, sep = fluff_by_level[lv]
            try:
                rec = run_cell(arm, lv, tradition, scen_cache[sid], pr, fluff, sep, caller)
            except Exception as e:  # noqa: BLE001 — leave pending (resumable), count -> nonzero exit
                with write_lock:
                    counters["failed"] += 1
                print(f"  FAILED {cell_key(arm, sid, pr, lv)}: {e}")
                return
            with write_lock:
                fh.write(json.dumps(rec) + "\n")
                fh.flush()
                counters["written"] += 1

        workers = max(1, concurrency)
        if workers == 1 or len(cells) <= 1:
            for c in cells:
                _run(c)
        else:
            with ThreadPoolExecutor(max_workers=workers) as ex:
                list(ex.map(_run, cells))
        fh.close()

    print(f"\nDONE — written {counters['written']}, failed {counters['failed']}")
    if counters["failed"]:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
