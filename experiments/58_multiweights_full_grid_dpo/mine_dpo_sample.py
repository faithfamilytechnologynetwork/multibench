"""Stage-2 DPO mining sampler (experiment 48): K=4 chains per cell from the SFT checkpoint, at a
temperature bump, to build within-cell preference pairs (own best vs own worst, band gap ≥ 2).

Samples the SFT LoRA served by serve_gemma_eval.py (model="sft") — NOT base — at temp 1.3, per
CELL (scenario × pressure), K=4 full 2-turn UNSTATED sittings. Distinct subject alias per k so the
judge keys don't collapse. Output = collect-schema sittings → banded full-scope (gemini) → the
pair-builder (build_dpo_pairs.py) counts max-gap pairs and reports the yield.

PILOT mode: MINE_SCENARIOS_PER_TRAD caps scenarios/tradition (default 10) for a cheap yield estimate
before committing to the full mining spend (architect gate). Set to 0 for the full run.

Env: EVAL_BASE_URL (endpoint + /v1). Run:
  MINE_SCENARIOS_PER_TRAD=10 EVAL_BASE_URL=<url> uv --project workflows/judging run \
    python experiments/48_multiweights_omissive_bias/mine_dpo_sample.py
"""

from __future__ import annotations

import json
import os
import random
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
TRADITIONS = [
    "buddhism", "eastern-christianity", "judaism", "roman-catholicism",
    "secular-sage", "sunni-islam", "taoism",
]
PRESSURES = ("secularize", "insistence", "false_authority", "good_cause", "flattery", "personal_appeal")
MODEL = "sft"  # the SFT LoRA served by serve_gemma_eval.py
K = 4
TEMPERATURE = 1.3
MAX_TOKENS = 2048
CONCURRENCY = 12
RETRIES = 4
TIMEOUT = 300
PER_TRAD = int(os.environ.get("MINE_SCENARIOS_PER_TRAD", "10"))  # target flat count/tradition
PILOT = 10   # the pilot's first-10 scenarios (already sampled+banded — reused via resume dedup)
SEED = 3446  # seeded-random selection of the extra scenarios (architect-locked)


import json as _json
# exp-58: when MINE_SCENARIO_MANIFEST is set, mine EXACTLY manifest["uncovered"][<tradition>] — the
# complement of #48's scoped set (recovered via the same seed logic). Overrides PER_TRAD selection;
# sampling itself is unchanged (K=4, temp 1.3, same subject aliases, same on-policy sft source).
MANIFEST_PATH = os.environ.get("MINE_SCENARIO_MANIFEST", "")
_MANIFEST = _json.loads(Path(MANIFEST_PATH).read_text())["uncovered"] if MANIFEST_PATH else None


def scoped_scenarios(all_ids, i, tradition=None):
    """Selection rule. If MINE_SCENARIO_MANIFEST is set (exp-58): return exactly the uncovered list
    for this tradition. Else (#48): flat PER_TRAD/tradition = pilot's first-10 REUSED + (PER_TRAD-10)
    seeded-random from the rest. Deterministic + per-tradition independent."""
    if _MANIFEST is not None:
        want = set(_MANIFEST[tradition])
        return [s for s in all_ids if s in want]  # preserve tradition order, restrict to uncovered
    if PER_TRAD == 0:
        return list(all_ids)
    pilot = list(all_ids[:PILOT])
    rest = list(all_ids[PILOT:])
    extra = random.Random(SEED + i).sample(rest, min(PER_TRAD - PILOT, len(rest)))
    return pilot + extra

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
    for i, t in enumerate(TRADITIONS):
        trad = load_tradition(str(ROOT / "traditions" / t))
        (OUT / t).mkdir(parents=True, exist_ok=True)
        done = _done_keys(OUT / t / "sittings.jsonl")
        sids = scoped_scenarios(trad.scenario_ids, i, tradition=t)
        for sid in sids:
            for pressure in PRESSURES:
                for k in range(K):
                    subject = f"sft-mine-s{k}"
                    if f"{subject}|{sid}|{pressure}" not in done:
                        tasks.append((t, sid, pressure, subject))
    print(f"mining tasks: {len(tasks)} (PER_TRAD={PER_TRAD or 'ALL'}, K={K}, temp={TEMPERATURE})")

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
            if (written + failed) % 100 == 0:
                print(f"progress: {written} written, {failed} failed")
    print(json.dumps({"written": written, "failed": failed, "total": len(tasks)}))


if __name__ == "__main__":
    main()
