# spir-92 — Multibrowser data platform (Postgres serving layer)

Builder thread. Project 92 / issue #92. Protocol: SPIR (strict). Spec + plan gates warranted.

## Status
- **2026-08-13** — Started. Phase: **specify**. No pre-existing spec; authoring from the issue.

## What this is
Move multibrowser off runtime GitHub-reading onto a **Postgres serving layer + thin API**
(new `apps/` member). Git stays source of truth; DB is a rebuildable serving cache. Four tiers:
corpus, results (score), raw, review. Review slice = the #85 read-write backend (auth + intake),
folded into this spec.

## Key context gathered
- No existing backend under `apps/` (only `multibrowser` SPA + `tradition_validator`). API is greenfield.
- Issue names `drizzle-kit generate` → Drizzle (TS ORM) owns migrations. Ingest is Python (`analysis ingest`).
- Tier contracts: `traditions/README.md`, `results/README.md` (Spec 49), `results-raw/README.md` (Spec 51).
- Review slice design = issue #85 + spec #83 (reviewer workspace, localStorage/GitHub-issue seam;
  "submit panel is the only seam to replace").
- Per-phase consult is `[codex, claude]` (Gemini blind to worktree). Full 3-way at PR gate.

## Open decisions the spec must settle (from issue Protocol)
schema · API surface · ingest contract · raw-tier storage (DB bytea vs object store) · auth · cutover order.

## Coordination
- Review-slice design is **Ben's (@benolio) seam** — coordinate. #85 stays the tracking issue.
