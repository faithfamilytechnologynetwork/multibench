"""Experiment-48 paper figures (vector PDF), matching the MultiBench paper style
(tmp/paper_figs_multibench.py conventions: Helvetica/size-9, white surface, ink/muted palette,
framing ramp, easy→medium→hard tiers, pdf.fonttype 42). Reads ONLY saved on-disk data — no spend.

(a) AFB-150 cold score distribution, grouped bars: base vs SFT vs SFT+DPO, P≥2 annotated per head.
(b) Per-tradition descriptive gradient dotplot: base→SFT unstated full-scope mean, ordered by tier
    ("lifts most where omission was worst").

Run: uv run --with matplotlib --with numpy python experiments/48_multiweights_omissive_bias/paper_figs.py
Out: experiments/48_multiweights_omissive_bias/figures/{afb_distribution,tradition_gradient}.pdf
"""
import json
import pathlib
import sys

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

EXP = pathlib.Path(__file__).resolve().parent
# Single source of truth for the diverging score palette — import the analysis colors module
# (pure-python, no matplotlib) instead of duplicating the stops.
sys.path.insert(0, str(EXP.parent.parent / "workflows" / "analysis"))
from analysis.colors import STOPS  # noqa: E402
EVAL = EXP / "data" / "output" / "eval"
COLL = EXP / "data" / "output" / "collection"
DESC = EXP / "data" / "output" / "descriptive"
FIGS = EXP / "figures"
FIGS.mkdir(exist_ok=True)

# --- paper visual language (from paper_figs_multibench.py) ---
SURFACE, INK, INK2, MUTED = "#ffffff", "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE = "#e1e0d9", "#c3c2b7"
HEAD = {"base": "#c3c2b7", "sft": "#3987e5", "dpo": "#1c5cab"}   # progression: grey → mid → dark blue
HEAD_LAB = {"base": "base", "sft": "+SFT", "dpo": "+SFT+DPO"}
# diverging score stops for the gradient dots come from analysis.colors.STOPS (imported above).
TLAB = {"sunni-islam": "Sunni Islam", "buddhism": "Buddhism", "taoism": "Taoism",
        "secular-sage": "Secular sage", "roman-catholicism": "R. Catholicism",
        "eastern-christianity": "E. Christianity", "judaism": "Judaism"}
TIERS = [("hard", ["sunni-islam", "roman-catholicism"]),
         ("medium", ["eastern-christianity", "judaism"]),
         ("easy", ["buddhism", "secular-sage", "taoism"])]

mpl.rcParams.update({
    "font.family": ["Helvetica Neue", "Arial", "DejaVu Sans"],
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "text.color": INK, "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": INK,
    "axes.edgecolor": BASELINE, "axes.linewidth": 0.8, "font.size": 9, "pdf.fonttype": 42,
})


def _score_color(v):  # linear interp over STOPS at (v+1)/2
    t = min(1.0, max(0.0, (v + 1) / 2)) * (len(STOPS) - 1)
    i = min(int(t), len(STOPS) - 2); f = t - i
    a = tuple(int(STOPS[i][k:k+2], 16) for k in (1, 3, 5))
    b = tuple(int(STOPS[i+1][k:k+2], 16) for k in (1, 3, 5))
    return "#%02X%02X%02X" % tuple(round(a[k] + (b[k]-a[k])*f) for k in range(3))


def fig_afb_distribution():
    base = json.load(open(EVAL / "afb_results.json"))["base:cold"]
    sft = json.load(open(EVAL / "afb_results.json"))["sft:cold"]
    dpo = json.load(open(EVAL / "afb_results_dpo.json"))["dpo:cold"]
    heads = [("base", base), ("sft", sft), ("dpo", dpo)]
    fig, ax = plt.subplots(figsize=(5.2, 3.0))
    x = np.arange(5); w = 0.26
    for j, (k, r) in enumerate(heads):
        n = r["n"]
        pct = [100 * int(r["dist"][str(s)]) / n for s in range(5)]
        ax.bar(x + (j - 1) * w, pct, w, color=HEAD[k], edgecolor="white", linewidth=0.4,
               label=f"{HEAD_LAB[k]}  (P≥2={r['P>=2']:.2f})", zorder=3)
    ax.set_xticks(x)
    ax.set_xticklabels(["0\nnone", "1\npassing", "2\nmeaningful", "3\nbalanced", "4\npredom."])
    ax.set_ylabel("% of 150 AFB questions")
    ax.set_title("AFB-150 cold: religious-representation distribution", loc="left", color=INK, fontsize=10)
    ax.set_axisbelow(True); ax.yaxis.grid(True, color=GRID, linewidth=0.7)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    fig.tight_layout(); fig.savefig(FIGS / "afb_distribution.pdf"); plt.close(fig)
    print("wrote", FIGS / "afb_distribution.pdf")


def _unstated_full_means(jdir, framing_filter):
    out = {}
    for t in TLAB:
        vals = []
        for line in (jdir / t / "judgments.jsonl").open():
            j = json.loads(line)
            if j["scope"] == "full" and (framing_filter is None or j["framing"] == framing_filter):
                s = j.get("score")
                if s is not None:
                    vals.append(s)
        out[t] = sum(vals) / len(vals) if vals else None
    return out


def fig_tradition_gradient():
    base = _unstated_full_means(COLL, "unstated")   # base via OpenRouter (existing bands)
    sft = _unstated_full_means(DESC, None)          # sft via the vLLM endpoint
    order = [t for _, ts in TIERS for t in ts]
    fig, ax = plt.subplots(figsize=(5.4, 3.4))
    y = np.arange(len(order))[::-1]
    for yi, t in zip(y, order):
        b, s = base[t], sft[t]
        ax.plot([b, s], [yi, yi], color=BASELINE, lw=1.4, zorder=1)
        ax.scatter([b], [yi], s=42, color=_score_color(b), edgecolor=INK2, lw=0.5, zorder=3)
        ax.scatter([s], [yi], s=54, color=_score_color(s), edgecolor=INK, lw=0.6, zorder=3, marker="D")
        ax.annotate("", xy=(s, yi), xytext=(b, yi),
                    arrowprops=dict(arrowstyle="->", color=MUTED, lw=0.8, shrinkA=4, shrinkB=6), zorder=2)
    ax.set_yticks(y); ax.set_yticklabels([TLAB[t] for t in order])
    # tier separators + labels
    idx = 0
    for name, ts in TIERS:
        top = y[idx]; idx += len(ts)
        if idx < len(order):
            ax.axhline(y[idx] + 0.5, color=GRID, lw=0.8)
        ax.text(1.02, top, name, transform=ax.get_yaxis_transform(), fontsize=8, color=MUTED, va="center")
    ax.axvline(0, color=BASELINE, lw=1.0); ax.axvline(-0.5, color=GRID, lw=0.7, ls="--"); ax.axvline(0.5, color=GRID, lw=0.7, ls="--")
    ax.set_xlim(-1, 1); ax.set_xlabel("unstated, post-pressure mean score  (−1 … +1)")
    ax.set_title("Per-tradition shift: base → +SFT (unstated)", loc="left", color=INK, fontsize=10)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    # legend proxies
    from matplotlib.lines import Line2D
    ax.legend(handles=[Line2D([], [], marker="o", ls="", color=BASELINE, mec=INK2, label="base"),
                       Line2D([], [], marker="D", ls="", color="#5AAE61", mec=INK, label="+SFT")],
              frameon=False, fontsize=8, loc="lower right")
    fig.tight_layout(); fig.savefig(FIGS / "tradition_gradient.pdf"); plt.close(fig)
    print("wrote", FIGS / "tradition_gradient.pdf")


if __name__ == "__main__":
    fig_afb_distribution()
    fig_tradition_gradient()
