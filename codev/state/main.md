# main (architect) — orchestration log

Architect session state for MultiBench. Companion to the per-builder `*_thread.md` files
in this directory. Last updated: 2026-07-02. **To resume: read "Open / next" below.**

## Project
MultiBench — a cross-tradition benchmark measuring whether an AI assistant is *good
spiritual company* (the formative effect of its counsel), generalizing JaleesBench beyond
Islam. Repo: `faithfamilytechnologynetwork/multibench` (public).
JaleesBench (the original, single-tradition tool being ported) lives locally at
`/Users/mwk/Development/fftn/taqwabench/jaleesbench/jaleesbench/`.

## Architecture (as built)
- **Tradition format** — `traditions/<id>/`, file-based (prose=Markdown, metadata=small YAML;
  only `scenarios/index.json` is JSON). `tradition.yaml` + README/source/guide + `scenarios/<ID>/`
  each with `scenario.yaml` + `turn1.md` + `judge-guidance.md` + `pressures.md`. Spec 1.
- **Judge seam:** each scenario's `judge-guidance.md` IS the judge's binding ground truth.
- **Universal core:** framings (unstated/stated/guided) + 6 pressures
  (`apps/tradition_validator/tradition_validator/core.py`).
- **apps/** — `tradition_validator` (format gate); `multibrowser` (frontend SPA, DEPLOYED).
  **workflows/** — `judging` (the LLM-as-judge pipeline, MERGED but fidelity-broken — see below).

## Traditions on `main` (5; all `validate-all --strict` clean)
sunni-islam (JLS,140) · eastern-christianity (BZ,106) · judaism (MSR,40) · buddhism (BUD,40) ·
taoism (TAO,40). **Scoring is numeric −1..+1 with NO band names** (per #17/#18): the 4 non-sunni
traditions' judge-guidance.md were normalized from per-tradition names (Like water, Myrrh, …) to
bare numbers; sunni-islam had no labels. Consider a CI `validate-all --strict` gate.

## Completed / merged
- **#1** Spec 1 (format + validator + sunni-islam) · **#4/#5/#6** governance/validator/rename.
- **#7 multibrowser** ✅ SHIPPED — PR #13 + Railway fixes #14/#15/#16. LIVE:
  https://multibrowser-production.up.railway.app (Railway proj 1c771f78, workspace Haadi;
  build=pnpm build, start=serve -s dist; `railway up --service multibrowser --detach`).
  Gotcha: Nixpacks defaults node 18 but Tailwind v4 oxide needs node>=20 → engines.node:20.x
  ([[railway-nixpacks-tailwind4-node20]]). Issue #7 closed, worktree/branch removed.
- **#17 band-name normalization** ✅ — PR #18 merged (d… /merge e435fb7). 226 judge-guidance.md
  + 4 READMEs → numeric. Worktree cleaned (`afx cleanup -p 17`, bare number, NOT -i).
- **#8/#20 judging pipeline** ✅ MERGED (merge commit 2afc35a) — but FIDELITY-BROKEN (see below).
- **#24 Gemini judge fix + `--scenarios`** ✅ MERGED (d4a7ac1). The port's Gemini judge 400'd on
  EVERY call (numeric score enum + additionalProperties that google-genai rejects) → dual judging
  was fully broken; mocked suite + CMAP missed it (they mock the provider seam). Fix =
  providers._to_gemini_schema (string enum + strip additionalProperties + cast back) + regression
  test hitting the real google.genai Schema. Plus `--scenarios N` (--limit caps subject-outer
  cells, not scenarios). [[testing-llm-pipelines-mock-boundary]]

## Active builder
- **spir-8 (judging, #8)** — pipeline merged; now on the **FIDELITY REMEDIATION** (below).
  verify-approval gate is **PENDING and MUST NOT be approved** until the fidelity fix lands +
  a good live run. Worktree `.builders/spir-8`.

## 🔴 The judging port-fidelity failure (the live thing)
"Port, don't redesign" (JaleesBench→judging) was the mandate; the port dropped the original's
NON-FUNCTIONAL behavior. Discovered when a live 5-scenario × 5-faith dual-judge test run crawled
(~28s/sitting, serial, full price) — it cost real tokens; the slowness was the only thing that
capped the loss. **Killed the run.** Ran a full 4-agent audit (JaleesBench vs port). Findings:
- **Serial collection AND judging** — JaleesBench is 16-way async-parallel (Semaphore+gather);
  port's `config.concurrency=8` field is DEAD (never read).
- **Batch judging dropped** — JaleesBench batches Anthropic+Gemini @50% w/ live fallback.
- **Subject-side prompt caching dropped** (framing 1h + turn-1); judge path kept its caching.
- **Judge thinking flipped ON** (original: off) AND Gemini thinking-tokens uncounted → cost
  UNDER-reported.
- **Deliverables rubric compressed** (rule 6/7 + 5 worked examples lost) → judge under-instructed.
- **`raw` judge text dropped**; weaker Gemini finish_reason diagnostic; v2 re-judge prompt to verify.
- Intentional reframes (NOT bugs): numeric scores, guide+judge-guidance anchor, Claude-only
  subjects, citation/mapping/html/web/Arabic dropped. Port also improved: self-judge skip,
  schema-constrained verdicts, injection hardening, coverage accounting.
- **User decisions:** thinking STAYS ON (deliberate deviation); FULL parallel+batch restore;
  Gemini stays `gemini-3.5-flash` (deviation). [[port-dont-redesign-fidelity]]
- **Remediation plan (authoritative):**
  `/private/tmp/claude-501/-Users-mwk-Development-faithfamilytechnologynetwork-multibench/df75091b-49c2-4945-875d-14d9ee6b868f/scratchpad/spec8-fidelity-remediation.md`
  Handed to spir-8: amend Spec 8 (promote parallelism/batching/caching/full-rubric to
  REQUIREMENTS + document deviations) → PHASED plan → **plan-approval (bring to user)** → implement
  (verification MUST include a real-client contract test + a live smoke).

## ✅ Reconciliation DONE (2026-07-02)
The 4 locally-patched judging files were verified byte-identical to origin/main (sole residual: a
stray unused `import copy` in providers.py, removed by edit — matching spir-8's flagged cleanup in
#24). Index synced via `git checkout origin/main -- <files>` + `git merge --ff-only origin/main`.
Main is now at d4a7ac1, clean except this architect-log file.

## Test-run mechanics (for the re-run after the fix)
Keys: ANTHROPIC from `/Users/mwk/Development/fftn/taqwabench/.env`; GEMINI from
`/Users/mwk/Development/hobbies/.env` (NOT in the jaleesbench .env). Run per tradition:
`uv --project workflows/judging run python -m judging run traditions/<id> --scenarios 5 --results-dir <dir>`.
Default config = 2 subjects (opus+sonnet) × dual judge (opus+gemini-3.5-flash) × 3 framings × 6
pressures × 2 scopes = 180 sittings/tradition. Re-run only AFTER fidelity fix (fast + batched).

## Key conventions
- **Merge style: MERGE COMMITS, not squash.** **Gates: never auto-approve — bring each to the user.**
- Per-phase consult = [codex, claude]; full 3-way CMAP only at the PR integration gate (diff inline).
- Porch checks: diff-scoped dispatcher `.codev/checks/test.sh` (app→cmd registry).
- `afx cleanup -p <N>` uses the BARE number (e.g. `-p 17`), not `-i`/zero-padded.

## Open / next  (RESUME HERE)
1. **spir-8 FIDELITY REMEDIATION — IMPLEMENTING** (plan-approval gate approved by the USER
   2026-07-02, explicit). Spec amended (M13–M21 + T18–T27) + 3-phase plan (r1 parallel+subject-
   caching → r2 batch+cost → r3 judge-quality+live-verify; ThreadPool over sync seams). Plan
   consult: Claude APPROVE; Codex's 4 tightening points addressed in iter 3 (62630dc: per-phase
   real-client construction checks, M19 raw = provider return-shape seam change, batch CLI/manifest
   tests, r1 set-equivalence). Expect implement-phase consults, then a single PR (Refs #8) →
   integration CMAP (full 3-way, diff inline) + pr gate → bring to the user.
   **r2 batching scope (USER decision 2026-07-02): Anthropic-only batching @0.5×; Gemini = live
   fallback** — the faithful port (JaleesBench batching.py:120-127 never batched Gemini; the
   spec's "+ Gemini batch job" came from JaleesBench's stale line-4 docstring). Spec M14/§4.6 +
   plan r2 wording to be corrected by the builder; no developer-API Gemini batching.
   **r1–r3 IMPLEMENTED** (150 mocked tests pass; M20 = verified no-op, JaleesBench's "v2 prompt"
   is aspirational docstring). **LIVE SUITE PASSED 3/3** (2026-07-02, run by architect — builder
   env has no creds): anchoring, prefix-cache-hit, T27 end-to-end smoke (36 sittings, dual-judge
   incl. gemini, report OK) in 325s total → parallelism confirmed (old serial ≈28s/sitting).
   **PR #25 open; integration CMAP DONE + posted** (comment 4869724880): Claude APPROVE (HIGH);
   Gemini COMMENT — its sole KEY_ISSUE (ValueError from resp.text) REFUTED against the installed
   google-genai SDK (_get_text returns None, no raise; that was legacy google-generativeai);
   codex CMAP hit the vendored-binary ENOENT. Architect verdict: APPROVE.
   **LIVE SUITE RE-RUN 4/4** (384s) after codex's fair RC — the new T21 subject-cache live test
   post-dated the first run; cache_read>0 now OBSERVED. All 3 phases unanimous per-phase consult.
   **pr gate APPROVED by the USER** (explicit) → **PR #25 MERGED** (8fa4d26, merge commit).
   **FULL LIVE 5×5 VERIFY RUN DONE (2026-07-02): CLEAN.** 900/900 sittings, 2700 judgments,
   uncovered=0, 0 failures, **$100.08 total**, ~90 min wall (vs ~14h+ serial pre-remediation).
   Results: `tmp/judging-runs/20260702/<tradition>/` (report.md/json per tradition; gitignored).
   Ran batched first per user choice, but Anthropic batches sat 1.5h+ at 0/900 → user said
   "cancel and do live" (batches cancelled at 0 succeeded = $0 wasted; Gemini cells had been
   live-judged meanwhile via a gemini-only panel config — idempotent keys made the split safe).
   Substance: headline scores 0.4–1.0 (opus) but steadfastness-under-pressure weak everywhere
   (−0.15..+0.1; e.g. judaism secularize −1.2) — benchmark discriminates.
   **verify-approval gate: PENDING, brought to user (AFK at ask) — DO NOT approve without
   explicit user word.** After approval: builder completes → `afx cleanup -p 8`.

## ⚠️ Codex-consult infra (2026-07-02)
Codev's vendored `@openai/codex` native binary went MISSING (`…/codex-darwin-arm64/vendor/
aarch64-apple-darwin/codex/codex` ENOENT) — broke the builder's r3-iter2 consult, blocked porch
(implement/r3/iter2 "Run remaining consultations (codex)"), and the codex leg of the CMAP.
**Interim fix by architect (user AFK, reversible):** symlinked `/opt/homebrew/bin/codex` (0.139.0)
into the vendor path; smoke-verified (consult -m codex → OK, 6s). **TODO: proper repair** —
`npm i -g @cluesmith/codev` at a quiet moment (Tower up ~9 days serving 10 workspaces; don't swap
files under it casually). To revert interim fix: rm the symlink.
2. **Do NOT approve spir-8's verify-approval gate** until the fidelity fix lands + a clean live run.
3. Consider CI `validate-all --strict` on push.

## Open issues
#8 (judging — merged but fidelity remediation in progress via spir-8). #1–#7, #17 closed.
