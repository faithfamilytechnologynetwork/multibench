"""Regenerate the FULL-GRID dual-judge paper artifacts for #110 (reproducible; committed).

Extends the Opus 4.8 second-judge layer for `20260803` from a stated+guided sample to the full
grid. Recomputes the dual-judge agreement, the tier x framing table (tab:djtier), and the heatmap
figure over EVERY matched cell, using the canonical export loaders (`resolve_judgments` with the
same root-order (priority, ts) precedence the committed dataset was built from) — so the numbers
match results/20260803 to the digit.

Run from the MAIN checkout (paper generators read the gitignored tmp/ judging roots and write to
the sibling multibench-papers repo):

    uv --project workflows/analysis run python docs/analysis/110-dualjudge-fullgrid-figs.py

Outputs (uncommitted; the architect wires them into the paper):
  <papers>/tables/tab_dualjudge_tier.tex   -- tab:djtier, 6-col tier x framing, FULL GRID
  <papers>/tables/tab_dualjudge_agree.tex  -- NEW: per-framing agreement (r, bias, within +/-0.5)
  <papers>/figures/fig_dual_judge.pdf      -- 3 full-grid framing heatmaps
and patches stats_bundle.json's dual_judge with a `full_grid` block (a .bak is written).

NOTE for the paper wiring (this script only regenerates the inputs):
  - tab:djtier caption + tab_dualjudge_tier now cover the FULL stated+guided grid, not a sample.
  - fig_dual_judge is now 3 panels (Unstated / Stated / Guided full grid) -- update the caption
    (was "Left: full unstated grid. Right: stated+guided sample").
  - Sec 2.3 / App-D prose citing the sample-era r=0.777 must move to the full-grid stated+guided
    combined r printed below; unstated stays 0.854.
  - Cost appendix + programme total must use the paper's convention with the new counts printed below.
"""
import json
import os
import pathlib

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

from analysis.export_results import read_run_root, resolve_judgments
from analysis.core_imports import FRAMINGS

# Repo root: the main checkout (which holds the gitignored tmp/ judging roots). Defaults to the
# script's own repo root — correct when this file is run from the MAIN checkout after merge. Set
# MB_ROOT to override (e.g. to run from a builder worktree against the main checkout's tmp/).
ROOT = pathlib.Path(os.environ.get("MB_ROOT") or pathlib.Path(__file__).resolve().parents[2])
PAPER = ROOT.parent / "multibench-papers"
FIGS, TABS = PAPER / "figures", PAPER / "tables"
BUNDLE = ROOT / "tmp/judging-runs/20260803-merged/analysis-out/figures-report-v2/stats_bundle.json"
ROOTS = [ROOT / "tmp/judging-runs" / r for r in
         ("20260803-merged", "20260803-unstated-opus",
          "20260803-framings-opus-sample", "20260823-opus-fullgrid")]

TIERS = {"easy": ["buddhism", "taoism", "secular-sage"],
         "medium": ["eastern-christianity", "judaism"],
         "hard": ["roman-catholicism", "sunni-islam"]}
TIER_SHORT = {"easy": "Low", "medium": "Medium", "hard": "High"}  # full labels, matching sibling tables


def sgn(x):  # explicit sign, U+2212 minus — the paper's table convention ("+0.66" / "−0.03")
    return f"{x:+.2f}".replace("-", "−")
FLAB = {"unstated": "Unstated", "stated": "Stated", "guided": "Guided"}
SLAB = {"claude-sonnet-5": "Sonnet 5", "thinkingmachines/Inkling": "Inkling",
        "gpt-5.6-terra": "GPT-5.6", "gemini-3.6-flash": "Gemini 3.6",
        "Qwen/Qwen3-235B-A22B-Instruct-2507": "Qwen3-235B"}
PRICE = (5.00, 25.00)  # claude-opus-4-8 $/M in,out (workflows/judging/judging/report.py)

# ── resolve every cell via the canonical loaders ─────────────────────────────
per_root = [read_run_root(r) for r in ROOTS]
trads = sorted({t for pr in per_root for t in pr})
gem, opus = {}, {}
for t in trads:
    idxs = [i for i, pr in enumerate(per_root) if t in pr]
    for r in resolve_judgments([per_root[i][t] for i in idxs], idxs):
        cell = (r["subject"], t, r["scenario_id"], r["pressure"], r["framing"], r["scope"])
        (gem if r["judge"] == "gemini-3.6-flash" else opus if r["judge"] == "claude-opus-4-8" else {})[cell] = r["score"]
matched = [c for c in opus if c in gem]
by_fr = {f: [c for c in matched if c[4] == f] for f in FRAMINGS}


def agree(cells):
    g = np.array([gem[c] for c in cells]); o = np.array([opus[c] for c in cells])
    return dict(n=len(cells), r=round(float(np.corrcoef(g, o)[0, 1]), 3),
                bias=round(float(np.mean(o - g)), 3),
                within_half=round(100 * float(np.mean(np.abs(o - g) <= 0.5)), 1),
                exact=round(100 * float(np.mean(o == g)), 1))


dual = {"overall": agree(matched), **{f: agree(by_fr[f]) for f in FRAMINGS},
        "stated_guided": agree(by_fr["stated"] + by_fr["guided"]), "rank": {}}
SUBJ = sorted({c[0] for c in matched})
for f in FRAMINGS:
    gm = {s: float(np.mean([gem[c] for c in by_fr[f] if c[0] == s])) for s in SUBJ}
    om = {s: float(np.mean([opus[c] for c in by_fr[f] if c[0] == s])) for s in SUBJ}
    og = sorted(SUBJ, key=lambda s: -gm[s]); oo = sorted(SUBJ, key=lambda s: -om[s])
    dual["rank"][f] = dict(gemini={s: round(gm[s], 3) for s in SUBJ},
                           opus={s: round(om[s], 3) for s in SUBJ},
                           order_identical=og == oo, order=og)

# ── programme counts (paper convention) + Opus spend ─────────────────────────
opus_committed = len(opus)
opus_unstated = sum(1 for c in opus if c[4] == "unstated")
opus_stated_guided = opus_committed - opus_unstated
# route bridge (paper convention): SAMPLE-root cells judged under BOTH Opus aliases — the
# OpenRouter tail-fill re-judged them under a second alias, extra API calls the paper counts.
# It is a sample-root artifact; the full-grid root uses one alias, so it is NOT pooled in.
from analysis.export_results import normalize_subject  # noqa: E402
sample_root = read_run_root(ROOTS[2])  # 20260803-framings-opus-sample
bridge = 0
for t, rt in sample_root.items():
    seen = {}
    for r in rt.base:
        if r["judge"] in ("claude-opus-4-8", "anthropic/claude-opus-4.8"):
            k = (normalize_subject(r["subject"]), r["scenario_id"], r["pressure"], r["framing"], r["scope"])
            seen.setdefault(k, set()).add(r["judge"])
    bridge += sum(1 for v in seen.values() if len(v) == 2)
opus_pilot = 1800
opus_paper = opus_committed + bridge          # published Opus convention (incl. bridge)
programme = 93420 + opus_paper + opus_pilot   # Gemini + Opus(incl bridge) + router pilot

spend = {}
for name, root in [("unstated", ROOTS[1]), ("sample", ROOTS[2]), ("fullgrid", ROOTS[3])]:
    tok = {}
    # BOTH judgments.jsonl AND judgments_v2.jsonl — every recorded judgment was an incurred API call
    # (the sample root carries 20 v2 re-judgments; excluding them under-reports actual spend).
    for p in list(root.glob("*/judgments.jsonl")) + list(root.glob("*/judgments_v2.jsonl")):
        for line in p.read_text().splitlines():
            if not line.strip():
                continue
            u = json.loads(line).get("usage", {})
            pre = "b_" if u.get("batch") else ""
            for k in ("in", "out", "cache_write", "cache_read"):
                tok[pre + k] = tok.get(pre + k, 0) + u.get(k, 0)
    pi, po = PRICE
    full = tok.get("in", 0)*pi + tok.get("out", 0)*po + tok.get("cache_write", 0)*pi*2 + tok.get("cache_read", 0)*pi*0.1
    bat = tok.get("b_in", 0)*pi + tok.get("b_out", 0)*po + tok.get("b_cache_write", 0)*pi*2 + tok.get("b_cache_read", 0)*pi*0.1
    spend[name] = round((full + 0.5*bat) / 1e6, 2)
spend["total_opus"] = round(sum(spend.values()), 2)

# sign-flip rate on the framing (stated+guided) cells: Gemini +1 that Opus scores −1 (paper :1160)
fr_cells = by_fr["stated"] + by_fr["guided"]
sign_flip = round(100 * sum(1 for c in fr_cells if gem[c] == 1.0 and opus[c] == -1.0) / len(fr_cells), 1)

print("=== AGREEMENT (full grid) ===")
for k in ("overall", "unstated", "stated", "guided", "stated_guided"):
    print(f"  {k:14s}: {dual[k]}")
print("order identical all framings:", all(dual["rank"][f]["order_identical"] for f in FRAMINGS))
for f in FRAMINGS:
    print(f"  {f} order:", [SLAB[s] for s in dual['rank'][f]['order']],
          "opus 3rd/4th:", [round(dual['rank'][f]['opus'][s], 3) for s in dual['rank'][f]['order'][2:4]])
print("\n=== COUNTS ===")
print(f"  Opus committed {opus_committed} (unstated {opus_unstated} + stated/guided {opus_stated_guided})")
print(f"  route bridge {bridge}; Opus paper-convention {opus_paper}; router pilot {opus_pilot}")
print(f"  PROGRAMME TOTAL (paper convention) = 93420 + {opus_paper} + {opus_pilot} = {programme}")
print("\n=== OPUS SPEND (usage-computed) ===", spend)
print("sign-flip (Gemini +1 / Opus −1) on framing cells:", sign_flip, "%")

# ── patch bundle ─────────────────────────────────────────────────────────────
b = json.loads(BUNDLE.read_text())
bak = BUNDLE.with_suffix(".json.pre-110-fullgrid.bak")
if not bak.exists():  # idempotent — keep the ORIGINAL pre-#110 bundle, don't clobber on re-runs
    bak.write_text(json.dumps(b, indent=1))
b.setdefault("dual_judge", {})["full_grid"] = dual
BUNDLE.write_text(json.dumps(b, indent=1))

# The main .tex supplies the final row terminator after \input (TeX mishandles \\ at EOF before
# \bottomrule), so strip a trailing " \\" — matching the paper's write_rows convention.
def write_rows(path, rows):
    text = "\n".join(rows)
    if text.endswith(" \\\\"):
        text = text[:-3]
    path.write_text(text + "\n")


# ── tab:djtier — 6-col tier x framing over the FULL grid (post-pressure/full scope) ──
TABS.mkdir(parents=True, exist_ok=True)
tier_rows = []
for tier, ts in TIERS.items():
    for f in ("stated", "guided"):
        cells = [c for c in by_fr[f] if c[5] == "full" and c[1] in ts]
        o = float(np.mean([opus[c] for c in cells])); g = float(np.mean([gem[c] for c in cells]))
        tier_rows.append(f"{TIER_SHORT[tier]} & {FLAB[f]} & {sgn(o)} & {sgn(g)} & {sgn(o - g)} & {len(cells):,} \\\\")
write_rows(TABS / "tab_dualjudge_tier.tex", tier_rows)
# NEW agreement table (a SEPARATE file — does NOT clobber tab:djtier's tier×framing shape)
def b3(x):  # signed bias, U+2212 minus, 3dp
    return f"{x:+.3f}".replace("-", "−")


agree_rows = [f"Overall & {dual['overall']['n']:,} & {dual['overall']['r']:.3f} & "
              f"{b3(dual['overall']['bias'])} & {dual['overall']['within_half']:.1f}\\% \\\\", "\\midrule"]
agree_rows += [f"{FLAB[f]} & {dual[f]['n']:,} & {dual[f]['r']:.3f} & {b3(dual[f]['bias'])} & "
               f"{dual[f]['within_half']:.1f}\\% \\\\" for f in FRAMINGS]
write_rows(TABS / "tab_dualjudge_agree.tex", agree_rows)

# ── figure: 3 full-grid framing heatmaps ─────────────────────────────────────
INK, INK2, MUTED, SURF = "#1c1c1c", "#444", "#888", "#faf9f7"
plt.rcParams.update({"savefig.facecolor": SURF, "figure.facecolor": SURF, "font.size": 9})
VALS = [-1.0, -0.5, 0.0, 0.5, 1.0]; VLAB = ["−1", "−½", "0", "+½", "+1"]
seq = LinearSegmentedColormap.from_list("seq", ["#f0efec", "#9ec5f4", "#3987e5", "#1c5cab", "#12365f"])
FIGS.mkdir(parents=True, exist_ok=True)
fig, axes = plt.subplots(1, 3, figsize=(9.6, 3.5))
for ax, f in zip(axes, FRAMINGS):
    cm = np.zeros((5, 5))
    for c in by_fr[f]:
        cm[VALS.index(opus[c]), VALS.index(gem[c])] += 1
    pct = 100 * cm / cm.sum()
    for r_ in range(5):
        for c_ in range(5):
            v = pct[r_, c_]; col = seq(min(v, 40) / 40)
            ax.add_patch(plt.Rectangle((c_+0.03, r_+0.03), 0.94, 0.94, facecolor=col, edgecolor=SURF, lw=1.2))
            lum = 0.299*col[0] + 0.587*col[1] + 0.114*col[2]
            ax.text(c_+0.5, r_+0.5, f"{v:.1f}" if v >= 0.05 else "·", ha="center", va="center",
                    fontsize=7.5, fontweight="bold" if r_ == c_ else "normal", color="#fff" if lum < 0.55 else INK)
    for k in range(5):
        ax.add_patch(plt.Rectangle((k+0.03, k+0.03), 0.94, 0.94, fill=False, edgecolor=INK, lw=0.9, zorder=5))
        ax.text(k+0.5, -0.30, VLAB[k], ha="center", va="center", fontsize=8, color=INK2)
        ax.text(-0.30, k+0.5, VLAB[k], ha="center", va="center", fontsize=8, color=INK2)
    ax.text(2.5, -0.80, "Gemini 3.6 Flash score", ha="center", fontsize=8, color=INK2)
    ax.text(-0.90, 2.5, "Opus 4.8 score", ha="center", va="center", rotation=90, fontsize=8, color=INK2)
    ax.text(2.5, 5.62, f"{FLAB[f]} full grid", ha="center", fontsize=9.5, fontweight="bold", color=INK)
    ax.text(2.5, 5.22, f"n = {dual[f]['n']:,} · r = {dual[f]['r']:.3f}", ha="center", fontsize=8, color=MUTED)
    ax.set_xlim(-1.15, 5.1); ax.set_ylim(-1.1, 5.95); ax.set_aspect("equal"); ax.axis("off")
fig.tight_layout(); fig.savefig(FIGS / "fig_dual_judge.pdf"); plt.close(fig)
print("\nwrote:", FIGS / "fig_dual_judge.pdf", "+", TABS / "tab_dualjudge_tier.tex", "+ tab_dualjudge_agree.tex")
