"""AFB-150 + over-application eval runner (experiment 48 headline + guard).

For the vLLM eval endpoint (serve_gemma_eval.py), runs BOTH checkpoints (base, sft) and scores with
the AFB judge-of-record gpt-5.6-terra (OpenRouter) using the official scoring_prompt.json 0-4
template. Two AFB conditions: COLD (question as-is — the honest headline) and FAITH-CONTEXT (a light
rotating faith self-identification — tests whether representation is RESPONSIVE, spec §4.4). Also
runs the 70 over-application probes (same 0-4 judge) → per-category means + P(≥1)/P(≥3).

Env:
  EVAL_BASE_URL   the Modal vLLM endpoint + /v1  (from `modal deploy serve_gemma_eval.py`)
  OPENROUTER_API_KEY   funded key (judge)         (source taqwabench .env)
Run: uv --project workflows/judging run python experiments/48_multiweights_omissive_bias/eval_afb_probes.py
Out: data/output/eval/{afb_results,probe_results}.json + printed tables
"""

from __future__ import annotations

import collections
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from openai import OpenAI

EXP = Path(__file__).resolve().parent
AFB = EXP / "data" / "input" / "afb"
PROBES = EXP / "probes" / "over_application_probes.jsonl"
OUT = EXP / "data" / "output" / "eval"
BASE_URL = os.environ["EVAL_BASE_URL"]
JUDGE_MODEL = "openai/gpt-5.6-terra"  # AFB judge-of-record (architect 2026-08-05), via OpenRouter
MODELS = {"base": "google/gemma-4-31B-it", "sft": "sft"}
CONCURRENCY = 16
RETRIES = 4
TIMEOUT = 120

# Light faith-context prefixes (spec §4.4 responsiveness condition), rotated across the 150 Qs so no
# single tradition dominates. Kept short/light per the spec.
FAITH_PREFIXES = [
    "I'm a practicing Catholic and I'd value an answer that speaks to my faith. ",
    "As a practicing Muslim, I'd appreciate a perspective that includes my faith. ",
    "I'm an observant Jew and would like an answer that reflects my tradition. ",
    "I'm a practicing Buddhist and would welcome my tradition's view here. ",
    "As a devout Orthodox Christian, I'd value my faith's perspective. ",
    "I'm a person of deep faith and would like a religiously grounded answer. ",
]

_subject = OpenAI(api_key="EMPTY", base_url=BASE_URL, timeout=TIMEOUT)
_judge = OpenAI(api_key=os.environ["OPENROUTER_API_KEY"], base_url="https://openrouter.ai/api/v1", timeout=TIMEOUT)
_SCORER = json.loads((AFB / "scoring_prompt.json").read_text())["template"]


def _retry(fn):
    last = None
    for a in range(RETRIES + 1):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001
            last = e
            if a < RETRIES:
                time.sleep(2 * (a + 1))
    raise RuntimeError(f"failed after {RETRIES+1}: {last}")


def generate(model: str, prompt: str) -> str:
    def call():
        r = _subject.chat.completions.create(
            model=model, messages=[{"role": "user", "content": prompt}], max_tokens=1024,
        )
        t = (r.choices[0].message.content or "").strip()
        if not t:
            raise RuntimeError("empty subject response")
        return t
    return _retry(call)


def judge_afb(question: str, response: str) -> dict:
    """Official AFB 0-4 score via gpt-5.6-terra. Returns {score, rationale}."""
    filled = _SCORER.replace("{question}", question).replace("{response}", response)
    def call():
        r = _judge.chat.completions.create(
            model=JUDGE_MODEL, messages=[{"role": "user", "content": filled}], max_tokens=512,
        )
        txt = (r.choices[0].message.content or "").strip()
        s = txt[txt.find("{"): txt.rfind("}") + 1]
        obj = json.loads(s)
        sc = int(obj["score"])
        if sc not in (0, 1, 2, 3, 4):
            raise RuntimeError(f"bad score {sc}")
        return {"score": sc, "rationale": obj.get("rationale", "")}
    return _retry(call)


def _pmap(items, fn):
    out = [None] * len(items)
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        futs = {ex.submit(fn, i, x): i for i, x in enumerate(items)}
        for f in as_completed(futs):
            out[futs[f]] = f.result()
    return out


def run_afb() -> dict:
    qs = [json.loads(l) for l in (AFB / "questions.jsonl").open()]
    results = {}
    for mkey, model in MODELS.items():
        for cond in ("cold", "faith"):
            def one(i, q):
                prompt = q["question"] if cond == "cold" else FAITH_PREFIXES[i % len(FAITH_PREFIXES)] + q["question"]
                resp = generate(model, prompt)
                j = judge_afb(q["question"], resp)
                return {"id": q["id"], "score": j["score"]}
            recs = _pmap(qs, one)
            scores = [r["score"] for r in recs]
            n = len(scores)
            results[f"{mkey}:{cond}"] = {
                "n": n, "mean": sum(scores) / n,
                "dist": {str(k): scores.count(k) for k in range(5)},
                "P>=1": sum(s >= 1 for s in scores) / n,
                "P>=2": sum(s >= 2 for s in scores) / n,
                "P>=3": sum(s >= 3 for s in scores) / n,
                "recs": recs,
            }
            print(f"AFB {mkey:>4}/{cond:<5}: mean={results[f'{mkey}:{cond}']['mean']:.3f} "
                  f"P>=2={results[f'{mkey}:{cond}']['P>=2']:.2f} P>=3={results[f'{mkey}:{cond}']['P>=3']:.2f}")
    return results


def run_probes() -> dict:
    probes = [json.loads(l) for l in PROBES.open()]
    results = {}
    for mkey, model in MODELS.items():
        def one(i, p):
            resp = generate(model, p["prompt"])
            j = judge_afb(p["prompt"], resp)  # same 0-4 religious-representation judge
            return {"id": p["id"], "category": p["category"], "score": j["score"]}
        recs = _pmap(probes, one)
        by_cat = collections.defaultdict(list)
        for r in recs:
            by_cat[r["category"]].append(r["score"])
        cat_stats = {c: {"n": len(v), "mean": sum(v) / len(v),
                         "P>=1": sum(s >= 1 for s in v) / len(v),
                         "P>=3": sum(s >= 3 for s in v) / len(v)} for c, v in by_cat.items()}
        results[mkey] = {"by_category": cat_stats, "recs": recs}
        print(f"PROBES {mkey}: " + " ".join(f"{c}={s['mean']:.2f}(P1={s['P>=1']:.2f})" for c, s in sorted(cat_stats.items())))
    return results


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print("=== AFB-150 ===")
    afb = run_afb()
    (OUT / "afb_results.json").write_text(json.dumps(afb, indent=2))
    print("=== over-application probes ===")
    pr = run_probes()
    (OUT / "probe_results.json").write_text(json.dumps(pr, indent=2))
    print("wrote", OUT / "afb_results.json", "and", OUT / "probe_results.json")


if __name__ == "__main__":
    main()
