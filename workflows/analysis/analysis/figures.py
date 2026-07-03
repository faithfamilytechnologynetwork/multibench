"""Optional matplotlib publication figures — the port of JaleesBench ``make_figures.py``.

Emitted only under ``--figures`` (spec S1); matplotlib is imported here and this module
is imported lazily by the CLI, so the HTML-only path never loads it (spec §7.3 / D7).

Fidelity to the source (spec §4.7):
- **F3**: the same seven-stop diverging colormap (from ``colors.STOPS``) + ``band_color``
  via ``TwoSlopeNorm(-1, 0, 1)``, and ``band_axis`` reference lines (dashed ±0.5, solid 0).
- **F4**: the steadfastness heatmap auto-scales contrast with ``TwoSlopeNorm(-vmax, 0, vmax)``,
  ``vmax = |M|.max()``.
- **F5**: every figure is saved as **both** ``.pdf`` (vector) and ``.png`` (``dpi=150``) via
  ``saveboth``, in a serif house style.

Deviations: **no ×0.5 rescale** (scores already −1…+1, D1) and **no band-name labels
anywhere** (D2) — axes read "Score (−1…+1; 0 = neutral)".
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # non-interactive; deterministic file output

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm  # noqa: E402

from analysis.aggregate import TraditionAggregate  # noqa: E402
from analysis.colors import STOPS  # noqa: E402
from analysis.core_imports import FRAMINGS, PRESSURES  # noqa: E402
from analysis.stats import TraditionStats  # noqa: E402

_VALID_FORMATS = ("pdf", "png")
_AXIS_LABEL = "Score (−1…+1; 0 = neutral)"

BAND_CMAP = LinearSegmentedColormap.from_list("mb_diverging", list(STOPS))
NORM = TwoSlopeNorm(vmin=-1.0, vcenter=0.0, vmax=1.0)


def band_color(score: float):
    """Diverging color for a numeric score (ported band_color; ×0.5 dropped, D1)."""
    return BAND_CMAP(NORM(score))


def band_axis(ax, vertical: bool = True) -> None:
    """Faint reference lines: dashed grey at ±0.5, solid grey at 0 (ported band_axis)."""
    setter = ax.axvline if vertical else ax.axhline
    for at in (-0.5, 0.5):
        setter(at, color="#CCCCCC", lw=0.8, ls=(0, (3, 3)), zorder=0)
    setter(0, color="#888888", lw=1.1, zorder=0)


def _apply_house_style() -> None:
    plt.rcParams.update({
        "figure.dpi": 150,
        "savefig.bbox": "tight",
        "font.family": "serif",
        "font.serif": ["DejaVu Serif", "Times New Roman"],
        "font.size": 10.5,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "axes.edgecolor": "#444444",
        "axes.grid": True,
        "grid.color": "#E6E6E6",
    })


def saveboth(fig, out_dir: Path, name: str, formats: list[str]) -> list[Path]:
    """Write a figure as each requested format (``.pdf`` vector + ``.png`` at dpi 150)."""
    written: list[Path] = []
    for ext in formats:
        path = out_dir / f"{name}.{ext}"
        fig.savefig(path, dpi=150)
        written.append(path)
    plt.close(fig)
    return written


def _rows(pairs):
    for agg, st in pairs:
        for s in agg.subjects:
            yield agg, st, s


def fig_scorecard(pairs, subjects):
    labels, points, los, his = [], [], [], []
    for agg, st in pairs:
        for s in agg.subjects:
            ci = st.per_subject[s].headline
            if ci is None:
                continue
            labels.append(f"{agg.tradition} · {s}")
            points.append(ci[0])
            los.append(ci[0] - ci[1])
            his.append(ci[2] - ci[0])
    fig, ax = plt.subplots(figsize=(8.4, 0.5 * len(labels) + 1.6))
    y = np.arange(len(labels))
    band_axis(ax, vertical=True)
    ax.errorbar(points, y, xerr=[los, his], fmt="none", ecolor="#8C8C8C", elinewidth=1.6, capsize=3)
    ax.scatter(points, y, s=130, c=[band_color(p) for p in points], edgecolor="white", zorder=3)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlim(-1.05, 1.05)
    ax.set_xlabel(_AXIS_LABEL)
    ax.set_title("Cross-tradition headline, with 95% CIs")
    ax.invert_yaxis()
    ax.grid(axis="y", visible=False)
    return fig


def fig_framing(pairs, subjects):
    n = len(pairs)
    fig, axes = plt.subplots(1, n, figsize=(2.4 * n + 0.6, 3.2), sharey=True)
    if n == 1:
        axes = [axes]
    x = np.arange(len(FRAMINGS))
    for ax, (agg, _st) in zip(axes, pairs):
        for k, s in enumerate(agg.subjects):
            bf = agg.scorecard[s]["by_framing"]
            ys = [bf.get(fr) for fr in FRAMINGS]
            ax.plot(x, ys, marker="o" if k == 0 else "D", label=s,
                    color="#1a6840" if k == 0 else "#2C7FB8")
        ax.axhline(0, color="#888888", lw=1.0, zorder=0)
        ax.set_xticks(x)
        ax.set_xticklabels([fr[:3] for fr in FRAMINGS])
        ax.set_ylim(-1.05, 1.05)
        ax.set_title(agg.tradition, fontsize=10)
    axes[0].set_ylabel(_AXIS_LABEL)
    axes[-1].legend(fontsize=7, loc="lower right")
    fig.suptitle("Framing staircase: unstated → stated → guided", fontweight="bold")
    return fig


def fig_steadfastness(pairs):
    cols = list(PRESSURES) + ["pooled"]
    labels, matrix = [], []
    for agg, _ in pairs:
        for s in agg.subjects:
            sc = agg.scorecard[s]
            row = [sc["steadfastness_by_pressure"].get(p) for p in PRESSURES] + [sc["steadfastness"]]
            matrix.append([np.nan if v is None else v for v in row])
            labels.append(f"{agg.tradition} · {s}")
    M = np.array(matrix, dtype=float)
    vmax = float(np.nanmax(np.abs(M))) or 1.0
    fig, ax = plt.subplots(figsize=(1.0 * len(cols) + 3.0, 0.42 * len(labels) + 1.4))
    im = ax.imshow(M, cmap=BAND_CMAP, norm=TwoSlopeNorm(vmin=-vmax, vcenter=0.0, vmax=vmax),
                   aspect="auto")
    ax.set_xticks(np.arange(len(cols)))
    ax.set_xticklabels(cols, rotation=40, ha="right", fontsize=8)
    ax.set_yticks(np.arange(len(labels)))
    ax.set_yticklabels(labels, fontsize=8)
    ax.axvline(len(PRESSURES) - 0.5, color="#444444", lw=1.0)
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            v = M[i, j]
            if not np.isnan(v):
                ax.text(j, i, f"{v:+.2f}", ha="center", va="center", fontsize=7,
                        color="#111111" if abs(v) < 0.33 * vmax else "#FFFFFF")
    ax.grid(False)
    fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02,
                 label="Steadfastness (Δ after pressure; − = degraded)")
    ax.set_title("Steadfastness by pressure (unstated)")
    return fig


def fig_distribution(pairs):
    order = ["-1.0", "-0.5", "0.0", "0.5", "1.0"]
    labels, rows = [], []
    for agg, _ in pairs:
        for s in agg.subjects:
            d = agg.score_distribution[s]
            total = sum(d.get(k, 0) for k in order) or 1
            rows.append([d.get(k, 0) / total for k in order])
            labels.append(f"{agg.tradition} · {s}")
    R = np.array(rows)
    y = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(8.4, 0.42 * len(labels) + 1.4))
    left = np.zeros(len(labels))
    for j, k in enumerate(order):
        ax.barh(y, R[:, j], left=left, color=band_color(float(k)), edgecolor="white", label=k)
        left = left + R[:, j]
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlim(0, 1)
    ax.set_xlabel("Share of per-judge verdicts")
    ax.invert_yaxis()
    ax.grid(axis="y", visible=False)
    ax.legend(ncol=5, fontsize=7, loc="lower center", bbox_to_anchor=(0.5, 1.01))
    ax.set_title("Score distributions")
    return fig


def emit_figures(aggregates: list[TraditionAggregate], stats: list[TraditionStats],
                 out_dir: Path, formats: list[str]) -> list[Path]:
    """Render all figures as PNG/PDF under ``out_dir``; returns the written paths (S1)."""
    bad = [f for f in formats if f not in _VALID_FORMATS]
    if bad:
        raise ValueError(f"unsupported figure format(s) {bad}; choose from {list(_VALID_FORMATS)}")
    if not formats:
        raise ValueError("no figure formats requested")

    _apply_house_style()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    pairs = list(zip(aggregates, stats))
    subjects = [s for agg in aggregates for s in agg.subjects]
    subjects = list(dict.fromkeys(subjects))  # first-seen order, deduped

    written: list[Path] = []
    written += saveboth(fig_scorecard(pairs, subjects), out_dir, "scorecard", formats)
    written += saveboth(fig_framing(pairs, subjects), out_dir, "framing", formats)
    written += saveboth(fig_steadfastness(pairs), out_dir, "steadfastness", formats)
    written += saveboth(fig_distribution(pairs), out_dir, "distribution", formats)
    return written
