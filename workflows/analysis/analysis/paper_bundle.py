"""The committed, reproducible paper `stats_bundle.json` generator (#120).

Produces the **combined two-judge** paper bundle (the `subj_overall` / `tier` / `model_tier` /
`trad_pooled` / `guided_residual_hard_minus_easy` / `subj_trad_framing` / `steadfastness_by_framing`
/ `pct_scen_negative_unstated` / `spread` / `gaps_pooled` / `dual_judge` schema that
`tmp/paper_figs_multibench.py` consumes) directly from the four judging-run roots — so a clean
checkout with the roots can regenerate the numbers the paper was built from, with **no gitignored
throwaway script** in the loop. Replaces the ad-hoc `tmp/report_figs_20260803_v3.py`; the figure
rendering (matplotlib) is separate and not the deliverable.

Every **score aggregate** is computed over the **combined cell score** (mean of present judges per
cell, via the canonical :func:`analysis.aggregate.cell_scores`) — no second averaging
implementation. **`dual_judge`** is the RAW Gemini-vs-Opus validation section (it compares the
judges against each other, never against their mean): its `full_grid` block is recomputed over every
double-judged cell on the completed grid, and the `route_bridge` (sample-root cells judged under both
Opus aliases) is computed from the raw rows. Deterministic (fixed seed, sorted keys) → byte-stable.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import numpy as np

from analysis.aggregate import cell_scores
from analysis.combined_stats import build_combined_runs
from analysis.export_results import read_run_root

# ── Paper taxonomy (the paper's fixed subject/tradition/tier vocabulary) ────────────
SIDS = ["claude-sonnet-5", "thinkingmachines/Inkling", "gpt-5.6-terra",
        "gemini-3.6-flash", "Qwen/Qwen3-235B-A22B-Instruct-2507"]
TOP2 = ["claude-sonnet-5", "thinkingmachines/Inkling"]
TRADS = ["buddhism", "taoism", "secular-sage", "eastern-christianity", "judaism",
         "roman-catholicism", "sunni-islam"]
TIERS = {"easy": ["buddhism", "taoism", "secular-sage"],
         "medium": ["eastern-christianity", "judaism"],
         "hard": ["roman-catholicism", "sunni-islam"]}
FRAMINGS = ["unstated", "stated", "guided"]
# OpenRouter-slug → canonical subject id (framings sample + judge pilot spell subjects that way).
SMAP = {"anthropic/claude-sonnet-5": "claude-sonnet-5",
        "thinkingmachines/inkling": "thinkingmachines/Inkling",
        "openai/gpt-5.6-terra": "gpt-5.6-terra",
        "google/gemini-3.6-flash": "gemini-3.6-flash",
        "qwen/qwen3-235b-a22b-2507": "Qwen/Qwen3-235B-A22B-Instruct-2507"}
OPUS_ALIASES = {"claude-opus-4-8", "anthropic/claude-opus-4.8"}
N_BOOT_DEFAULT, SEED_DEFAULT = 5000, 12345
_EXPECTED_CELLS = 93420  # 5 subjects × 519 scenarios × 6 pressures × 3 framings × 2 scopes


def _combined_rows(roots: list[str]) -> list[dict]:
    """Combined cells (mean of present judges per cell) as flat rows, over all roots."""
    rows: list[dict] = []
    for run in build_combined_runs(roots):
        for (subj, scen, pr, fr, scope), val in cell_scores(run.judgments).items():
            rows.append({"tradition": run.tradition, "framing": fr, "subject": subj,
                         "scenario_id": scen, "pressure": pr, "scope": scope, "score": val})
    return rows


def _raw_rows(root: Path) -> list[dict]:
    """base + judgments_v2 rows for every tradition of a root (v2 wins per identity)."""
    per = read_run_root(str(root))
    out: list[dict] = []
    for rt in per.values():
        by_id: dict[tuple, dict] = {}
        for j in rt.base + rt.v2:  # v2 appended last → later wins per identity
            key = (j["subject"], j["scenario_id"], j["pressure"], j["framing"], j["judge"], j["scope"])
            by_id[key] = j
        out.extend(by_id.values())
    return out


def _dedupe_opus(rows: list[dict]) -> tuple[list[dict], list[tuple]]:
    """Normalize+dedupe Opus rows (later ts wins) → (deduped, bridge pairs [(batch, openrouter)])."""
    by_id: dict[tuple, dict] = {}
    bridge: dict[tuple, dict] = {}
    for j in rows:
        if j["judge"] not in OPUS_ALIASES:
            continue
        subj = SMAP.get(j["subject"], j["subject"])
        key = (subj, j["tradition"], j["scenario_id"], j["pressure"], j["framing"], j["scope"])
        bridge.setdefault(key, {})[j["judge"]] = j["score"]
        cand = str(j.get("ts", ""))
        if key not in by_id or cand >= by_id[key]["_ts"]:
            by_id[key] = {**j, "subject": subj, "judge": "claude-opus-4-8", "_ts": cand}
    deduped = [{k: v for k, v in r.items() if k != "_ts"} for r in by_id.values()]
    bridge_pairs = [(v["claude-opus-4-8"], v["anthropic/claude-opus-4.8"])
                    for v in bridge.values() if len(v) == 2]
    return deduped, bridge_pairs


def _agree(pairs: list[tuple]) -> dict:
    g = np.array([p[0] for p in pairs]); o = np.array([p[1] for p in pairs])
    return {"n": len(pairs), "r": round(float(np.corrcoef(g, o)[0, 1]), 3),
            "bias": round(float(np.mean(o - g)), 4),
            "within_half": round(100 * float(np.mean(np.abs(o - g) <= 0.5)), 1),
            "exact": round(100 * float(np.mean(o == g)), 1)}


def _dual_judge(roots: list[str], subjects=SIDS, traditions=TRADS, tiers=TIERS) -> dict:
    """RAW Gemini-vs-Opus validation block (unchanged by the combined rule)."""
    SIDS, TRADS, TIERS = subjects, traditions, tiers  # noqa: F841 — parameterized taxonomy
    merged, opus_un_root, opus_fr_root = Path(roots[0]), Path(roots[1]), Path(roots[2])
    gem_lut: dict[tuple, float] = {}
    for j in _raw_rows(merged):
        if j["judge"] != "gemini-3.6-flash":
            continue
        gem_lut[(j["subject"], j["tradition"], j["scenario_id"], j["pressure"],
                 j["framing"], j["scope"])] = j["score"]
    opus_un = [j for j in _raw_rows(opus_un_root) if j["judge"] == "claude-opus-4-8"]
    opus_fr, bridge_pairs = _dedupe_opus(_raw_rows(opus_fr_root))

    def pair(rows):
        out = []
        for j in rows:
            g = gem_lut.get((j["subject"], j["tradition"], j["scenario_id"],
                             j["pressure"], j["framing"], j["scope"]))
            if g is not None:
                out.append((g, j["score"], j))
        return out

    pairs_un, pairs_fr = pair(opus_un), pair(opus_fr)
    dj: dict = {"unstated": _agree([(g, o) for g, o, _ in pairs_un]),
                "framings_sample": _agree([(g, o) for g, o, _ in pairs_fr]),
                "unstated_rank": {}, "framings_tier": {}}
    for scope_set, key in [(("turn1", "full"), "both"), (("full",), "full")]:
        d = defaultdict(lambda: ([], []))
        for g, o, j in pairs_un:
            if j["scope"] in scope_set:
                d[j["subject"]][0].append(o); d[j["subject"]][1].append(g)
        dj["unstated_rank"][key] = {
            s: {"opus": round(float(np.mean(d[s][0])), 3), "gemini": round(float(np.mean(d[s][1])), 3)}
            for s in SIDS if d[s][0]}
    for tier, trads in TIERS.items():
        for f in ["stated", "guided"]:
            sel = [(g, o) for g, o, j in pairs_fr
                   if j["scope"] == "full" and j["framing"] == f and j["tradition"] in trads]
            a = np.array(sel)
            dj["framings_tier"][f"{tier}|{f}"] = {
                "n": len(sel), "opus": round(float(a[:, 1].mean()), 3),
                "gemini": round(float(a[:, 0].mean()), 3),
                "delta": round(float(a[:, 1].mean() - a[:, 0].mean()), 3)}
    if bridge_pairs:
        b = np.array(bridge_pairs)
        dj["route_bridge"] = {
            "n": len(bridge_pairs), "r": round(float(np.corrcoef(b[:, 0], b[:, 1])[0, 1]), 3),
            "bias": round(float(np.mean(b[:, 1] - b[:, 0])), 4),
            "within_half": round(100 * float(np.mean(np.abs(b[:, 1] - b[:, 0]) <= 0.5)), 1),
            "exact": round(100 * float(np.mean(b[:, 1] == b[:, 0])), 1)}
    # full_grid: combined-cell agreement over EVERY double-judged cell (both scopes), on the
    # completed grid — raw Gemini vs raw Opus resolved across all four roots.
    gem, opus = {}, {}
    for run in build_combined_runs(roots):
        for r in run.judgments:
            cell = (r["subject"], run.tradition, r["scenario_id"], r["pressure"], r["framing"], r["scope"])
            if r["judge"] == "gemini-3.6-flash":
                gem[cell] = r["score"]
            elif r["judge"] == "claude-opus-4-8":
                opus[cell] = r["score"]
    matched = [c for c in opus if c in gem]
    by_fr = {f: [c for c in matched if c[4] == f] for f in FRAMINGS}

    def agr(cells):
        g = np.array([gem[c] for c in cells]); o = np.array([opus[c] for c in cells])
        return {"n": len(cells), "r": round(float(np.corrcoef(g, o)[0, 1]), 3),
                "bias": round(float(np.mean(o - g)), 3),
                "within_half": round(100 * float(np.mean(np.abs(o - g) <= 0.5)), 1),
                "exact": round(100 * float(np.mean(o == g)), 1)}

    subj = sorted({c[0] for c in matched})
    rank = {}
    for f in FRAMINGS:
        gm = {s: float(np.mean([gem[c] for c in by_fr[f] if c[0] == s])) for s in subj}
        om = {s: float(np.mean([opus[c] for c in by_fr[f] if c[0] == s])) for s in subj}
        og = sorted(subj, key=lambda s: -gm[s]); oo = sorted(subj, key=lambda s: -om[s])
        rank[f] = {"gemini": {s: round(gm[s], 3) for s in subj},
                   "opus": {s: round(om[s], 3) for s in subj},
                   "order_identical": og == oo, "order": og}
    dj["full_grid"] = {"overall": agr(matched), **{f: agr(by_fr[f]) for f in FRAMINGS},
                       "stated_guided": agr(by_fr["stated"] + by_fr["guided"]), "rank": rank}
    return dj


def build_paper_bundle(roots: list[str], *, subjects=SIDS, traditions=TRADS, tiers=TIERS,
                       top2=TOP2, expected_cells: int = _EXPECTED_CELLS,
                       n_boot: int = N_BOOT_DEFAULT, seed: int = SEED_DEFAULT) -> dict:
    """The full combined-score paper bundle (same schema as v2) over the four roots (README order).

    The subject/tradition/tier taxonomy is parameterized (defaults = the MultiBench paper set) so a
    small fixture can exercise the whole pipeline in CI without the gitignored launch roots.
    """
    SIDS, TRADS, TIERS, TOP2, _EXPECTED_CELLS = subjects, traditions, tiers, top2, expected_cells
    rows = _combined_rows(roots)
    if len(rows) != _EXPECTED_CELLS:
        raise ValueError(f"expected {_EXPECTED_CELLS} combined cells, got {len(rows)} — check the roots")
    acc: dict = defaultdict(lambda: defaultdict(list))
    acc1: dict = defaultdict(lambda: defaultdict(list))
    for j in rows:
        (acc if j["scope"] == "full" else acc1)[(j["tradition"], j["framing"], j["subject"])][j["scenario_id"]].append(j["score"])
    scen_ids = {t: sorted({j["scenario_id"] for j in rows if j["tradition"] == t}) for t in TRADS}
    n_scen = {t: len(scen_ids[t]) for t in TRADS}
    M, M1 = {}, {}
    for t in TRADS:
        for f in FRAMINGS:
            for s in SIDS:
                M[(t, f, s)] = np.array([np.mean(acc[(t, f, s)][sc]) for sc in scen_ids[t]])
                M1[(t, f, s)] = np.array([np.mean(acc1[(t, f, s)][sc]) for sc in scen_ids[t]])
    rng = np.random.default_rng(seed)
    idx = {t: rng.integers(0, n_scen[t], size=(n_boot, n_scen[t])) for t in TRADS}

    def boot(t, f, s, mat=M):
        v = mat[(t, f, s)]
        return float(v.mean()), v[idx[t]].mean(axis=1)

    def ci(bs):
        return float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))

    def pool(trads, f, subjects, mat=M):
        pts, bss = [], []
        for t in trads:
            per = [boot(t, f, s, mat) for s in subjects]
            pts.append(np.mean([p for p, _ in per])); bss.append(np.mean([b for _, b in per], axis=0))
        return float(np.mean(pts)), np.mean(bss, axis=0)

    bundle: dict = {"meta": {"n_boot": n_boot, "seed": seed,
                             "ci": "95% percentile scenario-cluster bootstrap", "n_scen": n_scen}}
    tier = {}
    for k, trads in TIERS.items():
        for f in FRAMINGS:
            p, b = pool(trads, f, SIDS); tier[f"{k}|{f}|all5"] = [p, *ci(b)]
            p2, b2 = pool(trads, f, TOP2); tier[f"{k}|{f}|top2"] = [p2, *ci(b2)]
    bundle["tier"] = tier
    trad_tbl = {}
    for t in TRADS:
        for f in FRAMINGS:
            p, b = pool([t], f, SIDS); trad_tbl[(t, f)] = [p, *ci(b)]
    bundle["trad_pooled"] = {f"{t}|{f}": v for (t, f), v in trad_tbl.items()}
    subj_overall, model_tier = {}, {}
    for s in SIDS:
        for f in FRAMINGS:
            p, b = pool(TRADS, f, [s]); subj_overall[f"{s}|{f}"] = [p, *ci(b)]
            for k, trads in TIERS.items():
                pt, bt = pool(trads, f, [s]); model_tier[f"{s}|{k}|{f}"] = [pt, *ci(bt)]
    bundle["subj_overall"] = subj_overall
    bundle["model_tier"] = model_tier
    resid = {}
    if "hard" in TIERS and "easy" in TIERS:  # the paper's hard−easy residual (skip on other taxonomies)
        for s in SIDS:
            ph, bh = pool(TIERS["hard"], "guided", [s]); pe, be = pool(TIERS["easy"], "guided", [s])
            resid[s] = [ph - pe, *ci(bh - be)]
    bundle["guided_residual_hard_minus_easy"] = resid
    stf = {}
    for s in SIDS:
        for t in TRADS:
            for f in FRAMINGS:
                p, b = boot(t, f, s); stf[f"{s}|{t}|{f}"] = [p, *ci(b)]
    bundle["subj_trad_framing"] = stf
    stead = {}
    for s in SIDS:
        for f in FRAMINGS:
            pts, bss = [], []
            for t in TRADS:
                pf, bf = boot(t, f, s, M); p1, b1 = boot(t, f, s, M1)
                pts.append(pf - p1); bss.append(bf - b1)
            stead[f"{s}|{f}"] = [float(np.mean(pts)), *ci(np.mean(bss, axis=0))]
    bundle["steadfastness_by_framing"] = stead
    pct_neg = {}
    for k, trads in TIERS.items():
        neg = tot = 0
        for t in trads:
            for sc in scen_ids[t]:
                vals = [v for s in SIDS for v in acc[(t, "unstated", s)][sc] + acc1[(t, "unstated", s)][sc]]
                tot += 1; neg += np.mean(vals) < 0
        pct_neg[k] = [int(neg), int(tot), round(100 * neg / tot, 1)]
    bundle["pct_scen_negative_unstated"] = pct_neg
    bundle["spread"] = {f: round(max(trad_tbl[(t, f)][0] for t in TRADS)
                                 - min(trad_tbl[(t, f)][0] for t in TRADS), 3) for f in FRAMINGS}
    gaps = {}
    for t in TRADS:
        pu, bu = pool([t], "unstated", SIDS); ps, bs_ = pool([t], "stated", SIDS)
        pg, bg = pool([t], "guided", SIDS)
        gaps[t] = {"recognition": [ps - pu, *ci(bs_ - bu)], "instruction": [pg - ps, *ci(bg - bs_)]}
    bundle["gaps_pooled"] = gaps
    bundle["dual_judge"] = _dual_judge(roots, subjects, traditions, tiers)
    return bundle
