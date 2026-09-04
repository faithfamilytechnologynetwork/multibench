# Plan: protestant-unified — a derived Protestant bench (36 scenarios), scored and published as the 8th leaderboard row

**Specification**: [codev/specs/119-protestant-unified-derived-38-.md](../specs/119-protestant-unified-derived-38-.md)

## Executive Summary

The spec fixes the architecture (a derived unified module, scored dual-judge, published as the 8th
cross-faith row) and the gate decisions (36 scenarios after dropping Q17/Q22; `question_id` via an
optional validator field; run-id = export-date `YYYYMMDD`; Opus = CEFE key in **batch**;
NAE/Lausanne = prose cross-check). This plan sequences that work so each phase is a single atomic
commit that is independently verifiable, dependencies first.

The spine: (1) make the scenario schema able to record study provenance; (2) lay down the module's
non-scenario files (the derived `guide.md`/`source.md`, taxonomies, index); (3) author the 36
consensus scenarios compiled from the worksheets with receipts, validating `--strict`; (4) run the
scoring battery behind the smoke→actuals→architect-go spend gate; (5) export the 8-row superset +
raw tier and prove the frozen tiers are byte-untouched; (6) produce the cross-faith analysis and
paper-ready numbers; (7) retire the monolith and pin the reconciliation test to the new run. Phases
1–3 are pure data/validator work reviewable before any spend; Phase 4 is the only phase that spends
money and it carries the human go-gate; Phases 5–7 publish and document.

All phase commits land in **one PR** (opened during/after the final implement phase unless the
architect asks earlier — a natural early-PR point is after Phase 3, to review the module before the
$360 run). The scoring run and export operate on local files (the worktree `traditions/` and the
gitignored `tmp/judging-runs/` roots); nothing here touches `results/20260803`,
`results-raw/20260803`, `results-raw/20260813-protestantism`, or the monolith scenarios.

## Phases (Machine Readable)

```json
{
  "phases": [
    {"id": "phase_1", "title": "Scenario question_id field in the validator"},
    {"id": "phase_2", "title": "Module skeleton and derived sources"},
    {"id": "phase_3", "title": "The 36 consensus scenarios, strict-validated"},
    {"id": "phase_4", "title": "Scoring run behind the spend gate"},
    {"id": "phase_5", "title": "Superset export, raw re-bake, and frozen-tier guard"},
    {"id": "phase_6", "title": "Cross-faith analysis and paper numbers"},
    {"id": "phase_7", "title": "Monolith retirement and reconciliation pin"}
  ]
}
```

## Phase Breakdown

### Phase 1: Scenario question_id field in the validator

**Dependencies**: None

#### Objective

Let a `scenario.yaml` record which study question it derives from, so the 36 scenarios carry
first-class provenance (spec Approach 1 / gate decision). Without this the closed `ScenarioMeta`
rejects the field.

#### Files to Create / Modify

- `apps/tradition_validator/tradition_validator/models.py` — add optional
  `question_id: str | None = None` to `ScenarioMeta`, constrained to `^Q\d{2}$`.
- `apps/tradition_validator/tests/test_scenarios.py` (or the nearest existing scenario-model test
  module) — a positive test (a valid `question_id` accepted; absence still valid) and a **negative
  test** (a malformed `question_id` rejected with a located error).
- Only if a schema doc enumerates scenario fields: update it to list `question_id` as optional.

#### Deliverables

- [ ] `ScenarioMeta.question_id` optional field, pattern-validated, defaulting to `None`.
- [ ] Positive + negative tests.
- [ ] Existing validator suite still green (no regressions on the other traditions).

#### Acceptance Criteria

- [ ] `uv --project apps/tradition_validator run python -m pytest apps/tradition_validator` passes,
      including the new tests.
- [ ] A scenario with no `question_id` still validates (back-compat for the seven existing
      traditions); a scenario with `question_id: "Q16"` validates; `question_id: "16"` fails.

#### Test Plan

Unit tests on the model (accept/omit/reject). Full validator pytest to confirm the seven existing
traditions and sunni-islam port tests still pass. Smoke: validate an existing tradition to prove no
regression.

### Phase 2: Module skeleton and derived sources

**Dependencies**: Phase 1

#### Objective

Create `traditions/protestant-unified/` and everything in it *except* the scenario folders: the
identity, taxonomies, the pan-Protestant `guide.md`, the derived `source.md`, the README, and the
scenario index. This is the module's non-scenario spine and is reviewable on its own.

#### Files to Create / Modify

- `traditions/protestant-unified/tradition.yaml` — id `protestant-unified`, `display_name`,
  `adherent_noun: Protestant Christian`, `scenario_id_pattern: ^UNI-\d{3}$`, `scholar_review:
  status: none`, taxonomies = the monolith's `disorders` / `graces` / `discernment` / `register` /
  `office` **verbatim** (no `communion` axis); `canonical_source` describing the derived common
  witness (`locus_unit: book`); a `construct` in the pan-Protestant idiom (priesthood of all
  believers speaking the truth in love — refactor §2).
- `traditions/protestant-unified/guide.md` — finalize from the saved draft (~1,100 words), verified
  consistent with the Q18/Q42 envelopes and crowning no wing; keep the "where Protestants differ,
  this guide is silent" section (military service, oaths, Sunday work, alcohol, fasting, the tithe,
  household deadlock — i.e. the excluded substance areas).
- `traditions/protestant-unified/source.md` — the derived common-witness source with the **status
  paragraph** (binds no church, describes overlap, binds content not creedal form) and a
  **documented NAE Statement of Faith + Lausanne Covenant prose cross-check**, reported either way.
- `traditions/protestant-unified/README.md` — scope, derivation provenance (the #109 study),
  `scholar_review: none` stated honestly, the strand coverage note (refactor §2.2/§2.3).
- `traditions/protestant-unified/scenarios/index.json` — `schema_version: 1` + the 36 ids
  `UNI-001 … UNI-036`.

#### Deliverables

- [ ] `tradition.yaml` with the five carried taxonomies and no `communion` axis.
- [ ] `guide.md`, `source.md`, `README.md` authored per the discipline above.
- [ ] `scenarios/index.json` listing 36 ids.
- [ ] A test/notes mapping each `UNI-0NN` id → its study `QNN` (the ordering, fixed here).

#### Acceptance Criteria

- [ ] The module validates at the structural/manifest level (the validator's manifest + index
      checks pass; scenario-folder drift is expected until Phase 3 and is the only outstanding
      finding).
- [ ] `source.md` contains the status paragraph and the NAE/Lausanne cross-check section.
- [ ] `git diff` touches only `traditions/protestant-unified/**` (no frozen path).

#### Test Plan

Run the validator against the module and confirm the only findings are "missing scenario folders /
index-vs-folder drift" (resolved in Phase 3). Manual: word-count `guide.md` (~1,100); read
`source.md` against the refactor §3 discipline; confirm the id↔question mapping covers exactly the
36 and excludes Q17/Q22/Q50/emphasis/substance.

### Phase 3: The 36 consensus scenarios, strict-validated

**Dependencies**: Phase 1, Phase 2

#### Objective

Author all 36 scenarios so the module passes `validate --strict` with zero findings — the craft
core. Each scenario is a life-first stimulus with ground truth **compiled from that question's
seven worksheets** (Counsel first, receipts into each strand's Grounding, silent columns named), no
vote-merging, keeping a genuine wrong answer.

#### Files to Create / Modify

- `traditions/protestant-unified/scenarios/UNI-0NN/` for each of the 36 — `scenario.yaml`
  (tags across the five taxonomies, `identity_signal: clean` default, `source_locus`/`locus_label`,
  and `question_id`), `turn1.md` (~130 words, Rule A: no church noun), `pressures.md` (~400 words,
  the six pressures), `judge-guidance.md` (~750 words, structured-union compilation with receipts).

#### Deliverables

- [ ] 36 scenario folders, one per kept question, each with the four files and a recorded
      `question_id`.
- [ ] Each `judge-guidance.md` traces every claim to a cited locus in that strand's worksheet
      Grounding; silent columns for the question are named as silent.
- [ ] Q18 and Q42 carry the **keep-with-envelope** treatment (crown no wing; Q42 states thin
      witness); Q40 states its thin witness.
- [ ] Difficulty bar: every scenario stages a genuine wrong answer the guidance scores below the
      faithful response.

#### Acceptance Criteria

- [ ] `uv --project apps/tradition_validator run python -m tradition_validator validate
      traditions/protestant-unified --strict` → **zero findings**.
- [ ] Exactly 36 scenario folders; recorded `question_id`s equal the 36 kept questions; Q17/Q22/Q50
      absent.
- [ ] `guide.md` and the Q18/Q42 `judge-guidance.md` are mutually consistent (crown no wing).

#### Test Plan

Discipline: author a **pilot tranche of ~6 first** (including one envelope scenario and one
thin-witness scenario) to lock the compilation register and the difficulty bar, then scale to all
36 under the locked format. Verification: strict validator (zero findings); a sampled derivation
audit (pick 3 scenarios, trace each `judge-guidance.md` claim to its worksheet locus and confirm
silent columns match `adjudicated.json`); a difficulty spot-check (a fluent-but-wrong answer scores
below the faithful one). The per-builder test dispatcher runs the validator pytest on the touched
`traditions/` app.

### Phase 4: Scoring run behind the spend gate

**Dependencies**: Phase 3

#### Objective

Produce the `protestant-unified` judging run — the scores the leaderboard row and the paper need —
under the $600 ceiling with the smoke → usage-computed-actuals → **architect go** → full-run gate.

#### Files to Create / Modify

- `tmp/judging-runs/<date>-protestant-unified/` (gitignored) — the run root the export later reads.
- A committed run-notes file (e.g. `experiments/<PR#>_protestant_unified/notes.md` or a run log in
  the module dir) recording smoke coverage, usage-computed actuals per key, the architect-go
  timestamp, and final coverage — the Spec-89 spend-table discipline.

#### Deliverables

- [ ] Keys sourced **only** via the `taqwabench/.env` seam: subjects + Gemini via `OPENROUTER_API_KEY`;
      Opus via the **CEFE** Anthropic judge key in **batch**. Never a personal Gemini key.
- [ ] Smoke run ≥50 cells on **both** judges; batch Opus confirmed working on the smoke.
- [ ] **Usage-computed actuals** (summed from run data, not estimates) reported; **STOP** for explicit
      architect go before the full run.
- [ ] Full battery 36 × 5 subjects × 6 pressures × 3 framings, both scopes, both judges full grid;
      coverage reported honestly in the manifest.

#### Acceptance Criteria

- [ ] Total spend ≤ $600 (alert at $450, pause at $550), reconciled from usage data.
- [ ] Gemini has a full grid across the tradition (so the later export's `_assert_full_grid`
      passes); Opus full grid present as the badge/validation layer.
- [ ] The full run was **not** launched before the architect's explicit go (recorded in notes).

#### Test Plan

Pre-flight: verify the `taqwabench/.env` keys resolve and that the seven `tmp/judging-runs/20260803-*`
roots still exist (needed downstream). Smoke: inspect coverage + verdict parseability on ≥50 cells,
both judges; compute actuals from the run data. Gate: send actuals to the architect and wait. Full:
monitor spend against the alert/pause thresholds; re-judge any gaps (budgeted). Run as background
tasks that end the turn (never a foreground poll loop).

### Phase 5: Superset export, raw re-bake, and frozen-tier guard

**Dependencies**: Phase 4

#### Objective

Publish the committed dataset tiers: a new-run-id superset that shows **8 tradition rows** (the
seven frozen + `protestant-unified`), its matching raw tier, and proof that every frozen artifact is
byte-untouched.

#### Files to Create / Modify

- `results/<date>/` (committed) — `analysis export` over the seven frozen `20260803` roots + the new
  `protestant-unified` root; equal-weight mean-of-means leaderboard, Gemini rankable, Opus badge-only.
- `results-raw/<date>/` (committed) — `analysis export-raw` over the **complete 8-tradition**
  superset; equal source fingerprint with the score tier.
- `apps/multibrowser/public/data-raw/<date>/` — rsynced baked bundle for the Railway re-bake.
- A fingerprint-equality test (extend the existing tier-fingerprint test coverage) asserting the
  score tier and raw tier at `<date>` share one fingerprint.

#### Deliverables

- [ ] Superset export passes `_assert_full_grid` and the roster-mapping asserts
      (`assert_uniform_subject_roster`, `_SUBJECT_VARIANTS`/`_JUDGE_VARIANTS`); exactly one Protestant
      cross-faith row (`protestant-unified`); monolith and strands contribute none.
- [ ] Raw tier covers all 8 traditions; fingerprint-equality test passes.
- [ ] Railway two-step re-bake (`rsync` → `railway up --no-gitignore --detach` from
      `apps/multibrowser`); the **live** manifest fingerprint matches the exported tier (HTML
      content-type on a baked path treated as "absent").
- [ ] Frozen-tier immutability: `git diff` empty on `results/20260803/`, `results-raw/20260803/`,
      `results-raw/20260813-protestantism/`, `traditions/protestantism/scenarios/**`.

#### Acceptance Criteria

- [ ] The existing paper-reconciliation test still passes unchanged (the `20260803` pin holds to its
      decimals).
- [ ] An intentional Gemini gap makes `_assert_full_grid` fail (gate is real); the real full grid
      passes.
- [ ] The SPA `/results` leaderboard shows 8 rows live.

#### Test Plan

Run both exporters; run the full validator/analysis test suite (per-builder dispatcher). Diff the
frozen paths (must be empty). Curl the live baked manifest and compare the fingerprint. Verify the
8th row renders in the SPA.

### Phase 6: Cross-faith analysis and paper numbers

**Dependencies**: Phase 5

#### Objective

Turn the run into the paper-ready analysis: per-tradition means + CIs, per-framing, steadfastness,
Opus-vs-Gemini agreement, and the 8-row leaderboard numbers, in the house `experiments/` convention.

#### Files to Create / Modify

- `experiments/<PR#>_protestant_unified/` — `notes.md`, `analyze.py`, `data/output/` (reusing the
  canonical aggregator; no second implementation of the mean-of-means).
- `docs/analysis/protestant-unified-round.md` — a short narrative summary with the paper-ready 8-row
  table and the key comparisons.
- Figures via **matplotlib** (per-tradition means with CIs, per-framing, Opus-vs-Gemini agreement).

#### Deliverables

- [ ] Per-tradition means + CIs, per-framing breakdown, steadfastness, Opus-vs-Gemini agreement.
- [ ] The 8-row leaderboard numbers, reconciling with the export by construction.
- [ ] `docs/analysis/` summary + matplotlib figures.

#### Acceptance Criteria

- [ ] The analysis numbers reconcile with the committed `results/<date>/` tier (equal-weight
      mean-of-means holds).
- [ ] Figures render from `analyze.py`; no hand-rolled HTML/SVG charts.

#### Test Plan

Recompute the 8-row means from the committed tier and assert they match the leaderboard. Regenerate
figures from `analyze.py`. Sanity-check protestant-unified against the monolith's record and the
study's priors (difficulty bar held — the bench is not trivially ceilinged).

### Phase 7: Monolith retirement and reconciliation pin

**Dependencies**: Phase 5 (retirement notes); Phase 6 + Waleed's acceptance (reconciliation pin)

#### Objective

Retire the monolith from active scoring operationally and pin the paper-reconciliation test to the
new run once Waleed accepts the headline numbers — closing the loop and protecting the new numbers
the way `20260803` is protected.

#### Files to Create / Modify

- `traditions/protestantism/README.md` — retirement note (frozen on disk for the raw viewer; retired
  from active scoring; the derived `protestant-unified` supersedes it for cross-faith scoring). This
  is the **only** permitted monolith edit.
- `results/README.md` — note the monolith's retirement, the operational exclusion (excluded from the
  new run and future record-run/superset inputs while discovery stays working), and the new 8-row
  run.
- The paper-reconciliation test — **add a pin for the new run** (its 8-row headline numbers) once
  Waleed accepts them; keep the `20260803` pin intact.

#### Deliverables

- [ ] Monolith README + `results/README.md` retirement/operational-exclusion notes.
- [ ] Reconciliation test pins the new run (after Waleed's acceptance) and still pins `20260803`.

#### Acceptance Criteria

- [ ] The monolith is excluded from the new run/export inputs, while `traditions/*/tradition.yaml`
      discovery and the raw viewer for `20260813-protestantism` still resolve.
- [ ] The reconciliation test passes with both pins.

#### Test Plan

Run the reconciliation test (both pins). Confirm discovery still lists the monolith and the raw
viewer resolves. Diff to confirm the only monolith change is its README.

## Risks and Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Scenario authoring slips the 09-09 freeze (36 hand compilations) | Medium | High | Pilot-lock ~6 first, then scale; front-load Phases 1–3 (09-04); the run is the only long pole after. |
| Spend overrun (batch est. ≈$360) | Low | High | Smoke → usage-computed actuals → architect go; alert $450, pause $550; batch Opus on CEFE. |
| Superset export blocked by `_assert_full_grid` (Gemini gap) | Medium | High | Run Gemini full grid; budget re-judge inside the ceiling; verify roster mappings before export. |
| Accidental mutation of a frozen tier | Low | High | Additive-only exports; new run-id; explicit `git diff` gate + reconciliation test before PR. |
| Loss of gitignored `tmp/judging-runs/20260803-*` roots (afx cleanup scar) | Low | High | Pre-flight existence check in Phase 4; never run cleanup. |
| A keep-with-envelope scenario (Q18/Q42) crowns a wing or reads easy | Medium | Medium | Envelope crowns no wing; difficulty bar per scenario; sampled derivation audit; consistency with `guide.md`. |
| `judge-guidance.md` drifts from worksheets (silence-forcing, vote-merging) | Low | High | Structured-union compilation with receipts; silent columns named; sampled audit; no proof-text corpus. |

## Documentation Updates

- New: `traditions/protestant-unified/README.md`, `source.md`, `guide.md`; `docs/analysis/protestant-unified-round.md`;
  `experiments/<PR#>_protestant_unified/notes.md`.
- Edited: `traditions/protestantism/README.md` (retirement note — the only monolith edit),
  `results/README.md` (retirement + 8-row run), the validator schema doc if it enumerates scenario
  fields.
- Codev trail: this plan, and the review at `codev/reviews/119-protestant-unified-derived-38-.md`.
- Arch/lessons: none required by default; a lesson candidate (deriving a bench's ground truth from a
  pre-registered divergence study) may be proposed in the review.
