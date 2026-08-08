"""AFB before/after exporter — committed intermediate → drop-in ``results-raw/<run-id>/`` catalog (#54 Phase 3).

Turns the Phase-2 collection intermediate (responses + Terra 0–4 verdicts for 150 AFB items × the
two subjects) into a generic raw-results catalog the multibrowser viewer reads unchanged — the
**second catalog type** the Spec 51 contract was built to carry. It reuses the byte-stable writer
(:class:`analysis.raw_writer.RawTierWriter`) and the generic preset cap/dedup
(:func:`analysis.raw_presets.dedup_per_item`) — no MultiBench code, no fork.

The catalog shape matches the shipped ``AFB_CATALOG`` test fixture (``apps/multibrowser`` genericity
tests): 0–4 scale, two checkpoint subjects, the Terra judge, a single ``condition=cold`` axis, a
single ``single`` scope, and ``groupBy instrument`` / group ``afb-150``.
"""

from __future__ import annotations

from pathlib import Path

from analysis.fingerprint import combine_fingerprint, fingerprint_line
from analysis.loaders import AnalysisInputError
from analysis.raw_presets import dedup_per_item
from analysis.raw_writer import RawTierWriter, WriteSummary, json_bytes

SCHEMA_VERSION = 1
GROUP = "afb-150"
SCOPE = "single"
CONDITION_AXIS = "condition"
CONDITION = "cold"
JUDGE_KEY = "terra"
JUDGE_LABEL = "gpt-5.6-terra"
VALID_SCORES = (0, 1, 2, 3, 4)
# The catalog hardcodes the subject labels + judge label, so the intermediate's provenance MUST match
# exactly — else the published artifact would carry a false claim. Waleed's scope is vanilla↔DPO only.
EXPECTED_SUBJECTS = ["gemma-4-31b-it", "mb-sft-dpo"]
EXPECTED_JUDGE = "openai/gpt-5.6-terra"

SCALE = {"min": 0, "center": 2, "max": 4}
# Score ramp as catalog DATA (the viewer's generic `catalogScoreColor` interpolates min→center→max).
# 0→2→4 = cool → neutral slate-grey (the calibration target, ~1–2) → warm. The GREY CENTER is
# deliberate: it does NOT paint 4 as "best" (no green) — the thesis is calibration (represent religion
# as a live perspective), not maximization (sermonizing = over-application at 4). Blue/orange extremes
# are colorblind-safe and survive light/dark theming; the center `#8B95A1` is a MEDIUM slate distinct
# from the viewer's near-white "no data" grey (`#E5E5E5`, rampColor.ts) so the two never blur in a grid.
# NOTE: this is a DIVERGING (center-grey) ramp, a deliberate deviation from the plan's "sequential
# dark→mid→light" phrasing — it fits `center:2` and the anti-"4-is-best" intent better (flagged to the
# architect; plan Change Log updated).
RAMP = ["#4C72B0", "#8B95A1", "#DD8452"]

DATASET = {
    "title": "AFB before/after — religious representation",
    "description": "AllFaith Benchmark (AFB) 150 cold-condition items: vanilla Gemma-4-31B beside the "
                   "MultiWeights (SFT+DPO) checkpoint, each scored 0–4 by GPT-5.6-Terra. Companion "
                   "artifact to the MultiWeights omissive-bias result (#48).",
    "language": "en",
    "license": "MIT",  # the AFB instrument is MIT (CEFE-AI); our responses/judgments published alongside
}
SUBJECT_LABELS = {"gemma-4-31b-it": "Vanilla Gemma-4-31B", "mb-sft-dpo": "MultiWeights (SFT+DPO)"}

# Fixed score→direction summary (schema-required; NOT "e.g."). rationale carries Terra's text.
SUMMARY = {
    0: "no religious representation",
    1: "passing mention of religion",
    2: "meaningful religious reference",
    3: "balanced religious and secular",
    4: "predominantly religious",
}

MAX_LABEL = 80


def _label(question: str) -> str:
    """Item label: whitespace collapsed, cut to ≤ 80 chars on a word boundary, `…` when truncated."""
    q = " ".join(question.split())
    if len(q) <= MAX_LABEL:
        return q
    cut = q[:MAX_LABEL - 1]  # reserve 1 char for the ellipsis → final label ≤ MAX_LABEL
    sp = cut.rfind(" ")
    if sp > 0:
        cut = cut[:sp]
    return cut + "…"


def _bad_score(score) -> bool:
    return isinstance(score, bool) or not isinstance(score, int) or score not in VALID_SCORES


def _bad_text(s) -> bool:
    return not isinstance(s, str) or not s.strip()


def _index(intermediate: dict) -> tuple[list[str], dict[str, str], dict[str, dict[str, dict]]]:
    """Validate the intermediate and index it → (items_sorted, question_by_item, cell_by_item_subject)."""
    if intermediate.get("schema_version") != SCHEMA_VERSION:
        raise AnalysisInputError(f"intermediate schema_version {intermediate.get('schema_version')!r} != {SCHEMA_VERSION}")
    if intermediate.get("condition") != CONDITION:
        raise AnalysisInputError(f"intermediate condition {intermediate.get('condition')!r} != {CONDITION!r}")
    subjects = intermediate.get("subjects")
    if subjects != EXPECTED_SUBJECTS:  # exact list + order — the catalog hardcodes their labels
        raise AnalysisInputError(f"intermediate subjects {subjects!r} != {EXPECTED_SUBJECTS!r} (vanilla↔DPO scope)")
    if intermediate.get("judge") != EXPECTED_JUDGE:  # else the published judge label would be a false claim
        raise AnalysisInputError(f"intermediate judge {intermediate.get('judge')!r} != {EXPECTED_JUDGE!r}")
    questions: dict[str, str] = {}
    cells: dict[str, dict[str, dict]] = {}
    for c in intermediate.get("cells", []):
        item_id, subject = c["item_id"], c["subject"]
        if subject not in subjects:
            raise AnalysisInputError(f"cell subject {subject!r} not in catalog subjects {subjects}")
        if _bad_text(c.get("response")):
            raise AnalysisInputError(f"cell {item_id}/{subject} has no/invalid response")
        if _bad_score(c.get("score")):
            raise AnalysisInputError(f"cell {item_id}/{subject} has invalid score {c.get('score')!r}")
        if _bad_text(c.get("rationale")):
            raise AnalysisInputError(f"cell {item_id}/{subject} has no/invalid rationale")
        if _bad_text(c.get("question")):
            raise AnalysisInputError(f"cell {item_id}/{subject} has no question")
        prev_q = questions.setdefault(item_id, c["question"])
        if prev_q != c["question"]:
            raise AnalysisInputError(f"inconsistent question text for item {item_id!r}")
        by_subj = cells.setdefault(item_id, {})
        if subject in by_subj:
            raise AnalysisInputError(f"duplicate cell {item_id}/{subject} in intermediate")
        by_subj[subject] = c
    if not cells:
        raise AnalysisInputError("intermediate has no cells")
    for item_id, by_subj in cells.items():  # every item must carry every subject
        missing = [s for s in subjects if s not in by_subj]
        if missing:
            raise AnalysisInputError(f"item {item_id!r} missing subjects {missing}")
    return sorted(cells), questions, cells


def _shard_doc(item_id: str, question: str, subjects: list[str], by_subj: dict[str, dict]) -> dict:
    """One shard per item: a cell per subject (catalog order), cold-condition single-turn transcript."""
    doc_cells = []
    for subject in subjects:
        c = by_subj[subject]
        score = c["score"]
        doc_cells.append({
            "subject": subject,
            "conditions": {CONDITION_AXIS: CONDITION},
            "transcript": [{"role": "user", "content": question},
                           {"role": "assistant", "content": c["response"]}],
            "verdicts": [{"judge": JUDGE_KEY, "scope": SCOPE, "score": score,
                          "summary": SUMMARY[score], "rationale": c["rationale"]}],
        })
    return {"schema_version": SCHEMA_VERSION, "cells": doc_cells}


def _dpo_base_preset(items_sorted: list[str], questions: dict[str, str],
                     cells: dict[str, dict[str, dict]], subjects: list[str]) -> list[dict]:
    """The single before/after preset: items ranked by |score(dpo) − score(base)|, N ≤ PRESET_CAP.

    Absolute delta (per the approved spec's ``|dpo − base|``) so the biggest movements in BOTH
    directions ship (hiding regressions would be curation bias — architect ruling). Descending by
    magnitude with a stable ``item`` tie-break; ``dedup_per_item`` enforces one-entry-per-item + cap.
    """
    base, dpo = subjects[0], subjects[1]
    cands = []
    for item_id in items_sorted:
        by = cells[item_id]
        delta = abs(by[dpo]["score"] - by[base]["score"])
        cands.append((delta, item_id))
    cands.sort(key=lambda e: (-e[0], e[1]))  # |Δ| desc, then item id asc (group is constant here)
    entries = dedup_per_item(
        {"key": f"dpo-base:{GROUP}:{item_id}", "label": f"{item_id} · {_label(questions[item_id])}",
         "params": {"group": GROUP, "item": item_id, "scope": SCOPE, "a": base, "b": dpo,
                    "conditions": {CONDITION_AXIS: CONDITION}}}
        for (_delta, item_id) in cands
    )
    if not entries:
        return []
    return [{"key": "dpo-base", "label": "Omission → repair (|Δ| dpo vs base)",
             "description": "Items where the DPO checkpoint's score moves most from vanilla Gemma "
                            "(both directions).", "entries": entries}]


def export(intermediate: dict, out_root: str | Path, run_id: str) -> WriteSummary:
    """Write the AFB catalog + per-item shards to ``<out_root>/<run_id>/`` via the byte-stable writer."""
    items_sorted, questions, cells = _index(intermediate)
    subjects = intermediate["subjects"]

    writer = RawTierWriter(out_root, run_id, prune=True)  # validates run_id
    items_meta = []
    verdict_rows = []
    for item_id in items_sorted:
        shard_path = f"{GROUP}/{item_id}.json.gz"
        writer.add_shard(shard_path, json_bytes(_shard_doc(item_id, questions[item_id], subjects, cells[item_id])))
        items_meta.append({"id": item_id, "label": _label(questions[item_id]), "group": GROUP, "shard": shard_path})
        # Judgment fingerprint via the CANONICAL `fingerprint_line` (the same one both MB tiers use),
        # so it carries the full resolved-judgment identity INCLUDING `direction` (our synthesized
        # summary) and `rationale` — matching `analysis.fingerprint`'s convention. AFB's single
        # `condition` axis maps onto the tuple's pressure slot; `framing` is unused. `content_fingerprint`
        # (from the writer, over shard bytes) additionally covers the transcript/response text, which the
        # judgment fingerprint does not. AFB has no cross-tier `results/` partner → self-consistent.
        for subject in subjects:
            c = cells[item_id][subject]
            verdict_rows.append({
                "tradition": GROUP, "subject": subject, "scenario_id": item_id,
                "pressure": CONDITION, "framing": "", "judge": JUDGE_KEY, "scope": SCOPE,
                "score": c["score"], "direction": SUMMARY[c["score"]], "rationale": c["rationale"],
            })

    catalog = {
        "schema_version": SCHEMA_VERSION,
        "dataset": DATASET,
        "scale": dict(SCALE),
        "ramp": list(RAMP),
        "subjects": [{"id": s, "label": SUBJECT_LABELS.get(s, s)} for s in subjects],
        "judges": [{"key": JUDGE_KEY, "label": JUDGE_LABEL, "fullGrid": True}],
        "conditionAxes": [{"key": CONDITION_AXIS, "label": "Condition",
                           "values": [{"id": CONDITION, "label": "Cold"}]}],
        "groupBy": {"key": "instrument", "label": "Instrument"},
        "scopes": [{"id": SCOPE, "label": SCOPE}],
        "items": items_meta,
        "presets": _dpo_base_preset(items_sorted, questions, cells, subjects),
        # Self-consistent judgment fingerprint (no cross-tier `results/` partner; the viewer tolerates
        # a null cross-tier lookup). content_fingerprint over the shard bytes comes from the writer.
        "fingerprint": combine_fingerprint(fingerprint_line(r) for r in verdict_rows),
        "content_fingerprint": writer.content_fingerprint,
    }
    return writer.write(catalog)
