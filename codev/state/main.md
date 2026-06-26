# main (architect) — orchestration log

Architect session state for MultiBench. Companion to the per-builder `*_thread.md` files
in this directory. Last updated: 2026-06-25. **To resume: read "Open / next" below.**

## Project
MultiBench — a cross-tradition benchmark measuring whether an AI assistant is *good
spiritual company* (the formative effect of its counsel), generalizing JaleesBench beyond
Islam. Repo: `faithfamilytechnologynetwork/multibench` (public).

## Architecture (as built)
- **Tradition format** — `traditions/<id>/`, file-based: prose = Markdown, metadata = small
  YAML; the only JSON is `scenarios/index.json`. `tradition.yaml` + README/source/guide +
  `scenarios/<ID>/` each with `scenario.yaml` + `turn1.md` + `judge-guidance.md` +
  `pressures.md`. Contract: Spec 1 / `traditions/README.md`.
- **Judge seam:** each scenario's `judge-guidance.md` IS the judge's binding ground truth.
- **Universal core:** framings (unstated/stated/guided) + 6 pressures, shared across
  traditions (`apps/tradition_validator/tradition_validator/core.py`).
- **apps/** — `tradition_validator` (Python/uv/Typer, the format gate); `multibrowser`
  (frontend SPA — PR #13, merging). **workflows/** — `judging` (#8, spec at gate).

## Traditions on `main` (5; all `validate-all --strict` clean)
sunni-islam (JLS,140) · eastern-christianity (BZ,106) · judaism (MSR,40) · buddhism
(BUD,40) · taoism (TAO,40). Traditions 2–5 were added **directly to main** via `claude/*`
branches (bypassing the validator) — they pass; consider a CI `validate-all` gate.

## Completed / merged
- **#1** Spec 1 — format + `tradition_validator` + sunni-islam (PR #2)
- **#6** rename probe→scenario / scenario.md→turn1.md (PR #9 + #10)
- **#4** governance docs (PR #12) · **#5** validator polish (PR #11)
- Builders air-4/5/6 removed.

## Active builders
- **spir-7 (multibrowser, #7)** — ✅ **SPIR COMPLETE & DEPLOYED (2026-06-25).** PR #13 merged
  (merge commit a499b6d) + 3 Railway-build config fixes (#14 pnpm10, #15 .npmrc hoisted, #16
  engines.node:20.x). **LIVE on Railway: https://multibrowser-production.up.railway.app** (HTTP
  200, SPA fallback works). verify-approval gate **APPROVED by user** → protocol complete.
  **Railway:** new project `multibrowser` (id 1c771f78, workspace Haadi) / service a0bb447d /
  env VITE_MULTIBENCH_REPO=faithfamilytechnologynetwork/multibench + VITE_MULTIBENCH_REF=main;
  builder=Nixpacks, build=pnpm build, start=serve -s dist. Deploy from `apps/multibrowser`:
  `railway up --service multibrowser --detach`. **Build gotcha (root-caused, see memory
  [[railway-nixpacks-tailwind4-node20]]):** Nixpacks defaults nodejs_18 but Tailwind v4 oxide
  linux binary needs node>=20 → "Cannot find native binding"; fix = engines.node:20.x in
  package.json. **CLEANED UP (2026-06-25, user-authorized):** issue #7 closed; worktree removed
  (was clean) + branch builder/spir-7 deleted (-D; only porch-bookkeeping commits beyond main).
- **spir-8 (judging, #8)** — spec DRAFTED, **at the spec-approval gate, AWAITING USER
  APPROVAL.** Reviewed = faithful PORT of JaleesBench's judging + generalization (per the
  user's "port, don't redesign"). User's 3 direct answers recorded: collection = minimal
  Claude collector; judge panel = config-driven, default Opus 4.8 + Gemini Flash 3.5; bands
  normalized to −1..+1 (labels cosmetic). 3 small hardening additions flagged (structured-
  output verdicts, self-judge skip, prompt-injection handling). Flagged for user
  confirmation: Guided framing as a **context-prefix** (not API system param), per Waleed's
  2026-06-12 ruling. **Architect recommendation: APPROVE.**

## Key decisions & conventions
- **multibrowser** = pure frontend Vite SPA on the team standard stack (ref:
  `cluesmith/shannon/apps/web`); GitHub client-side runtime data layer; Railway static.
  (Pivoted: static SSG → Flask → SPA. Python is not the tool for UI.)
- **Merge style: MERGE COMMITS, not squash** (porch default; user-corrected).
- **Porch checks (mixed-language repo):** `porch.checks` is global-only — use the diff-scoped
  dispatcher `.codev/checks/test.sh` (app→cmd registry; runs only the builder's touched app's
  tests). Landing via PR #13. codev gap filed: `cluesmith/codev#1103`.
- **Per-phase consult = [codex, claude]** (Gemini consult can't see the worktree); full 3-way
  only at the PR integration CMAP (diff inline — Gemini works there).
- **Gates:** never auto-approve — bring each to the user.

## Open / next  (RESUME HERE)
1. **DECIDE: spec 8 (#8) spec-approval** — the main open user decision (predates the spir-7
   deploy detour). Architect recommends **APPROVE**. On yes: `porch approve 8 spec-approval
   --a-human-explicitly-approved-this` + tell spir-8 to proceed to plan. (Or: strip any of the
   3 hardening additions / confirm the Guided-framing handling.)
2. **spir-7 ✅ FULLY CLOSED** — merged + live on Railway, verify gate approved, issue #7 closed,
   worktree + branch removed. Nothing left to do.
3. After #8 implements: spir-7 ↔ spir-8 coordinate the inert results seam ↔ the #8 result schema.
4. Consider CI `validate-all --strict` on push.

## Open issues
#7 (multibrowser — PR #13, merging) · #8 (judging — spec at gate). #1–#6 closed.
