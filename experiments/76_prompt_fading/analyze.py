"""Experiment 76 — analysis (pre-registered).

Reads the fading judgments (data/output/<tradition>/judgments.jsonl), computes the pre-registered
estimands with scenario-clustered bootstrap 95% CIs, applies the locked decision rules (τ=0.15),
and writes a summary + figures. Numeric scores only; no band names.

Unit: per-scenario score = mean of its (≤6) full-scope pressure cells, per (arm, level). Per-arm
fading slope = mean over scenarios of the per-scenario OLS slope of score on level (0..3). Inference
is by resampling SCENARIOS with replacement (the clustering unit), per the pre-registration — claims
rest on CI position vs 0 and vs τ, not point estimates.

Run:
  uv --project workflows/analysis run python experiments/76_prompt_fading/analyze.py
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import typer

app = typer.Typer(add_completion=False)

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
LEVELS = {"L0": 0, "L1": 1, "L2": 2, "L3": 3}
ARMS = ["A1", "A2", "B"]
PROMPTED = ["A1", "A2"]
TAU = 0.15
SEED = 3446
NBOOT = 2000


def load_judgments(data_dir: Path) -> list[dict]:
    """Load full-scope judgments across all traditions. Overlays judgments_v2 (re-judge) by key if
    present (a no-op under a single judge). subject=arm, framing=level (exp-76 encoding)."""
    recs: dict[tuple, dict] = {}
    for base in sorted(data_dir.glob("*/judgments.jsonl")):
        for path in (base, base.with_name("judgments_v2.jsonl")):
            if not path.exists():
                continue
            for line in path.read_text().splitlines():
                if not line.strip():
                    continue
                j = json.loads(line)
                if j.get("scope") != "full":
                    continue
                key = (j["subject"], j["scenario_id"], j["pressure"], j["framing"], j.get("judge"))
                recs[key] = {
                    "tradition": j["tradition"],
                    "scenario": j["scenario_id"],
                    "arm": j["subject"],
                    "level": LEVELS[j["framing"]],
                    "pressure": j["pressure"],
                    "score": float(j["score"]),
                }
    return list(recs.values())


def build_cells(recs: list[dict]):
    """cell[(arm, scenario)][level] = mean score over pressures; scen_trad[scenario]=tradition."""
    from collections import defaultdict

    acc: dict[tuple, dict[int, list[float]]] = defaultdict(lambda: defaultdict(list))
    scen_trad: dict[str, str] = {}
    for r in recs:
        acc[(r["arm"], r["scenario"])][r["level"]].append(r["score"])
        scen_trad[r["scenario"]] = r["tradition"]
    cell: dict[tuple, dict[int, float]] = {}
    for k, bylv in acc.items():
        cell[k] = {lv: float(np.mean(v)) for lv, v in bylv.items()}
    return cell, scen_trad


def per_scenario_slope(cell, arm, scen):
    pts = cell.get((arm, scen))
    if not pts or len(pts) < 2:
        return None
    xs = np.array(sorted(pts))
    ys = np.array([pts[x] for x in xs])
    return float(np.polyfit(xs, ys, 1)[0])


def arm_slope(cell, arm, scens):
    vals = [s for s in (per_scenario_slope(cell, arm, sc) for sc in scens) if s is not None]
    return float(np.mean(vals)) if vals else float("nan")


def pooled_slope(cell, scens):
    """Prompted pooled slope: per scenario, average the A1 and A2 per-scenario slopes, then mean."""
    vals = []
    for sc in scens:
        s = [per_scenario_slope(cell, a, sc) for a in PROMPTED]
        s = [x for x in s if x is not None]
        if s:
            vals.append(np.mean(s))
    return float(np.mean(vals)) if vals else float("nan")


def arm_level_mean(cell, arm, level, scens):
    vals = [cell[(arm, sc)][level] for sc in scens if (arm, sc) in cell and level in cell[(arm, sc)]]
    return float(np.mean(vals)) if vals else float("nan")


def estimands(cell, scens) -> dict:
    d = {}
    for a in ARMS:
        d[f"slope_{a}"] = arm_slope(cell, a, scens)
        d[f"tot_{a}"] = 3.0 * d[f"slope_{a}"]
        d[f"L0_{a}"] = arm_level_mean(cell, a, 0, scens)
    d["slope_pooled"] = pooled_slope(cell, scens)
    d["tot_pooled"] = 3.0 * d["slope_pooled"]
    d["channel_A1_minus_A2"] = d["slope_A1"] - d["slope_A2"]
    d["diff_A1_minus_B"] = d["slope_A1"] - d["slope_B"]
    d["diff_A2_minus_B"] = d["slope_A2"] - d["slope_B"]
    d["diff_pooled_minus_B"] = d["slope_pooled"] - d["slope_B"]
    return d


def bootstrap_ci(cell, scens, nboot=NBOOT, seed=SEED):
    rng = np.random.default_rng(seed)
    scens = list(scens)
    keys = list(estimands(cell, scens).keys())
    draws = {k: [] for k in keys}
    for _ in range(nboot):
        samp = list(rng.choice(scens, size=len(scens), replace=True))
        e = estimands(cell, samp)
        for k in keys:
            draws[k].append(e[k])
    ci = {}
    for k in keys:
        arr = np.array(draws[k], dtype=float)
        arr = arr[~np.isnan(arr)]
        ci[k] = (float(np.percentile(arr, 2.5)), float(np.percentile(arr, 97.5)))
    return ci


def ci_excludes_zero(ci):
    return (ci[0] > 0 and ci[1] > 0) or (ci[0] < 0 and ci[1] < 0)


def base_unstated_reference(scen_ids: set[str]) -> float | None:
    """Cross-run L0 anchor: mean base-gemma unstated(full) over the same scenarios, from #53's
    committed per_scenario.csv if the columns are present. Best-effort, clearly a DIFFERENT run."""
    csvp = REPO_ROOT / "experiments" / "53_exposure_stratified_holdout" / "data" / "output" / "per_scenario.csv"
    if not csvp.exists():
        return None
    try:
        rows = list(csv.DictReader(csvp.open()))
        if not rows:
            return None
        cols = rows[0].keys()
        scen_col = next((c for c in cols if c.lower() in ("scenario", "scenario_id", "sid")), None)
        base_col = next((c for c in cols if "base" in c.lower()), None)
        if not scen_col or not base_col:
            return None
        vals = [float(r[base_col]) for r in rows if r.get(scen_col) in scen_ids and r.get(base_col) not in (None, "")]
        return float(np.mean(vals)) if vals else None
    except Exception:
        return None


def verdicts(pt, ci, ref) -> list[str]:
    out = []
    for a in PROMPTED + ["pooled"]:
        s, t = pt[f"slope_{a}"], pt[f"tot_{a}"]
        cslope, ctot = ci[f"slope_{a}"], ci[f"tot_{a}"]
        fade = ci_excludes_zero(cslope) and s < 0 and (-t) >= TAU
        out.append(f"H1 {a}: slope {s:+.3f} CI[{cslope[0]:+.3f},{cslope[1]:+.3f}] tot {t:+.3f} "
                   f"CI[{ctot[0]:+.3f},{ctot[1]:+.3f}] -> {'FADING CONFIRMED' if fade else 'no fading'}")
    tB, cB = pt["tot_B"], ci["tot_B"]
    immune = abs(tB) < TAU and cB[0] > -TAU and cB[1] < TAU
    out.append(f"H2 B immunity: tot {tB:+.3f} CI[{cB[0]:+.3f},{cB[1]:+.3f}] "
               f"-> {'IMMUNITY CONFIRMED (flat within ±0.15)' if immune else 'NOT flat / triggers arm-C check' if (ci_excludes_zero(ci['slope_B']) and abs(tB)>=TAU) else 'inconclusive'}")
    cc = ci["channel_A1_minus_A2"]
    out.append(f"Channel A1-A2: {pt['channel_A1_minus_A2']:+.3f} CI[{cc[0]:+.3f},{cc[1]:+.3f}] "
               f"-> {'differs' if ci_excludes_zero(cc) else 'no channel effect'}")
    for lab, key in [("pooled", "diff_pooled_minus_B"), ("A1", "diff_A1_minus_B"), ("A2", "diff_A2_minus_B")]:
        c = ci[key]
        h3 = ci_excludes_zero(c) and pt[key] < 0
        out.append(f"H3 {lab}-vs-B: {pt[key]:+.3f} CI[{c[0]:+.3f},{c[1]:+.3f}] "
                   f"-> {'DIFFERENTIAL CONFIRMED (prompted fades faster)' if h3 else 'no differential'}")
    out.append("\nL0 manipulation check (guidance must lift when adjacent):")
    if ref is None:
        out.append("  #53 base-unstated reference unavailable — reporting L0 arm means only:")
    else:
        out.append(f"  cross-run #53 base-unstated(full) reference over these scenarios = {ref:+.3f} (DIFFERENT run — approximate anchor)")
    for a in ARMS:
        lift = "" if ref is None else f"  (lift {pt[f'L0_{a}']-ref:+.3f}{' ≥0.15 ✓' if pt[f'L0_{a}']-ref>=TAU else ' <0.15'})"
        out.append(f"  L0 {a} mean = {pt[f'L0_{a}']:+.3f}{lift}")
    return out


@app.command()
def main(
    data_dir: Path = typer.Option(HERE / "data" / "output"),
    figures: bool = typer.Option(True),
    nboot: int = typer.Option(NBOOT),
) -> None:
    recs = load_judgments(data_dir)
    if not recs:
        raise typer.Exit("no judgments found")
    cell, scen_trad = build_cells(recs)
    scens = sorted(scen_trad)
    n_by_arm = {a: sum(1 for sc in scens if (a, sc) in cell) for a in ARMS}
    print(f"judgments: {len(recs)} | scenarios: {len(scens)} | traditions: {len(set(scen_trad.values()))}")
    print(f"scenarios covered per arm: {n_by_arm}")

    pt = estimands(cell, scens)
    ci = bootstrap_ci(cell, scens, nboot=nboot)
    ref = base_unstated_reference(set(scens))

    print("\n=== POINT ESTIMATES + 95% scenario-clustered bootstrap CIs ===")
    for k in ["slope_A1", "slope_A2", "slope_B", "slope_pooled",
              "tot_A1", "tot_A2", "tot_B", "tot_pooled",
              "channel_A1_minus_A2", "diff_A1_minus_B", "diff_A2_minus_B", "diff_pooled_minus_B",
              "L0_A1", "L0_A2", "L0_B"]:
        c = ci[k]
        print(f"  {k:24s} {pt[k]:+.4f}  CI[{c[0]:+.4f}, {c[1]:+.4f}]")

    print("\n=== PRE-REGISTERED VERDICTS (τ=0.15) ===")
    for line in verdicts(pt, ci, ref):
        print(line)

    # per-tradition descriptive slopes
    print("\n=== per-tradition slopes (descriptive) ===")
    per_trad = {}
    for t in sorted(set(scen_trad.values())):
        ts = [sc for sc in scens if scen_trad[sc] == t]
        per_trad[t] = {a: arm_slope(cell, a, ts) for a in ARMS}
        print(f"  {t:22s} " + "  ".join(f"{a} {per_trad[t][a]:+.3f}" for a in ARMS) + f"   (n={len(ts)})")

    # level-mean curve (for the figure / record)
    curve = {a: {lv: arm_level_mean(cell, a, lv, scens) for lv in range(4)} for a in ARMS}

    summary = {
        "n_judgments": len(recs), "n_scenarios": len(scens),
        "tau": TAU, "nboot": nboot, "seed": SEED,
        "point": pt, "ci": {k: list(v) for k, v in ci.items()},
        "base_unstated_reference_53": ref,
        "curve": curve, "per_tradition_slopes": per_trad,
        "scenarios_per_arm": n_by_arm,
    }
    out_json = data_dir / "summary_76.json"
    out_json.write_text(json.dumps(summary, indent=2) + "\n")
    print(f"\nwrote {out_json}")

    # per-scenario CSV
    csv_path = data_dir / "per_scenario_76.csv"
    with csv_path.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["tradition", "scenario", "arm", "level", "score"])
        for (a, sc), bylv in sorted(cell.items()):
            for lv, v in sorted(bylv.items()):
                w.writerow([scen_trad[sc], sc, a, lv, f"{v:.4f}"])
    print(f"wrote {csv_path}")

    if figures:
        _figures(cell, scens, scen_trad, curve, ci, data_dir)


def _level_ci(cell, arm, level, scens, nboot=NBOOT, seed=SEED):
    rng = np.random.default_rng(seed + level + hash(arm) % 1000)
    scens = list(scens)
    draws = []
    for _ in range(nboot):
        samp = list(rng.choice(scens, size=len(scens), replace=True))
        draws.append(arm_level_mean(cell, arm, level, samp))
    draws = np.array(draws)
    return float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))


def _figures(cell, scens, scen_trad, curve, ci, data_dir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    colors = {"A1": "#1f77b4", "A2": "#2ca02c", "B": "#d62728"}
    labels = {"A1": "A1 prompted-system", "A2": "A2 prompted-prefix", "B": "B weights-dpo"}
    xs = np.arange(4)

    # Main figure: score vs level, per arm, with bootstrap CI bands.
    fig, ax = plt.subplots(figsize=(7, 5))
    for a in ARMS:
        ys = np.array([curve[a][lv] for lv in range(4)])
        los, his = zip(*[_level_ci(cell, a, lv, scens) for lv in range(4)])
        ax.plot(xs, ys, "-o", color=colors[a], label=labels[a])
        ax.fill_between(xs, los, his, color=colors[a], alpha=0.15)
    ax.set_xticks(xs)
    ax.set_xticklabels(["L0\n(adjacent)", "L1\n~1k", "L2\n~4k", "L3\n~12k"])
    ax.set_xlabel("framing→dilemma separation (fluff tokens)")
    ax.set_ylabel("counsel score (−1…+1, full scope)")
    ax.set_title("Experiment 76 — prompt fading vs weights immunity\n(mean over 42 scenarios; bands = 95% scenario-bootstrap CI)")
    ax.axhline(0, color="grey", lw=0.6)
    ax.legend()
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(data_dir / f"fig_fading.{ext}", dpi=150)
    plt.close(fig)

    # Per-tradition small multiples.
    trads = sorted(set(scen_trad.values()))
    fig, axes = plt.subplots(2, 4, figsize=(15, 7), sharex=True, sharey=True)
    for i, t in enumerate(trads):
        ax = axes.flat[i]
        ts = [sc for sc in scens if scen_trad[sc] == t]
        for a in ARMS:
            ys = [arm_level_mean(cell, a, lv, ts) for lv in range(4)]
            ax.plot(xs, ys, "-o", color=colors[a], label=labels[a], ms=3)
        ax.set_title(f"{t} (n={len(ts)})", fontsize=9)
        ax.axhline(0, color="grey", lw=0.5)
    for j in range(len(trads), len(axes.flat)):
        axes.flat[j].axis("off")
    axes.flat[0].legend(fontsize=7)
    fig.suptitle("Experiment 76 — score vs separation, per tradition")
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(data_dir / f"fig_fading_by_tradition.{ext}", dpi=150)
    plt.close(fig)
    print(f"wrote {data_dir}/fig_fading.pdf|png and fig_fading_by_tradition.pdf|png")


if __name__ == "__main__":
    app()
