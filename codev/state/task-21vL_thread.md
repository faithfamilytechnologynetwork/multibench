# task-21vL thread — Contributor-session governance docs

## 2026-08-13 — start

Task: make external / AI-assisted contributions arrive with Spec/Plan/Review docs.
No porch project for this task — direct doc work, single small PR, merge commit.

Four touch points:
1. CLAUDE.md + AGENTS.md — add "Contributing WITHOUT the builder machinery" section,
   addressed to the AI session (both files auto-loaded by sessions).
2. .github/PULL_REQUEST_TEMPLATE.md — create (absent); add 3-checkbox docs section + exempt.
3. CONTRIBUTING.md — create (absent); short human-facing pointer.
4. Link (not duplicate) the reference examples: specs/54, plans/54, reviews/48.

Placement in CLAUDE.md/AGENTS.md: after "File Naming Convention" (which describes the three-doc
naming) and before "Git Workflow" — thematically adjacent.

## 2026-08-13 — PR open

Committed all four touch points on builder/task-21vL, pushed, opened PR #87 against main.
- CLAUDE.md + AGENTS.md: identical "Contributing WITHOUT the builder machinery" section
  inserted between "File Naming Convention" and "Git Workflow", addressed to the AI session.
- .github/PULL_REQUEST_TEMPLATE.md (new): Summary + Codev governance docs checklist
  (spec/plan/review + exempt).
- CONTRIBUTING.md (new): human-facing tier rule + template links; links reviewed/54 examples.
- All reference examples linked, not duplicated; verified all link targets exist.

Docs-only change, no code or tests to run. Notified architect. Waiting for review/merge —
not self-merging (governance: PR merge is the human's call).
