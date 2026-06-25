# Plan 7 — SPA plan consult: rebuttal

**Reviewers:** Codex (REQUEST_CHANGES — 2) · Claude (APPROVE — "exceptionally thorough; complete
spec coverage; verified codebase claims; sound TanStack Query architecture; clean phase
decomposition a builder can follow without ambiguity"). Both Codex points **accepted and fixed**.

1. **`base: './'` (Phase 6) would likely break deep-link asset loading.** Correct — for a
   root-served SPA with history fallback, relative asset URLs break on nested routes like
   `/t/sunni-islam/JLS-001` (assets would resolve relative to the deep path). → **Fixed**: Phase 6
   now uses **`base: '/'`** (the Vite default — absolute `/assets/…`), with the rationale spelled
   out and `base: './'` explicitly rejected. (The relative-base habit came from GitHub-Pages-subpath
   hosting; Railway serves at a root domain, so absolute is correct.)

2. **Spec-mandated fallback paths weren't explicitly owned/tested in the phases.** → **Fixed** by
   assigning each to a specific phase with an explicit test:
   - **`git-trees truncated:true` → per-directory listing fallback** — Phase 2 `github.ts`
     deliverable + a `truncated:true` test.
   - **`index.json` missing/invalid → derive the scenario set from the tree's `scenarios/*/`
     folders (with a notice)** — Phase 2 `queries.ts` (`useTradition`) + a test, reusing the P1
     drift/union logic.
   - **Unknown `traditionId`/`scenarioId` → in-SPA 404 validated against discovered data** — Phase 4
     (tradition route) and Phase 5 (scenario route) deliverables + tests.

Claude (APPROVE) verified the codebase claims (the 5 real traditions + diverse axes, the GitHub
CORS/rate facts, the shannon stack) and raised no blockers.

Net: a real deploy-asset bug fixed, and three degradation paths moved from implicit to
phase-owned-with-tests. The SPA architecture and 6-phase decomposition are unchanged and endorsed.
