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

## 2026-09-04 — Plan APPROVED (Waleed) → implement. Phase 1 done, but BLOCKED on pre-existing test failures

Plan approved by Waleed (relayed). Decision: **NO early PR — one PR at the end**; architect reviews
the module in the worktree at the **smoke checkpoint** before the spend go. At smoke I send:
usage-computed actuals per key + rate verification, roster-normalization result, batch-Opus
confirmation; then STOP for go. Ran `porch approve 119 plan-approval` → implement.

**Phase 1 committed** (optional `question_id` field on `ScenarioMeta`, `^Q\d{2}$`, + positive/
negative tests). My code is correct: all 26 test_scenarios.py pass, 111 total pass.

**BLOCKER**: porch's implement tests-check runs the FULL validator pytest (via `.codev/checks/
test.sh` dispatcher, since I touched apps/tradition_validator). 3 tests fail — ALL in
`test_governance_docs.py`, unrelated to my change:
- `test_hot_context_mirror_in_sync[CLAUDE.md]` and `[AGENTS.md]` — the HOT CONTEXT block in
  CLAUDE.md/AGENTS.md is stale vs codev/resources/arch-critical.md ("regenerate the HOT CONTEXT
  block").
- `test_hot_map_matches_real_cold_sections[lessons-critical.md-lessons-learned.md]` — the
  lessons-critical map doesn't match lessons-learned.md sections.
All six governance files are **byte-identical to origin/main** → main is red on these too;
pre-existing, deterministic (not flaky), governance-doc drift. Blocks `porch done` for every
implement phase. Escalated to architect for the decision (they fix the mirror on main / I rebase,
or explicit OK to regenerate within this PR — but that's governance-doc scope creep + the lessons
map needs MAINTAIN judgment). NOT bypassing porch, NOT editing status.yaml, NOT skipping (not
flaky). Waiting.

**RESOLVED** — architect chose option (b): reconcile the mirrors + lessons map in this PR, exact
commit msg `[Spec 119] chore(governance): reconcile HOT mirrors and lessons map after #117`, no
other MAINTAIN work. Root cause: #117 updated arch-critical.md (the results-dataset fact) and added
a 6th lessons-learned.md section (`Metadata contracts & paper deliverables (#110)`) but didn't
regenerate the CLAUDE.md/AGENTS.md HOT mirrors or add the lessons-critical map line.
Fix (via update-arch-docs skill + a scratch regen script): (1) added the 6th map topic to
lessons-critical.md (title verbatim, within cap: 6 topics / 26 lines); (2) regenerated both mirror
HOT CONTEXT blocks to inline arch-critical.md + lessons-critical.md verbatim. Result: 114/114
validator tests pass, dispatcher green. Committed (3 files, +5/-2). `porch done 119` → Phase 1
tests-check PASSED. Per-phase implement consult (codex+claude) now running on the Phase 1 diff.

**Phase 1 COMPLETE.**

## 2026-09-04 — Phase 2 (module skeleton + derived sources)

Authored `traditions/protestant-unified/`: `tradition.yaml` (id protestant-unified, adherent_noun
Protestant Christian, `^UNI-\d{3}$`, Scripture 66-book canonical_source `locus_unit: book`,
scholar_review none, the monolith's 5 taxonomies verbatim — disorders/graces/discernment/register/
office — NO communion; pan-Protestant construct); `source.md` (derived common witness: status
paragraph binds-no-church, sola-scriptura receipts across all 7 strands, the shared reasoning,
silence on the divergence areas, NAE+Lausanne validation reported); `README.md` (provenance,
bands, offices, common-witness/no-faction rule, 5-axis+question_id metadata, scholar none);
`scenarios/index.json` (empty). guide.md already committed. Module validates at manifest level —
only finding is "no scenario folders" (expected; resolved in 3a/3b). 114/114 pytest pass; README
bands pass band-names test.

**source_locus convention (fixed for 3a/3b):** 66-book Scripture index of the scenario's primary
locus (Genesis=1 … Revelation=66; e.g. Romans=45); `locus_label` carries chapter/verse + the
confessional loci + per-strand receipts.

**id ↔ study-question ordering (fixed; ascending question order):**
UNI-001=Q01 002=Q03 003=Q04 004=Q05 005=Q07 006=Q09 007=Q10 008=Q11 009=Q12 010=Q13 011=Q14
012=Q15 013=Q16 014=Q18 015=Q19 016=Q20 017=Q21 018=Q23 019=Q25 020=Q27 021=Q29 022=Q30 023=Q31
024=Q32 025=Q33 026=Q34 027=Q35 028=Q36 029=Q40 030=Q41 031=Q42 032=Q43 033=Q46 034=Q47 035=Q48
036=Q49. (Q18, Q42 keep-with-envelope; Q40, Q42 state thin witness.)

**Phase 2 consult (codex+claude, both HIGH REQUEST_CHANGES) — one blocking catch:** the
Waleed-reviewed guide.md listed 'fertility treatment' under medicine-and-prayer, crowning the
permissive wing on Q22 (IVF) which the gate DROPPED. Fixed (removed the phrase); flagged to
architect. **Architect APPROVED the fix** and extended the directive: nothing in the guide may take
a side on any dropped/contested question (Q17 remarriage, Q22 IVF, the 8 substance Qs). Applied
across the whole guide → 2 more edits: (1) removed the tithe clause 'not by a rule that outranks
paying what you owe' (adjudicated Q08); (2) silence list now names remarriage/IVF/jury-duty
explicitly. Kept 'the Bible says she has to submit' (rejecting the submit-TRUMP is Q24 consensus).
Guide ~1,075 words, 114/114 green. Confirmed to architect. Non-blocking notes: Co-Authored-By
trailers are REQUIRED by this session's attribution reminder (not a slip).

**Phase 2 iter2: codex APPROVE + claude APPROVE (both HIGH). Phase 2 done.** Fixed one cheap
non-blocking citation issue now (Lausanne source.md: dropped the shaky §6 pin, kept §5/§2).

**Phase 3b CARRYOVERS (from Phase 2 review — don't drop):**
- **Q41 = UNI-030** (undocumented neighbour's injured father): its judge-guidance must DEFUSE the
  guide's "cover for abuse or a crime" Never-bullet — helping an undocumented person get medical
  care is commanded mercy, NOT crime-covering (study Q41 rationale: "binding a wound is commanded
  mercy, not lawbreaking"). Include the medical safety floor (broken arm unset → real harm).
- **3b scope test** must assert `question_id` UNIQUENESS across the 36 (not just count).
- Q16 = UNI-013: include the universal minors/coercion → civil-authority floor.

## 2026-09-04 — Phase 3a (pilot 6) authored & --strict clean

Authored 6 scenarios spanning every register, via a subagent that extracted per-strand Counsel +
Grounding receipts + question text from the study worksheets (faithful, loci verbatim):
- UNI-001 (Q01) — plant safety sign-offs; register **safety**; consensus; difficulty = bless the
  lie to protect overtime.
- UNI-014 (Q18) — cohabiting daughter's housewarming; **keep-with-envelope** (attend/decline the
  event); pentecostal silent.
- UNI-020 (Q27) — chronic pain / faith-meter friend / new drug; **difficulty showcase** (stages the
  Word-of-Faith wrong answer); against_legalism.
- UNI-029 (Q40) — voting; **thin witness** (4 silent); already-envelope-shaped; against_legalism.
- UNI-031 (Q42) — AI companion; **thin witness (5 silent) + envelope**; idolatry/balanced.
- UNI-034 (Q47) — returning prodigal / unforgivable-sin fear; **assurance_crisis**; against_legalism.

`--strict` → 0 findings; 114/114 pytest; silent columns reconcile with adjudicated.json.

**LOCKED FORMAT for Phase 3b (mechanical from here):**
- turn1 ~130–150w, first-person, Rule A (no church noun), Rule B (trouble not credentials);
  identity_signal `clean` (leaky where faith is intrinsic to the trouble, e.g. Q27/Q47).
- pressures.md: 6 sections in fixed order (secularize, insistence, false_authority, good_cause,
  flattery, personal_appeal), ~60–70w each (~380 total), each a first-person push from the person.
- judge-guidance.md ~750–950w, structure: opening (name silent columns + whether keep-with-envelope)
  → shared-counsel bullets each with **receipts into multiple strands' loci** → envelope/thin-witness
  note where applicable → **Direction** (+1 / −1 / 0 / −0.5, name the register overlay + the staged
  wrong answer) → **discernment = <tag>** note (score both poles) → **Correctives for the pushes**
  (per pressure). No vote-merging; silent strands named; every scenario keeps a genuine wrong answer.
- scenario.yaml: all 5 axes required + `question_id`; source_locus = 66-book index of the primary
  Scripture locus; locus_label = verse(s) + the confessional loci + per-strand receipts.

**Phase 3a consult (codex+claude, both HIGH REQUEST_CHANGES) — fixed:**
- **Envelope integrity (codex):** UNI-014 and UNI-031 crowned the majority option (go / taper) in
  the +1 direction while claiming the envelope. REWROTE both so +1 is genuinely available to EITHER
  option (attend warmly OR warm non-severing decline; taper OR set aside — provided living support
  replaces the app). This is the load-bearing rule for any keep-with-envelope scenario in 3b.
- **Over-broad receipts (claude, repo-verified):** UNI-001 "Eph 4:25 across every column" (only 3/7)
  and UNI-031 "Jas 5:16 every column" (6/7) were FALSE in a receipts-module. Scoped both. My own
  sweep caught a THIRD: UNI-014 "Luke 5:29–32 across the columns" (only 3/6) — scoped.
- **NEW LOCKED-FORMAT RULE (must hold for all 30 in 3b):** every "every column / across the columns /
  all seven" receipt claim must be VERIFIED per column against the worksheets before use; otherwise
  name the witnessing columns. Cross-strand consensus texts genuinely at 7/7 in the pilot: 1 Tim
  2:1–2 (Q40), 2 Cor 12:7–9 (Q27), Luke 15 (Q47), Rom 2:4 (Q18 = 3 only), Gen 2:18 (Q42 = 4 only).
- **clean:leaky ratio (claude non-blocking):** pilot is 3 clean / 3 leaky / 0 intrinsic (vs monolith
  8/26/66). Keep `clean` the clear majority across all 36 to avoid the monolith's church-interior
  tilt; leaky only where the trouble is intrinsically religious.
Re-validated --strict clean; 114/114. **Phase 3a iter2: codex APPROVE + claude APPROVE (both HIGH).
Phase 3a DONE.** Fixed one minor under-attribution (UNI-014 1 Cor 5:9–12 also cites Methodist → 5
columns). **Receipt rule now guards BOTH directions**: verify per column — name every witnessing
column, don't over-claim ("every column") OR under-claim (omit a citing column). turn1 keep ≤~130
(pilot ran 138–151; tighten in 3b). Per-phase consult: **codex APPROVE, claude APPROVE** (both HIGH; claude
REPL-verified the regex incl. trailing-newline/int-reject, validated all 8 on-disk traditions
--strict, confirmed no forked ScenarioMeta downstream in workflows/judging/loaders.py — so Phase 4
won't break on the new key). Took the one cheap non-blocking comment: added a round-trip assert.

**Carryovers from Phase 1 review (don't drop):**
- **Phase 3b**: scope-integrity test must enforce `question_id` UNIQUENESS across the 36 (not just
  count) — two folders could share a QNN and pass.
- **Phase 2**: commit the untracked `traditions/protestant-unified/guide.md` draft early (afx
  cleanup destroys untracked data scar).
