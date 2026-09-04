# spir-119 — protestant-unified derived 38-scenario bench

Builder thread for Project 119. Free-text situational log.

## 2026-09-04 — Specify phase kickoff

**Task**: Build the derived `protestant-unified` tradition from the 38 same-advice questions of
the #109 guidance-divergence study, score it (dual judge, $600 ceiling), publish as the 8th
cross-faith leaderboard row for the CHI paper. Paper freeze **2026-09-09** (hard).

**Orientation done:**
- Read `docs/analysis/protestantbench-refactor.md` (the adopted decision spec; only unified-module
  parts apply this round — §3 unified source discipline, §4 composition, §6 module rules,
  §7 scoring/leaderboard).
- Read `docs/analysis/protestant-guidance-divergence-study.md` (v1 study; D=0.16 → Pathway B
  minimal; 78% same / 6% emphasis / 16% substance).
- Read `codings/adjudicated.json`. Confirmed **38 kept = 39 `same` minus Q50** (cremation,
  all-silent). Emphasis (Q06,44,45) and substance (Q02,08,24,26,28,37,38,39) are OUT (baked).
  Kept list: Q01,03,04,05,07,09,10,11,12,13,14,15,16,17,18,19,20,21,22,23,25,27,29,30,31,32,33,
  34,35,36,40,41,42,43,46,47,48,49.
- Studied module format: sunni-islam (worked example) + protestantism monolith (register + the
  disorders/graces/discernment/register/office taxonomies to carry; drop `communion`).
- **Validator finding**: `ScenarioMeta` is closed (`extra="forbid"`). Recording each scenario's
  study `question_id` needs an optional validator-schema field + negative test — the `parity_key`
  pattern the refactor §4 endorsed. This is a plan phase (validator code change → per-builder
  test dispatcher runs its pytest suite).

**Guide draft**: architect sent the Waleed-reviewed draft `guide.md` via `afx send --file`; saved
to `traditions/protestant-unified/guide.md` as the authoring starting point (not final).

**Audit done** (14 flagged questions, 98 worksheets read via subagent). My recommendations:
- **keep (10)**: Q16, Q19, Q21, Q27, Q30, Q31, Q40, Q41, Q43, Q47 — variation is idiom/route/
  degree, or a fringe the strand's own standards reject (Q27/Q30/Q31 Word-of-Faith / deliverance-
  only), or downstream of what the scenario asks (Q16 divorce, Q41 advocacy).
- **keep-with-envelope (4)**: Q17 (remarriage: Old Order/strict-Pentecostal/some Baptist forbid
  while former spouse lives — strongest hidden substantive split), Q18 (attend celebratory event),
  Q22 (IVF — 5/7 silent + conservative wings against; leading DROP candidate), Q42 (AI companion —
  5/7 silent).
- **drop**: none outright; Q22 offered to Waleed as defensible drop (→37), Q17 as drop if he wants
  zero remarriage-permission ambiguity.

Spec written to `codev/specs/119-protestant-unified-derived-38-.md` with full audit table + gate
notes. About to commit + signal SPEC_DRAFTED (porch runs the 3-way consult; then spec-approval
gate — human/Waleed decides audit rows + open questions).

**Open questions surfaced for the gate**: (1) the 14 audit outcomes [Critical]; (2) `question_id`
mechanism = validator field vs side-table [recommend validator]; (3) confirm the new superset
run-id string (NOT 20260803); (4) NAE/Lausanne validation depth [recommend prose cross-check].

## 2026-09-04 — SPEC-APPROVAL GATE PASSED (Waleed, relayed by architect)

2-way consult (codex+claude, both REQUEST_CHANGES/HIGH) → all 9 findings folded in + rebuttal.
A truncated architect message ('rove.') came first; I HELD and did not approve on the fragment.
Then two clean RESEND messages carried Waleed's explicit approval + all decisions:

**Gate decisions (binding):**
- **AUDIT: DROP Q17 (remarriage) and DROP Q22 (IVF) → final scope = 36 scenarios.** Q18, Q42
  keep-with-envelope (Q42 states thin witness); other 10 keep as-is.
- **Run-id** = export-date `YYYYMMDD` (never 20260803); protestant-unified gets its own
  `tmp/judging-runs/<date>-protestant-unified` root, superset also reads the 7 frozen 20260803 roots.
- **question_id** = Approach 1: optional `ScenarioMeta.question_id` field + negative test.
- **Opus key** = CEFE Anthropic judge key, **BATCH**, authorized for this run only; org cap GONE
  (CEFE ran the 62k-cell #110 re-judge by batch through 09-02). Target ≈$180 Opus + ≈$180
  OpenRouter ≈ $360; $600 ceiling unchanged; full run still waits for smoke actuals + architect go.
- **NAE/Lausanne** = documented prose cross-check in source.md, reported either way.

Final 36 list: Q01,03,04,05,07,09,10,11,12,13,14,15,16,18,19,20,21,23,25,27,29,30,31,32,33,34,35,
36,40,41,42,43,46,47,48,49 → UNI-001…UNI-036.

Spec updated (counts 38→36, grid 6,480 cells/judge, batch spend ~$360, gate-decisions section,
open questions marked RESOLVED). Committed; ran `porch approve 119 spec-approval` (explicit human
approval relayed) → advanced to plan.

## 2026-09-04 — Plan drafted

7 phases: (1) validator `question_id` field + negative test; (2) module skeleton + derived
guide.md/source.md/README/index; (3) the 36 consensus scenarios strict-validated (pilot-lock ~6
first); (4) scoring run behind the smoke→actuals→architect-go spend gate (CEFE batch Opus); (5)
superset export (8 rows) + raw re-bake + frozen-tier guard + fingerprint-equality; (6) cross-faith
analysis + paper numbers (experiments/ + docs/analysis + matplotlib); (7) monolith retirement +
reconciliation pin (after Waleed accepts numbers). One PR; natural early-PR point after Phase 3.
Signalling PLAN_DRAFTED → porch runs 2-way consult → plan-approval gate.

**Plan consult (codex+claude, both REQUEST_CHANGES/HIGH, claude repo-verified) → all folded in.**
Key corrections (I re-verified against the repo):
- Export inputs are NOT "seven 20260803 roots" — they are FOUR phase-shaped roots consumed in a
  load-bearing ORDER: 20260803-merged, 20260803-unstated-opus, 20260803-framings-opus-sample, then
  **20260823-opus-fullgrid LAST** (wins merge precedence, earns Opus full_grid). They live in the
  **main checkout** ../../tmp/judging-runs/, not the worktree.
- A run root = per-tradition subdirs: <root>/<tradition>/judgments.jsonl + report.json (exporter's
  full-grid universe comes from report.json).
- Phase 4 now names configs (protestant-unified-{run,gemini,opus-batch}.yaml) + CLI (judging run /
  batch-judge submit|collect / judging report). Existing protestantism-opus-openrouter.yaml is
  LIVE ("no batch, do NOT touch CEFE") → CEFE batch is a DISTINCT path. CEFE key: map
  ANTHROPIC_JUDGE_API_KEY→ANTHROPIC_API_KEY scoped to the Opus batch cmds only (native/batch code
  hardcodes ANTHROPIC_API_KEY, ignores api_key_env).
- Frozen guard = `git diff origin/main...HEAD -- <paths>` (plain diff is empty post-commit).
- Assert Opus 6,480/6,480 (per-framing n_judged==n_expected), not just the tolerant full_grid badge.
- source_locus convention fixed in Phase 2 (66-book Scripture index; Romans=45; not default-1).
- Phase 3 split → 3a pilot-6 (early-PR point) + 3b remaining-30. Now 8 phases.
- Phase 7 pin = apps/multibrowser/src/lib/leaderboard.test.ts; fallback if Waleed acceptance late.
- Confirmed no-ops: SPA discovers run-ids at runtime (no frontend change); fingerprint-equality
  test already exists (test_export_raw_writer.py:219); reconciliation test on committed artifact.

Rebuttal written. Committing "Plan with multi-agent review" → porch done → plan-approval gate.

## 2026-09-04 — PLAN-APPROVAL GATE reached (awaiting human)

Plan went through 3 consult iterations (codex+claude); converged. claude verified against the repo
all three rounds (COMMENT by iter-2/3); codex's blockers (export-root reality, run mechanism, CEFE
key mapping, silent live-fallback, deploy-before-merge, config/command pairing) all resolved with
verified repo facts. Iter-3 refinements folded: two-config shape (dropped opus-batch; key from
env), config↔command pairing, Opus 6,480 from run root not pooled manifest, frozen guard +
results/20260813-protestantism, post-merge deploy split, Phase 2 band-names/maintainers fixes.

8 phases final. Requested plan-approval gate; notified architect; NOT self-approving — waiting for
explicit human approval, then I run `porch approve 119 plan-approval` and enter implement (Phase 1).
