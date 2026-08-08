"""AFB before/after collection RUNNER (#54 Phase 2 wiring; the actual run is Phase 5).

Thin adapter: builds the real OpenAI-SDK clients (the Modal subject endpoint + the OpenRouter Terra
judge), wires them into the SDK-free, resumable core ``analysis.afb_collect.collect``, and records a
committed intermediate at ``experiments/54_afb_before_after/data/collection.json``.

Run (needs the endpoint + funded keys — Phase 5 only), from the repo root:

    EVAL_BASE_URL="https://<modal-url>/v1" \
    uv --project workflows/judging run python experiments/54_afb_before_after/collect_afb.py

Config is via env / module constants (no arg-parsing — this is a fixed one-shot):
  EVAL_BASE_URL       the Modal vLLM endpoint + /v1 (from `modal deploy .../serve_gemma_eval.py`)
  OPENROUTER_API_KEY  funded key for the Terra judge — sourced from taqwabench/.env if unset
  AFB_RUN_ID          catalog run-id (default: afb-cold-<the operator sets it>); required at run time

Keys are read at runtime and NEVER echoed or committed. Usage/cost is appended to a gitignored
run.log for the Phase-5 spend reconciliation — never into the shipped intermediate.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

from openai import OpenAI

# The core lives in workflows/analysis (SDK-free, dispatcher-tested); import it directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "workflows" / "analysis"))
from analysis.afb_collect import collect, load_afb_items  # noqa: E402

EXP = Path(__file__).resolve().parent
AFB = EXP.parents[1] / "experiments" / "48_multiweights_omissive_bias" / "data" / "input" / "afb"
DATA = EXP / "data"
OUT = DATA / "collection.json"
RUN_LOG = DATA / "run.log"                       # gitignored; usage/cost for reconciliation
TAQWA_ENV = Path("/Users/mwk/Development/fftn/taqwabench/.env")

JUDGE_MODEL = "openai/gpt-5.6-terra"              # AFB judge-of-record (via OpenRouter)
# Catalog subject id -> served vLLM model name (the serve script exposes base + dpo=mb-sft-dpo).
SERVED = {"gemma-4-31b-it": "google/gemma-4-31B-it", "mb-sft-dpo": "dpo"}
SUBJECTS = ["gemma-4-31b-it", "mb-sft-dpo"]
# Pinned decoding — IDENTICAL for both subjects (greedy → reproducible companion artifact).
DECODING = {"temperature": 0.0, "seed": 0, "max_tokens": 1024}
CONCURRENCY = 16
RETRIES = 4
TIMEOUT = 120


def _env_key(name: str) -> str:
    """Return an API key from the environment, falling back to taqwabench/.env — never echoed."""
    if os.environ.get(name):
        return os.environ[name]
    if TAQWA_ENV.is_file():
        for line in TAQWA_ENV.read_text().splitlines():
            line = line.strip()
            if line.startswith(f"{name}=") and not line.startswith("#"):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit(f"{name} not set and not found in {TAQWA_ENV} — cannot run (no personal keys).")


def _log(msg: str) -> None:
    RUN_LOG.parent.mkdir(parents=True, exist_ok=True)
    with RUN_LOG.open("a", encoding="utf-8") as fh:
        fh.write(msg + "\n")


def _retry(fn):
    last = None
    for attempt in range(RETRIES + 1):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001 — bounded retry, then fail fast (no fallback)
            last = e
            if attempt < RETRIES:
                time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"failed after {RETRIES + 1} attempts: {last}")


def main() -> None:
    run_id = os.environ.get("AFB_RUN_ID")
    if not run_id:
        raise SystemExit("AFB_RUN_ID is required (e.g. afb-cold-20260808).")
    base_url = os.environ.get("EVAL_BASE_URL")
    if not base_url:
        raise SystemExit("EVAL_BASE_URL is required (the Modal endpoint + /v1).")

    subject = OpenAI(api_key="EMPTY", base_url=base_url, timeout=TIMEOUT)  # keyless Modal endpoint
    judge_client = OpenAI(api_key=_env_key("OPENROUTER_API_KEY"),
                          base_url="https://openrouter.ai/api/v1", timeout=TIMEOUT)
    scorer = json.loads((AFB / "scoring_prompt.json").read_text())["template"]
    usage = {"subject_tokens": 0, "judge_tokens": 0}

    def generate(subject_id: str, prompt: str) -> str:
        def call():
            r = subject.chat.completions.create(
                model=SERVED[subject_id], messages=[{"role": "user", "content": prompt}], **DECODING)
            usage["subject_tokens"] += getattr(r.usage, "total_tokens", 0) or 0
            text = (r.choices[0].message.content or "").strip()
            if not text:
                raise RuntimeError("empty subject response")
            return text
        return _retry(call)

    def judge(question: str, response: str) -> dict:
        filled = scorer.replace("{question}", question).replace("{response}", response)
        def call():
            r = judge_client.chat.completions.create(
                model=JUDGE_MODEL, messages=[{"role": "user", "content": filled}], max_tokens=512)
            usage["judge_tokens"] += getattr(r.usage, "total_tokens", 0) or 0
            txt = (r.choices[0].message.content or "").strip()
            obj = json.loads(txt[txt.find("{"): txt.rfind("}") + 1])  # fail fast on non-JSON
            score = int(obj["score"])
            if score not in (0, 1, 2, 3, 4):
                raise RuntimeError(f"judge score out of range: {score}")
            return {"score": score, "rationale": obj.get("rationale", "")}
        return _retry(call)

    items = load_afb_items(AFB / "questions.jsonl")
    _log(f"[{run_id}] start: {len(items)} items x {len(SUBJECTS)} subjects, decoding={DECODING}")

    # Serving smoke — one base + one dpo call — BEFORE the full loop (fail before spending broadly).
    for su in SUBJECTS:
        _ = generate(su, items[0]["question"])
    _log(f"[{run_id}] serving smoke ok for {SUBJECTS}")

    doc = collect(items, SUBJECTS, generate, judge, decoding=DECODING, run_id=run_id,
                  out_path=OUT, judge_model=JUDGE_MODEL, concurrency=CONCURRENCY)
    _log(f"[{run_id}] complete: {len(doc['cells'])} cells; usage={usage}")
    print(f"wrote {OUT} ({len(doc['cells'])} cells). usage={usage}")


if __name__ == "__main__":
    main()
