"""Phase 6 analysis for Spec 119 (protestant-unified) — paper-ready numbers + figures.

Reconciles BY CONSTRUCTION with the committed ``results/20260905/`` score tier: every
number here flows through the canonical aggregator (``build_combined_runs`` →
``aggregate_tradition`` → ``compute_tradition_stats``), so there is **no second
mean-of-means implementation** and no hand-rolled chart. The leaderboard ranking score
per tradition is the equal-weight mean over subjects × framings of the combined
``by_framing[full]`` breakdown (scope=full, pressure=all) — the #120/#121 two-judge
``mean_of_judges`` rule.

Run (from repo root):

    uv --project workflows/analysis run python experiments/119_protestant_unified/analyze.py

Two hard-fail reconciliation assertions (see ``_assert_reconciliation``) gate the run.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import typer

from analysis.aggregate import TraditionAggregate, aggregate_tradition
from analysis.combined_stats import (
    build_combined_runs,
    combined_subj_overall,
    export_combined_mean_of_means,
)
from analysis.export_results import (
    CANONICAL_SUBJECTS,
    FRAMINGS,
    read_run_root,
    resolve_judgments,
)
from analysis.figures import emit_figures
from analysis.stats import TraditionStats, compute_tradition_stats

# The 5 judging-run roots in load-bearing priority order (relative to the repo root of the
# worktree; the roots live in the MAIN checkout, hence the ``../../``).
ROOTS: list[str] = [
    "../../tmp/judging-runs/20260803-merged",
    "../../tmp/judging-runs/20260803-unstated-opus",
    "../../tmp/judging-runs/20260803-framings-opus-sample",
    "../../tmp/judging-runs/20260823-opus-fullgrid",
    "../../tmp/judging-runs/20260904-protestant-unified",
]

# The committed score tier this analysis must reconcile with.
RESULTS_DIR = Path("results/20260905")
PU = "protestant-unified"
_FULL = "full"
_ALL = "all"
_TOL = 1e-9

# Judge canonical model ids (post-normalization).
_GEMINI = "gemini-3.6-flash"
_OPUS = "claude-opus-4-8"

_HERE = Path("experiments/119_protestant_unified")
_OUT = _HERE / "data" / "output"

app = typer.Typer(add_completion=False, help="Spec 119 Phase 6 analysis.")


# ── Ranking mean-of-means ─────────────────────────────────────────────────────────


def _ranking_mean_of_means(agg: TraditionAggregate) -> float:
    """Equal-weight mean over subjects × framings of the combined ``by_framing[full]``
    breakdown (scope=full, pressure=all) — the per-tradition leaderboard ranking score."""
    vals = [
        agg.scorecard[s]["by_framing"][fr]
        for s in CANONICAL_SUBJECTS
        for fr in FRAMINGS
        if s in agg.scorecard and agg.scorecard[s]["by_framing"].get(fr) is not None
    ]
    return sum(vals) / len(vals)


def _ranking_from_shard(shard: dict) -> float:
    """The same ranking score derived from a committed shard's ``combined`` block:
    ``combined[subject][framing]['full']['all'][0]`` averaged over subjects × framings."""
    combined = shard["combined"]
    vals: list[float] = []
    for s in CANONICAL_SUBJECTS:
        if s not in combined:
            continue
        for fr in FRAMINGS:
            cell = combined[s].get(fr, {}).get(_FULL, {}).get(_ALL)
            if cell is not None:
                vals.append(cell[0])
    return sum(vals) / len(vals)


# ── Reconciliation assertions (hard-fail) ─────────────────────────────────────────


def _assert_reconciliation(
    aggregates: list[TraditionAggregate],
    roots: list[str],
    ranking: dict[str, float],
) -> None:
    """Two hard-fail checks tying this analysis to the committed score tier."""
    # (b.1) The combined subj_overall (from aggregates) equals the results-export mean-of-means.
    lhs = combined_subj_overall(aggregates)
    rhs = export_combined_mean_of_means(roots)
    if set(lhs) != set(rhs):
        raise AssertionError(
            f"subj_overall key mismatch: only-agg={sorted(set(lhs) - set(rhs))} "
            f"only-export={sorted(set(rhs) - set(lhs))}"
        )
    for key in lhs:
        if abs(lhs[key] - rhs[key]) > _TOL:
            raise AssertionError(
                f"subj_overall reconciliation failed at {key}: "
                f"aggregates={lhs[key]!r} != export={rhs[key]!r} (Δ={lhs[key] - rhs[key]:.2e})"
            )

    # (b.2) Per-tradition ranking mean-of-means equals the committed shard's combined block.
    for tradition, mine in ranking.items():
        shard_path = RESULTS_DIR / f"{tradition}.json"
        if not shard_path.is_file():
            raise AssertionError(f"missing committed shard for reconciliation: {shard_path}")
        theirs = _ranking_from_shard(json.loads(shard_path.read_text(encoding="utf-8")))
        if abs(mine - theirs) > _TOL:
            raise AssertionError(
                f"ranking reconciliation failed for {tradition}: "
                f"recomputed={mine!r} != shard={theirs!r} (Δ={mine - theirs:.2e})"
            )


# ── Opus-vs-Gemini agreement (protestant-unified) ─────────────────────────────────


def _agreement_pu(root: str) -> dict:
    """Opus-vs-Gemini agreement over every protestant-unified cell BOTH judges scored.

    Reads the raw per-judge rows from ``root`` (the 20260904-protestant-unified run),
    pairs Gemini vs Opus on (subject, scenario_id, pressure, framing, scope), and reports
    Pearson r, bias = mean(Opus − Gemini), the within-±0.5 fraction, the exact-match
    fraction, and n (paired cells)."""
    raws = read_run_root(root)
    if PU not in raws:
        raise AssertionError(f"{PU} not found under {root}")
    rows = resolve_judgments([raws[PU]])  # canonical judge/subject ids

    per_cell: dict[tuple, dict[str, float]] = defaultdict(dict)
    for r in rows:
        cell = (r["subject"], r["scenario_id"], r["pressure"], r["framing"], r["scope"])
        per_cell[cell][r["judge"]] = r["score"]

    gem: list[float] = []
    opus: list[float] = []
    for judges in per_cell.values():
        if _GEMINI in judges and _OPUS in judges:
            gem.append(judges[_GEMINI])
            opus.append(judges[_OPUS])
    if not gem:
        raise AssertionError(f"{PU}: no cells scored by BOTH judges under {root}")

    g = np.array(gem, dtype=float)
    o = np.array(opus, dtype=float)
    diff = o - g
    n = int(g.size)
    # Pearson r (guard a degenerate zero-variance vector, though real data has variance).
    if g.std() == 0 or o.std() == 0:
        r = float("nan")
    else:
        r = float(np.corrcoef(o, g)[0, 1])
    return {
        "n": n,
        "pearson_r": r,
        "bias_opus_minus_gemini": float(diff.mean()),
        "within_half_fraction": float(np.mean(np.abs(diff) <= 0.5)),
        "exact_match_fraction": float(np.mean(diff == 0.0)),
    }


# ── paper_numbers.json assembly ───────────────────────────────────────────────────


def _ci(ci: list | None) -> dict | None:
    return None if ci is None else {"point": ci[0], "lo": ci[1], "hi": ci[2]}


def _per_framing_combined(agg: TraditionAggregate) -> dict:
    """Per-tradition combined by_framing[full] means, subj_overall style (subject|framing),
    plus a per-framing mean over subjects (the framing-staircase value)."""
    per_subject_framing: dict[str, float] = {}
    by_framing_acc: dict[str, list[float]] = defaultdict(list)
    for s in CANONICAL_SUBJECTS:
        if s not in agg.scorecard:
            continue
        for fr in FRAMINGS:
            v = agg.scorecard[s]["by_framing"].get(fr)
            if v is not None:
                per_subject_framing[f"{s}|{fr}"] = v
                by_framing_acc[fr].append(v)
    framing_mean = {fr: sum(vs) / len(vs) for fr, vs in by_framing_acc.items()}
    return {"by_subject_framing": per_subject_framing, "framing_mean_over_subjects": framing_mean}


def _build_paper_numbers(
    aggregates: list[TraditionAggregate],
    stats: list[TraditionStats],
    ranking: dict[str, float],
    agreement: dict,
) -> dict:
    agg_by = {a.tradition: a for a in aggregates}
    st_by = {s.tradition: s for s in stats}

    # Ranked table (descending ranking score).
    ranked = sorted(ranking.items(), key=lambda kv: kv[1], reverse=True)
    ranked_table = [
        {"tradition": t, "ranking_mean_of_means": v, "rank": i}
        for i, (t, v) in enumerate(ranked, start=1)
    ]

    per_tradition: dict[str, dict] = {}
    for t, agg in agg_by.items():
        st = st_by[t]
        headlines = {
            s: _ci(st.per_subject[s].headline)
            for s in CANONICAL_SUBJECTS
            if s in st.per_subject
        }
        per_tradition[t] = {
            "ranking_mean_of_means": ranking[t],
            "per_subject_unstated_headline": headlines,
            "per_framing_combined": _per_framing_combined(agg),
        }

    pu_st = st_by[PU]
    pu_steadfastness = {
        s: _ci(pu_st.per_subject[s].steadfastness)
        for s in CANONICAL_SUBJECTS
        if s in pu_st.per_subject
    }

    return {
        "meta": {
            "spec": 119,
            "tradition": PU,
            "roots": ROOTS,
            "results_dir": str(RESULTS_DIR),
            "ranking_rule": "mean_of_judges",
            "ranking_score": (
                "equal-weight mean over subjects x framings of combined by_framing[full] "
                "(scope=full, pressure=all)"
            ),
            "subjects": list(CANONICAL_SUBJECTS),
            "framings": list(FRAMINGS),
        },
        "ranked_table": ranked_table,
        "per_tradition": per_tradition,
        "protestant_unified_steadfastness": pu_steadfastness,
        "protestant_unified_judge_agreement": agreement,
    }


@app.command()
def main() -> None:
    """Build combined aggregates/stats, reconcile with the committed tier, and write outputs."""
    typer.echo(f"Building combined runs over {len(ROOTS)} roots ...")
    runs = build_combined_runs(ROOTS)
    aggregates = [aggregate_tradition(r) for r in runs]
    stats = [compute_tradition_stats(a) for a in aggregates]
    typer.echo(f"  traditions: {[a.tradition for a in aggregates]}")

    ranking = {a.tradition: _ranking_mean_of_means(a) for a in aggregates}

    typer.echo("Reconciliation assertions ...")
    _assert_reconciliation(aggregates, ROOTS, ranking)
    typer.echo("  OK: subj_overall (aggregates == results-export mean-of-means) <= 1e-9")
    typer.echo("  OK: per-tradition ranking (recomputed == committed shard combined) <= 1e-9")

    typer.echo("Opus-vs-Gemini agreement (protestant-unified) ...")
    agreement = _agreement_pu(ROOTS[-1])

    _OUT.mkdir(parents=True, exist_ok=True)
    paper_numbers = _build_paper_numbers(aggregates, stats, ranking, agreement)
    out_path = _OUT / "paper_numbers.json"
    out_path.write_text(json.dumps(paper_numbers, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    typer.echo(f"  wrote {out_path}")

    typer.echo("Emitting figures (pdf, png) ...")
    figures = emit_figures(aggregates, stats, _OUT / "figures", ["pdf", "png"])
    for f in figures:
        typer.echo(f"  wrote {f}")

    # ── Concise stdout summary ────────────────────────────────────────────────────
    typer.echo("\n=== Ranked leaderboard (combined two-judge mean_of_judges) ===")
    for row in paper_numbers["ranked_table"]:
        marker = "  <-- protestant-unified" if row["tradition"] == PU else ""
        typer.echo(f"  {row['rank']}. {row['tradition']:<22} {row['ranking_mean_of_means']:+.4f}{marker}")

    pu_pf = paper_numbers["per_tradition"][PU]["per_framing_combined"]["framing_mean_over_subjects"]
    typer.echo("\n=== protestant-unified per-framing combined mean (over subjects) ===")
    for fr in FRAMINGS:
        typer.echo(f"  {fr:<9} {pu_pf[fr]:+.4f}")

    typer.echo("\n=== protestant-unified per-subject unstated-headline (point [lo, hi]) ===")
    for s, ci in paper_numbers["per_tradition"][PU]["per_subject_unstated_headline"].items():
        typer.echo(f"  {s:<40} {ci['point']:+.4f} [{ci['lo']:+.4f}, {ci['hi']:+.4f}]")

    typer.echo("\n=== protestant-unified steadfastness per subject (point [lo, hi]) ===")
    for s, ci in paper_numbers["protestant_unified_steadfastness"].items():
        if ci is None:
            typer.echo(f"  {s:<40} (none)")
        else:
            typer.echo(f"  {s:<40} {ci['point']:+.4f} [{ci['lo']:+.4f}, {ci['hi']:+.4f}]")

    a = agreement
    typer.echo("\n=== Opus-vs-Gemini agreement (protestant-unified) ===")
    typer.echo(
        f"  n={a['n']}  pearson_r={a['pearson_r']:.4f}  bias(Opus-Gemini)={a['bias_opus_minus_gemini']:+.4f}  "
        f"within-0.5={a['within_half_fraction']:.4f}  exact={a['exact_match_fraction']:.4f}"
    )
    typer.echo("\nDone.")


if __name__ == "__main__":
    app()
