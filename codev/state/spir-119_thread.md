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
(pilot ran 138–151; tighten in 3b).

## 2026-09-04 — Phase 3b (remaining 30) — plan & handling notes

All 30 are "keep" consensus scenarios (no new envelopes — Q18/Q42 were the only two, both in pilot).
3 extraction agents running (batches: Q03–14, Q15–31 subset, Q32–49 subset). Author per the LOCKED
FORMAT + receipt rule (both directions). Remaining id↔Q map (from the thread's full list):
UNI-002=Q03 003=Q04 004=Q05 005=Q07 006=Q09 007=Q10 008=Q11 009=Q12 010=Q13 011=Q14 012=Q15
013=Q16 015=Q19 016=Q20 017=Q21 018=Q23 019=Q25 021=Q29 022=Q30 023=Q31 024=Q32 025=Q33 026=Q34
027=Q35 028=Q36 030=Q41 032=Q43 033=Q46 035=Q48 036=Q49.

**SPECIAL HANDLING (don't miss):**
- **UNI-013 (Q16)** porn discovery: include the universal **minors/coercion → civil-authority** floor
  (Reformed Notes). Wing variation (divorce downstream) is NOT what the scenario asks — keep.
- **UNI-030 (Q41)** undocumented neighbour's injured father: judge-guidance must **DEFUSE the guide's
  "cover for a crime" bullet** — helping get medical care is commanded mercy, not lawbreaking
  ("binding a wound is commanded mercy"); include the medical safety floor (broken arm unset). Likely
  register: safety.
- **Silent columns to NAME** (from adjudicated.json): Q23→R2, Q25→R6, Q31→R1(anabaptist), Q33→R1+R2,
  Q34→R2, Q43→R5(pentecostal), Q49→R3. Resolve R-codes via each worksheet's own silence flag (the
  extraction gives per-strand silence). Most others 0 silent.
- **internal_variation among the 30** (all KEEP per the spec-gate audit): Q16,19,21,30,31,41,43 —
  variation is idiom/route/degree or a fringe the standards reject (Q30/Q31 deliverance-only,
  faith-maximalist); note lightly where load-bearing, do not crown a wing.
- identity_signal: default **clean**; leaky only where the trouble is intrinsically religious
  (assurance, prayer, church-conflict). Keep clean the majority.

**Authoring approach (Phase 3b):** 7 exemplars authored by me (UNI-001/014/020/024/029/031/034,
all committed, --strict clean). Remaining 29 delegated to 3 general-purpose drafting agents
(batches Q03-14, Q15-31 subset, Q33-49 subset) reading a shared spec
(scratchpad/authoring-spec.md) + the exemplars + worksheets from disk. **Ground truth is the judge
seam, so my review is the quality gate**, not the agents: on return I (1) validate --strict; (2)
spot-check receipts PER COLUMN against the worksheets (the load-bearing rule — no over/under-claim);
(3) verify difficulty bar + no-crowning + silent columns named; (4) confirm special handling —
UNI-030/Q41 crime-covering DEFUSAL, UNI-033/Q46 register guidance_claim, UNI-036/Q49 register grief,
UNI-013/Q16 minors floor; (5) fix issues, then commit + per-phase consult. Never ship agent-drafted
ground truth unreviewed. Per-phase consult: **codex APPROVE, claude APPROVE** (both HIGH; claude
REPL-verified the regex incl. trailing-newline/int-reject, validated all 8 on-disk traditions
--strict, confirmed no forked ScenarioMeta downstream in workflows/judging/loaders.py — so Phase 4
won't break on the new key). Took the one cheap non-blocking comment: added a round-trip assert.

**Carryovers from Phase 1 review (don't drop):**
- **Phase 3b**: scope-integrity test must enforce `question_id` UNIQUENESS across the 36 (not just
  count) — two folders could share a QNN and pass.
- **Phase 2**: commit the untracked `traditions/protestant-unified/guide.md` draft early (afx
  cleanup destroys untracked data scar).

## 2026-09-04 — Phase 3b COMPLETE (all 36 scenarios) — review done

All 29 delegated scenarios landed (batches A/B/C). **My review:**
- `validate --strict` → **0 findings** on all 36; **114/114** pytest (band-names scans every
  judge-guidance).
- `question_id` set = exactly the 36 kept Qs (36 unique, no dups, no Q17/Q22/Q50).
- identity_signal **28 clean / 8 leaky / 0 intrinsic** (clean majority — no monolith tilt).
- registers: 30 standard, 2 safety (UNI-001/030), 2 grief (UNI-023/036), 1 guidance_claim
  (UNI-033), 1 assurance_crisis (UNI-034). discernment 21 antinom / 10 legal / 5 balanced.
- All 36 carry Direction + discernment= + Correctives; turn1 all ≤155w.
- **Receipt audits (per-column, sampled)** all accurate: UNI-005 Mark 8:36 not in Lutheran ✓;
  UNI-004 1 Cor 7 not in Anabaptist ✓; UNI-011 Matt 5:42 = 6 cols all-but-Reformed ✓; UNI-030 Matt
  25 = 6 cols all-but-Reformed ✓; UNI-002 Matt 18:15 + Rom 12 all-7 ✓.
- Special handling verified: UNI-030 crime-defusal (mercy≠lawbreaking; safety), UNI-033
  guidance_claim, UNI-036 grief (rejects "at least it was early"; Anglican silent), UNI-013 minors
  floor, UNI-015 holds shared warning WITHOUT crowning marriage-permit/forbid.
- **KNOWN DEVIATION — length:** delegated judge-guidance runs 950–1330w vs ~750 target (25/36
  >950). Content faithful; flagging for the per-phase consult. If flagged → targeted compression of
  Direction/Correctives (NOT receipts) on the >1100 offenders (UNI-023/036/033/022/018/019/030/021/035).

Phase 3b committed; running per-phase consult next.

## 2026-09-04 — Phase 3b review fixes (iter1: claude APPROVE, codex REQUEST_CHANGES)

3 items, all fixed:
- **Receipt over-claims:** exhaustive per-column audit (subagent) → 6 false "every column" claims
  (incl. 1 in my own exemplar UNI-024). Fixed + re-verified: UNI-024 Matt18→4 cols, Gen1/Jas3→
  all-but-Lutheran; UNI-019 1Kings→all-but-Lutheran; UNI-022 2Tim1:7→Pentecostal-only; UNI-008 Prov
  bundle split (only 22:26-27 universal). Lesson: my sampling missed some — receipts need EXHAUSTIVE
  per-column verification, not spot-checks.
- **Process-vocab leak (claude catch):** 'spec-approval gate'/'keep-with-envelope' stripped from
  judge ground truth of UNI-014/015/031.
- **Length:** compressed 12 files >1050w (prose only; bullets/loci/scores untouched, diff-verified).
  Range now 747-1277. Structural finding: ~750 target unreachable — receipt bullets alone run
  459-607w (the derived-with-receipts contract); residual length is receipts, not verbosity. Made
  the case in the rebuttal; if architect wants a hard cap the only lever is fewer named columns (a
  fidelity trade I won't make unasked).
--strict 0; 114/114; scores+structure intact on all 36. iter2 consult running.

## 2026-09-04 — Phase 3b iter3: BOTH APPROVE (HIGH). MODULE COMPLETE.

codex APPROVE + claude APPROVE (fresh 12-claim receipt audit found zero false attributions).
protestant-unified is fully built: 36 scenarios, --strict 0 findings, receipts per-column verified,
process/coding vocab stripped from ground truth, length at faithful floor. Phases 1/2/3a/3b DONE.

Next: **Phase 4 — scoring run** (the only phase that spends). Opens toward the SMOKE CHECKPOINT
where (per architect) they review the module in this worktree + I send usage-computed actuals per
key + rate verification + roster-normalization result + batch-Opus confirmation, then STOP for the
explicit go. Keys via taqwabench/.env (OpenRouter subjects+Gemini; CEFE Anthropic key BATCH for
Opus, scoped ANTHROPIC_JUDGE_API_KEY→ANTHROPIC_API_KEY). Run roots in MAIN checkout
../../tmp/judging-runs/<date>-protestant-unified/protestant-unified/. Configs: protestant-unified-
run.yaml (full panel) + -gemini.yaml. Pre-flight: verify the 4 frozen roots exist by exact name
(20260803-merged, -unstated-opus, -framings-opus-sample, 20260823-opus-fullgrid).

## 2026-09-04 — Phase 4 setup done; awaiting architect confirm before first live spend

No-spend prep complete: configs built (protestant-unified-{run,gemini}.yaml, identical to
protestantism #89), run-notes scaffolded (experiments/119_protestant_unified/notes.md), pre-flight
clean (keys + 4 frozen roots present, run-root shape confirmed, CLI signatures understood). Smoke
designed: collect --scenarios 1 (90 cells, OPENROUTER) → judge --config gemini (OPENROUTER) →
batch-judge submit+collect --no-fallback ANTHROPIC_API_KEY=CEFE (Opus batch) → report. Est ~$2-4.
Sent architect the smoke plan + 2 qs (OK to run? async-batch timing on smoke). Holding for confirm
before spending on live keys — first real money, at the architect's own checkpoint. NEVER export
GEMINI_API_KEY. Module is --strict clean + consult-approved, in the worktree for architect review.

## 2026-09-04 — SMOKE COMPLETE → STOPPED at spend gate (awaiting architect GO)

Batch smoke fully validated:
- CEFE probe passed (live Opus, no org-cap). Batch smoke: 90 cells, 360 judgments (Gemini 180 +
  Opus 180), uncovered 0, 0 failed. Opus batch collected via CEFE in ~12 min, 0 errored, all
  `batch:True` (batch-priced). Roster normalization PASS (5 subjects + 2 judges map in the export
  variant maps).
- Actuals (usage-computed, prices 2026-08-03): OpenRouter $4.53 + Opus batch $4.57 = $9.10 smoke.
- Full-run estimate ×36: ~$328 (OR ~$163 + Opus ~$165), under $600. Reconciles with plan ~$360.
- Sent architect the smoke report (2 msgs; part 2 held for busy). STOPPED — will NOT run the full
  ~$328 run without explicit architect GO.

**Full-run mechanics (ready once GO):** root `../../tmp/judging-runs/<date>-protestant-unified/
protestant-unified` (flat per-tradition; export root = the parent). Sequence: collect (all 36, 5
subjects) → judge --config gemini (Gemini live) → batch-judge submit + poll-collect --no-fallback
(Opus batch CEFE) → assert Opus 6,480/6,480 (per-framing n_judged==n_expected) → report. Watch spend
alert $450 / pause $550. Keys: OPENROUTER + ANTHROPIC_API_KEY=CEFE; never GEMINI_API_KEY.

## 2026-09-04 — RULE CHANGE (Waleed): equal-weight MEAN of both judges per cell
Architect heads-up: scoring rule is now the equal-weight mean of Gemini+Opus per cell, everywhere.
A SEPARATE builder implements it in exporter/leaderboard/analysis. For me:
- **Phase 4 (the run) is UNCHANGED** — I already run BOTH judges at full grid (Gemini full + Opus
  full via batch), which is exactly what mean-of-both needs (Opus is no longer badge-only; it's now
  a ranking input, so full-grid Opus is required — I was already doing 6,480/6,480). Continue.
- After the run completes: **STOP before Phase 5. Do NOT start the superset export.** Wait for the
  architect's amended-rule message, then rebase Phase 5/7 on the other builder's PR.
Acknowledged to architect.

## 2026-09-05 — PR #121 (two-judge mean) MERGED to main (106c1f39)
Architect: after the Opus batch collects → (1) report Opus actuals + 6,480/6,480 check [still required
first]; (2) rebase on main to pick up #121 (exporter/analysis now emit the combined two-judge-mean
ranking; manifest ranking block); (3) Phase 5 export 8-row superset, run-id = export date; (4) Phase 7
pin MAY include 20260803 (Waleed accepted those numbers). Stop-before-Phase-5 lifts once Opus reported.
My branch touched validator/traditions/judging-configs — no overlap expected with #121
(exporter/analysis/leaderboard), so rebase should be clean.

## 2026-09-05 — FULL RUN COMPLETE + rebased on main (#121)
- Run done: 12,960 judgments, uncovered 0; Opus & Gemini 6,480/6,480 (per-framing 2160 each). 1 Opus
  cell was unparseable on first collect → re-submitted as BATCH (no live top-up). Final actuals:
  OpenRouter $160.25 + Opus batch $168.03 = **$328.28** (on estimate; tripwires not tripped).
  Run root: ../../tmp/judging-runs/20260904-protestant-unified/protestant-unified (gitignored).
- Rebased on origin/main (post-#121). Only conflict = governance docs (CLAUDE/AGENTS/lessons-critical)
  — took main's canonical version (my #117 reconciliation superseded by #120/#121). --strict PASS,
  validator 114/114, judging 185/9-skip, #121 two-judge-mean exporter present. Force-with-lease pushed
  builder/spir-119 (remote had only my superseded pre-rebase commits).
- Architect clarifications: (a) Phase 5/7 use the combined two-judge rule (exporter emits it);
  8-row superset, run-id=export date; pin may include 20260803. (b) FROZEN-GUARD shape: raw catalog
  manifests have NO ranking block (#121 dropped as unread); only score-tier results/<run>/manifest.json
  carries ranking{rule,score_key:combined,judges,single_judge_cells}; raw shards per-judge only.
  My new-run-id export won't touch 20260803 → branch-base diff stays empty on frozen paths.
- Phase 4 done; consult running. Next: Phase 5 export under the new rule.

## 2026-09-04 — Phase 4 consult iter1 → fixes (docs/reconciliation only)
Both reviewers confirmed the RUN is complete/correct (claude re-derived the whole grid from raw:
12,960 unique cells, 6,480/judge, every Opus cell `batch:True`, gate order respected, $328.28 under
ceiling). codex REQUEST_CHANGES + claude COMMENT on the operational record — 4 items, all applied:
1. **All-in total.** $328.28 was run-only; added smoke ($9.10) + probe (exact $0.007) → **all-in
   $337.39** (billed 2026-08-03 rates), with an **ALL-IN COST RECONCILIATION** section in notes.
2. **Rate reconciliation.** report.py table dated 2026-08-03; two SUBJECT promos (sonnet-5 $2/$10,
   gpt-5.6-terra $1/$6) expired 2026-08-31, before the 09-04/05 run. No console-invoice access →
   stated a **range**: all-in **$337.39 (billed) … $356.16 (current standard)**; invoices named
   authoritative. Under $450 alert either way. Judges (gemini/Opus) unaffected.
3. **CEFE probe.** Recorded as architect-**pre-authorized** (quoted the "YES, approved as a key-path
   probe only… ≤10 cells, $1 cap, separate dir" message) in the Gate log — not an unratified
   deviation. Ran exactly inside the envelope; no live top-up during the run.
4. **Stale docs.** notes header (Opus→co-ranking mean, not badge); dropped blank placeholder table;
   config comments fixed (`--fallback`→`--no-fallback`, dropped `run --scenarios 2`/"validation
   coverage"/"full_grid:false"). No code/run-data changed. Rebuttal:
   `119-phase_4-iter1-rebuttals.md`. Re-running consult (iter2).

## 2026-09-05 — Phase 4 consult iter2 → real number errors fixed (esp. probe cap breach)
Both reviewers REQUEST_CHANGES on the reconciliation numbers (run still verified correct). Three
errors in my iter1 correction, all fixed canonically via `judging/report.py._usage_cost` (no more
hand arithmetic):
1. **Probe cost misreported.** iter1 `$0.007` was the collection-only total from a report.json
   written BEFORE the Opus judgments landed. Actual live Opus spend = **$1.2282** → **BREACHES the
   architect's $1 cost cap by ~23%** (cell count 10 was within cap). Corrected the record (was
   falsely "within cap") and **flagged to architect for ratification** — their cap. Repo scar: sum
   usage from data, never trust a report figure.
2. **Chronology backwards.** Promos expired 2026-08-31 = BEFORE the 09-04/05 run → standard rates are
   the *likely actual*, billed figure is a floor (I'd written "after this run").
3. **Run standard arithmetic $346.51/$345.94 → $345.37.** Terra scales exactly ×2.0 incl. its 633k
   cache-read tokens (promo is half of standard); my hand-delta ignored the cache discount. Matches
   both reviewers.
Final figures: run $328.28/$345.37, smoke $9.10/$9.61, probe $1.23 (live, over cap), **all-in
$338.61 (floor) / $356.20 (likely actual)** — under $450 alert. Rebuttal
`119-phase_4-iter2-rebuttals.md`. Notified architect of the cap breach. Re-consulting (iter3).

## 2026-09-05 — Phase 4 consult iter3 APPROVED + architect notes rework
- **iter3: codex APPROVE ("None"), claude APPROVE.** Run verified complete/correct; all reconciliation
  figures match to the cent. claude's 3 non-blocking nits all folded in below.
- **Architect ratified the probe cap overage** (2026-09-05T07:08:25Z, "$1.23 vs $1 cap RATIFIED, no
  rework"). Recorded in Gate log + probe section.
- **Architect notes-format instruction applied:** ONE figure of record = **$338.62** usage-computed
  **billed actual** ($328.28 run + $9.10 smoke + $1.24 probe). Spend table is billed-only; the
  standard-rate recompute is now a single labeled footnote ("what-if: OpenRouter standard rates for
  the 2 promo-priced subjects, for invoice reconciliation only" → $356.21), out of the table/summaries.
- **claude cent-fix:** probe row now $1.24 = $1.2282 CEFE Opus + $0.0070 qwen collection (the $0.007
  the earlier stale report showed); all-in $338.61 → **$338.62**. CEFE-cap quantity stays $1.23.
- **Carry-forward (claude nit #2):** `experiments/119_protestant_unified/` uses the issue number;
  spec/plan say `experiments/<PR#>_…`. Rename to the PR number at PR time (before Phase 6 fills it).
- Phase 4 substantively COMPLETE + approved. Still HOLDING before Phase 5 per architect standing order.

## 2026-09-05 — Phase 5 export DONE (architect GO 07:14:51Z)
Exported the 8-row superset, run-id **20260905** (export date), roots in load-bearing order
(20260803-merged, -unstated-opus, -framings-opus-sample, 20260823-opus-fullgrid, 20260904-protestant-unified),
`--single-judge-attempts 3`.
- **results/20260905/** (score tier, 328K): 8 traditions; ranking block `rule: mean_of_judges,
  score_key: combined, judges [opus,gemini]`, single_judge_cells attempts=3 count=2 (both from
  20260803 data — judaism MSR-025, sunni-islam JLS-122; protestant-unified full-grid, 0 single-judge).
  **The 7 record shards are byte-identical to frozen results/20260803** (verified) — only
  protestant-unified is new.
- **results-raw/20260905/** (raw tier, 142M gz): 555 per-scenario shards, all 8 traditions
  (protestant-unified 36). **Equal source fingerprint** with score tier: sha256:532e7b0f…
- **Frozen-tier immutability**: branch-base diff on results/20260803, results/20260813-protestantism,
  results-raw/{20260803,20260813-protestantism}, traditions/protestantism (excl. README) — CLEAN.
- Analysis suite 268 passed / 12 skip. SPA discovers runs by globbing the GitHub tree (no registry to
  update); appears post-merge on default branch. Baked bundle + live verification are POST-MERGE
  (verify phase), not this phase.
- **Per-tradition combined mean (ranked):** buddhism +0.6695, secular-sage +0.6349, taoism +0.6308,
  eastern-christianity +0.5405, **protestant-unified +0.4863 (5th)**, judaism +0.4656,
  roman-catholicism +0.3635, sunni-islam +0.3597. Commit e21bbb62. Running Phase 5 consult.

## 2026-09-05 — Phase 5 consult iter1: codex REQUEST_CHANGES (test) + claude APPROVE
- **codex** blocked on the missing committed-artifact fingerprint test (plan required it); **claude
  APPROVE** with the same ask as comment #4 (generic sweep). Added to `test_export_raw_writer.py`:
  `test_committed_score_raw_fingerprints_equal[run]` — parametrized over every committed dual-tier
  run (20260803, 20260813-protestantism, 20260905), asserts equal sha256 fingerprints on real bytes;
  + `test_committed_20260905_superset_shape` (combined ranking, 8 traditions incl protestant-unified).
  Suite 272 passed. Rebuttal `119-phase_5-iter1-rebuttals.md`. Re-consulting.
- **Phase 7 / review-doc TODOs from claude (non-blocking, carry-forward):**
  1. `results-raw/README.md` stale (519 shards/~126MB launch text; retention N=2 now exceeded ~305MB
     across 3 raw runs). **Architect DECIDED 2026-09-05T07:31Z: NO prune in #119** — keep
     results-raw/{20260803 (paper-pinned), 20260813-protestantism, 20260905}. Any retirement is a
     separate dedicated PR later on Waleed's call. Phase 7: just note the 3-runs-vs-N=2 policy tension
     in the review as a follow-up (no prune action).
  2. `results/README.md` "Producing/refreshing" block still 4-root 20260803 — add the exact 5-root
     command (load-bearing order + `--single-judge-attempts 3`).
  3. Spec says "Gemini ranks, Opus badge-only" but artifact ships `mean_of_judges`/`combined` — record
     the architect-sanctioned deviation in the review doc (paper table uses combined).
  5. `/results` default = newest by generated_at → a future 20260803 re-export flips default back to
     7-row; add to verify checklist.
  6. Dispatcher skips analysis on data-only changes → committed-tier tests run manually (ran green).

## 2026-09-05 — Phase 6 DONE (cross-faith analysis + paper numbers)
Built via canonical reuse (delegated the mechanical analyze.py to a subagent; I verified it
independently — re-ran, reconciliation passes live, scorecard.png renders correctly, then wrote the
narrative doc myself for voice/terminology fidelity).
- `experiments/119_protestant_unified/analyze.py` (Typer): build_combined_runs → aggregate_tradition
  → compute_tradition_stats over the 5 roots; `emit_figures` (scorecard/framing/steadfastness/
  distribution, 95% CIs); Opus-vs-Gemini agreement. HARD-FAILS unless per-tradition means reconcile
  with committed results/20260905 combined block ≤1e-9 — BOTH assertions pass.
- `docs/analysis/protestant-unified-round.md`: 8-row leaderboard, framing staircase, per-subject
  unstated-headline CIs, steadfastness, judge agreement. Terminology per Waleed (normative traditions;
  no mannered prose; full names; final-analysis voice).
- `data/output/`: paper_numbers.json + combined_stats.json + 8 figures.
- `test_phase6_reconcile_119.py` (2 passed); full analysis suite 274 passed.
- **protestant-unified = 5th (+0.4863)**, between eastern-christianity and judaism, in the
  normative-tradition lower cluster. Unstated (hardest) +0.0539 (near neutral, with RC/sunni/EC);
  guided +0.8241 (framing lift +0.77). Opus-vs-Gemini r=0.810, bias +0.045, within-±0.5 92.1%.
- Commit 158a1c8f. Running Phase 6 consult.

## 2026-09-05 — Phase 6 consult iter1: codex REQUEST_CHANGES (per-tradition CIs) + claude APPROVE
Addressed all, reusing the canonical paper_bundle bootstrap (no new stats). NB a delegated fork
returned 0 tool-uses (did NOT execute) — caught it by verifying git status/grep before trusting;
did the refinement myself.
- Per-tradition 95% CIs (scenario-cluster bootstrap, seed 12345/5000, matches trad_pooled).
  analyze.py hard-asserts bootstrap point == canonical mean-of-means ≤1e-9 (all 8). New
  tradition_ranking figure. protestant-unified +0.4863 **[+0.368, +0.590]** — CI overlaps judaism &
  eastern-christianity → "lower normative band", not a sharp 5th (now stated in the doc).
- combined_stats.json now written BY analyze.py (build_combined_stats) — data/output reproducible.
- Typer --root/--results-dir options (post-merge portability).
- Monolith sanity-check: results/20260813-protestantism combined +0.0286, far below PU +0.486
  (different scenario set/construct — directional).
- Staleness guard added to test_phase6_reconcile_119.py (committed paper_numbers.json vs shards).
  Suite 275 passed. Commit 4f3bf8c8. Re-consulting.
