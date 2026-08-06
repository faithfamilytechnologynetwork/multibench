"""Experiment 57 — DPO mining sampler: K=4 chains per TRAIN-HALF cell from the split-SFT policy.

Adapted from #48's mine_dpo_sample.py (kept untouched). Two changes for the split experiment:
  1. Scenario set = the committed TRAIN HALF only (259 scen), FULL grid — every train-half cell,
     NO subsetting (Waleed directive 2026-08-06). Held-out scenarios are NEVER sampled/trained.
  2. Output + model wired to the split endpoint (serve_split_eval.py serves mb-sft-split50 as "sft").

Samples model="sft" (= mb-sft-split50 via the split endpoint) at temp 1.3, K=4 full 2-turn UNSTATED
sittings/cell, distinct subject alias per k. Resumable (keyed subject|scenario|pressure). Output =
collect-schema sittings → banded full-scope (gemini) → build_dpo_pairs_split.py.

Expected: 259 train scen × 6 pressures × K4 = 6,216 sittings (12,432 endpoint generations).

Env: EVAL_BASE_URL (split endpoint + /v1). Run from repo root:
  EVAL_BASE_URL=<url> uv --project workflows/judging run \
    python experiments/57_multiweights_split/mine_dpo_split.py
"""

from __future__ import annotations

import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from openai import OpenAI

from judging.loaders import load_scenario, load_tradition

EXP = Path(__file__).resolve().parent
OUT = EXP / "data" / "output" / "mining"
ROOT = EXP.parent.parent
SPLIT = EXP / "split" / "train_scenarios.json"
TRADITIONS = [
    "buddhism", "eastern-christianity", "judaism", "roman-catholicism",
    "secular-sage", "sunni-islam", "taoism",
]
PRESSURES = ("secularize", "insistence", "false_authority", "good_cause", "flattery", "personal_appeal")
MODEL = "sft"  # = mb-sft-split50, served by serve_split_eval.py
K = 4
TEMPERATURE = 1.3
MAX_TOKENS = 2048
CONCURRENCY = 12
RETRIES = 4
TIMEOUT = 300

TRAIN_IDS = set(json.loads(SPLIT.read_text())["scenario_ids"])

_client = OpenAI(api_key="EMPTY", base_url=os.environ["EVAL_BASE_URL"], timeout=TIMEOUT)
_locks: dict[str, threading.Lock] = {t: threading.Lock() for t in TRADITIONS}


def _call(messages):
    last = None
    for a in range(RETRIES + 1):
        try:
            r = _client.chat.completions.create(model=MODEL, messages=messages,
                                                temperature=TEMPERATURE, max_tokens=MAX_TOKENS)
            t = (r.choices[0].message.content or "").strip()
            if not t:
                raise RuntimeError("empty response")
            u = r.usage
            return t, {"in": getattr(u, "prompt_tokens", 0) or 0, "out": getattr(u, "completion_tokens", 0) or 0}
        except Exception as e:  # noqa: BLE001
            last = e
            if a < RETRIES:
                time.sleep(2 * (a + 1))
    raise RuntimeError(f"call failed after {RETRIES+1}: {last}")


def _sitting(subject, tradition, sid, pressure, turn1, push):
    reply1, u1 = _call([{"role": "user", "content": turn1}])
    reply2, u2 = _call([
        {"role": "user", "content": turn1},
        {"role": "assistant", "content": reply1},
        {"role": "user", "content": push},
    ])
    return {
        "subject": subject, "tradition": tradition, "scenario_id": sid, "pressure": pressure,
        "framing": "unstated", "context_prefix": None, "model": MODEL,
        "ts": datetime.now(timezone.utc).isoformat(), "temperature": TEMPERATURE, "usage": [u1, u2],
        "turns": [
            {"role": "user", "content": turn1},
            {"role": "assistant", "content": reply1},
            {"role": "user", "content": push},
            {"role": "assistant", "content": reply2},
        ],
    }


def _done_keys(path: Path):
    if not path.exists():
        return set()
    return {f"{json.loads(l)['subject']}|{json.loads(l)['scenario_id']}|{json.loads(l)['pressure']}"
            for l in path.open()}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tasks = []
    for t in TRADITIONS:
        trad = load_tradition(str(ROOT / "traditions" / t))
        (OUT / t).mkdir(parents=True, exist_ok=True)
        done = _done_keys(OUT / t / "sittings.jsonl")
        sids = [sid for sid in trad.scenario_ids if sid in TRAIN_IDS]  # TRAIN-HALF full grid
        for sid in sids:
            for pressure in PRESSURES:
                for k in range(K):
                    subject = f"sft-mine-s{k}"
                    if f"{subject}|{sid}|{pressure}" not in done:
                        tasks.append((t, sid, pressure, subject))
    print(f"mining tasks: {len(tasks)} (TRAIN-HALF full grid, K={K}, temp={TEMPERATURE})")

    def run_one(task):
        t, sid, pressure, subject = task
        scen = load_scenario(str(ROOT / "traditions" / t), sid)
        rec = _sitting(subject, t, sid, pressure, scen.turn1, scen.pressures[pressure])
        with _locks[t]:
            with (OUT / t / "sittings.jsonl").open("a") as f:
                f.write(json.dumps(rec) + "\n")

    written = failed = 0
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        futs = {ex.submit(run_one, task): task for task in tasks}
        for fut in as_completed(futs):
            try:
                fut.result(); written += 1
            except Exception as e:  # noqa: BLE001
                failed += 1
                print(f"FAILED {futs[fut][:3]}: {e}")
            if (written + failed) % 200 == 0:
                print(f"progress: {written} written, {failed} failed")
    print(json.dumps({"written": written, "failed": failed, "total": len(tasks)}))


if __name__ == "__main__":
    main()
