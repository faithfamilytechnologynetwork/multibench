"""Experiment 53: exposure-stratified pseudo-holdout memorization check.

Analysis-only, zero network. Joins base + SFT unstated/full descriptive scores with
per-scenario / per-cell SFT training exposure, computes the dose-response and a
base-score-matched exposed-vs-unexposed contrast, and emits one MB-paper-style figure.

Run:
  uv run --with pandas --with numpy --with matplotlib \
    python experiments/53_exposure_stratified_holdout/analyze.py
"""
from __future__ import annotations
import json, glob, os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(HERE, "data", "output")
os.makedirs(OUT, exist_ok=True)

BASE_GLOB = os.path.join(ROOT, "tmp/exp48-data/output/collection/*/judgments.jsonl")
SFT_GLOB  = os.path.join(ROOT, "tmp/exp48-data/output/descriptive/*/judgments.jsonl")
SFT_TRAIN = os.path.join(ROOT, "tmp/exp48-data/output/sft/sft_train_guided.jsonl")

RNG = np.random.default_rng(0)
NBOOT = 2000
TAU = 0.15          # pre-registered materiality threshold (band scale)
MIN_STRATUM = 5     # min cells per arm for a stratum to enter the matched estimate


def load_desc(glob_pat, framing="unstated", scope="full"):
    rows = []
    for p in glob.glob(glob_pat):
        for l in open(p):
            if not l.strip():
                continue
            d = json.loads(l)
            if d.get("framing") == framing and d.get("scope") == scope:
                rows.append((d["scenario_id"], d["pressure"], d["tradition"], float(d["score"])))
    return pd.DataFrame(rows, columns=["scenario_id", "pressure", "tradition", "score"])


def load_exposure():
    exposed = set()          # (scenario_id, pressure) cells in training
    per_scen = {}            # scenario_id -> exposure count 0..6
    for l in open(SFT_TRAIN):
        d = json.loads(l)
        exposed.add((d["scenario_id"], d["pressure"]))
        per_scen[d["scenario_id"]] = per_scen.get(d["scenario_id"], 0) + 1
    return exposed, per_scen


def boot_mean_ci(vals, nboot=NBOOT):
    vals = np.asarray(vals, dtype=float)
    if len(vals) == 0:
        return (np.nan, np.nan, np.nan, 0)
    idx = RNG.integers(0, len(vals), size=(nboot, len(vals)))
    means = vals[idx].mean(axis=1)
    return (float(vals.mean()), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5)), len(vals))


def main():
    base = load_desc(BASE_GLOB).rename(columns={"score": "base"})
    sft  = load_desc(SFT_GLOB).rename(columns={"score": "sft"})
    df = base.merge(sft[["scenario_id", "pressure", "sft"]], on=["scenario_id", "pressure"], how="inner")
    assert len(df) == len(base) == len(sft), f"join mismatch {len(df)} {len(base)} {len(sft)}"
    df["lift"] = df["sft"] - df["base"]

    exposed_cells, per_scen = load_exposure()
    df["exposed"] = df.apply(lambda r: (r.scenario_id, r.pressure) in exposed_cells, axis=1)
    df["scen_exposure"] = df["scenario_id"].map(lambda s: per_scen.get(s, 0))

    n_scen = df["scenario_id"].nunique()
    print(f"cells={len(df)} scenarios={n_scen} exposed_cells={df.exposed.sum()} "
          f"unexposed_cells={(~df.exposed).sum()}")
    print(f"overall: base={df.base.mean():+.3f} sft={df.sft.mean():+.3f} lift={df.lift.mean():+.3f}")

    # ---- 1. scenario-level dose-response (issue primary) ----
    scen = (df.groupby("scenario_id")
              .agg(tradition=("tradition", "first"),
                   exposure=("scen_exposure", "first"),
                   base=("base", "mean"), sft=("sft", "mean"), lift=("lift", "mean"))
              .reset_index())
    dose_rows = []
    for e in range(0, 7):
        sub = scen[scen.exposure == e]
        m, lo, hi, n = boot_mean_ci(sub["lift"].values)
        bm = sub["base"].mean() if n else np.nan
        dose_rows.append(dict(exposure=e, n_scen=n, base_mean=bm, lift=m, lo=lo, hi=hi))
    dose = pd.DataFrame(dose_rows)
    print("\n== scenario-level dose-response (raw) ==")
    print(dose.to_string(index=False,
          formatters={"base_mean": "{:+.3f}".format, "lift": "{:+.3f}".format,
                      "lo": "{:+.3f}".format, "hi": "{:+.3f}".format}))

    # ---- 2. cell-level exposed vs unexposed: raw ----
    exp_cells = df[df.exposed]; unx_cells = df[~df.exposed]
    em, elo, ehi, en = boot_mean_ci(exp_cells["lift"].values)
    um, ulo, uhi, un = boot_mean_ci(unx_cells["lift"].values)
    print(f"\n== cell-level raw ==")
    print(f"exposed   n={en:5d} lift={em:+.3f} [{elo:+.3f},{ehi:+.3f}] base={exp_cells.base.mean():+.3f}")
    print(f"unexposed n={un:5d} lift={um:+.3f} [{ulo:+.3f},{uhi:+.3f}] base={unx_cells.base.mean():+.3f}")
    print(f"raw Δ(exposed-unexposed) = {em-um:+.3f}")

    # ---- 3. base-score-matched (standardize exposed -> unexposed base-score dist) ----
    strata = sorted(df["base"].unique())
    unx_w = unx_cells["base"].value_counts(normalize=True)
    incl = [s for s in strata
            if (exp_cells.base == s).sum() >= MIN_STRATUM and (unx_cells.base == s).sum() >= MIN_STRATUM]
    print(f"\n== base-score strata (matched) ==  included={incl}")
    print(f"{'base':>6} {'n_exp':>6} {'liftE':>7} {'n_unx':>6} {'liftU':>7} {'w_unx':>6} {'diff':>7}")
    rows = []
    for s in strata:
        e = exp_cells[exp_cells.base == s]["lift"]; u = unx_cells[unx_cells.base == s]["lift"]
        w = float(unx_w.get(s, 0.0))
        diff = (e.mean() - u.mean()) if (len(e) and len(u)) else np.nan
        flag = "" if s in incl else "  (thin)"
        print(f"{s:+6.1f} {len(e):6d} {e.mean():+7.3f} {len(u):6d} {u.mean():+7.3f} {w:6.3f} "
              f"{diff:+7.3f}{flag}")
        rows.append((s, w, len(e), e.mean() if len(e) else np.nan, len(u), u.mean() if len(u) else np.nan))

    # standardized (matched) means over included strata, reweighted to unexposed dist
    wsum = sum(unx_w.get(s, 0.0) for s in incl)
    matched_exp = sum(unx_w.get(s, 0.0) * exp_cells[exp_cells.base == s]["lift"].mean() for s in incl) / wsum
    matched_unx = sum(unx_w.get(s, 0.0) * unx_cells[unx_cells.base == s]["lift"].mean() for s in incl) / wsum
    delta_matched = matched_exp - matched_unx
    frac_unx_incl = (unx_cells.base.isin(incl)).mean()
    print(f"\nmatched exposed lift  = {matched_exp:+.3f}")
    print(f"matched unexposed lift= {matched_unx:+.3f}  (unexposed mass in incl strata = {frac_unx_incl:.2%})")
    print(f"Δ_matched (exposed-unexposed, standardized) = {delta_matched:+.3f}   τ={TAU}")

    # bootstrap Δ_matched (resample cells, recompute standardization on fixed incl strata)
    eb = exp_cells[["base", "lift"]].values; ub = unx_cells[["base", "lift"]].values
    deltas = []
    for _ in range(NBOOT):
        e_s = eb[RNG.integers(0, len(eb), len(eb))]
        u_s = ub[RNG.integers(0, len(ub), len(ub))]
        w = {s: (u_s[:, 0] == s).mean() for s in incl}
        wtot = sum(w.values())
        if wtot == 0:
            continue
        me = sum(w[s] * e_s[e_s[:, 0] == s][:, 1].mean() for s in incl) / wtot
        mu = sum(w[s] * u_s[u_s[:, 0] == s][:, 1].mean() for s in incl) / wtot
        deltas.append(me - mu)
    dlo, dhi = np.percentile(deltas, [2.5, 97.5])
    print(f"Δ_matched 95% CI = [{dlo:+.3f}, {dhi:+.3f}]")

    # strict 13-scenario zero-exposure holdout fallback bound
    z = scen[scen.exposure == 0]
    zm, zlo, zhi, zn = boot_mean_ci(z["lift"].values)
    print(f"\nstrict zero-exposure holdout: n_scen={zn} lift={zm:+.3f} [{zlo:+.3f},{zhi:+.3f}] "
          f"base={z.base.mean():+.3f}")

    # ---- 4. within-tradition dose-response summary (exp0 vs exp>=5) ----
    print("\n== within-tradition: low-exposure(0-1) vs high(5-6) scenario lift ==")
    print(f"{'tradition':22} {'nLo':>4} {'liftLo':>7} {'nHi':>4} {'liftHi':>7}")
    for tr in sorted(scen.tradition.unique()):
        t = scen[scen.tradition == tr]
        lo_ = t[t.exposure <= 1]; hi_ = t[t.exposure >= 5]
        print(f"{tr:22} {len(lo_):4d} "
              f"{lo_.lift.mean() if len(lo_) else float('nan'):+7.3f} "
              f"{len(hi_):4d} {hi_.lift.mean() if len(hi_) else float('nan'):+7.3f}")

    # ---- persist tidy numbers ----
    dose.to_csv(os.path.join(OUT, "dose_response.csv"), index=False)
    scen.to_csv(os.path.join(OUT, "per_scenario.csv"), index=False)
    summary = dict(
        overall_lift=float(df.lift.mean()), overall_base=float(df.base.mean()), overall_sft=float(df.sft.mean()),
        n_cells=int(len(df)), n_scenarios=int(n_scen),
        exposed_cells=int(df.exposed.sum()), unexposed_cells=int((~df.exposed).sum()),
        raw_exposed_lift=em, raw_unexposed_lift=um, raw_delta=em - um,
        matched_exposed_lift=matched_exp, matched_unexposed_lift=matched_unx,
        delta_matched=delta_matched, delta_matched_ci=[float(dlo), float(dhi)],
        tau=TAU, included_strata=[float(s) for s in incl],
        unexposed_mass_in_incl=float(frac_unx_incl),
        zero_exposure_n_scen=int(zn), zero_exposure_lift=zm, zero_exposure_ci=[zlo, zhi],
    )
    json.dump(summary, open(os.path.join(OUT, "summary.json"), "w"), indent=2)

    make_figure(dose, scen, df, incl, unx_w, delta_matched, dlo, dhi)
    print(f"\nwrote {OUT}/{{dose_response.csv,per_scenario.csv,summary.json,fig_dose_response.png}}")
    return summary


def make_figure(dose, scen, df, incl, unx_w, delta_matched, dlo, dhi):
    """MB-paper-style: scenario-level dose-response (raw) + base-score-matched line."""
    # matched dose-response: standardize each exposure group's CELL lift to exp0 base dist
    exp0_w = df[df.scen_exposure == 0]["base"].value_counts(normalize=True)
    incl0 = [s for s in sorted(df.base.unique())
             if (df[df.scen_exposure == 0].base == s).sum() >= 1]
    matched_line = []
    for e in range(0, 7):
        g = df[df.scen_exposure == e]
        num = den = 0.0
        for s in incl0:
            w = float(exp0_w.get(s, 0.0)); gs = g[g.base == s]["lift"]
            if w > 0 and len(gs):
                num += w * gs.mean(); den += w
        matched_line.append(num / den if den else np.nan)

    plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False,
                         "figure.dpi": 150})
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    x = dose["exposure"].values
    C_RAW, C_MATCH, C_BASE = "#2b6cb0", "#c05621", "#718096"

    ax.axhline(0, color="#cbd5e0", lw=1, zorder=0)
    ax.axhline(df.lift.mean(), color=C_RAW, lw=1, ls=":", alpha=0.6, zorder=0)
    ax.annotate(f"pooled lift {df.lift.mean():+.2f}", (6, df.lift.mean()),
                xytext=(0, 4), textcoords="offset points", ha="right", fontsize=8.5, color=C_RAW)

    yerr = np.vstack([dose["lift"] - dose["lo"], dose["hi"] - dose["lift"]])
    ax.errorbar(x, dose["lift"], yerr=yerr, fmt="o-", color=C_RAW, lw=2, ms=6, capsize=3,
                label="Raw scenario lift (95% CI)", zorder=3)
    ax.plot(x, matched_line, "s--", color=C_MATCH, lw=2, ms=5,
            label="Matched to exp-0 base difficulty (does not flatten)", zorder=4)

    for xi, n in zip(x, dose["n_scen"]):
        ax.annotate(f"n={n}", (xi, -1.02), ha="center", va="top", fontsize=7.5, color="#4a5568")

    ax.set_xlabel("Training exposure  (# of scenario's 6 pressure-cells in SFT set)")
    ax.set_ylabel("base → SFT descriptive lift\n(unstated, post-pressure; band scale)")
    ax.set_title("MultiWeights descriptive lift rises with training exposure\n"
                 "(memorization check — Exp 53, gemma-4-31b, N=519 scenarios)", fontsize=11.5)
    ax.set_ylim(-1.15, 1.15); ax.set_xticks(range(0, 7))
    ax.text(0.02, 0.04,
            f"Cell-level matched Δ(exposed−unexposed) = {delta_matched:+.2f}  "
            f"95% CI [{dlo:+.2f}, {dhi:+.2f}]   (τ={TAU})",
            transform=ax.transAxes, fontsize=8.5, color="#2d3748",
            bbox=dict(boxstyle="round,pad=0.35", fc="#f7fafc", ec="#cbd5e0"))
    ax.legend(loc="upper left", fontsize=8.5, framealpha=0.9)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_dose_response.png"), bbox_inches="tight")
    fig.savefig(os.path.join(OUT, "fig_dose_response.pdf"), bbox_inches="tight")  # vector, paper convention
    plt.close(fig)


if __name__ == "__main__":
    main()
