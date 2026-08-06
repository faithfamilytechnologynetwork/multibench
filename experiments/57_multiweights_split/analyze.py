"""Experiment 57 — 50/50 scenario-holdout transfer analysis.

Joins the freshly-collected SPLIT-model unstated/full descriptive scores (per cell) with the reused
base (from #53's committed per_scenario.csv), aggregates per scenario, partitions by the committed
50/50 split, and reports the THREE-WAY comparison that is this experiment's deliverable:

  held-out transfer lift  (CI)   — the properly-measured on-bench lift on never-trained scenarios
    vs  train-half memorization-reference lift  (CI)   — same model, scenarios it trained on
    vs  #48 full-model aggregate +0.83  and  #53 zero-exposure transferable +0.22

Pre-registered decision rules (see notes.md) are applied verbatim; tau=0.15. All CIs are
scenario-clustered bootstrap (we aggregate to per-scenario first, then resample scenarios).

Analysis-only, zero network. Run:
  uv run --with pandas --with numpy --with matplotlib \
    python experiments/57_multiweights_split/analyze.py [--model sft|dpo]
"""
from __future__ import annotations

import glob
import json
import os
import sys

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(HERE, "data", "output")
os.makedirs(OUT, exist_ok=True)

BASE_CSV = os.path.join(ROOT, "experiments/53_exposure_stratified_holdout/data/output/per_scenario.csv")
SPLIT_DIR = os.path.join(HERE, "split")

RNG = np.random.default_rng(0)
NBOOT = 5000
TAU = 0.15
REF48_AGG = 0.83   # #48 full-model aggregate unstated lift (memorization-confounded)
REF53_ZERO = 0.22  # #53 strict zero-exposure transferable estimate (mostly sunni)


def load_desc_scores(model: str):
    """Per-cell unstated/full scores for the split MODEL (sft|dpo)."""
    pat = os.path.join(OUT, f"descriptive_{model}", "*", "judgments.jsonl")
    rows = []
    for p in glob.glob(pat):
        for line in open(p):
            if not line.strip():
                continue
            d = json.loads(line)
            if d.get("framing") == "unstated" and d.get("scope") == "full":
                rows.append((d["scenario_id"], d["pressure"], float(d["score"])))
    if not rows:
        sys.exit(f"no judgments found under {pat} — has the descriptive run finished?")
    df = pd.DataFrame(rows, columns=["scenario_id", "pressure", "model_score"])
    return df


def boot_mean_ci(vals, nboot=NBOOT):
    vals = np.asarray(vals, dtype=float)
    if len(vals) == 0:
        return (np.nan, np.nan, np.nan, 0)
    idx = RNG.integers(0, len(vals), size=(nboot, len(vals)))
    means = vals[idx].mean(axis=1)
    return (float(vals.mean()), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5)), len(vals))


def boot_diff_ci(a, b, nboot=NBOOT):
    """CI for mean(a) - mean(b), independent resamples (train vs holdout are disjoint scenarios)."""
    a = np.asarray(a, float); b = np.asarray(b, float)
    ia = RNG.integers(0, len(a), size=(nboot, len(a)))
    ib = RNG.integers(0, len(b), size=(nboot, len(b)))
    d = a[ia].mean(1) - b[ib].mean(1)
    return float(a.mean() - b.mean()), float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


def main():
    model = "sft"
    if "--model" in sys.argv:
        model = sys.argv[sys.argv.index("--model") + 1]

    # split labels
    train_ids = set(json.load(open(os.path.join(SPLIT_DIR, "train_scenarios.json")))["scenario_ids"])
    hold_ids = set(json.load(open(os.path.join(SPLIT_DIR, "holdout_scenarios.json")))["scenario_ids"])

    # base + #48 reference, per scenario
    ref = pd.read_csv(BASE_CSV)  # scenario_id, tradition, exposure, base, sft(=#48 full), lift(=#48)
    ref = ref.rename(columns={"sft": "sft48", "lift": "lift48"})

    # split-model per-cell -> per-scenario mean (unstated/full)
    cells = load_desc_scores(model)
    n_cells = len(cells)
    scen_model = cells.groupby("scenario_id")["model_score"].mean().rename(f"{model}_score")

    df = ref.merge(scen_model, on="scenario_id", how="left")
    missing = df[f"{model}_score"].isna().sum()
    if missing:
        print(f"WARNING: {missing} scenarios have no {model} descriptive score (incomplete run?)")
    df["split"] = df["scenario_id"].map(
        lambda s: "train" if s in train_ids else ("holdout" if s in hold_ids else "??"))
    assert (df["split"] != "??").all(), "scenario missing from split lists"
    df["lift"] = df[f"{model}_score"] - df["base"]

    hold = df[df.split == "holdout"].dropna(subset=["lift"])
    train = df[df.split == "train"].dropna(subset=["lift"])

    print(f"model={model}  cells={n_cells}  scenarios={len(df)}  "
          f"(holdout {len(hold)}, train {len(train)})")

    # ---- headline three-way ----
    hm, hlo, hhi, hn = boot_mean_ci(hold["lift"].values)
    tm, tlo, thi, tn = boot_mean_ci(train["lift"].values)
    dm, dlo, dhi = boot_diff_ci(train["lift"].values, hold["lift"].values)
    hold_post = hold[f"{model}_score"].mean()
    train_post = train[f"{model}_score"].mean()

    print("\n== THREE-WAY (this experiment's deliverable) ==")
    print(f"HELD-OUT transfer lift = {hm:+.3f}  95% CI [{hlo:+.3f}, {hhi:+.3f}]  "
          f"(n={hn};  post-{model} mean {hold_post:+.3f};  base {hold.base.mean():+.3f})")
    print(f"TRAIN-half memo lift   = {tm:+.3f}  95% CI [{tlo:+.3f}, {thi:+.3f}]  "
          f"(n={tn};  post-{model} mean {train_post:+.3f};  base {train.base.mean():+.3f})")
    print(f"Δ (train - held-out)   = {dm:+.3f}  95% CI [{dlo:+.3f}, {dhi:+.3f}]   tau={TAU}")
    print(f"REFERENCES:  #48 full-model aggregate = {REF48_AGG:+.2f}   #53 zero-exposure = {REF53_ZERO:+.2f}")
    print(f"base balance across halves: holdout {hold.base.mean():+.3f} vs train {train.base.mean():+.3f} "
          f"(Δ {hold.base.mean()-train.base.mean():+.3f} — should be ~0 for a clean random split)")

    # ---- pre-registered decision ----
    ci_excl0 = not (hlo <= 0 <= hhi)
    weak = ci_excl0 and hlo > TAU
    strong = weak and hold_post > 0
    if not ci_excl0:
        verdict = "NO TRANSFER — held-out lift CI includes 0; on-bench lift is memorization."
    elif strong:
        verdict = "TRANSFER CONFIRMED (STRONG) — held-out lift > tau AND held-out post crosses positive."
    elif weak:
        verdict = "TRANSFER CONFIRMED (WEAK) — held-out lift > tau but post stays <=0."
    else:
        verdict = "TRANSFER WEAK / mostly-memorization — held-out lift CI excludes 0 but <= tau."
    print(f"\nPRE-REGISTERED VERDICT: {verdict}")

    # ---- per-tradition held-out (descriptive, with CI) ----
    print("\n== per-tradition HELD-OUT lift (descriptive; hard tier = sunni-islam, roman-catholicism) ==")
    print(f"{'tradition':22} {'nHold':>5} {'liftHold':>9} {'95% CI':>18} {'postHold':>9} {'liftTrain':>10}")
    per_trad = []
    for tr in sorted(df.tradition.unique()):
        h = hold[hold.tradition == tr]; t = train[train.tradition == tr]
        m, lo, hi, n = boot_mean_ci(h["lift"].values)
        tmn = t["lift"].mean() if len(t) else np.nan
        post = h[f"{model}_score"].mean() if len(h) else np.nan
        print(f"{tr:22} {n:5d} {m:+9.3f}  [{lo:+.3f},{hi:+.3f}] {post:+9.3f} {tmn:+10.3f}")
        per_trad.append(dict(tradition=tr, n_holdout=int(n), lift_holdout=m, lo=lo, hi=hi,
                             post_holdout=float(post), lift_train=float(tmn)))

    # ---- persist ----
    df.to_csv(os.path.join(OUT, f"per_scenario_57_{model}.csv"), index=False)
    summary = dict(
        model=model, n_cells=int(n_cells), n_holdout=int(hn), n_train=int(tn),
        heldout_lift=hm, heldout_ci=[hlo, hhi], heldout_post=float(hold_post), heldout_base=float(hold.base.mean()),
        train_lift=tm, train_ci=[tlo, thi], train_post=float(train_post), train_base=float(train.base.mean()),
        delta_train_minus_heldout=dm, delta_ci=[dlo, dhi], tau=TAU,
        base_balance_delta=float(hold.base.mean() - train.base.mean()),
        ref_48_aggregate=REF48_AGG, ref_53_zero_exposure=REF53_ZERO,
        verdict=verdict, per_tradition=per_trad,
    )
    json.dump(summary, open(os.path.join(OUT, f"summary_57_{model}.json"), "w"), indent=2)

    make_figure(model, hm, hlo, hhi, tm, tlo, thi, per_trad, hold_post)
    print(f"\nwrote {OUT}/{{per_scenario_57_{model}.csv, summary_57_{model}.json, fig_transfer_{model}.pdf/.png}}")
    return summary


def make_figure(model, hm, hlo, hhi, tm, tlo, thi, per_trad, hold_post):
    """Three-way comparison + per-tradition held-out lift (MB-paper style)."""
    plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False,
                         "figure.dpi": 150})
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(11.5, 4.8), gridspec_kw={"width_ratios": [1, 1.25]})
    C_HOLD, C_TRAIN, C_REF = "#2b6cb0", "#c05621", "#718096"

    # left: three-way bars
    labels = ["Held-out\n(transfer)", "Train-half\n(memorization)", "#48 full\n(+0.83)", "#53 zero-exp\n(+0.22)"]
    vals = [hm, tm, REF48_AGG, REF53_ZERO]
    errs = [[hm - hlo, tm - tlo, 0, 0], [hhi - hm, thi - tm, 0, 0]]
    colors = [C_HOLD, C_TRAIN, C_REF, C_REF]
    axL.axhline(0, color="#cbd5e0", lw=1)
    axL.axhline(TAU, color="#a0aec0", lw=1, ls=":")
    axL.bar(range(4), vals, color=colors, yerr=errs, capsize=4, width=0.66)
    axL.annotate(f"τ={TAU}", (3.4, TAU), fontsize=8, color="#4a5568", va="bottom")
    axL.set_xticks(range(4)); axL.set_xticklabels(labels, fontsize=8.5)
    axL.set_ylabel("base → split-model descriptive lift\n(unstated, post-pressure; band scale)")
    axL.set_title(f"On-bench lift: transfer vs memorization ({model})", fontsize=10.5)

    # right: per-tradition held-out lift with CI
    trs = [p["tradition"] for p in per_trad]
    m = [p["lift_holdout"] for p in per_trad]
    lo = [p["lift_holdout"] - p["lo"] for p in per_trad]
    hi = [p["hi"] - p["lift_holdout"] for p in per_trad]
    hard = {"sunni-islam", "roman-catholicism"}
    y = range(len(trs))
    axR.axvline(0, color="#cbd5e0", lw=1)
    axR.errorbar(m, list(y), xerr=[lo, hi], fmt="o", color=C_HOLD, capsize=3)
    for i, p in enumerate(per_trad):
        if p["tradition"] in hard:
            axR.get_yticklabels()  # styled below
    axR.set_yticks(list(y))
    axR.set_yticklabels([f"★ {t}" if t in hard else t for t in trs], fontsize=9)
    axR.set_xlabel("held-out lift (95% CI)")
    axR.set_title("Per-tradition held-out transfer (★ = hard tier)", fontsize=10.5)

    fig.suptitle("MultiWeights-split: does the recipe help on the actual benchmark, measured properly?\n"
                 f"(Exp 57, gemma-4-31b, clean 50/50 scenario holdout, N=519; held-out post-{model} "
                 f"mean {hold_post:+.2f})", fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(os.path.join(OUT, f"fig_transfer_{model}.png"), bbox_inches="tight")
    fig.savefig(os.path.join(OUT, f"fig_transfer_{model}.pdf"), bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
