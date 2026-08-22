#!/usr/bin/env python3
"""Compute the study aggregates from the adjudicated codings.

Inputs (all in this directory once coding is complete):
  codings/adjudicated.json  {Q01: {severity, clusters: [[R..],..], silent: [R..],
                                   outliers: [R..], rationale}}
  codings/grounding.json    {Q01: {grounding: shared|parallel|divergent, note}}
  codings/mapping.json      {Q01: {R1: strand, ...}}   (committed after coding)

Outputs: output/summary.json, output/pairwise_agreement.csv, output/per_domain.csv
"""
import csv
import json
from collections import defaultdict
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
STRANDS = [
    "lutheran",
    "reformed-presbyterian",
    "anglican",
    "baptist",
    "methodist-wesleyan",
    "pentecostal",
    "anabaptist",
]
DOMAINS = {}
for i in range(1, 8):
    DOMAINS[f"Q{i:02d}"] = "work"
for i in range(8, 15):
    DOMAINS[f"Q{i:02d}"] = "money"
for i in range(15, 25):
    DOMAINS[f"Q{i:02d}"] = "family"
for i in range(25, 32):
    DOMAINS[f"Q{i:02d}"] = "body_mind"
for i in range(32, 37):
    DOMAINS[f"Q{i:02d}"] = "social"
for i in range(37, 42):
    DOMAINS[f"Q{i:02d}"] = "civic"
for i in range(42, 45):
    DOMAINS[f"Q{i:02d}"] = "digital"
for i in range(45, 49):
    DOMAINS[f"Q{i:02d}"] = "interior"
for i in range(49, 51):
    DOMAINS[f"Q{i:02d}"] = "grief"


def load(name):
    return json.loads((HERE / "codings" / name).read_text(encoding="utf-8"))


def main():
    adj = load("adjudicated.json")
    grounding = load("grounding.json")
    mapping = load("mapping.json")
    (HERE / "output").mkdir(exist_ok=True)

    sev_counts = defaultdict(int)
    dom_sev = defaultdict(lambda: defaultdict(int))
    pair_same = defaultdict(int)
    pair_n = defaultdict(int)
    outlier_counts = defaultdict(int)
    silent_counts = defaultdict(int)
    grid = defaultdict(int)  # (severity, grounding) -> n
    substance_questions = []

    for q, c in sorted(adj.items()):
        sev = c["severity"]
        sev_counts[sev] += 1
        dom_sev[DOMAINS[q]][sev] += 1
        g = grounding.get(q, {}).get("grounding", "uncoded")
        grid[(sev, g)] += 1
        if sev == "substance":
            substance_questions.append(q)
        unmap = mapping[q]
        for r in c.get("silent", []):
            silent_counts[unmap[r]] += 1
        for r in c.get("outliers", []):
            outlier_counts[unmap[r]] += 1
        cluster_of = {}
        for idx, cluster in enumerate(c["clusters"]):
            for r in cluster:
                cluster_of[unmap[r]] = idx
        for a, b in combinations(sorted(cluster_of), 2):
            pair_n[(a, b)] += 1
            if cluster_of[a] == cluster_of[b]:
                pair_same[(a, b)] += 1

    n = sum(sev_counts.values())
    D = sev_counts["substance"] / n if n else 0.0
    sub_domains = defaultdict(int)
    for q in substance_questions:
        sub_domains[DOMAINS[q]] += 1
    top3 = sum(sorted(sub_domains.values(), reverse=True)[:3])
    concentrated_domains = (
        top3 / len(substance_questions) >= 0.7 if substance_questions else True
    )
    total_outliers = sum(outlier_counts.values())
    top_strand, top_share = None, 0.0
    if total_outliers:
        top_strand = max(outlier_counts, key=outlier_counts.get)
        top_share = outlier_counts[top_strand] / total_outliers

    summary = {
        "n_questions": n,
        "severity_counts": dict(sev_counts),
        "D_substantive_divergence_share": round(D, 4),
        "substance_questions": substance_questions,
        "substance_by_domain": dict(sub_domains),
        "concentrated_by_domain_rule": concentrated_domains,
        "outlier_counts_by_strand": dict(outlier_counts),
        "top_outlier_strand": top_strand,
        "top_outlier_share_of_outliers": round(top_share, 4),
        "silence_counts_by_strand": dict(silent_counts),
        "advice_x_grounding": {f"{s}|{g}": v for (s, g), v in sorted(grid.items())},
    }
    (HERE / "output" / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    with (HERE / "output" / "pairwise_agreement.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["strand_a", "strand_b", "n_both_answered", "share_same_cluster"])
        for a, b in combinations(STRANDS, 2):
            key = tuple(sorted((a, b)))
            nn = pair_n.get(key, 0)
            w.writerow([a, b, nn, round(pair_same.get(key, 0) / nn, 4) if nn else ""])

    with (HERE / "output" / "per_domain.csv").open("w", newline="") as f:
        w = csv.writer(f)
        sevs = ["same", "emphasis", "substance"]
        w.writerow(["domain", "n"] + sevs)
        for dom in sorted({v for v in DOMAINS.values()}):
            row = dom_sev[dom]
            w.writerow([dom, sum(row.values())] + [row.get(s, 0) for s in sevs])

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
