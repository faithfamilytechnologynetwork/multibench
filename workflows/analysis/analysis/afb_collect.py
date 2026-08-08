"""AFB before/after collection — the resumable, idempotent core (#54 Phase 2).

Collects, for each AFB item × subject in the **cold** condition, the model's **response text**
plus a judge's 0–4 score + rationale, into a compact committed intermediate
(``experiments/54_afb_before_after/data/collection.json``) that Phase 3's ``export-afb`` consumes.

**SDK-free by design.** The money-touching I/O — the subject endpoint and the Terra judge — is
**injected** as two callables, so this logic is unit-tested with mocks (no network, no spend); the
thin ``experiments/54`` runner supplies the real OpenAI-SDK clients. See #48's ``eval_afb_probes.py``
for why a dedicated run is needed: it persisted ``{id, score}`` and discarded the response text.

**Two-state, resumable, idempotent.** Collection runs in two passes so an interruption never repays
completed paid work and a judge failure after generation doesn't force re-generation:

1. **generate** — for every cell missing a ``response``, call ``generate(subject, prompt)`` and
   persist the response (atomic full-file replace) before judging.
2. **judge** — for every cell with a ``response`` but no ``score``, call
   ``judge(question, response)`` and persist the verdict.

Resume skips cells whose state is already satisfied; a completed collection issues zero calls.
Before returning, :func:`collect` validates completeness (exactly ``len(items) × len(subjects)``
unique cells, each with a non-empty response and an integer score in 0–4) — nothing partial is ever
handed to the exporter.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from analysis.loaders import AnalysisInputError

SCHEMA_VERSION = 1
VALID_SCORES = (0, 1, 2, 3, 4)


def _bad_score(score) -> bool:
    """A valid score is a real int 0–4 — NOT bool (True==1) and NOT float (2.0==2)."""
    return isinstance(score, bool) or not isinstance(score, int) or score not in VALID_SCORES


def _bad_text(s) -> bool:
    """Valid response/rationale text is a non-empty string."""
    return not isinstance(s, str) or not s.strip()

# Injected I/O contracts (kept out of this module so it stays SDK-free / mock-testable):
GenerateFn = Callable[[str, str], str]              # (subject_id, prompt) -> response text
JudgeFn = Callable[[str, str], dict]                # (question, response) -> {"score": int, "rationale": str}


def afb_item_id(q_id: str) -> str:
    """Map an AFB instrument id (``q0001``) to the catalog item id (``AFB-001``)."""
    n = int(q_id.lstrip("q"))
    return f"AFB-{n:03d}"


def load_afb_items(questions_path: str | Path) -> list[dict]:
    """Read the vendored AFB ``questions.jsonl`` → ``[{item_id, question}]`` (instrument order)."""
    items: list[dict] = []
    seen: set[str] = set()
    for line in Path(questions_path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        item_id = afb_item_id(row["id"])
        if item_id in seen:
            raise AnalysisInputError(f"duplicate AFB item id {item_id!r} in {questions_path}")
        seen.add(item_id)
        items.append({"item_id": item_id, "question": row["question"]})
    if not items:
        raise AnalysisInputError(f"no AFB items in {questions_path}")
    return items


def _cell_key(item_id: str, subject: str) -> tuple[str, str]:
    return (item_id, subject)


def _prompt(question: str, condition: str) -> str:
    if condition != "cold":
        raise AnalysisInputError(f"unsupported condition {condition!r} (only 'cold' this run)")
    return question  # cold = the question verbatim (no faith-context prefix)


class _Store:
    """The intermediate file as a resumable cell store; every mutation is an atomic full rewrite."""

    def __init__(self, path: Path, *, run_id: str, condition: str, subjects: list[str],
                 judge: str, decoding: dict, items: list[dict]) -> None:
        self._path = path
        self._meta = {
            "schema_version": SCHEMA_VERSION, "run_id": run_id, "condition": condition,
            "subjects": list(subjects), "judge": judge, "decoding": dict(decoding),
        }
        self._questions = {it["item_id"]: it["question"] for it in items}
        # cell state keyed by (item_id, subject); values carry response?/score?/rationale?
        self._cells: dict[tuple[str, str], dict] = {}
        if path.exists():
            self._load_existing()

    def _load_existing(self) -> None:
        doc = json.loads(self._path.read_text(encoding="utf-8"))
        # Meta must match the requested run (a stale/mismatched checkpoint is a hard error, not a
        # silent overwrite — fail fast rather than mixing schema/decoding/subjects across runs).
        if doc.get("schema_version") != SCHEMA_VERSION:
            raise AnalysisInputError(
                f"checkpoint {self._path} schema_version={doc.get('schema_version')!r} != {SCHEMA_VERSION}")
        for k in ("run_id", "condition", "subjects", "judge", "decoding"):
            if doc.get(k) != self._meta[k]:
                raise AnalysisInputError(
                    f"checkpoint {self._path} has {k}={doc.get(k)!r}, expected {self._meta[k]!r} "
                    f"— refusing to resume a mismatched run"
                )
        subjects = set(self._meta["subjects"])
        for c in doc.get("cells", []):
            key = _cell_key(c["item_id"], c["subject"])
            if key in self._cells:
                raise AnalysisInputError(f"duplicate checkpoint cell {key} in {self._path}")
            if c["item_id"] not in self._questions:  # unknown item → would KeyError on flush; reject cleanly
                raise AnalysisInputError(f"checkpoint cell for unknown item {c['item_id']!r}")
            if c["subject"] not in subjects:
                raise AnalysisInputError(f"checkpoint cell for unknown subject {c['subject']!r}")
            if c.get("question") is not None and c["question"] != self._questions[c["item_id"]]:
                raise AnalysisInputError(f"checkpoint question mismatch for {c['item_id']!r}")
            self._cells[key] = {k: c[k] for k in ("response", "score", "rationale") if k in c}

    def get(self, item_id: str, subject: str) -> dict:
        return self._cells.get(_cell_key(item_id, subject), {})

    def set_response(self, item_id: str, subject: str, response: str) -> None:
        self._cells.setdefault(_cell_key(item_id, subject), {})["response"] = response
        self._flush()

    def set_verdict(self, item_id: str, subject: str, score, rationale) -> None:
        # Strict judge contract: an actual int 0–4 (NOT bool/float/str-coercible) + a non-empty rationale.
        if _bad_score(score):
            raise AnalysisInputError(
                f"judge returned non-integer/out-of-range score {score!r} for {item_id}/{subject}")
        if _bad_text(rationale):
            raise AnalysisInputError(f"judge returned empty rationale for {item_id}/{subject}")
        cell = self._cells.setdefault(_cell_key(item_id, subject), {})
        cell["score"] = score
        cell["rationale"] = rationale
        self._flush()

    def _serialize(self) -> dict:
        cells = []
        for (item_id, subject) in sorted(self._cells):  # deterministic order
            c = self._cells[(item_id, subject)]
            row = {"item_id": item_id, "question": self._questions[item_id], "subject": subject}
            for k in ("response", "score", "rationale"):
                if k in c:
                    row[k] = c[k]
            cells.append(row)
        return {**self._meta, "cells": cells}

    def _flush(self) -> None:
        """Atomically replace the intermediate file (write temp + os.replace)."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(self._path.suffix + ".tmp")
        tmp.write_text(json.dumps(self._serialize(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        os.replace(tmp, self._path)

    def validate_complete(self, items: list[dict], subjects: list[str]) -> None:
        """Fail fast unless every (item, subject) cell meets the FULL strict contract.

        Applies the same strictness as :meth:`set_verdict` (int 0–4, not bool/float; non-empty text)
        so a resumed/hand-edited checkpoint carrying ``score: 2.0``/``true`` or a blank rationale
        cannot be marked complete and reach the exporter.
        """
        expected = {(it["item_id"], su) for it in items for su in subjects}
        have = set(self._cells)
        missing = expected - have
        if missing:
            raise AnalysisInputError(f"collection incomplete: {len(missing)} cell(s) missing, e.g. {sorted(missing)[:3]}")
        extra = have - expected
        if extra:
            raise AnalysisInputError(f"collection has {len(extra)} unexpected cell(s), e.g. {sorted(extra)[:3]}")
        for key in sorted(expected):
            c = self._cells[key]
            if _bad_text(c.get("response")):
                raise AnalysisInputError(f"cell {key} has no/invalid response")
            if _bad_score(c.get("score")):
                raise AnalysisInputError(f"cell {key} has invalid score {c.get('score')!r}")
            if _bad_text(c.get("rationale")):
                raise AnalysisInputError(f"cell {key} has no/invalid rationale")


def collect(items: list[dict], subjects: list[str], generate: GenerateFn, judge: JudgeFn, *,
            decoding: dict, run_id: str, out_path: str | Path, condition: str = "cold",
            judge_model: str = "openai/gpt-5.6-terra", concurrency: int = 1,
            on_persist: Callable[[str, str, str], None] | None = None) -> dict:
    """Collect responses + verdicts for every item × subject; resumable, idempotent, validated.

    Two passes (generate, then judge), each concurrency-bounded with a **single writer** (results
    are persisted on the calling thread, so the atomic full-file replace is never racy). A mid-pass
    failure NEVER discards completed paid work: every succeeding cell in the pass is persisted, and
    an aggregate error is raised only after the pass drains (resume then re-issues just the failed
    cells). ``on_persist(phase, item_id, subject)`` fires after each persisted cell (progress hook).
    Returns the final intermediate document (also written to ``out_path``).
    """
    if not items or not subjects:
        raise AnalysisInputError("collect requires non-empty items and subjects")
    out_path = Path(out_path)
    store = _Store(out_path, run_id=run_id, condition=condition, subjects=subjects,
                   judge=judge_model, decoding=decoding, items=items)
    q = {it["item_id"]: it["question"] for it in items}
    note = on_persist or (lambda *_: None)

    # Pass 1 — generation: fill any cell missing a response (persist before judging).
    gen_work = [(it["item_id"], su) for it in items for su in subjects
                if not store.get(it["item_id"], su).get("response")]
    _run_pass(gen_work, concurrency,
              task=lambda item_id, su: generate(su, _prompt(q[item_id], condition)),
              persist=lambda item_id, su, resp: store.set_response(item_id, su, _require_text(resp, item_id, su)),
              on_done=lambda item_id, su: note("generate", item_id, su))

    # Pass 2 — judging: fill any cell with a response but no score.
    judge_work = [(it["item_id"], su) for it in items for su in subjects
                  if store.get(it["item_id"], su).get("response") and store.get(it["item_id"], su).get("score") is None]
    _run_pass(judge_work, concurrency,
              task=lambda item_id, su: judge(q[item_id], store.get(item_id, su)["response"]),
              persist=lambda item_id, su, v: store.set_verdict(item_id, su, v.get("score"), v.get("rationale")),
              on_done=lambda item_id, su: note("judge", item_id, su))

    store.validate_complete(items, subjects)
    return json.loads(out_path.read_text(encoding="utf-8"))


def _require_text(resp: str, item_id: str, subject: str) -> str:
    if not isinstance(resp, str) or not resp.strip():
        raise AnalysisInputError(f"empty response for {item_id}/{subject}")
    return resp


def _run_pass(work: list[tuple[str, str]], concurrency: int, *, task, persist, on_done) -> None:
    """Run ``task`` for each (item, subject) with bounded concurrency; ``persist`` on the main thread.

    Crucially, a failure does NOT throw away completed paid work: every succeeding cell is persisted
    (on the calling thread, so the atomic write never races), failures are collected, and an
    aggregate ``AnalysisInputError`` is raised only after the whole pass drains. Resume then re-issues
    only the failed cells — one flaky judge cannot re-cost the rest of the queue.
    """
    if not work:
        return
    if concurrency <= 1:
        for item_id, su in work:  # sequential: a raise here has persisted every prior success already
            persist(item_id, su, task(item_id, su))
            on_done(item_id, su)
        return
    errors: list[str] = []
    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        futs = {ex.submit(task, item_id, su): (item_id, su) for item_id, su in work}
        for fut in as_completed(futs):
            item_id, su = futs[fut]
            try:
                # persist is inside the try: a persist failure (e.g. set_verdict rejecting a malformed
                # verdict) must NOT escape and discard the other completed futures either.
                persist(item_id, su, fut.result())  # main-thread persist → atomic write never races
            except Exception as e:  # noqa: BLE001 — collect, persist the rest, raise after the drain
                errors.append(f"{item_id}/{su}: {e!r}")
                continue
            on_done(item_id, su)
    if errors:
        raise AnalysisInputError(
            f"{len(errors)} cell(s) failed this pass (successes persisted; resume re-issues only these): "
            f"{errors[0]}" + (f" (+{len(errors) - 1} more)" if len(errors) > 1 else ""))
