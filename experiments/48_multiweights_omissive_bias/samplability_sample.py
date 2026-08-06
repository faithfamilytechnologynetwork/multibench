"""Samplability diagnostic sampler (experiment 48, §4.1 — the HARD GATE).

Question (taqwabench's $100-saving warning): does BASE gemma, sampled unstated at a temperature
bump, EVER produce tradition-faithful counsel? If the good band barely appears, DPO-on-base is
futile and stage-1 distillation is mandatory (we've already chosen stage-1-first + DPO-on-SFT, so
this is the confirmatory MECHANISM figure, and the per-tradition histogram is the formal gate).

Design (architect-approved, 2026-08-05): per SCENARIO (not per cell), ONE pressure assigned by
deterministic rotation over the 6 canonical pressures (covers all ~evenly), K=4 UNSTATED 2-turn
samples from base gemma at temp 1.3. Distinct subject alias per sample k (`gemma-4-31b-it-samp{k}`)
so the downstream judge's key (subject|scenario|pressure|framing|judge|scope) does not collapse the
4 samples. Output is collect-schema sittings → banded FULL-scope only by the judge pipeline.

Route: OpenRouter (funded key), slug google/gemma-4-31b-it (same base model we will tune). The
collection pipeline has no temperature/K knob, so this calls the OpenAI-compat endpoint directly,
reusing judging.loaders for scenario/pressure text and capturing the OpenRouter serving `provider`
per call (same provenance discipline as collection). Resumable: skips sittings already written.

Run (key sourced in the shell):
  uv --project workflows/judging run python experiments/48_multiweights_omissive_bias/samplability_sample.py
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
OUT = EXP / "data" / "output" / "samplability"
ROOT = EXP.parent.parent  # worktree root
TRADITIONS = [
    "buddhism", "eastern-christianity", "judaism", "roman-catholicism",
    "secular-sage", "sunni-islam", "taoism",
]
PRESSURES = ("secularize", "insistence", "false_authority", "good_cause", "flattery", "personal_appeal")
MODEL = "google/gemma-4-31b-it"
K = 4
TEMPERATURE = 1.3
MAX_TOKENS = 2048
BASE_URL = "https://openrouter.ai/api/v1"
CONCURRENCY = 16
RETRIES = 4
REQUEST_TIMEOUT = 90  # fail a hung connection fast (the all-night flap) so the retry can recover

_client = OpenAI(api_key=os.environ["OPENROUTER_API_KEY"], base_url=BASE_URL, timeout=REQUEST_TIMEOUT)
_locks: dict[str, threading.Lock] = {t: threading.Lock() for t in TRADITIONS}


def _call(messages: list[dict]) -> tuple[str, dict]:
    """One temp-1.3 completion. Returns (text, usage-with-provider). Retries transient errors."""
    last = None
    for attempt in range(RETRIES + 1):
        try:
            resp = _client.chat.completions.create(
                model=MODEL, messages=messages, temperature=TEMPERATURE, max_tokens=MAX_TOKENS,
            )
            text = (resp.choices[0].message.content or "").strip()
            if not text:
                raise RuntimeError("empty response")
            u = resp.usage
            usage = {"in": getattr(u, "prompt_tokens", 0) or 0, "out": getattr(u, "completion_tokens", 0) or 0}
            prov = getattr(resp, "provider", None)
            if prov:
                usage["provider"] = prov
            return text, usage
        except Exception as e:  # noqa: BLE001 — transient; retry then raise
            last = e
            if attempt < RETRIES:
                time.sleep(2 * (attempt + 1))  # backoff through a flap wave
    raise RuntimeError(f"call failed after {RETRIES + 1}: {last}")


def _sitting(subject: str, tradition: str, sid: str, pressure: str, turn1: str, push: str) -> dict:
    """One K-sample: 2-turn UNSTATED sitting (no context_prefix). Same schema as collect.py."""
    reply1, u1 = _call([{"role": "user", "content": turn1}])
    reply2, u2 = _call([
        {"role": "user", "content": turn1},
        {"role": "assistant", "content": reply1},
        {"role": "user", "content": push},
    ])
    return {
        "subject": subject, "tradition": tradition, "scenario_id": sid, "pressure": pressure,
        "framing": "unstated", "context_prefix": None, "model": MODEL,
        "ts": datetime.now(timezone.utc).isoformat(), "temperature": TEMPERATURE,
        "usage": [u1, u2],
        "turns": [
            {"role": "user", "content": turn1},
            {"role": "assistant", "content": reply1},
            {"role": "user", "content": push},
            {"role": "assistant", "content": reply2},
        ],
    }


def _done_keys(path: Path) -> set[str]:
    if not path.exists():
        return set()
    keys = set()
    for line in path.open():
        r = json.loads(line)
        keys.add(f"{r['subject']}|{r['scenario_id']}|{r['pressure']}|{r['framing']}")
    return keys


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tasks = []
    gidx = 0
    for t in TRADITIONS:
        trad = load_tradition(str(ROOT / "traditions" / t))
        (OUT / t).mkdir(parents=True, exist_ok=True)
        done = _done_keys(OUT / t / "sittings.jsonl")
        for sid in trad.scenario_ids:
            pressure = PRESSURES[gidx % len(PRESSURES)]  # deterministic rotation, one per scenario
            gidx += 1
            for k in range(K):
                subject = f"gemma-4-31b-it-samp{k}"
                if f"{subject}|{sid}|{pressure}|unstated" in done:
                    continue
                tasks.append((t, sid, pressure, subject))
    limit = os.environ.get("SAMP_LIMIT")
    if limit:
        tasks = tasks[: int(limit)]  # smoke
    print(f"tasks to run: {len(tasks)} (resumable; {sum(len(_done_keys(OUT/t/'sittings.jsonl')) for t in TRADITIONS)} already done)")

    def run_one(task):
        t, sid, pressure, subject = task
        scen = load_scenario(str(ROOT / "traditions" / t), sid)
        rec = _sitting(subject, t, sid, pressure, scen.turn1, scen.pressures[pressure])
        with _locks[t]:
            with (OUT / t / "sittings.jsonl").open("a") as f:
                f.write(json.dumps(rec) + "\n")
        return t

    written = 0
    failed = 0
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        futs = {ex.submit(run_one, task): task for task in tasks}
        for fut in as_completed(futs):
            try:
                fut.result()
                written += 1
            except Exception as e:  # noqa: BLE001
                failed += 1
                print(f"FAILED {futs[fut][:3]}: {e}")
            if (written + failed) % 200 == 0:
                print(f"progress: {written} written, {failed} failed")
    print(json.dumps({"written": written, "failed": failed, "total_tasks": len(tasks)}))


if __name__ == "__main__":
    main()
