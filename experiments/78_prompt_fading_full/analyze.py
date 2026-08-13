"""Experiment 78 — analysis (pre-registered).

Reads the full-corpus fading judgments (data/output/<tradition>/judgments.jsonl), computes the
pre-registered estimands with scenario-clustered bootstrap 95% CIs, applies the locked decision rules
(tau=0.15), and writes a summary + figures. Numeric scores only; no band names.

Two arms (exp-78): subject=arm in {A1 (base gemma + guide.md as system), B (mb-sft-dpo + the stated
sentence as system)}; framing=level in {L0..L3}. Unit: per-scenario score = mean of its (<=6) full-
scope pressure cells, per (arm, level). Per-arm fading slope = mean over scenarios of the per-scenario
OLS slope of score on level (0..3). Inference resamples SCENARIOS with replacement (the clustering
unit), per the pre-registration — claims rest on CI position vs 0 and vs tau, not point estimates.

Pre-registered estimands:
  1. slope_A1, slope_B (pooled) + headline diff = slope_A1 - slope_B.
  2. Per-tradition slope_A1 (POWERED: RC n=76, sunni n=140) with within-tradition bootstrap CIs.
  3. Per-tradition L0 lift = A1@L0 - base-unstated(#53) reference (the "sunni guided-floor" question).
  4. Normative-vs-non-normative contrast on slope_A1 (normative = sunni-islam, roman-catholicism,
     judaism; EC sensitivity reported both ways).
  5. stated-B (78) vs unstated-B (#76) on the shared scenarios (reads #76's committed per_scenario_76.csv).

Run:
  uv --project workflows/analysis run python experiments/78_prompt_fading_full/analyze.py
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import typer

app = typer.Typer(add_completion=False)

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
LEVELS = {"L0": 0, "L1": 1, "L2": 2, "L3": 3}
ARMS = ["A1", "B"]
TAU = 0.15
SEED = 3446
NBOOT = 2000

# Pre-registered normative set (Waleed's standing term for the binding-claims tier). EC (Orthodoxy)
# is borderline — the normative contrast is reported with EC in each bucket (sensitivity).
NORMATIVE = {"sunni-islam", "roman-catholicism", "judaism"}
NONNORMATIVE = {"buddhism", "taoism", "secular-sage", "eastern-christianity"}


# --------------------------------------------------------------------------- load
def load_judgments(data_dir: Path) -> list[dict]:
    """Load full-scope judgments across all traditions. Overlays judgments_v2 by key if present
    (a no-op under a single judge). subject=arm, framing=level."""
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
                if j["subject"] not in ARMS:
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
    acc: dict[tuple, dict[int, list[float]]] = defaultdict(lambda: defaultdict(list))
    scen_trad: dict[str, str] = {}
    for r in recs:
        acc[(r["arm"], r["scenario"])][r["level"]].append(r["score"])
        scen_trad[r["scenario"]] = r["tradition"]
    cell: dict[tuple, dict[int, float]] = {}
    for k, bylv in acc.items():
        cell[k] = {lv: float(np.mean(v)) for lv, v in bylv.items()}
    return cell, scen_trad


# --------------------------------------------------------------------------- slopes
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


def arm_level_mean(cell, arm, level, scens):
    vals = [cell[(arm, sc)][level] for sc in scens if (arm, sc) in cell and level in cell[(arm, sc)]]
    return float(np.mean(vals)) if vals else float("nan")


def estimands(cell, scens) -> dict:
    d = {}
    for a in ARMS:
        d[f"slope_{a}"] = arm_slope(cell, a, scens)
        d[f"tot_{a}"] = 3.0 * d[f"slope_{a}"]
        d[f"L0_{a}"] = arm_level_mean(cell, a, 0, scens)
    d["diff_A1_minus_B"] = d["slope_A1"] - d["slope_B"]
    return d


def bootstrap_ci(func, scens, nboot=NBOOT, seed=SEED):
    """Generic scenario-clustered bootstrap: func(sample_scens) -> dict of scalars."""
    rng = np.random.default_rng(seed)
    scens = list(scens)
    keys = list(func(scens).keys())
    draws = {k: [] for k in keys}
    for _ in range(nboot):
        samp = list(rng.choice(scens, size=len(scens), replace=True))
        e = func(samp)
        for k in keys:
            draws[k].append(e[k])
    ci = {}
    for k in keys:
        arr = np.array(draws[k], dtype=float)
        arr = arr[~np.isnan(arr)]
        ci[k] = (float(np.percentile(arr, 2.5)), float(np.percentile(arr, 97.5))) if len(arr) else (float("nan"), float("nan"))
    return ci


def ci_excludes_zero(ci):
    return (ci[0] > 0 and ci[1] > 0) or (ci[0] < 0 and ci[1] < 0)


# --------------------------------------------------------------------------- L0 reference (#53)
def base_unstated_by_scenario() -> dict[str, float]:
    """Cross-run L0 anchor: base-gemma unstated(full) per scenario, from #53's committed
    per_scenario.csv (column `base`). A DIFFERENT run — approximate external anchor, not a within-
    experiment floor."""
    csvp = REPO_ROOT / "experiments" / "53_exposure_stratified_holdout" / "data" / "output" / "per_scenario.csv"
    out: dict[str, float] = {}
    if not csvp.exists():
        return out
    for r in csv.DictReader(csvp.open()):
        sid = r.get("scenario_id")
        b = r.get("base")
        if sid and b not in (None, ""):
            try:
                out[sid] = float(b)
            except ValueError:
                pass
    return out


# --------------------------------------------------------------------------- #76 cross-run B
def exp76_unstated_B() -> dict[tuple[str, int], float]:
    """#76 unstated-B per (scenario, level) from the committed per_scenario_76.csv (arm B)."""
    csvp = REPO_ROOT / "experiments" / "76_prompt_fading" / "data" / "output" / "per_scenario_76.csv"
    out: dict[tuple[str, int], float] = {}
    if not csvp.exists():
        return out
    for r in csv.DictReader(csvp.open()):
        if r.get("arm") == "B":
            out[(r["scenario"], int(r["level"]))] = float(r["score"])
    return out


# --------------------------------------------------------------------------- verdicts
def verdicts(pt, ci, l0lift, l0lift_ci) -> list[str]:
    out = []
    # H1 prompted fade (A1)
    s, t = pt["slope_A1"], pt["tot_A1"]
    cs, ct = ci["slope_A1"], ci["tot_A1"]
    fade = ci_excludes_zero(cs) and s < 0 and (-t) >= TAU
    out.append(f"H1 A1 fade: slope {s:+.3f} CI[{cs[0]:+.3f},{cs[1]:+.3f}] tot {t:+.3f} "
               f"CI[{ct[0]:+.3f},{ct[1]:+.3f}] -> {'FADING CONFIRMED' if fade else 'significant but sub-tau' if ci_excludes_zero(cs) and s<0 else 'no fading'}")
    # H2 immunity (B)
    tB, cB = pt["tot_B"], ci["tot_B"]
    immune = abs(tB) < TAU and cB[0] > -TAU and cB[1] < TAU
    out.append(f"H2 B immunity: tot {tB:+.3f} CI[{cB[0]:+.3f},{cB[1]:+.3f}] "
               f"-> {'IMMUNITY CONFIRMED (flat within +/-0.15)' if immune else 'NOT equivalence-flat'}")
    # H3 differential (headline)
    d, cd = pt["diff_A1_minus_B"], ci["diff_A1_minus_B"]
    h3 = ci_excludes_zero(cd) and d < 0
    out.append(f"H3 diff A1-B (headline): {d:+.3f} CI[{cd[0]:+.3f},{cd[1]:+.3f}] "
               f"-> {'DIFFERENTIAL CONFIRMED (prompted fades faster)' if h3 else 'no differential'}")
    # Manipulation check (pooled L0 lift of A1 vs #53 base-unstated)
    out.append("\nL0 manipulation check (A1 must lift above the base-unstated floor when adjacent):")
    la, cla = l0lift["A1"], l0lift_ci["A1"]
    lb, clb = l0lift["B"], l0lift_ci["B"]
    out.append(f"  A1@L0 lift vs #53 base-unstated = {la:+.3f} CI[{cla[0]:+.3f},{cla[1]:+.3f}]"
               f"{' >= 0.15 PASS' if la >= TAU else ' < 0.15'}  (cross-run anchor, approximate)")
    out.append(f"  B@L0  lift vs #53 base-unstated = {lb:+.3f} CI[{clb[0]:+.3f},{clb[1]:+.3f}]")
    return out


# --------------------------------------------------------------------------- main
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
    trads = sorted(set(scen_trad.values()))
    n_by_arm = {a: sum(1 for sc in scens if (a, sc) in cell) for a in ARMS}
    print(f"judgments: {len(recs)} | scenarios: {len(scens)} | traditions: {len(trads)}")
    print(f"scenarios covered per arm: {n_by_arm}")

    base53 = base_unstated_by_scenario()

    # ---- pooled estimands + CIs ----
    pt = estimands(cell, scens)
    ci = bootstrap_ci(lambda s: estimands(cell, s), scens, nboot=nboot)

    # ---- L0 lift vs #53 (pooled), per arm ----
    def l0lift_fn(sample_scens) -> dict:
        out = {}
        for a in ARMS:
            diffs = [cell[(a, sc)][0] - base53[sc]
                     for sc in sample_scens
                     if (a, sc) in cell and 0 in cell[(a, sc)] and sc in base53]
            out[a] = float(np.mean(diffs)) if diffs else float("nan")
        return out
    l0lift = l0lift_fn(scens)
    l0lift_ci = bootstrap_ci(l0lift_fn, scens, nboot=nboot)

    print("\n=== POOLED ESTIMANDS + 95% scenario-clustered bootstrap CIs ===")
    for k in ["slope_A1", "slope_B", "diff_A1_minus_B", "tot_A1", "tot_B", "L0_A1", "L0_B"]:
        c = ci[k]
        print(f"  {k:20s} {pt[k]:+.4f}  CI[{c[0]:+.4f}, {c[1]:+.4f}]")

    print("\n=== PRE-REGISTERED VERDICTS (tau=0.15) ===")
    for line in verdicts(pt, ci, l0lift, l0lift_ci):
        print(line)

    # ---- per-tradition (POWERED) slopes + L0 lift, within-tradition bootstrap ----
    print("\n=== per-tradition slopes + L0 lift (within-tradition scenario bootstrap) ===")
    per_trad = {}
    for t in trads:
        ts = [sc for sc in scens if scen_trad[sc] == t]

        def trad_fn(sample, ts_arms=ARMS):
            e = {f"slope_{a}": arm_slope(cell, a, sample) for a in ts_arms}
            e["diff_A1_minus_B"] = e["slope_A1"] - e["slope_B"]
            e["A1_L0lift"] = float(np.mean([cell[("A1", sc)][0] - base53[sc]
                                            for sc in sample
                                            if ("A1", sc) in cell and 0 in cell[("A1", sc)] and sc in base53]) or float("nan")) \
                if any(("A1", sc) in cell and sc in base53 for sc in sample) else float("nan")
            return e
        ept = trad_fn(ts)
        eci = bootstrap_ci(trad_fn, ts, nboot=nboot)
        per_trad[t] = {"n": len(ts), "point": ept, "ci": {k: list(v) for k, v in eci.items()},
                       "normative": t in NORMATIVE}
        cA1 = eci["slope_A1"]
        print(f"  {t:22s} n={len(ts):3d}  slope_A1 {ept['slope_A1']:+.3f} CI[{cA1[0]:+.3f},{cA1[1]:+.3f}]"
              f"  slope_B {ept['slope_B']:+.3f}  L0lift {ept['A1_L0lift']:+.3f}"
              f"  {'[normative]' if t in NORMATIVE else ''}")

    # ---- normative vs non-normative contrast on slope_A1 (EC both ways) ----
    print("\n=== normative vs non-normative contrast on slope_A1 ===")
    def contrast(norm_set):
        norm_scens = [sc for sc in scens if scen_trad[sc] in norm_set]
        non_scens = [sc for sc in scens if scen_trad[sc] not in norm_set]
        return norm_scens, non_scens

    def contrast_point_ci(norm_set, tag):
        norm_scens, non_scens = contrast(norm_set)
        point = arm_slope(cell, "A1", norm_scens) - arm_slope(cell, "A1", non_scens)
        rng = np.random.default_rng(SEED)
        draws = []
        for _ in range(nboot):
            ns = list(rng.choice(norm_scens, size=len(norm_scens), replace=True))
            xs = list(rng.choice(non_scens, size=len(non_scens), replace=True))
            draws.append(arm_slope(cell, "A1", ns) - arm_slope(cell, "A1", xs))
        lo, hi = float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))
        print(f"  {tag:32s} slope_A1(norm) - slope_A1(non) = {point:+.3f} CI[{lo:+.3f},{hi:+.3f}]"
              f" -> {'more fade in normative' if (lo<0 and hi<0) else 'no clear contrast'}")
        return {"point": point, "ci": [lo, hi], "normative_set": sorted(norm_set)}
    contrast_main = contrast_point_ci(NORMATIVE, "NORMATIVE={sunni,RC,judaism}")
    contrast_ec = contrast_point_ci(NORMATIVE | {"eastern-christianity"}, "+ EC in normative (sensitivity)")

    # ---- stated-B (78) vs unstated-B (#76) on shared scenarios ----
    print("\n=== stated-B (78) vs unstated-B (#76), shared scenarios ===")
    b76 = exp76_unstated_B()
    shared = sorted({sc for (sc, _lv) in b76} & {sc for (a, sc) in cell if a == "B"})
    stated_vs_unstated = {"n_shared": len(shared), "per_level": {}, "slope_delta": None}
    if shared:
        for lv in range(4):
            d78 = [cell[("B", sc)][lv] for sc in shared if ("B", sc) in cell and lv in cell[("B", sc)]]
            d76 = [b76[(sc, lv)] for sc in shared if (sc, lv) in b76]
            if d78 and d76:
                delta = float(np.mean(d78) - np.mean(d76))
                stated_vs_unstated["per_level"][f"L{lv}"] = {"78_stated_B": float(np.mean(d78)),
                                                             "76_unstated_B": float(np.mean(d76)),
                                                             "delta": delta}
                print(f"  L{lv}: 78 stated-B {np.mean(d78):+.3f}  76 unstated-B {np.mean(d76):+.3f}  Δ {delta:+.3f}")
        # paired per-scenario slope delta with scenario bootstrap
        def slope76(sc):
            pts = {lv: b76[(sc, lv)] for lv in range(4) if (sc, lv) in b76}
            if len(pts) < 2:
                return None
            xs = np.array(sorted(pts)); ys = np.array([pts[x] for x in xs])
            return float(np.polyfit(xs, ys, 1)[0])
        def slope_delta_fn(sample):
            ds = []
            for sc in sample:
                s78 = per_scenario_slope(cell, "B", sc); s76 = slope76(sc)
                if s78 is not None and s76 is not None:
                    ds.append(s78 - s76)
            return {"slope_delta": float(np.mean(ds)) if ds else float("nan")}
        sd = slope_delta_fn(shared)["slope_delta"]
        sdci = bootstrap_ci(slope_delta_fn, shared, nboot=nboot)["slope_delta"]
        stated_vs_unstated["slope_delta"] = {"point": sd, "ci": list(sdci)}
        print(f"  slope Δ (78 stated-B − 76 unstated-B) over {len(shared)} shared scen = {sd:+.4f} "
              f"CI[{sdci[0]:+.4f},{sdci[1]:+.4f}]")
    else:
        print("  (no shared scenarios / #76 CSV unavailable)")

    # ---- curve for the figure ----
    curve = {a: {lv: arm_level_mean(cell, a, lv, scens) for lv in range(4)} for a in ARMS}

    summary = {
        "n_judgments": len(recs), "n_scenarios": len(scens), "n_traditions": len(trads),
        "tau": TAU, "nboot": nboot, "seed": SEED,
        "arms": ARMS, "scenarios_per_arm": n_by_arm,
        "point": pt, "ci": {k: list(v) for k, v in ci.items()},
        "l0_lift_vs_base53": l0lift, "l0_lift_ci": {k: list(v) for k, v in l0lift_ci.items()},
        "curve": curve,
        "per_tradition": per_trad,
        "normative_contrast": {"main": contrast_main, "ec_in_normative": contrast_ec},
        "stated_B_vs_76_unstated_B": stated_vs_unstated,
    }
    out_json = data_dir / "summary_78.json"
    out_json.write_text(json.dumps(summary, indent=2) + "\n")
    print(f"\nwrote {out_json}")

    # per-scenario CSV
    csv_path = data_dir / "per_scenario_78.csv"
    with csv_path.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["tradition", "scenario", "arm", "level", "score"])
        for (a, sc), bylv in sorted(cell.items()):
            for lv, v in sorted(bylv.items()):
                w.writerow([scen_trad[sc], sc, a, lv, f"{v:.4f}"])
    print(f"wrote {csv_path}")

    if figures:
        _figures(cell, scens, scen_trad, curve, data_dir, nboot)


def _level_ci(cell, arm, level, scens, nboot, seed=SEED):
    rng = np.random.default_rng(seed + level + (0 if arm == "A1" else 500))
    scens = list(scens)
    draws = [arm_level_mean(cell, arm, level, list(rng.choice(scens, size=len(scens), replace=True)))
             for _ in range(nboot)]
    draws = np.array(draws)
    return float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))


def _figures(cell, scens, scen_trad, curve, data_dir, nboot):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    colors = {"A1": "#1f77b4", "B": "#d62728"}
    labels = {"A1": "A1 prompted-guide (base + guide.md)", "B": "B stated-weights (dpo + stated)"}
    xs = np.arange(4)

    fig, ax = plt.subplots(figsize=(7, 5))
    for a in ARMS:
        ys = np.array([curve[a][lv] for lv in range(4)])
        los, his = zip(*[_level_ci(cell, a, lv, scens, min(nboot, 800)) for lv in range(4)])
        ax.plot(xs, ys, "-o", color=colors[a], label=labels[a])
        ax.fill_between(xs, los, his, color=colors[a], alpha=0.15)
    ax.set_xticks(xs)
    ax.set_xticklabels(["L0\n(adjacent)", "L1\n~1k", "L2\n~4k", "L3\n~12k"])
    ax.set_xlabel("framing→dilemma separation (fluff tokens)")
    ax.set_ylabel("counsel score (−1…+1, full scope)")
    ax.set_title(f"Experiment 78 — prompt fading vs stated-weights immunity\n"
                 f"(mean over {len(scens)} scenarios; bands = 95% scenario-bootstrap CI)")
    ax.axhline(0, color="grey", lw=0.6)
    ax.legend()
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(data_dir / f"fig_fading_78.{ext}", dpi=150)
    plt.close(fig)

    trads = sorted(set(scen_trad.values()))
    fig, axes = plt.subplots(2, 4, figsize=(15, 7), sharex=True, sharey=True)
    for i, t in enumerate(trads):
        ax = axes.flat[i]
        ts = [sc for sc in scens if scen_trad[sc] == t]
        for a in ARMS:
            ys = [arm_level_mean(cell, a, lv, ts) for lv in range(4)]
            ax.plot(xs, ys, "-o", color=colors[a], label=labels[a], ms=3)
        tag = " [norm]" if t in NORMATIVE else ""
        ax.set_title(f"{t}{tag} (n={len(ts)})", fontsize=9)
        ax.axhline(0, color="grey", lw=0.5)
    for j in range(len(trads), len(axes.flat)):
        axes.flat[j].axis("off")
    axes.flat[0].legend(fontsize=6)
    fig.suptitle("Experiment 78 — score vs separation, per tradition (full corpus)")
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(data_dir / f"fig_fading_78_by_tradition.{ext}", dpi=150)
    plt.close(fig)
    print(f"wrote {data_dir}/fig_fading_78.pdf|png and fig_fading_78_by_tradition.pdf|png")


if __name__ == "__main__":
    app()
