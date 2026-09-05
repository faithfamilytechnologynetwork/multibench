"""Phase 6 analysis for Spec 119 (protestant-unified) — paper-ready numbers + figures.

Reconciles BY CONSTRUCTION with the committed ``results/20260905/`` score tier: every
number here flows through the canonical aggregator (``build_combined_runs`` →
``aggregate_tradition`` → ``compute_tradition_stats``), so there is **no second
mean-of-means implementation** and no hand-rolled chart. The leaderboard ranking score
per tradition is the equal-weight mean over subjects × framings of the combined
``by_framing[full]`` breakdown (scope=full, pressure=all) — the #120/#121 two-judge
``mean_of_judges`` rule. Per-tradition confidence intervals reuse the canonical
scenario-cluster bootstrap from ``analysis.paper_bundle`` (``_combined_rows`` + the same
seed/n_boot/percentile convention), so the CI method matches the paper's ``trad_pooled``.

Run (from repo root):

    uv --project workflows/analysis run python experiments/124_protestant_unified/analyze.py

Reconciliation is gated by hard-fail assertions (see ``_assert_reconciliation`` and the
bootstrap-point check in ``main``).
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
    build_combined_stats,
    combined_subj_overall,
    export_combined_mean_of_means,
)
from analysis.export_results import (
    CANONICAL_SUBJECTS,
    FRAMINGS,
    read_run_root,
    resolve_judgments,
)
from analysis.figures import _apply_house_style, band_color, emit_figures, saveboth
from analysis.paper_bundle import _combined_rows
from analysis.stats import TraditionStats, compute_tradition_stats

# The 5 judging-run roots in load-bearing priority order. The roots live in the MAIN
# checkout, hence the ``../../`` default (correct when run from the builder worktree).
DEFAULT_ROOTS: list[str] = [
    "../../tmp/judging-runs/20260803-merged",
    "../../tmp/judging-runs/20260803-unstated-opus",
    "../../tmp/judging-runs/20260803-framings-opus-sample",
    "../../tmp/judging-runs/20260823-opus-fullgrid",
    "../../tmp/judging-runs/20260904-protestant-unified",
]
DEFAULT_RESULTS_DIR = "results/20260905"
# The retired 7-strand monolith's committed score tier, for the sanity-check comparison.
MONOLITH_SHARD = Path("results/20260813-protestantism/protestantism.json")

PU = "protestant-unified"
_FULL = "full"
_ALL = "all"
_TOL = 1e-9
# Canonical scenario-cluster bootstrap settings — identical to analysis.paper_bundle.
_N_BOOT = 5000
_SEED = 12345

# Judge canonical model ids (post-normalization).
_GEMINI = "gemini-3.6-flash"
_OPUS = "claude-opus-4-8"

_OUT = Path("experiments/124_protestant_unified/data/output")

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


def _monolith_mean_of_means() -> float | None:
    """The retired protestantism monolith's combined mean-of-means, for a sanity-check.

    The monolith's committed shard (``20260813-protestantism``) predates the #120 combined
    block, so it carries only per-judge ``means``. Because the combined score is the mean of
    the two judges and both are full-grid here, the combined mean-of-means equals the average
    of each judge's mean-of-means (mean-of-means is linear). Returns ``None`` if the shard is
    absent. NB this is a DIFFERENT scenario set and a DIFFERENT construct (the 7-strand
    monolith, not the same-advice common witness) — a directional comparison only."""
    if not MONOLITH_SHARD.is_file():
        return None
    means = json.loads(MONOLITH_SHARD.read_text(encoding="utf-8"))["means"]
    per_judge = []
    for judge in (_GEMINI, _OPUS):
        jm = means.get(judge)
        if jm is None:
            return None
        vals = [
            jm[s][fr][_FULL][_ALL][0]
            for s in CANONICAL_SUBJECTS
            for fr in FRAMINGS
            if s in jm and jm[s].get(fr, {}).get(_FULL, {}).get(_ALL) is not None
        ]
        per_judge.append(sum(vals) / len(vals))
    return sum(per_judge) / len(per_judge)


# ── Per-tradition scenario-cluster bootstrap CIs (canonical method) ────────────────


def _tradition_cis(roots: list[str], *, n_boot: int = _N_BOOT, seed: int = _SEED) -> dict:
    """95% scenario-cluster bootstrap CIs for each tradition's combined mean, reusing the
    exact ``analysis.paper_bundle`` machinery (``_combined_rows`` + per-scenario means matrix
    + shared per-tradition resample indices). Returns ``{tradition: {'overall': CI,
    'per_framing': {framing: CI}}}`` where each CI is ``{'point','lo','hi'}``. The ``overall``
    point is the equal-weight mean over subjects × framings (the leaderboard ranking score);
    ``per_framing`` pools over subjects for one framing (matches the paper's ``trad_pooled``)."""
    rows = _combined_rows(roots)
    acc: dict = defaultdict(lambda: defaultdict(list))
    for j in rows:
        if j["scope"] != _FULL:
            continue
        acc[(j["tradition"], j["framing"], j["subject"])][j["scenario_id"]].append(j["score"])

    traditions = sorted({t for (t, _f, _s) in acc})
    scen_ids = {
        t: sorted({sc for (tt, _f, _s), d in acc.items() if tt == t for sc in d})
        for t in traditions
    }
    n_scen = {t: len(scen_ids[t]) for t in traditions}
    mat = {key: np.array([np.mean(d[sc]) for sc in scen_ids[key[0]]]) for key, d in acc.items()}
    # Fail loud on any grid gap: an empty (t,f,s,scenario) cell makes np.mean([]) → nan, which
    # would then slip silently through the ≤1e-9 reconciliation guards (abs(nan-x)>tol is False).
    for key, v in mat.items():
        if v.size == 0 or not np.all(np.isfinite(v)):
            raise AssertionError(f"non-finite/empty per-scenario means for {key} — grid gap?")
    rng = np.random.default_rng(seed)
    idx = {t: rng.integers(0, n_scen[t], size=(n_boot, n_scen[t])) for t in traditions}

    def boot(t: str, f: str, s: str) -> tuple[float, np.ndarray]:
        v = mat[(t, f, s)]
        return float(v.mean()), v[idx[t]].mean(axis=1)

    def pct(bs: np.ndarray) -> tuple[float, float]:
        return float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))

    out: dict = {}
    for t in traditions:
        per_framing: dict = {}
        all_pts: list[float] = []
        all_bss: list[np.ndarray] = []
        for f in FRAMINGS:
            per = [boot(t, f, s) for s in CANONICAL_SUBJECTS if (t, f, s) in mat]
            pts = [p for p, _b in per]
            bss = [b for _p, b in per]
            fb = np.mean(bss, axis=0)
            lo, hi = pct(fb)
            per_framing[f] = {"point": float(np.mean(pts)), "lo": lo, "hi": hi}
            all_pts += pts
            all_bss += bss
        overall_boot = np.mean(all_bss, axis=0)
        lo, hi = pct(overall_boot)
        out[t] = {
            "overall": {"point": float(np.mean(all_pts)), "lo": lo, "hi": hi},
            "per_framing": per_framing,
        }
    return out


# ── Reconciliation assertions (hard-fail) ─────────────────────────────────────────


def _assert_reconciliation(
    aggregates: list[TraditionAggregate],
    roots: list[str],
    ranking: dict[str, float],
    results_dir: Path,
) -> None:
    """Hard-fail checks tying this analysis to the committed score tier."""
    # (b.1) The combined subj_overall (from aggregates) equals the results-export mean-of-means.
    lhs = combined_subj_overall(aggregates)
    rhs = export_combined_mean_of_means(roots)
    if set(lhs) != set(rhs):
        raise AssertionError(
            f"subj_overall key mismatch: only-agg={sorted(set(lhs) - set(rhs))} "
            f"only-export={sorted(set(rhs) - set(lhs))}"
        )
    for key in lhs:
        if not (np.isfinite(lhs[key]) and np.isfinite(rhs[key]) and abs(lhs[key] - rhs[key]) <= _TOL):
            raise AssertionError(
                f"subj_overall reconciliation failed at {key}: "
                f"aggregates={lhs[key]!r} != export={rhs[key]!r} (Δ={lhs[key] - rhs[key]:.2e})"
            )

    # (b.2) Per-tradition ranking mean-of-means equals the committed shard's combined block.
    for tradition, mine in ranking.items():
        shard_path = results_dir / f"{tradition}.json"
        if not shard_path.is_file():
            raise AssertionError(f"missing committed shard for reconciliation: {shard_path}")
        theirs = _ranking_from_shard(json.loads(shard_path.read_text(encoding="utf-8")))
        if not (np.isfinite(mine) and np.isfinite(theirs) and abs(mine - theirs) <= _TOL):
            raise AssertionError(
                f"ranking reconciliation failed for {tradition}: "
                f"recomputed={mine!r} != shard={theirs!r} (Δ={mine - theirs:.2e})"
            )


def _assert_ci_points_reconcile(ranking: dict[str, float], cis: dict) -> None:
    """The bootstrap central estimate per tradition must equal the canonical mean-of-means to
    ≤1e-9 — otherwise the CI would be drawn around a different point than the ranked score.
    (Holds exactly for the uniform grid: per-scenario means average to the cell mean.)"""
    for tradition, mine in ranking.items():
        boot_pt = cis[tradition]["overall"]["point"]
        # ``not (… <= tol)`` (not ``> tol``) so a nan on either side fails loud rather than passing.
        if not (np.isfinite(mine) and np.isfinite(boot_pt) and abs(mine - boot_pt) <= _TOL):
            raise AssertionError(
                f"CI point vs ranking mismatch for {tradition}: ranking={mine!r} "
                f"!= bootstrap_point={boot_pt!r} (Δ={mine - boot_pt:.2e})"
            )


# ── Opus-vs-Gemini agreement (protestant-unified) ─────────────────────────────────


def _agreement_pu(root: str) -> tuple[dict, np.ndarray, np.ndarray]:
    """Opus-vs-Gemini agreement over every protestant-unified cell BOTH judges scored.

    Reads the raw per-judge rows from ``root`` (the 20260904-protestant-unified run),
    pairs Gemini vs Opus on (subject, scenario_id, pressure, framing, scope), and reports
    Pearson r, bias = mean(Opus − Gemini), the within-±0.5 fraction, the exact-match
    fraction, and n (paired cells). Also returns the paired (Gemini, Opus) arrays for the figure."""
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
    if g.std() == 0 or o.std() == 0:
        r = float("nan")
    else:
        r = float(np.corrcoef(o, g)[0, 1])
    summary = {
        "n": n,
        "pearson_r": r,
        "bias_opus_minus_gemini": float(diff.mean()),
        "within_half_fraction": float(np.mean(np.abs(diff) <= 0.5)),
        "exact_match_fraction": float(np.mean(diff == 0.0)),
    }
    return summary, g, o


def _fig_judge_agreement(gem: np.ndarray, opus: np.ndarray, summary: dict,
                         out_dir: Path, formats: list[str]) -> list[Path]:
    """A 5×5 score-agreement heatmap (Gemini × Opus) over every protestant-unified cell both
    judges scored, with the equal-score diagonal and the r/bias/within-0.5 annotation. The scale
    is discrete (−1…+1 in 0.5 steps), so the honest representation is a count grid, not a scatter.
    matplotlib only (house style)."""
    import matplotlib.pyplot as plt

    _apply_house_style()
    scale = [-1.0, -0.5, 0.0, 0.5, 1.0]
    pos = {v: i for i, v in enumerate(scale)}

    def snap(x: float) -> float:
        return round(x * 2) / 2  # nearest half-step; scores are already on-scale

    counts = np.zeros((5, 5))  # rows = Opus, cols = Gemini
    for g_, o_ in zip(gem, opus):
        counts[pos[snap(float(o_))], pos[snap(float(g_))]] += 1

    fig, ax = plt.subplots(figsize=(5.4, 4.8))
    im = ax.imshow(counts, origin="lower", cmap="Greens", aspect="equal")
    thresh = counts.max() * 0.5
    for i in range(5):
        for j in range(5):
            c = int(counts[i, j])
            if c:
                ax.text(j, i, str(c), ha="center", va="center", fontsize=8,
                        color=("white" if counts[i, j] > thresh else "#222222"))
    ax.plot([-0.5, 4.5], [-0.5, 4.5], color="#c0392b", lw=1.0, ls="--", zorder=3)  # equal-score line
    ax.set_xticks(range(5)); ax.set_xticklabels([f"{v:+.1f}" for v in scale])
    ax.set_yticks(range(5)); ax.set_yticklabels([f"{v:+.1f}" for v in scale])
    ax.set_xlabel("Gemini 3.6 Flash score")
    ax.set_ylabel("Claude Opus 4.8 score")
    ax.set_title(
        f"protestant-unified judge agreement (n={summary['n']})\n"
        f"r={summary['pearson_r']:.3f}, bias={summary['bias_opus_minus_gemini']:+.3f}, "
        f"within ±0.5 = {summary['within_half_fraction']:.1%}"
    )
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="cells")
    fig.tight_layout()
    return saveboth(fig, out_dir, "judge_agreement", formats)


# ── Per-tradition ranked figure (mean + 95% CI) ────────────────────────────────────


def _fig_tradition_ranking(ranked_table: list[dict], out_dir: Path, formats: list[str]) -> list[Path]:
    """Horizontal ranked figure of the 8 tradition combined means with 95% CI error bars;
    protestant-unified is marked. matplotlib only (house style), no hand-rolled SVG/HTML."""
    import matplotlib.pyplot as plt

    _apply_house_style()
    rows = list(reversed(ranked_table))  # highest at top
    labels = [r["tradition"] for r in rows]
    pts = [r["ranking_mean_of_means"] for r in rows]
    los = [r["ranking_mean_of_means"] - r["ci_lo"] for r in rows]
    his = [r["ci_hi"] - r["ranking_mean_of_means"] for r in rows]
    ys = list(range(len(rows)))

    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    ax.axvline(0.0, color="#999999", lw=0.8, zorder=1)
    for y, r in zip(ys, rows):
        color = band_color(r["ranking_mean_of_means"])
        ax.errorbar(
            r["ranking_mean_of_means"], y, xerr=[[r["ranking_mean_of_means"] - r["ci_lo"]],
                                                 [r["ci_hi"] - r["ranking_mean_of_means"]]],
            fmt="o", color=color, ecolor="#888888", elinewidth=1.1, capsize=3, ms=8,
            markeredgecolor=("black" if r["tradition"] == PU else color),
            markeredgewidth=(1.6 if r["tradition"] == PU else 0.0), zorder=3,
        )
    ax.set_yticks(ys)
    ax.set_yticklabels([f"{r['rank']}. {lab}" + (" (this work)" if r["tradition"] == PU else "")
                        for r, lab in zip(rows, labels)])
    ax.set_xlim(-1.0, 1.0)
    ax.set_xlabel("Combined two-judge mean (−1…+1; 0 = neutral), 95% CI")
    ax.set_title("Cross-tradition ranking — combined two-judge mean")
    fig.tight_layout()
    return saveboth(fig, out_dir, "tradition_ranking", formats)


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
    cis: dict,
    agreement: dict,
    monolith: float | None,
    roots: list[str],
    results_dir: Path,
) -> dict:
    agg_by = {a.tradition: a for a in aggregates}
    st_by = {s.tradition: s for s in stats}

    # Ranked table (descending ranking score), each row carrying its 95% CI.
    ranked = sorted(ranking.items(), key=lambda kv: kv[1], reverse=True)
    ranked_table = [
        {
            "tradition": t,
            "ranking_mean_of_means": v,
            "ci_lo": cis[t]["overall"]["lo"],
            "ci_hi": cis[t]["overall"]["hi"],
            "rank": i,
        }
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
            "ranking_ci": cis[t]["overall"],
            "per_framing_ci": cis[t]["per_framing"],
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
            "roots": roots,
            "results_dir": str(results_dir),
            "ranking_rule": "mean_of_judges",
            "ranking_score": (
                "equal-weight mean over subjects x framings of combined by_framing[full] "
                "(scope=full, pressure=all)"
            ),
            "ci_method": "95% percentile scenario-cluster bootstrap (analysis.paper_bundle)",
            "n_boot": _N_BOOT,
            "seed": _SEED,
            "subjects": list(CANONICAL_SUBJECTS),
            "framings": list(FRAMINGS),
            "monolith_20260813_combined_mean_of_means": monolith,
        },
        "ranked_table": ranked_table,
        "per_tradition": per_tradition,
        "protestant_unified_steadfastness": pu_steadfastness,
        "protestant_unified_judge_agreement": agreement,
    }


@app.command()
def main(
    roots: list[str] = typer.Option(
        DEFAULT_ROOTS, "--root", "-r",
        help="Judging-run roots in load-bearing order (default: the 5 Spec-119 roots).",
    ),
    results_dir: str = typer.Option(
        DEFAULT_RESULTS_DIR, "--results-dir",
        help="Committed score tier to reconcile against (default: results/20260905).",
    ),
) -> None:
    """Build combined aggregates/stats, reconcile with the committed tier, and write outputs."""
    roots = list(roots)
    results_path = Path(results_dir)

    typer.echo(f"Building combined runs over {len(roots)} roots ...")
    runs = build_combined_runs(roots)
    aggregates = [aggregate_tradition(r) for r in runs]
    stats = [compute_tradition_stats(a) for a in aggregates]
    typer.echo(f"  traditions: {[a.tradition for a in aggregates]}")

    ranking = {a.tradition: _ranking_mean_of_means(a) for a in aggregates}

    typer.echo("Reconciliation assertions ...")
    _assert_reconciliation(aggregates, roots, ranking, results_path)
    typer.echo("  OK: subj_overall (aggregates == results-export mean-of-means) <= 1e-9")
    typer.echo("  OK: per-tradition ranking (recomputed == committed shard combined) <= 1e-9")

    typer.echo("Per-tradition scenario-cluster bootstrap CIs (canonical method) ...")
    cis = _tradition_cis(roots)
    _assert_ci_points_reconcile(ranking, cis)
    typer.echo("  OK: bootstrap central estimate == canonical mean-of-means <= 1e-9 (all 8)")

    typer.echo("Opus-vs-Gemini agreement (protestant-unified) ...")
    agreement, agree_gem, agree_opus = _agreement_pu(roots[-1])

    monolith = _monolith_mean_of_means()
    if monolith is not None:
        typer.echo(f"  monolith (20260813-protestantism) combined mean-of-means: {monolith:+.4f}")

    _OUT.mkdir(parents=True, exist_ok=True)

    # combined_stats.json — written HERE (canonical build_combined_stats) so data/output is
    # fully reproducible from analyze.py, not from a separate `analysis combined-stats` call.
    combined_stats = build_combined_stats(roots)
    (_OUT / "combined_stats.json").write_text(
        json.dumps(combined_stats, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    typer.echo(f"  wrote {_OUT / 'combined_stats.json'}")

    paper_numbers = _build_paper_numbers(
        aggregates, stats, ranking, cis, agreement, monolith, roots, results_path
    )
    out_path = _OUT / "paper_numbers.json"
    out_path.write_text(json.dumps(paper_numbers, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    typer.echo(f"  wrote {out_path}")

    typer.echo("Emitting figures (pdf, png) ...")
    figures = emit_figures(aggregates, stats, _OUT / "figures", ["pdf", "png"])
    figures += _fig_tradition_ranking(paper_numbers["ranked_table"], _OUT / "figures", ["pdf", "png"])
    figures += _fig_judge_agreement(agree_gem, agree_opus, agreement, _OUT / "figures", ["pdf", "png"])
    for f in figures:
        typer.echo(f"  wrote {f}")

    # ── Concise stdout summary ────────────────────────────────────────────────────
    typer.echo("\n=== Ranked leaderboard (combined two-judge mean_of_judges, 95% CI) ===")
    for row in paper_numbers["ranked_table"]:
        marker = "  <-- protestant-unified" if row["tradition"] == PU else ""
        typer.echo(
            f"  {row['rank']}. {row['tradition']:<22} {row['ranking_mean_of_means']:+.4f} "
            f"[{row['ci_lo']:+.4f}, {row['ci_hi']:+.4f}]{marker}"
        )
    if monolith is not None:
        typer.echo(f"  (monolith 20260813-protestantism, combined: {monolith:+.4f} — different scenario set)")

    pu_pf = paper_numbers["per_tradition"][PU]["per_framing_combined"]["framing_mean_over_subjects"]
    pu_pfci = paper_numbers["per_tradition"][PU]["per_framing_ci"]
    typer.echo("\n=== protestant-unified per-framing combined mean (over subjects), 95% CI ===")
    for fr in FRAMINGS:
        c = pu_pfci[fr]
        typer.echo(f"  {fr:<9} {pu_pf[fr]:+.4f} [{c['lo']:+.4f}, {c['hi']:+.4f}]")

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
