# Plan: protestant-unified — a derived Protestant bench (36 scenarios), scored and published as the 8th leaderboard row

**Specification**: [codev/specs/119-protestant-unified-derived-38-.md](../specs/119-protestant-unified-derived-38-.md)

## Executive Summary

The spec fixes the architecture (a derived unified module, scored dual-judge, published as the 8th
cross-faith row) and the gate decisions (36 scenarios after dropping Q17/Q22; `question_id` via an
optional validator field; run-id = export-date `YYYYMMDD`; Opus = the CEFE Anthropic judge key in
**batch**; NAE/Lausanne = a prose cross-check). This plan sequences that work so each phase is a
single atomic commit that is independently verifiable, dependencies first.

The spine: (1) make the scenario schema record study provenance; (2) lay down the module's
non-scenario files (the derived `guide.md`/`source.md`, taxonomies, index, and the `source_locus`
convention); (3a/3b) author the 36 consensus scenarios compiled from the worksheets with receipts —
a locked pilot of 6, then the remaining 30 — validating `--strict`; (4) run the scoring battery
behind the smoke→actuals→**architect-go** spend gate, with the exact judging configs and CLI; (5)
export the 8-row superset + raw tier and prove the frozen tiers are byte-untouched *against the
branch base*; (6) produce the cross-faith analysis and paper numbers; (7) retire the monolith and
pin the leaderboard reconciliation test to the new run.

Two repository facts corrected after review, load-bearing for Phases 4–5:

- **The export inputs are not "seven per-tradition 20260803 roots."** They are four *phase-shaped*
  run roots consumed **in order** (`results/README.md`): `20260803-merged`,
  `20260803-unstated-opus`, `20260803-framings-opus-sample`, then **`20260823-opus-fullgrid` last**
  (its verdicts win merge precedence and earn Opus `full_grid`). Order is load-bearing; the
  full-grid root does **not** match a `20260803-*` glob.
- **A run root is a directory of per-tradition subdirs** (`<root>/<tradition>/judgments.jsonl`
  (+ `judgments_v2.jsonl`) + `report.json`). Phase 4 must produce
  `tmp/judging-runs/<date>-protestant-unified/protestant-unified/…` with a `report.json` (the
  exporter derives its full-grid scenario universe from `report.json`).

Verified conveniences (no work needed): the SPA discovers run-ids at runtime
(`rawRunIds`/`resultsRunIds`, `apps/multibrowser/src/lib/queries.ts`) — no frontend change; the
cross-tier fingerprint-equality test already exists (`test_export_raw_writer.py:219`) — Phase 5
extends it; the Python paper-reconciliation test runs against the **committed** artifact
(`test_export_results.py:808`), so the `20260803` pin is independent of the gitignored roots.

All phase commits land in **one PR** (opened after Phase 3b — the natural early-PR point — if the
architect wants the module reviewed before the ~$360 run; otherwise after the final phase). The
scoring run and export operate on local files; nothing here touches `results/20260803`,
`results-raw/20260803`, `results-raw/20260813-protestantism`, or the monolith scenarios.

## Phases (Machine Readable)

```json
{
  "phases": [
    {"id": "phase_1", "title": "Scenario question_id field in the validator"},
    {"id": "phase_2", "title": "Module skeleton, derived sources, and locus convention"},
    {"id": "phase_3a", "title": "Pilot tranche: six scenarios, format and difficulty locked"},
    {"id": "phase_3b", "title": "The remaining 30 scenarios, strict-validated"},
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
first-class provenance (spec Approach 1 / gate decision). Sequenced first for a second reason
verified in review: `.codev/checks/test.sh` runs the validator pytest only when
`apps/tradition_validator` appears in the branch diff vs `origin/main`; landing this phase first is
what makes the Phase 3 validator suite run. **Do not reorder.**

#### Files to Create / Modify

- `apps/tradition_validator/tradition_validator/models.py` — add optional
  `question_id: str | None = None` to `ScenarioMeta`, constrained to `^Q\d{2}$`.
- `apps/tradition_validator/tests/test_scenarios.py` — positive (valid `question_id` accepted;
  absence still valid) and **negative** (malformed `question_id` rejected, located error) tests.

#### Deliverables

- [ ] `ScenarioMeta.question_id` optional, pattern-validated, default `None`.
- [ ] Positive + negative tests; existing suite green.

#### Acceptance Criteria

- [ ] `uv --project apps/tradition_validator run python -m pytest apps/tradition_validator` passes.
- [ ] No `question_id` still validates (back-compat for the seven traditions); `"Q16"` validates;
      `"16"` fails.

#### Test Plan

Model unit tests (accept/omit/reject); full validator pytest to confirm no regression on the
existing traditions.

### Phase 2: Module skeleton, derived sources, and locus convention

**Dependencies**: Phase 1

#### Objective

Create `traditions/protestant-unified/` and everything except the scenario folders: identity,
taxonomies, the pan-Protestant `guide.md`, the derived `source.md`, README, the scenario index, and
— critically — the **`source_locus`/`locus_label` convention** the 36 scenarios will follow.

#### Files to Create / Modify

- `traditions/protestant-unified/tradition.yaml` — id `protestant-unified`, `display_name`,
  `adherent_noun: Protestant Christian`, `scenario_id_pattern: ^UNI-\d{3}$`,
  `scholar_review: status: none`, taxonomies = the monolith's `disorders` / `graces` /
  `discernment` / `register` / `office` **verbatim** (no `communion` axis); a pan-Protestant
  `construct` (the priesthood of all believers speaking the truth in love — refactor §2).
  **`canonical_source` = the Holy Scriptures (66-book Protestant canon) as *norma normans*, exactly
  as the monolith declares it, with `locus_unit: book`** — the derived `source.md` is the module's
  *instrument*, but Scripture remains the cited canonical source shared by every strand.
- **The locus convention (decided here, followed by all 36):** `source_locus` = the 1–66 canonical
  index of the scenario's *primary* Scripture locus (e.g. Romans = 45), matching the monolith's
  usage; `locus_label` = free text naming the specific confessional loci and the per-strand receipts
  the `judge-guidance.md` compiles. This prevents the "default everything to 1" provenance smell in
  the one module whose premise is receipts.
- `traditions/protestant-unified/guide.md` — finalize from the saved draft (~1,100 words), verified
  consistent with the Q18/Q42 envelopes, crowning no wing; keep the "where Protestants differ, this
  guide is silent" section (military service, oaths, Sunday work, alcohol, fasting, the tithe,
  household deadlock).
- `traditions/protestant-unified/source.md` — the derived common-witness source with the **status
  paragraph** (binds no church, describes overlap, binds content not creedal form) and a
  **documented NAE Statement of Faith + Lausanne Covenant prose cross-check**, reported either way.
- `traditions/protestant-unified/README.md` — scope, derivation provenance (#109 study),
  `scholar_review: none` stated honestly, the strand-coverage note (refactor §2.2/§2.3).
- `traditions/protestant-unified/scenarios/index.json` — `schema_version: 1` + `UNI-001 … UNI-036`.
- Notes/table mapping each `UNI-0NN` ↔ its study `QNN` (ordering fixed here).

#### Deliverables

- [ ] `tradition.yaml` with the five carried taxonomies, no `communion` axis, Scripture as
      canonical source, `locus_unit: book`.
- [ ] The `source_locus`/`locus_label` convention written down.
- [ ] `guide.md`, `source.md` (status paragraph + NAE/Lausanne cross-check), `README.md`,
      `scenarios/index.json` (36 ids).

#### Acceptance Criteria

- [ ] The module validates at the manifest/index level (only outstanding finding = missing scenario
      folders, resolved in Phase 3).
- [ ] `guide.md`/`source.md`/`README.md` prose passes `test_band_names_normalized.py` (it globs
      `traditions/**` for band-name labels — no band names in prose).
- [ ] `git diff origin/main...HEAD` touches only `traditions/protestant-unified/**`.

#### Test Plan

Validator against the module (expect only scenario-folder drift). Run the band-names test.
Word-count `guide.md` (~1,100); read `source.md` against refactor §3; confirm the id↔question
mapping is exactly the 36 (Q17/Q22/Q50/emphasis/substance excluded).

### Phase 3a: Pilot tranche — six scenarios, format and difficulty locked

**Dependencies**: Phase 1, Phase 2

#### Objective

Author six representative scenarios end-to-end to lock the `judge-guidance.md` compilation register,
the `source_locus`/`locus_label` usage, and the difficulty bar **before** scaling — mirroring the
study's pilot discipline. Include **one keep-with-envelope** (Q18 or Q42) and **one thin-witness**
(Q40 or Q42) so both hard cases are settled in the pilot.

#### Files to Create / Modify

- Six `traditions/protestant-unified/scenarios/UNI-0NN/` folders — `scenario.yaml` (tags across the
  five taxonomies, `identity_signal: clean`, `source_locus`/`locus_label`, `question_id`),
  `turn1.md` (~130 words, Rule A: no church noun), `pressures.md` (~400 words, six pressures),
  `judge-guidance.md` (~750 words, structured-union compilation with receipts).

#### Deliverables

- [ ] Six scenarios validating `--strict` (as a subset, with the index trimmed to the six or the
      remaining thirty stubbed — whichever keeps `--strict` meaningful for the pilot).
- [ ] The envelope scenario crowns no wing; the thin-witness scenario names its silence.
- [ ] Each `judge-guidance.md` traces every claim to a worksheet locus; a genuine wrong answer is
      staged and scored below the faithful response.

#### Acceptance Criteria

- [ ] `validate … --strict` clean over the pilot set.
- [ ] A derivation audit on 2 of the 6 confirms claims trace to worksheet Grounding and silent
      columns match `adjudicated.json`.

#### Test Plan

Strict validator on the pilot; manual derivation + difficulty audit; confirm the locked format is
documented in the mapping notes so Phase 3b is mechanical.

### Phase 3b: The remaining 30 scenarios, strict-validated

**Dependencies**: Phase 3a

#### Objective

Author the remaining 30 scenarios under the locked format so the full module passes `validate
--strict` with zero findings.

#### Files to Create / Modify

- 30 more `traditions/protestant-unified/scenarios/UNI-0NN/` folders (same four files each);
  `scenarios/index.json` complete at 36.

#### Deliverables

- [ ] 36 scenario folders total; recorded `question_id`s equal the 36 kept questions; Q17/Q22/Q50
      absent.
- [ ] Q18/Q42 envelope treatment; Q40 thin-witness statement.
- [ ] Difficulty bar per scenario.

#### Acceptance Criteria

- [ ] `uv --project apps/tradition_validator run python -m tradition_validator validate
      traditions/protestant-unified --strict` → **zero findings**.
- [ ] `test_band_names_normalized.py` passes over all 36 `judge-guidance.md`.
- [ ] `guide.md` and the Q18/Q42 `judge-guidance.md` are mutually consistent (crown no wing).

#### Test Plan

Strict validator (zero findings); a sampled derivation audit (3 more scenarios); a difficulty
spot-check. Per-builder dispatcher runs the validator pytest (works because Phase 1 put the
validator in the branch diff).

### Phase 4: Scoring run behind the spend gate

**Dependencies**: Phase 3b

#### Objective

Produce the `protestant-unified` judging run under the $600 ceiling with the smoke →
usage-computed-actuals → **architect go** → full-run gate, using explicit configs and CLI so nothing
is improvised against a live key.

#### Files to Create / Modify

- `workflows/judging/configs/protestant-unified-run.yaml` (full panel), `…-gemini.yaml`
  (Gemini rankable), `…-opus-batch.yaml` (Opus via the CEFE key, batch) — modeled on the existing
  `protestantism-*.yaml` configs but pointed at `traditions/protestant-unified` and its own results
  dir. **Note the existing `protestantism-opus-openrouter.yaml` is a *live* OpenRouter path
  ("no batch … do NOT touch the CEFE key"); the CEFE batch path here is the distinct native
  `batch-judge submit`/`collect` mechanism, so this is a new config, not a tweak of that one.**
- `tmp/judging-runs/<date>-protestant-unified/protestant-unified/` (gitignored) — the run root, in
  the required **per-tradition-subdir** shape, with `judgments.jsonl` (+ `judgments_v2.jsonl`) and a
  **`report.json`** (from `judging report`), which the exporter's full-grid universe depends on.
- A committed run-notes file `experiments/<PR#>_protestant_unified/notes.md` — smoke coverage,
  usage-computed actuals per key, the architect-go timestamp, final coverage (Spec-89 spend table).

#### Deliverables

- [ ] **Key handling:** subjects + Gemini via `OPENROUTER_API_KEY` from the `taqwabench/.env` seam.
      Opus via the **CEFE** key: because the native Anthropic + batch code paths hardcode
      `ANTHROPIC_API_KEY` and ignore `api_key_env`, map `ANTHROPIC_JUDGE_API_KEY` (CEFE) →
      `ANTHROPIC_API_KEY` **only** for the Opus batch commands (a scoped env, not a global export),
      and never use the plain personal Anthropic/Gemini keys.
- [ ] CLI path stated: `judging run` (subjects + Gemini live) / `batch-judge submit` +
      `batch-judge collect` (Opus batch) / `judging report` (produce `report.json`).
- [ ] Smoke ≥50 cells on **both** judges; **batch Opus confirmed working on the smoke** before any
      full submission.
- [ ] **Usage-computed actuals** (summed from run data, not estimates) reported; **STOP** for
      explicit architect go before the full run.
- [ ] Full battery 36 × 5 × 6 × 3, both scopes, both judges full grid; coverage in the manifest.
- [ ] **Opus completeness check**: assert all **6,480** expected Opus judgments present (per-framing
      `n_judged == n_expected`) — not merely the tolerant `full_grid` badge — before Phase 5.

#### Acceptance Criteria

- [ ] Total spend ≤ $600 (alert $450, pause $550), reconciled from usage data (~$180 Opus batch +
      ~$180 OpenRouter ≈ $360 expected).
- [ ] Gemini has a strictly complete grid (so Phase 5's `_assert_full_grid` passes); Opus 6,480/6,480.
- [ ] The full run was **not** launched before the architect's explicit go (timestamp in notes).

#### Test Plan

Pre-flight: verify the `taqwabench/.env` keys resolve, **and** that all four export roots exist by
exact name — `20260803-merged`, `20260803-unstated-opus`, `20260803-framings-opus-sample`,
`20260823-opus-fullgrid` (not a `20260803-*` glob). **These roots live in the *main checkout* at
`../../tmp/judging-runs/`, not the worktree** — the new `<date>-protestant-unified` root goes there
too, and the Phase 5 export is run with paths into the main checkout's `tmp/judging-runs/` so all
roots resolve together. Smoke: coverage + verdict parseability on ≥50
cells, both judges; compute actuals from data. Gate: send actuals to the architect and wait. Full:
monitor spend vs alert/pause; re-judge gaps (budgeted). Run judging as background tasks that end the
turn (never a foreground poll loop).

### Phase 5: Superset export, raw re-bake, and frozen-tier guard

**Dependencies**: Phase 4

#### Objective

Publish the committed tiers: a new-run-id superset showing **8 tradition rows** (the four frozen
phase-roots + `protestant-unified`), its matching raw tier, and proof the frozen artifacts are
byte-untouched.

#### Files to Create / Modify

- `results/<date>/` (committed) — `analysis export` over the four frozen roots **in load-bearing
  order** (`20260803-merged`, `20260803-unstated-opus`, `20260803-framings-opus-sample`,
  `20260823-opus-fullgrid`) **plus** `<date>-protestant-unified` appended; equal-weight
  mean-of-means, Gemini rankable, Opus badge-only.
- `results-raw/<date>/` (committed) — `analysis export-raw` over the **complete 8-tradition**
  superset (~141 MB gz added; under the 200 MB/run cap); equal source fingerprint with the score
  tier (extend `test_export_raw_writer.py:219`).
- `apps/multibrowser/public/data-raw/<date>/` — the **new** run is the baked bundle; the older raw
  run falls back to the committed GitHub tier (only one run ships baked — state this).

#### Deliverables

- [ ] Superset export passes `_assert_full_grid` + the roster asserts
      (`assert_uniform_subject_roster`, `_SUBJECT_VARIANTS`/`_JUDGE_VARIANTS`); exactly one
      Protestant cross-faith row (`protestant-unified`); monolith and strands contribute none.
- [ ] Raw tier covers all 8 traditions; fingerprint-equality test passes.
- [ ] Railway two-step re-bake (`rsync` → `railway up --no-gitignore --detach` from
      `apps/multibrowser`); the **live** manifest fingerprint matches the exported tier (HTML
      content-type on a baked path treated as "absent").
- [ ] **Frozen-tier immutability against the branch base** (not plain `git diff`, which is empty
      after commits): `git diff --exit-code origin/main...HEAD -- results/20260803
      results-raw/20260803 results-raw/20260813-protestantism traditions/protestantism/scenarios` is
      clean; the only monolith change (Phase 7) is its README.

#### Acceptance Criteria

- [ ] The existing paper-reconciliation test (`test_export_results.py:808`, committed-artifact
      based) still passes unchanged.
- [ ] An intentional Gemini gap makes `_assert_full_grid` fail; the real full grid passes.
- [ ] `/results` shows 8 rows live.

#### Test Plan

Run both exporters; run the analysis/validator suites (per-builder dispatcher). Branch-base diff on
the frozen paths (empty). Curl the live baked manifest, compare fingerprint. Verify the 8th row in
the SPA.

### Phase 6: Cross-faith analysis and paper numbers

**Dependencies**: Phase 5

#### Objective

Turn the run into paper-ready analysis: per-tradition means + CIs, per-framing, steadfastness,
Opus-vs-Gemini agreement, and the 8-row numbers, in the house `experiments/` convention.

#### Files to Create / Modify

- `experiments/<PR#>_protestant_unified/` — `notes.md`, `analyze.py`, `data/output/` (reusing the
  canonical aggregator; no second mean-of-means implementation).
- `docs/analysis/protestant-unified-round.md` — narrative summary + paper-ready 8-row table.
- matplotlib figures (per-tradition means with CIs, per-framing, Opus-vs-Gemini agreement).

#### Deliverables

- [ ] Per-tradition means + CIs, per-framing, steadfastness, Opus-vs-Gemini agreement.
- [ ] The 8-row numbers, reconciling with the export by construction.
- [ ] `docs/analysis/` summary + matplotlib figures.

#### Acceptance Criteria

- [ ] Analysis numbers reconcile with the committed `results/<date>/` tier (mean-of-means holds).
- [ ] Figures render from `analyze.py`; no hand-rolled HTML/SVG charts.

#### Test Plan

Recompute the 8-row means from the committed tier and assert they match the leaderboard; regenerate
figures; sanity-check protestant-unified vs the monolith record and the study priors (difficulty
bar held — not trivially ceilinged).

### Phase 7: Monolith retirement and reconciliation pin

**Dependencies**: Phase 5 (retirement notes); Phase 6 + Waleed's acceptance (reconciliation pin)

#### Objective

Retire the monolith from active scoring operationally, and pin the leaderboard reconciliation test
to the new run once Waleed accepts the headline numbers — protecting the new numbers the way
`20260803` is protected.

#### Files to Create / Modify

- `traditions/protestantism/README.md` — retirement note (frozen on disk for the raw viewer; retired
  from active scoring; `protestant-unified` supersedes it for cross-faith scoring). **The only
  permitted monolith edit.**
- `results/README.md` — the monolith's retirement, the operational exclusion (out of the new
  run/export inputs; discovery + the `20260813-protestantism` raw viewer still resolve), and the new
  8-row run.
- **The leaderboard reconciliation pin**: the portable paper pin lives in
  `apps/multibrowser/src/lib/leaderboard.test.ts` — add the new run's 8-row headline numbers there
  (the Python `test_export_results.py` reconciliation is committed-artifact-based and keeps its own
  `20260803` pin). Add the new pin **after** Waleed accepts the numbers.

#### Deliverables

- [ ] Monolith README + `results/README.md` retirement/operational-exclusion notes.
- [ ] `leaderboard.test.ts` pins the new run (post-acceptance) alongside the existing pin.

#### Acceptance Criteria

- [ ] Monolith excluded from the new run/export inputs; discovery + the raw viewer still resolve.
- [ ] The reconciliation test passes with both pins.
- [ ] **Fallback if acceptance is late** (near the 09-09 freeze): land the retirement notes now and
      open/keep the PR without the new pin; add the pin in a follow-up commit once Waleed accepts —
      never block the PR on the human acceptance.

#### Test Plan

Run `leaderboard.test.ts` (both pins) and the Python reconciliation test. Confirm discovery lists
the monolith and the raw viewer resolves. Branch-base diff to confirm the only monolith change is
its README.

## Risks and Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Scenario authoring slips the 09-09 freeze (36 hand compilations) | Medium | High | Pilot-lock (3a) then scale (3b); front-load Phases 1–3b (09-04); the run is the only long pole after. |
| Wrong/incomplete export roots or wrong order | Medium | High | Use the four named roots in `results/README.md` order (full-grid Opus last); pre-flight each by exact name; never a `20260803-*` glob. |
| Phase 4 improvised against a live key | Medium | High | Explicit configs + CLI in the plan; scoped `ANTHROPIC_JUDGE_API_KEY`→`ANTHROPIC_API_KEY` map for Opus batch only; smoke first; never the plain key. |
| Spend overrun (batch est. ≈$360) | Low | High | Smoke → usage-computed actuals → architect go; alert $450, pause $550; batch Opus on CEFE. |
| Superset export blocked by `_assert_full_grid` (Gemini gap) | Medium | High | Gemini full grid; budget re-judge inside the ceiling; roster mappings verified; also assert Opus 6,480/6,480. |
| Frozen-tier mutation missed because plain `git diff` is empty post-commit | Low | High | Guard with `git diff origin/main...HEAD -- <frozen paths>`; reconciliation test on the committed artifact. |
| Loss of gitignored run roots incl. `20260823-opus-fullgrid` (afx cleanup scar) | Low | High | Pre-flight existence check by exact name in Phase 4; never run cleanup. |
| Envelope scenario (Q18/Q42) crowns a wing or reads easy | Medium | Medium | Envelope crowns no wing; difficulty bar; sampled derivation audit; guide/envelope consistency. |
| Phase 7 pin blocked on late human acceptance near freeze | Medium | Medium | Land retirement notes without the pin; add the pin in a follow-up; never block the PR. |

## Documentation Updates

- New: `traditions/protestant-unified/{README.md,source.md,guide.md}`;
  `docs/analysis/protestant-unified-round.md`; `experiments/<PR#>_protestant_unified/notes.md`;
  `workflows/judging/configs/protestant-unified-*.yaml`.
- Edited: `traditions/protestantism/README.md` (retirement — the only monolith edit),
  `results/README.md` (retirement + 8-row run), `apps/multibrowser/src/lib/leaderboard.test.ts`
  (new pin, post-acceptance).
- Codev trail: this plan; the review at `codev/reviews/119-protestant-unified-derived-38-.md`.
- Arch/lessons: none required by default; a lesson candidate (deriving a bench's ground truth from a
  pre-registered divergence study; and the export's phase-shaped-roots gotcha) may be proposed in
  the review.
