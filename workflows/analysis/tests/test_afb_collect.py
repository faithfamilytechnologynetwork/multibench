"""Tests for the AFB collection core (`analysis.afb_collect`, #54 Phase 2).

Money-touching I/O is injected, so these mock ``generate``/``judge`` — no network, no spend. They
pin the load-bearing guarantees: two-state resumability (judge-after-generate never re-generates),
idempotence, completeness validation, atomic checkpointing, and that the pinned decoding is recorded.
"""

from __future__ import annotations

import json

import pytest

from analysis.afb_collect import afb_item_id, collect, load_afb_items
from analysis.loaders import AnalysisInputError

ITEMS = [{"item_id": "AFB-001", "question": "Q1?"}, {"item_id": "AFB-002", "question": "Q2?"}]
SUBJECTS = ["gemma-4-31b-it", "mb-sft-dpo"]
DECODING = {"temperature": 0.0, "seed": 0, "max_tokens": 1024}


class _Recorder:
    """Deterministic mock generate/judge that counts calls (score = len(subject) % 5)."""

    def __init__(self):
        self.gen_calls, self.judge_calls = [], []

    def generate(self, subject, prompt):
        self.gen_calls.append((subject, prompt))
        return f"resp::{subject}::{prompt}"

    def judge(self, question, response):
        self.judge_calls.append((question, response))
        return {"score": len(response) % 5, "rationale": f"because {response[:5]}"}


def _collect(tmp_path, rec, **kw):
    return collect(ITEMS, SUBJECTS, rec.generate, rec.judge, decoding=DECODING,
                   run_id="afb-test", out_path=tmp_path / "collection.json", **kw)


def test_item_id_mapping():
    assert afb_item_id("q0001") == "AFB-001"
    assert afb_item_id("q0150") == "AFB-150"


def test_full_collection_shape_and_decoding_recorded(tmp_path):
    rec = _Recorder()
    doc = _collect(tmp_path, rec)
    assert len(rec.gen_calls) == 4 and len(rec.judge_calls) == 4  # 2 items × 2 subjects
    assert doc["run_id"] == "afb-test" and doc["condition"] == "cold"
    assert doc["subjects"] == SUBJECTS and doc["judge"] == "openai/gpt-5.6-terra"
    assert doc["decoding"] == DECODING  # pinned decoding recorded verbatim
    assert len(doc["cells"]) == 4
    cell = doc["cells"][0]
    assert set(cell) == {"item_id", "question", "subject", "response", "score", "rationale"}
    assert cell["response"].startswith("resp::")


def test_prompt_is_question_verbatim_cold(tmp_path):
    rec = _Recorder()
    _collect(tmp_path, rec)
    assert all(prompt in ("Q1?", "Q2?") for _subj, prompt in rec.gen_calls)  # cold = question verbatim


def test_idempotent_rerun_issues_no_calls_and_is_byte_stable(tmp_path):
    rec1 = _Recorder()
    _collect(tmp_path, rec1)
    first = (tmp_path / "collection.json").read_bytes()
    rec2 = _Recorder()
    _collect(tmp_path, rec2)  # resume a complete collection
    assert rec2.gen_calls == [] and rec2.judge_calls == []  # zero calls
    assert (tmp_path / "collection.json").read_bytes() == first  # byte-stable


def test_resume_skips_completed_cells(tmp_path):
    rec = _Recorder()
    # Seed a complete checkpoint for AFB-001 (both subjects), leave AFB-002 unstarted.
    seed = {
        "schema_version": 1, "run_id": "afb-test", "condition": "cold", "subjects": SUBJECTS,
        "judge": "openai/gpt-5.6-terra", "decoding": DECODING,
        "cells": [
            {"item_id": "AFB-001", "question": "Q1?", "subject": s, "response": "r", "score": 1, "rationale": "x"}
            for s in SUBJECTS
        ],
    }
    (tmp_path / "collection.json").write_text(json.dumps(seed))
    _collect(tmp_path, rec)
    assert len(rec.gen_calls) == 2 and len(rec.judge_calls) == 2  # only AFB-002 × 2 subjects
    assert all(item_id_prompt in ("Q2?",) for _s, item_id_prompt in rec.gen_calls)


def test_judge_after_generate_resume_does_not_regenerate(tmp_path):
    """A cell with a persisted response but no verdict resumes with judge only — never re-generation."""
    rec = _Recorder()
    seed = {
        "schema_version": 1, "run_id": "afb-test", "condition": "cold", "subjects": SUBJECTS,
        "judge": "openai/gpt-5.6-terra", "decoding": DECODING,
        "cells": (
            # AFB-001: responses present, NO scores (interrupted after generation)
            [{"item_id": "AFB-001", "question": "Q1?", "subject": s, "response": "kept-resp"} for s in SUBJECTS]
            # AFB-002: fully done
            + [{"item_id": "AFB-002", "question": "Q2?", "subject": s, "response": "r", "score": 2, "rationale": "x"}
               for s in SUBJECTS]
        ),
    }
    (tmp_path / "collection.json").write_text(json.dumps(seed))
    doc = _collect(tmp_path, rec)
    assert rec.gen_calls == []              # NEVER re-generated
    assert len(rec.judge_calls) == 2       # only the two un-judged AFB-001 cells
    afb1 = [c for c in doc["cells"] if c["item_id"] == "AFB-001"]
    assert all(c["response"] == "kept-resp" for c in afb1)  # kept the persisted response
    assert all(q == "Q1?" and r == "kept-resp" for q, r in rec.judge_calls)


def test_concurrency_produces_same_result(tmp_path):
    rec = _Recorder()
    doc = _collect(tmp_path, rec, concurrency=4)
    assert len(doc["cells"]) == 4
    assert len(rec.gen_calls) == 4 and len(rec.judge_calls) == 4


def test_completeness_rejects_bad_score(tmp_path):
    rec = _Recorder()
    rec.judge = lambda q, r: {"score": 7, "rationale": "out of range"}  # invalid
    with pytest.raises(AnalysisInputError):
        _collect(tmp_path, rec)


def test_empty_response_fails_fast(tmp_path):
    rec = _Recorder()
    rec.generate = lambda subject, prompt: "   "  # blank
    with pytest.raises(AnalysisInputError):
        _collect(tmp_path, rec)


def test_mismatched_checkpoint_refused(tmp_path):
    (tmp_path / "collection.json").write_text(json.dumps({
        "schema_version": 1, "run_id": "afb-test", "condition": "cold", "subjects": SUBJECTS,
        "judge": "openai/gpt-5.6-terra", "decoding": {"temperature": 0.9}, "cells": [],  # different decoding
    }))
    with pytest.raises(AnalysisInputError):
        _collect(tmp_path, _Recorder())


def test_load_afb_items_from_vendored_instrument(tmp_path):
    p = tmp_path / "questions.jsonl"
    p.write_text('{"id": "q0001", "question": "A?"}\n{"id": "q0002", "question": "B?"}\n')
    items = load_afb_items(p)
    assert items == [{"item_id": "AFB-001", "question": "A?"}, {"item_id": "AFB-002", "question": "B?"}]
