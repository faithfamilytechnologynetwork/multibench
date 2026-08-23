#!/usr/bin/env python3
"""Merge the double codings + adjudicated disputes into codings/adjudicated.json.

For each question: if the two coders for its half agree (same severity AND same
cluster partition), take the first coder's entry; otherwise take the adjudicator's.
Also writes codings/agreement.json with the inter-coder agreement statistics.

Usage: python3 merge_codings.py --disputes <path-to-adjudicated_disputes.json>
"""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
QUESTIONS = [f"Q{i:02d}" for i in range(1, 51)]


def canon(clusters):
    return sorted(sorted(c) for c in clusters)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--disputes", required=True)
    args = ap.parse_args()

    cod = {k: json.loads((HERE / "codings" / f"coder_{k}.json").read_text()) for k in "ABCD"}
    disputes = json.loads(Path(args.disputes).read_text())

    adjudicated, disagreed = {}, []
    sev_match = part_match = 0
    for q in QUESTIONS:
        first, second = (cod["A"], cod["B"]) if q in cod["A"] else (cod["C"], cod["D"])
        e1, e2 = first[q], second[q]
        s_ok = e1["severity"] == e2["severity"]
        p_ok = canon(e1["clusters"]) == canon(e2["clusters"])
        sev_match += s_ok
        part_match += s_ok and p_ok
        if s_ok and p_ok:
            adjudicated[q] = e1
        else:
            disagreed.append(q)
            if q not in disputes:
                raise SystemExit(f"disagreement on {q} but no adjudicated entry")
            adjudicated[q] = disputes[q]

    extra = set(disputes) - set(disagreed)
    if extra:
        raise SystemExit(f"adjudicated entries for non-disagreements: {sorted(extra)}")

    for q, e in adjudicated.items():
        members = sorted([r for c in e["clusters"] for r in c] + e.get("silent", []))
        if members != [f"R{i}" for i in range(1, 8)]:
            raise SystemExit(f"{q}: clusters+silent != R1..R7: {members}")
        if e["severity"] not in ("same", "emphasis", "substance"):
            raise SystemExit(f"{q}: bad severity {e['severity']}")

    (HERE / "codings" / "adjudicated.json").write_text(
        json.dumps(adjudicated, indent=2), encoding="utf-8"
    )
    agreement = {
        "n_questions": len(QUESTIONS),
        "severity_exact_match": sev_match,
        "severity_match_rate": round(sev_match / len(QUESTIONS), 4),
        "partition_exact_match": part_match,
        "partition_match_rate": round(part_match / len(QUESTIONS), 4),
        "adjudicated_questions": disagreed,
    }
    (HERE / "codings" / "agreement.json").write_text(
        json.dumps(agreement, indent=2), encoding="utf-8"
    )
    print(json.dumps(agreement, indent=2))


if __name__ == "__main__":
    main()
