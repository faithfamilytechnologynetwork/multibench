"""Combined two-judge ranked aggregates over multiple run roots (#120).

The committed, tested primitive behind the v3 paper `stats_bundle.json`: it computes the **combined**
(mean-of-present-judges-per-cell) aggregates + scenario-cluster bootstrap CIs over the four
`20260803` roots — the numbers the paper and `/results` leaderboard rank on since #120.

Why not `analysis report`: that goes through ``load_corpus``, which requires a ``report.json`` per
dir and **rejects a duplicate tradition across dirs** — it structurally cannot ingest the four
overlapping roots (the Gemini run + the report-less Opus layers). So this reuses the results-export
seam instead: ``read_run_root`` + ``resolve_judgments`` (multi-root, priority-ordered) → a shim run
→ the canonical ``aggregate_tradition`` (duck-typed on ``.judgments``/``.subjects``/``.report``) →
``compute_tradition_stats``. Feeding ``aggregate_tradition`` **all** judges' resolved rows makes its
``cell_scores`` reducer average the present judges per cell — so every aggregate it returns is the
combined score, with **no second implementation** of the averaging convention.

Output is deterministic (fixed bootstrap seed, sorted keys) → byte-stable.
"""
from __future__ import annotations

from dataclasses import dataclass

from analysis.aggregate import TraditionAggregate, aggregate_tradition
from analysis.core_imports import FRAMINGS
from analysis.export_results import (
    CANONICAL_SUBJECTS,
    build_corpus_export,
    read_run_root,
    resolve_judgments,
)
from analysis.loaders import AnalysisInputError
from analysis.stats import N_BOOT, SEED, compute_tradition_stats, stats_to_dict

_FULL = "full"


@dataclass(frozen=True)
class _CombinedRun:
    """A minimal run shim that ``aggregate_tradition`` duck-types on (spec §4.2).

    Carries the ALL-judge resolved rows, so ``cell_scores`` averages the present judges per cell —
    i.e. the combined two-judge score. ``judges`` lists the real judges that contributed.
    """

    tradition: str
    judgments: list[dict]
    subjects: list[str]
    judges: list[str]
    report: dict


def build_combined_runs(roots: list[str]) -> list[_CombinedRun]:
    """One combined (all-judge) run shim per tradition, across the given roots (priority-ordered)."""
    per_root = [read_run_root(r) for r in roots]
    traditions = sorted({t for root in per_root for t in root})
    runs: list[_CombinedRun] = []
    for tradition in traditions:
        present = [(i, root[tradition]) for i, root in enumerate(per_root) if tradition in root]
        raws = [rt for _i, rt in present]
        priorities = [i for i, _rt in present]
        rows = resolve_judgments(raws, priorities)
        reports = [rt.report for rt in raws if rt.report is not None]
        if not reports:
            raise AnalysisInputError(
                f"{tradition}: no run root provides report.json — cannot pin the scenario universe")
        judges = sorted({r["judge"] for r in rows})
        runs.append(_CombinedRun(
            tradition=tradition, judgments=rows,
            subjects=list(CANONICAL_SUBJECTS), judges=judges, report=reports[0]))
    return runs


def combined_subj_overall(aggregates: list[TraditionAggregate]) -> dict[str, float]:
    """`subject|framing` → the equal-weight mean across traditions of the combined
    ``by_framing[full]`` breakdown — the paper's ``subj_overall`` **point** on the combined score.

    Reconciles by construction with the results-export combined leaderboard mean-of-means (both are
    the mean over traditions of ``breakdown_mean(cell_scores(all judges), …, scope=full)``)."""
    out: dict[str, float] = {}
    for subject in CANONICAL_SUBJECTS:
        for framing in FRAMINGS:
            vals = [
                a.scorecard[subject]["by_framing"][framing]
                for a in aggregates
                if subject in a.scorecard and a.scorecard[subject]["by_framing"].get(framing) is not None
            ]
            if vals:
                out[f"{subject}|{framing}"] = sum(vals) / len(vals)
    return out


def build_combined_stats(roots: list[str], *, n_boot: int = N_BOOT, seed: int = SEED) -> dict:
    """The combined ranked-aggregate bundle: per-(tradition, subject) CIs (same schema as
    ``analysis_stats.json``, but over the combined cell score) + the combined ``subj_overall`` point.
    """
    runs = build_combined_runs(roots)
    aggregates = [aggregate_tradition(r) for r in runs]
    stats = [compute_tradition_stats(a, n_boot=n_boot, seed=seed) for a in aggregates]
    bundle = stats_to_dict(stats)
    bundle["subj_overall_point"] = combined_subj_overall(aggregates)
    return bundle


def export_combined_mean_of_means(roots: list[str]) -> dict[str, float]:
    """`subject|framing` → the combined mean-of-means computed from the RESULTS-EXPORT combined block
    (``TraditionExport.combined_means``), for scope=full, pressure=all. The reconciliation counterpart
    to :func:`combined_subj_overall`: both must agree (and with the v3 bundle) to ≤1e-9."""
    exports = build_corpus_export(roots)
    out: dict[str, float] = {}
    for subject in CANONICAL_SUBJECTS:
        for framing in FRAMINGS:
            vals = [
                exp.combined_means[(subject, framing, _FULL, "all")].mean
                for exp in exports.values()
                if (subject, framing, _FULL, "all") in exp.combined_means
            ]
            if vals:
                out[f"{subject}|{framing}"] = sum(vals) / len(vals)
    return out
