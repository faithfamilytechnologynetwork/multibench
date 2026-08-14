# spir-92 — Multibrowser data platform (Postgres serving layer)

Builder thread. Project 92 / issue #92. Protocol: SPIR (strict). Spec + plan gates warranted.

## Status
- **2026-08-13** — Started. Phase: **specify**. No pre-existing spec; authoring from the issue.
- **2026-08-13** — Spec drafted & committed (`[Spec 92] Initial specification draft`). Signaled
  SPEC_DRAFTED; porch runs the 3-way (codex+claude) consult next. Checks (exists + required
  sections) pass.

## Spec recommendations (my calls, open to consult/architect)
- Overall arch: Postgres+thin API behind existing `lib/queries.ts` hook seam (issue's direction).
- Raw storage: **Postgres bytea** now, object-storage as escape hatch.
- Ingest: **Python `analysis ingest`** → Drizzle-owned schema via SQL + schema-drift contract test.
- Auth: **magic-link primary**, optional GitHub OAuth.
- Cutover order: results → raw → corpus → review (lowest-risk-first).
- 4 Critical open Qs flagged for architect: raw storage, ingest/schema authority, auth scope,
  corpus-in-DB-vs-git.

## Architect resolutions (2026-08-14) — all 4 Critical + 3 Important settled
- Raw storage: **bytea in Postgres** (A); object storage = escape hatch only.
- Ingest: **Python `analysis ingest`** → Drizzle schema via SQL + CI schema-drift contract test (A).
- Auth: **magic-link primary + optional GitHub OAuth**; OAuth-in-first-slice = plan-time cost call.
- Corpus: **moves to DB**. End state = **ZERO runtime GitHub reads** (github.ts + SHA poll retired).
- Cutover: order results→raw→corpus→review approved; **PR PER TIER** (not one mega-PR).
- Fail-soft: **fail visibly with a notice, NO GitHub fallback** (don't rebuild dual-source — the scar).
- Spec finalized with these; running porch check/done → consult → spec-approval gate.

## Consult iter1 (2026-08-14): codex REQUEST_CHANGES, claude COMMENT — both HIGH, converged
Accepted ~all. Spec revised + rebuttal written. Key fixes:
- "UI unchanged" ⚔ "zero GitHub reads" contradiction (8 routes use useLatestSha, RateLimitBanner
  imports github.ts) → reworded to "no redesign, bounded mechanical swaps"; fixed false Current-State claim.
- Ingest: independent per-tier + raw-only runs (AFB) + corpus content-hash provenance + transactional publish.
- Two data classes: serving-cache (rebuildable) vs operational review store (authoritative, backup/restore).
- Review security posture: authz isolation, single-use tokens, CSRF, PII deletion, email-provider (Resend collision).
- Read-endpoint posture + caching; retention N → Important; cost ceiling (actuals, not estimates); per-tier rollback.
Committed `[Spec 92] Specification with multi-agent review`. Running porch done → re-verify.

## Still-open (plan-time)
Freshness/version endpoint · API framework (Hono/Fastify/Express) · review data model (w/ Ben) ·
OAuth-in-first-slice y/n · raw retention N.

## Spec gate: APPROVED by Waleed (2026-08-14). Advanced to PLAN.

## Plan (2026-08-14) — DRAFTED
9 phases across **4 tier-PRs** (results→raw→corpus→review), architect's PR-per-tier call.
Plan-level decisions settled:
- API framework: **Hono** (+Drizzle +node-postgres); Fastify fallback.
- Freshness: single **`GET /api/version`** per-tier provenance envelope; replaces SHA poll.
- **Table-level Drizzle schema for all serving tiers = Phase 1** (architect note). Review tables =
  Phase 8 migration, gated on Ben's sign-off.
- Raw retention **N=2**; review auth first slice = **magic-link only** (OAuth deferred).
- Magic-link email transport chosen w/ Ben, **must not collide with `resend` CLI rule** (no direct
  api.resend.com; default Postmark/SES).
- Read cache: fingerprint-keyed ETag + immutable.
- Pre-always-on **cost gate** vs actuals (not a phase).
Phase→PR: P3→PR1(results), P5→PR2(raw), P7→PR3(corpus, deletes github.ts → ZERO GitHub reads), P9→PR4(review).
Flagged risk: porch multi-PR-per-project gate friction — raise w/ architect before P3 opens PR1.
Checks pass (plan_exists, has_phases_json, 9 phases). Signaling PLAN_DRAFTED → porch 2-way consult.

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
