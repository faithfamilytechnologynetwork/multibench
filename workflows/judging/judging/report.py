"""Aggregate judgments into per-scenario results + a tradition-level report (spec §5.8/§5.9).

All scores are on the canonical −1…+1 scale. A *cell* score is the **mean of its present
judges' scores** (judgments overlay v2 by key, §5.9); a breakdown *mean* is the unweighted
mean of the in-scope cell scores (uncovered cells excluded — never counted as 0.0). The score
distribution is taken over **per-judge verdicts** (only those land on the five-value grid).
Taxonomy breakdowns read the tradition's **declared** axes (generic — works for any tradition,
M7). Coverage is reported explicitly (no silent zeros). Writes ``report.md`` + ``report.json``;
computable from partial data — it never hard-fails (M12).
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from judging.config import Config, default_config
from judging.judge import judgment_key, load_judgments, load_skips
from judging.loaders import load_scenario, load_tradition
from judging.rubric import TECHNIQUE_IDS
from judging.scores import SCORES, mean

_FRAMINGS_REPORT = ("unstated", "stated", "guided")

# USD per million tokens (input, output). Approximate, dated — a config constant the operator
# updates as provider prices change (spec §5.8 #6: "small, clearly-dated price table").
PRICES_DATED = "2026-06 (approximate — update PRICES as prices change)"
PRICES: dict[str, tuple[float, float]] = {
    "claude-opus-4-8": (5.00, 25.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-haiku-4-5": (1.00, 5.00),
    "gemini-3.5-flash": (1.50, 9.00),
}


def _add_usage(acc: dict, u: dict) -> None:
    for k in ("in", "out", "cache_write", "cache_read"):
        acc[k] = acc.get(k, 0) + (u.get(k, 0) or 0)


def _usage_cost(model: str, tok: dict) -> float | None:
    """USD for accumulated usage, or ``None`` if the model has no listed price.

    1h-cache writes bill ~2x input, reads ~0.1x (Anthropic); non-cache models just use in/out.
    """
    if model not in PRICES:
        return None
    pi, po = PRICES[model]
    return (
        tok.get("in", 0) * pi
        + tok.get("out", 0) * po
        + tok.get("cache_write", 0) * pi * 2.0
        + tok.get("cache_read", 0) * pi * 0.1
    ) / 1e6


def _tokens_in(tok: dict) -> int:
    return tok.get("in", 0) + tok.get("cache_write", 0) + tok.get("cache_read", 0)


def _cell(j: dict) -> tuple:
    return (j["subject"], j["scenario_id"], j["pressure"], j["framing"], j["scope"])


def _cell_scores(judgments: list[dict]) -> dict[tuple, float]:
    """Mean of each cell's present-judge scores (the canonical reducer, §5.9)."""
    by: dict[tuple, list[float]] = defaultdict(list)
    for j in judgments:
        by[_cell(j)].append(j["score"])
    return {c: mean(v) for c, v in by.items()}  # never empty: a cell exists iff it has a score


def _mean_over(
    cell_scores: dict[tuple, float],
    subject: str,
    *,
    framing: str | None = None,
    scope: str | None = None,
    pressure: str | None = None,
    scenarios: set[str] | None = None,
) -> float | None:
    """Unweighted mean of in-scope cell scores; ``None`` if none cover the filter (never 0.0)."""
    vals: list[float] = []
    for (su, sc, pr, fr, scp), val in cell_scores.items():
        if su != subject:
            continue
        if framing is not None and fr != framing:
            continue
        if scope is not None and scp != scope:
            continue
        if pressure is not None and pr != pressure:
            continue
        if scenarios is not None and sc not in scenarios:
            continue
        if val is not None:
            vals.append(val)
    return mean(vals)


def _read_sittings(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def build_report(
    results_dir: str | Path, tradition_dir: str | Path, config: Config | None = None
) -> dict:
    """Compute the report data (the machine-readable shape behind report.json)."""
    config = config or default_config()
    rd = Path(results_dir)
    judgments = load_judgments(rd)
    skips = load_skips(rd)
    sittings = _read_sittings(rd / "sittings.jsonl")
    tradition = load_tradition(tradition_dir)

    # Union of judged + collected + skipped, so a subject/scenario that produced only skips or
    # zero successful judgments still appears in the report (null/excluded, never hidden — M12).
    subjects = sorted(
        {j["subject"] for j in judgments}
        | {st["subject"] for st in sittings}
        | {sk["subject"] for sk in skips}
    )
    judges = sorted({j["judge"] for j in judgments})
    cs = _cell_scores(judgments)
    scen_ids = sorted(
        {j["scenario_id"] for j in judgments} | {st["scenario_id"] for st in sittings}
    )

    # Per-scenario tags for taxonomy breakdowns (read each scenario's declared tags).
    tags: dict[str, dict[str, list[str]]] = {}
    for sid in scen_ids:
        try:
            tags[sid] = dict(load_scenario(tradition_dir, sid).meta.tags)
        except Exception:  # noqa: BLE001 — a scenario the judgments reference is unreadable
            tags[sid] = {}

    # 1. Scorecard: headline (unstated, full), steadfastness (full − turn1), per-framing.
    scorecard: dict[str, dict] = {}
    for s in subjects:
        full = _mean_over(cs, s, framing="unstated", scope="full")
        t1 = _mean_over(cs, s, framing="unstated", scope="turn1")
        steadfast = None if (full is None or t1 is None) else full - t1
        by_pressure: dict[str, float | None] = {}
        for pr in config.pressures:
            pf = _mean_over(cs, s, framing="unstated", scope="full", pressure=pr)
            pt = _mean_over(cs, s, framing="unstated", scope="turn1", pressure=pr)
            by_pressure[pr] = None if (pf is None or pt is None) else pf - pt
        by_framing = {
            fr: _mean_over(cs, s, framing=fr, scope="full") for fr in _FRAMINGS_REPORT
        }
        scorecard[s] = {
            "headline": full,
            "steadfastness": steadfast,
            "steadfastness_by_pressure": by_pressure,
            "by_framing": by_framing,
        }

    # 2. Score distribution over per-judge verdicts (string keys for JSON stability).
    distribution: dict[str, dict[str, int]] = {
        s: {str(sc): 0 for sc in SCORES} for s in subjects
    }
    for j in judgments:
        key = str(float(j["score"]))
        if key in distribution[j["subject"]]:
            distribution[j["subject"]][key] += 1

    # 3. Inter-judge agreement (cells with >=2 present judgments).
    by_cell: dict[tuple, list[float]] = defaultdict(list)
    for j in judgments:
        by_cell[_cell(j)].append(j["score"])
    multi = [v for v in by_cell.values() if len(v) >= 2]
    exact = sum(1 for v in multi if max(v) == min(v))
    within_one = sum(1 for v in multi if (max(v) - min(v)) <= 0.5)
    agreement = {
        "cells": len(multi),
        "exact_pct": (exact / len(multi)) if multi else None,
        "within_one_pct": (within_one / len(multi)) if multi else None,
    }
    # Per-scenario agreement (exact% over that scenario's >=2-judge cells) + worst (§5.8 #3).
    scen_cells: dict[str, list[list[float]]] = defaultdict(list)
    for cell, scores in by_cell.items():
        if len(scores) >= 2:
            scen_cells[cell[1]].append(scores)
    scenario_agreement = {
        sid: sum(1 for v in cl if max(v) == min(v)) / len(cl) for sid, cl in scen_cells.items()
    }
    worst = min(scenario_agreement, key=lambda s: scenario_agreement[s], default=None)
    agreement["worst_scenario"] = worst
    agreement["worst_scenario_exact_pct"] = scenario_agreement.get(worst) if worst else None

    # 4. Breakdowns by DECLARED taxonomy axes (generic — any tradition, M7); unstated, full.
    taxonomies: dict[str, dict[str, dict[str, float | None]]] = {}
    for axis in tradition.manifest.taxonomies:
        axis_values = sorted({v for sid in tags for v in tags[sid].get(axis, [])})
        per_value: dict[str, dict[str, float | None]] = {}
        for value in axis_values:
            scen_with = {sid for sid in tags if value in tags[sid].get(axis, [])}
            per_value[value] = {
                s: _mean_over(cs, s, framing="unstated", scope="full", scenarios=scen_with)
                for s in subjects
            }
        taxonomies[axis] = per_value

    # 5. Seven-technique usage (% of a subject's judgments listing each id).
    tech_total: dict[str, int] = defaultdict(int)
    tech_count: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for j in judgments:
        tech_total[j["subject"]] += 1
        for t in j.get("techniques_used", []):
            tech_count[j["subject"]][t] += 1
    techniques = {
        s: {
            t: (tech_count[s][t] / tech_total[s]) if tech_total[s] else None
            for t in TECHNIQUE_IDS
        }
        for s in subjects
    }

    # 6. Per-scenario results (unstated, full).
    by_scenario = {
        sid: {
            s: _mean_over(cs, s, framing="unstated", scope="full", scenarios={sid})
            for s in subjects
        }
        for sid in scen_ids
    }

    # 7. Coverage (no silent zeros): expected cells from sittings x panel x scope minus skips.
    expected: set[str] = set()
    for st in sittings:
        for judge in config.judges:
            if judge.model == st["subject"]:  # self-judge skip
                continue
            for scope in config.scopes:
                expected.add(
                    "|".join(
                        [
                            st["subject"],
                            st["scenario_id"],
                            st["pressure"],
                            st["framing"],
                            judge.model,
                            scope,
                        ]
                    )
                )
    judged_keys = {judgment_key(j) for j in judgments}
    uncovered = sorted(expected - judged_keys)

    # 8. Cost: collection (subject usage in sittings) + judging (judge usage in judgments).
    subj_tok: dict[str, dict] = defaultdict(dict)
    for st in sittings:
        for u in st.get("usage") or []:
            _add_usage(subj_tok[st["subject"]], u)
    judge_tok: dict[str, dict] = defaultdict(dict)
    for j in judgments:
        if j.get("usage"):
            _add_usage(judge_tok[j["judge"]], j["usage"])
    cost_rows: list[dict] = []
    total_usd = 0.0
    fully_priced = True
    for stage, toks in (("collection", subj_tok), ("judging", judge_tok)):
        for model, tok in sorted(toks.items()):
            usd = _usage_cost(model, tok)
            fully_priced = fully_priced and usd is not None
            total_usd += usd or 0.0
            cost_rows.append(
                {
                    "stage": stage,
                    "model": model,
                    "tokens_in": _tokens_in(tok),
                    "tokens_out": tok.get("out", 0),
                    "usd": usd,
                }
            )
    cost = {
        "rows": cost_rows,
        "total_usd": total_usd,
        "fully_priced": fully_priced,
        "prices_dated": PRICES_DATED,
    }

    return {
        "tradition": tradition.id,
        "subjects": subjects,
        "judges": judges,
        "counts": {
            "sittings": len(sittings),
            "judgments": len(judgments),
            "cells": len(cs),
            "expected_cells": len(expected),
            "uncovered": len(uncovered),
            "skipped_self": len(skips),
        },
        "scorecard": scorecard,
        "score_distribution": distribution,
        "agreement": agreement,
        "taxonomies": taxonomies,
        "techniques": techniques,
        "by_scenario": by_scenario,
        "scenario_agreement": scenario_agreement,
        "cost": cost,
    }


def _fmt(x: float | None) -> str:
    return "—" if x is None else f"{x:+.2f}"


def _pct(x: float | None) -> str:
    return "—" if x is None else f"{x:.0%}"


def render_markdown(rep: dict) -> str:
    subjects = rep["subjects"]
    L: list[str] = [f"# Judging report — {rep['tradition']}", ""]
    c = rep["counts"]
    L.append(
        f"Subjects: {len(subjects)} · Judges: {', '.join(rep['judges']) or '—'} · "
        f"Sittings: {c['sittings']} · Judgments: {c['judgments']}"
    )
    L.append(
        f"Coverage: judged {c['expected_cells'] - c['uncovered']}/{c['expected_cells']} cells · "
        f"uncovered: {c['uncovered']} · skipped self-judgments: {c['skipped_self']}"
    )
    L += ["", "*All scores on the −1…+1 scale; “—” = uncovered (no judgments), never 0.*", ""]

    def row(label: str, fn) -> str:
        return f"| {label} | " + " | ".join(fn(s) for s in subjects) + " |"

    # Scorecard
    L += ["## Scorecard", "", "| | " + " | ".join(subjects) + " |", "|---|" + "---|" * len(subjects)]
    L.append(row("Headline (Unstated, after pressure)", lambda s: _fmt(rep["scorecard"][s]["headline"])))
    L.append(row("Steadfastness (full − turn1)", lambda s: _fmt(rep["scorecard"][s]["steadfastness"])))
    for fr in _FRAMINGS_REPORT:
        L.append(row(f"Framing: {fr}", lambda s, fr=fr: _fmt(rep["scorecard"][s]["by_framing"].get(fr))))
    L.append("")

    # Score distribution
    L += ["## Score distribution (per-judge verdicts)", "", "| | " + " | ".join(subjects) + " |", "|---|" + "---|" * len(subjects)]
    for sc in SCORES:
        k = str(sc)
        L.append(row(f"{sc:+.1f}", lambda s, k=k: str(rep["score_distribution"][s].get(k, 0))))
    L.append("")

    # Agreement
    a = rep["agreement"]
    L += ["## Inter-judge agreement", ""]
    L.append(f"- Exact: {_pct(a['exact_pct'])} · Within one level: {_pct(a['within_one_pct'])} ({a['cells']} cells with ≥2 judges)")
    if a.get("worst_scenario"):
        L.append(
            f"- Worst scenario for agreement: {a['worst_scenario']} "
            f"({_pct(a['worst_scenario_exact_pct'])} exact)"
        )
    L.append("")

    # Taxonomy breakdowns
    for axis, values in rep["taxonomies"].items():
        if not values:
            continue
        L += [f"## By {axis} (Unstated, after pressure)", "", "| | " + " | ".join(subjects) + " |", "|---|" + "---|" * len(subjects)]
        for value, per_subject in values.items():
            L.append(row(value, lambda s, ps=per_subject: _fmt(ps.get(s))))
        L.append("")

    # Techniques (tradition-neutral heading — M7)
    L += ["## Counseling-technique use (% of judgments)", "", "| | " + " | ".join(subjects) + " |", "|---|" + "---|" * len(subjects)]
    for t in TECHNIQUE_IDS:
        L.append(row(t, lambda s, t=t: _pct(rep["techniques"][s].get(t))))
    L.append("")

    # Per-scenario results (Unstated, after pressure) + agreement — §5.8 #5
    L += [
        "## By scenario (Unstated, after pressure)",
        "",
        "| Scenario | " + " | ".join(subjects) + " | Agreement |",
        "|---|" + "---|" * (len(subjects) + 1),
    ]
    for sid in sorted(rep["by_scenario"]):
        scores = " | ".join(_fmt(rep["by_scenario"][sid].get(s)) for s in subjects)
        agr = _pct(rep["scenario_agreement"].get(sid))
        L.append(f"| {sid} | {scores} | {agr} |")
    L.append("")

    # Cost — §5.8 #6
    cost = rep["cost"]
    L += ["## Cost", "", "| Stage | Model | Tokens in | Tokens out | USD |", "|---|---|---|---|---|"]
    for r in cost["rows"]:
        usd = "—" if r["usd"] is None else f"${r['usd']:.2f}"
        L.append(f"| {r['stage']} | {r['model']} | {r['tokens_in']:,} | {r['tokens_out']:,} | {usd} |")
    note = "" if cost["fully_priced"] else " (partial — unpriced model(s) present)"
    L.append(f"| **total** | | | | **${cost['total_usd']:.2f}**{note} |")
    L += ["", f"*Prices per Mtok, {cost['prices_dated']}.*", ""]

    return "\n".join(L) + "\n"


def write_report(
    results_dir: str | Path, tradition_dir: str | Path, config: Config | None = None
) -> dict:
    """Build the report and write ``report.md`` + ``report.json``. Returns a small summary."""
    rd = Path(results_dir)
    rd.mkdir(parents=True, exist_ok=True)
    rep = build_report(rd, tradition_dir, config)
    (rd / "report.json").write_text(json.dumps(rep, indent=2) + "\n", encoding="utf-8")
    (rd / "report.md").write_text(render_markdown(rep), encoding="utf-8")
    return {
        "tradition": rep["tradition"],
        "subjects": len(rep["subjects"]),
        "judgments": rep["counts"]["judgments"],
        "uncovered": rep["counts"]["uncovered"],
    }
