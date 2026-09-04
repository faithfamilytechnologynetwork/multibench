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
open questions marked RESOLVED). Committing + running `porch approve 119 spec-approval` (explicit
human approval relayed), then into the plan phase.
