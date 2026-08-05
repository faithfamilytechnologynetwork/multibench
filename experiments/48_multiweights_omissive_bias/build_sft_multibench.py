"""Build the pooled bare SFT set (experiment 48, stage-1 context distillation).

Adapts taqwabench's build_sft_guided.py to MultiBench: joins the collected GUIDED sittings with
their Gemini judgments (per subject|scenario|pressure|framing), keeps a sitting iff its score is
**≥ +0.5 on BOTH scopes** (full AND turn1) — the architect's faithful translation of taqwabench's
"band ≥ +1 top-2-of-5" onto MultiBench's 5-point −1..+1 ladder. Screens (carried over): no explicit
guide references, no dangling [n]-citation markers. The guided turns are already BARE (the guide
lives in context_prefix OUTSIDE the turns — verified at smoke), so "re-render bare" = use turns
as-is. NO scenario holdout, NO per-tradition balancing (pool is corpus-representative; architect
2026-08-05). Output masks assistant tokens downstream; both assistant turns carry loss.

Run: uv --project workflows/judging run python experiments/48_multiweights_omissive_bias/build_sft_multibench.py
"""

from __future__ import annotations

import collections
import hashlib
import json
import re
from pathlib import Path

EXP = Path(__file__).resolve().parent
COLL = EXP / "data" / "output" / "collection"
OUTDIR = EXP / "data" / "output" / "sft"
TRADITIONS = [
    "buddhism", "eastern-christianity", "judaism", "roman-catholicism",
    "secular-sage", "sunni-islam", "taoism",
]
THRESHOLD = 0.5  # score >= +0.5 on BOTH scopes (architect ruling 2026-08-05)

# Screens (verbatim from taqwabench build_sft_guided.py).
MARKER = re.compile(r"\[\d+\]")
RESOLVES = re.compile(r"(?im)^(\*{0,2}(references|sources|citations)\b|\[\d+\]\s*[A-Z؀-ۿ])")
GUIDE_REF = re.compile(
    r"(?i)(context above|the context for this conversation|as instructed|"
    r"my instructions|my guidelines|the guide(?:lines)? (?:above|says|asks)|"
    r"i was (?:asked|told) to|per the (?:context|instructions))")


def dangling_markers(turns) -> bool:
    text = turns[1]["content"] + "\n" + turns[3]["content"]
    return bool(MARKER.search(text)) and not RESOLVES.search(text)


def _key(r: dict) -> tuple:
    return (r["subject"], r["scenario_id"], r["pressure"], r["framing"])


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    rows = []
    stats = collections.Counter()
    per_trad = collections.Counter()
    for t in TRADITIONS:
        sfile = COLL / t / "sittings.jsonl"
        jfile = COLL / t / "judgments.jsonl"
        # scores[key][scope] = score  (guided only)
        scores: dict[tuple, dict] = collections.defaultdict(dict)
        for line in jfile.open():
            j = json.loads(line)
            if j["framing"] != "guided":
                continue
            scores[_key(j)][j["scope"]] = j.get("score")
        for line in sfile.open():
            r = json.loads(line)
            if r["framing"] != "guided":
                continue
            stats["guided_total"] += 1
            sc = scores.get(_key(r), {})
            full, turn1 = sc.get("full"), sc.get("turn1")
            if full is None or turn1 is None:
                stats["missing_judgment"] += 1
                continue
            if full < THRESHOLD or turn1 < THRESHOLD:
                stats["below_threshold"] += 1
                continue
            m = GUIDE_REF.search(r["turns"][1]["content"] + "\n" + r["turns"][3]["content"])
            if m:
                stats["guide_ref_screened"] += 1
                stats[f"ref:{m.group(0).lower()}"] += 1
                continue
            if dangling_markers(r["turns"]):
                stats["dangling_screened"] += 1
                continue
            rows.append({
                "tradition": t, "scenario_id": r["scenario_id"], "pressure": r["pressure"],
                "full_score": full, "turn1_score": turn1, "turns": r["turns"],
            })
            per_trad[t] += 1
            stats["kept"] += 1

    out = OUTDIR / "sft_train_guided.jsonl"
    with out.open("w") as fh:
        for row in sorted(rows, key=lambda x: (x["tradition"], x["scenario_id"], x["pressure"])):
            fh.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")

    print(f"KEPT {stats['kept']} of {stats['guided_total']} guided "
          f"({100*stats['kept']/max(stats['guided_total'],1):.1f}%)")
    print(f"  below_threshold={stats['below_threshold']}  guide_ref_screened={stats['guide_ref_screened']}"
          f"  dangling_screened={stats['dangling_screened']}  missing_judgment={stats['missing_judgment']}")
    print("  per-tradition kept:", dict(per_trad))
    print("  screened phrases:", {k[4:]: v for k, v in stats.items() if k.startswith("ref:")})
    print("  sha256:", hashlib.sha256(out.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
