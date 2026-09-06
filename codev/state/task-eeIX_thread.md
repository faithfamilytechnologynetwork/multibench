# task-eeIX — Flip judaism scholar_review to complete

**Task (Waleed's decision, 2026-09-06):** mark the judaism tradition's first expert
scholar-review pass as complete.

## What I changed
- `traditions/judaism/tradition.yaml` — `scholar_review.status: in_progress → reviewed`.
- `traditions/judaism/README.md` `## Scholar review` — rewrote to state the first expert
  pass is **complete** (Daniel Slate, Yeshiva/Kollel; 10-scenario sample + guide + source via
  the review tool; corrections applied in PR #114; formal submission recorded 2026-09-06).
  Kept the honest note that this is one reviewer from one stream and further multi-stream
  review is welcome, and that the status decision is Waleed's.
- `apps/tradition_validator/tests/test_judaism_slate_revision.py` — the regression guard
  pinned `status == "in_progress"`; updated it to `"reviewed"` with a note on Waleed's decision.

## Key decision: "complete" → schema value `reviewed`
The schema (`tradition_validator/models.py:34`) allows only `none | in_progress | reviewed`.
There is **no `complete` literal** — writing `complete` verbatim fails `--strict` validation
and would never render as done in the SPA (`TraditionHeader.tsx:16` treats `reviewed` as the
green success badge). So "complete" (Waleed's plain-English word) maps to the schema's terminal
value `reviewed`. Flagged this mapping to the architect. If the literal string "complete" is
actually wanted, that's a larger schema + SPA + test change (~4 files) — not done here.

## Verification
- `validate traditions/judaism --strict` → PASS (0 errors, 0 warnings).
- `pytest apps/tradition_validator/tests/` → 114 passed.
- Confirmed no other file pins judaism status to `in_progress` (the two remaining hits are a
  generic value→color map and the schema enum).

## Status
PR opened; reported number to architect. STOP — do not merge without architect's relay of approval.
