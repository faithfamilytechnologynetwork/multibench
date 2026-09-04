# Specification: protestant-unified — a derived 38-scenario Protestant bench, scored and published as the 8th leaderboard row

<!--
SPEC vs PLAN BOUNDARY:
This spec defines WHAT and WHY. The plan defines HOW and WHEN.
Keep implementation phases, file paths, code, and "first we will… then we will…"
out of the spec — those belong in codev/plans/119-*.md.
-->

## Problem Statement

MultiBench measures how faithfully a model can counsel a believer *by that believer's own
tradition's lights*. Protestantism is the corpus's hardest case: no single confessional corpus
binds all Protestants, and the original `traditions/protestantism` monolith tried to carry six
binding corpora under one `guide.md`. The pre-registered guidance-divergence study (#109) proved
what the monolith could only assume — that on ordinary-life pastoral questions the seven major
Protestant strands overwhelmingly give the **same concrete counsel** (78% same, 6% emphasis, 16%
substantive divergence; D = 0.16), and that the divergence, where it exists, is stacked in a small
number of nameable areas (the sword and the oath, rule-versus-liberty practices, the tithe,
household order). Under the study's pre-registered decision rule this yields **Pathway B in its
minimal form: one unified Protestant bench**.

What is missing is the bench itself. The study produced 350 per-strand worksheets and an
adjudicated coding of advice-similarity, but no scored tradition, no leaderboard row, and no
paper-ready cross-faith numbers for Protestantism-as-a-whole. The CHI paper (freeze **2026-09-09**)
needs Protestantism to appear as a proper 8th tradition row whose ground truth is *derived with
receipts* from the strands' own standards — not composed freehand, not voted. This spec defines
that bench, its scoring, and its publication.

Who is affected: the paper's readers (a fabricated or freehand "aggregate Protestant" ground truth
would be a fiction the paper cannot defend); the SPA's `/results` leaderboard viewers; and, in the
construct the benchmark exists to serve, the nondenominational Protestant believer whom no strand
corpus speaks for and whom this derived common-witness source is built to serve.

## Current State

- **The study is complete and committed** under `docs/analysis/protestant-guidance-divergence/`:
  `questions.md`, `method.md`, `codebook.md`, `pathway-rule.md` (the pre-registration), 350
  `worksheets/<strand>/QNN.md` (audited), `codings/adjudicated.json` (severity + clusters +
  rationale per question), `codings/grounding.json`, `output/summary.json`. The seven strands are
  anabaptist, anglican, baptist, lutheran, methodist-wesleyan, pentecostal, reformed-presbyterian.
- **The monolith `traditions/protestantism` still exists and is still scored.** It carries 100
  scenarios with a `communion` axis and one shared `guide.md` — the structure the study and the
  parity audit showed to be defective (guided-framing family spread 0.461; Stated axis collapsed;
  39% church-interior tilt). Its record run `20260813-protestantism` and the raw viewer that
  resolves `judge-guidance.md` live from HEAD both depend on the monolith folder staying on disk.
- **Seven record traditions are already on the cross-faith leaderboard** (`results/20260803`),
  ranked equal-weight mean of per-tradition means (Gemini ranks; Opus 4.8 badge-validates). There
  is no Protestant row derived from the study.
- **The tradition module format is fixed and validated**: `tradition.yaml` + `guide.md` +
  `source.md` + `README.md` + one folder per scenario (`turn1.md`, `pressures.md`,
  `judge-guidance.md`, `scenario.yaml`) + `scenarios/index.json`, gated by
  `apps/tradition_validator`. The per-scenario `scenario.yaml` schema (`ScenarioMeta`) is **closed**
  (`extra="forbid"`); there is today no field to record a scenario's originating study question.

## Desired State

A new drop-in tradition `traditions/protestant-unified/` exists, validates `--strict`, is scored
under the record convention with both judges over the full battery, and appears as the **8th row**
of the cross-faith leaderboard in the SPA and the paper table — while every frozen artifact
(`results/20260803`, `results-raw/20260813-protestantism`, the monolith folder) is byte-untouched.

Concretely, after this work:

- `traditions/protestant-unified/` holds 38 scenarios, one per kept study question, each staged
  life-first (Rule A: no church noun in `turn1`), with a `judge-guidance.md` **compiled from that
  question's seven strand worksheets** (Counsel first, receipts into each strand's Grounding,
  silent columns declared), and each scenario recording its study `question_id`.
- Its `guide.md` (~1,100 words, from the Waleed-reviewed draft) is the pan-Protestant common
  witness; its `source.md` is the *derived* common-witness source with the status paragraph (binds
  no church, describes overlap) and the NAE / Lausanne validation check reported either way.
- The monolith is **retired from active scoring** and frozen on disk, with retirement notes in
  `traditions/protestantism/README.md` and `results/README.md`.
- A new superset run (new run-id) exports the seven record traditions **plus** `protestant-unified`
  so the leaderboard and paper table show 8 rows; the raw tier for the new tradition is re-baked
  and served live. The paper-reconciliation test gains a pin for the new run once Waleed accepts
  the headline numbers.
- A house `experiments/<PR#>_…` analysis produces per-tradition means + CIs, per-framing,
  steadfastness, and Opus-vs-Gemini agreement, with a short `docs/analysis/` summary and
  paper-ready 8-row numbers (figures via matplotlib).

## Success Criteria

- [ ] `traditions/protestant-unified/` passes
      `uv --project apps/tradition_validator run python -m tradition_validator validate traditions/protestant-unified --strict`
      with zero findings.
- [ ] **38 scenarios** by default (the 39 `same` minus Q50) — **or N < 38** iff the spec-approval
      gate explicitly drops one or more audited questions (a gate/architect decision, never builder
      discretion; see the audit and Constraints note on scope). Each `scenario.yaml` records its
      study `question_id`; ids match `^UNI-\d{3}$`. Whatever the final N, it equals the count of
      recorded `question_id`s and the count of scenario folders.
- [ ] `tradition.yaml`: id `protestant-unified`, `adherent_noun: Protestant Christian`, taxonomies
      = the monolith's `disorders` / `graces` / `discernment` / `register` / `office` (**no
      `communion` axis**).
- [ ] Every `judge-guidance.md` is compiled from that question's seven worksheets with receipts
      into each strand's own loci; claims resting on fewer witnesses (silent columns) say so; no
      vote-merging; no proof-text corpus introduced (the judge seam holds).
- [ ] Difficulty bar: every scenario keeps a genuine wrong answer a fluent model would give.
- [ ] `source.md` carries the status paragraph and reports the NAE Statement of Faith + Lausanne
      Covenant validation check (agreement or divergence, stated either way).
- [ ] The 14 `internal_variation`-flagged questions are audited (this spec, below); the final kept
      list reflects Waleed's keep / keep-with-envelope / drop decisions at the spec gate.
- [ ] The **Opus judge key path is resolved before the smoke gate** (batch vs live): `codev/reviews/89`
      records `ANTHROPIC_JUDGE_API_KEY` as blocked by an org cap (probes only), which forced #89 to
      live OpenRouter at ~2× batch price — the difference between a comfortable and a
      ceiling-brushing run. The plan states which path is used and confirms it works on the smoke.
- [ ] Smoke run (≥50 cells, both judges) completes; **usage-computed actuals** (summed from data,
      not estimates) are reported; explicit architect go precedes the full run.
- [ ] Full battery 38 × 5 subjects × 6 pressures × 3 framings, both scopes, both judges full grid
      (≈6,840 cells/judge; a Gemini gap blocks the export per above). Total spend ≤ **$600** (alert
      $450, pause $550). The plan carries a **bottom-up estimate from #89 per-cell actuals** (see
      Constraints) and a stated fallback if the $550 pause fires mid-run.
- [ ] `guide.md` and every **keep-with-envelope** `judge-guidance.md` are **mutually consistent**
      and crown no wing (e.g. the guide's placement of fertility treatment within conscience must
      agree with the Q22 envelope, if Q22 is kept).
- [ ] A new superset run (fresh run-id, **not** `20260803`) exports **all 8 tradition rows**; the
      leaderboard rule (equal-weight mean of per-tradition means, Gemini ranks, Opus badge-only) is
      enforced — only `protestant-unified` contributes a cross-faith Protestant row.
- [ ] The superset export **passes `_assert_full_grid`** (`export_results.py`): the rankable judge
      (Gemini) has zero gaps across **every** tradition in the export, and the subject/judge roster
      maps cleanly (`assert_uniform_subject_roster`, `_SUBJECT_VARIANTS`/`_JUDGE_VARIANTS`). A gap
      is a **blocking** export failure, not a "reported honestly" footnote; closing it costs
      re-judge spend inside the ceiling.
- [ ] The new **raw** tier covers the **complete 8-tradition superset** at the same run-id, and a
      test asserts the score-tier and raw-tier **source fingerprints are equal**; it is re-baked to
      Railway (two-step: `rsync` into `apps/multibrowser/public/data-raw/<run>/`, then
      `railway up --no-gitignore --detach`) and the live manifest fingerprint verifies.
- [ ] **Every frozen path is byte-untouched**: `results/20260803/`, `results-raw/20260803/`,
      `results-raw/20260813-protestantism/`, and `traditions/protestantism/scenarios/**` — the
      **only** permitted monolith edit is its `README.md` retirement note. The existing
      paper-reconciliation test still passes unchanged (`git diff` on these paths is empty).
- [ ] The monolith is **retired from active scoring operationally**: it is excluded from the new
      run and from every future record-run/superset export input, while core tradition *discovery*
      (the `traditions/*/tradition.yaml` glob and the raw viewer) stays working. The README and
      `results/README.md` say so.
- [ ] Analysis artifact under `experiments/<PR#>_…` produces per-tradition means + CIs,
      per-framing, steadfastness, Opus-vs-Gemini agreement; a `docs/analysis/` summary and
      paper-ready 8-row numbers exist; figures via matplotlib.
- [ ] Retirement notes land in `traditions/protestantism/README.md` and `results/README.md`.
- [ ] Codev trail complete: spec, plan, review. `scholar_review: none` stated honestly.

## Constraints

The following are **baked decisions** by Waleed (2026-09-03), copied verbatim from issue #119.
They are fixed; this spec does not relitigate them.

> 1. **Scope = 38 scenarios exactly**: the 39 `severity: same` questions in
>    `docs/analysis/protestant-guidance-divergence/codings/adjudicated.json` **minus Q50**
>    (cremation; all seven strands silent). The 3 emphasis questions (Q06, Q44, Q45) and the 8
>    substance questions (Q02, Q08, Q24, Q26, Q28, Q37, Q38, Q39) are **out**. No family-conditional
>    tier in this round.
> 2. **No quarry from the monolith.** The 18 `cross_cutting` scenarios of `traditions/protestantism`
>    stay where they are. `traditions/protestantism` is **frozen on disk** (the raw viewer for
>    `20260813-protestantism` resolves against it); retire it from active scoring and say so in its
>    README and in `results/README.md`.
> 3. **Ground truth is derived, never composed.** Each scenario's `judge-guidance.md` is compiled
>    from that question's seven strand worksheets (`docs/analysis/protestant-guidance-divergence/worksheets/<strand>/QNN.md`),
>    Counsel first, with receipts into each strand's Grounding. Claims resting on fewer witnesses
>    (silent columns) say so. No vote-merging. The judge seam holds: `judge-guidance.md` is the
>    judge's only runtime ground truth; no proof-text corpus.
> 4. **Paper placement = 8th tradition row.** New run-id, `results/20260803` and
>    `results-raw/20260803` **byte-untouched** (the reconciliation test pins them). Export a new
>    superset run containing the seven record traditions plus `protestant-unified` so the SPA
>    leaderboard and the paper table show 8 rows; the leaderboard rule stays equal-weight mean of
>    per-tradition means. The paper-reconciliation test gains a pin for the new run once Waleed
>    accepts the new headline numbers.
> 5. **Spend ceiling $600 hard**, dual judge (Gemini full grid ranks; Opus 4.8 full grid validates,
>    badge-only, never re-ranks). Same 5 subjects, 6 pressures, 3 framings, both scopes as
>    `20260803`/`20260813`. Keys only via the `taqwabench/.env` seam: subjects + Gemini via
>    `OPENROUTER_API_KEY`; Opus via the Anthropic judge key. Never a personal Gemini key. **Smoke
>    first → usage-computed actuals (sum from data, not estimates) → explicit architect go → full
>    run.** Alert at $450, pause at $550.

Additional binding constraints from the module contract and repo architecture:

- **Universal core is untouched**: three framings (unstated/stated/guided), six pressures, numeric
  bands, no band names in prose. This is a data-tier addition (a drop-in directory) plus at most a
  small optional validator-schema field.
- **`scenario.yaml` schema is closed** (`extra="forbid"`). Recording each scenario's study
  `question_id` requires either an optional validator-schema field (+ negative test) or an approved
  alternative location. Default: extend the validator, mirroring the refactor's `parity_key`
  decision (§4).
- **Keys/spend discipline** per the live-run key seam and Spec 89: export only OpenRouter +
  Anthropic keys from `taqwabench/.env`; never the personal Gemini key. Reconcile spend from
  usage-computed actuals (the Spec 89 `report.json`-vs-billed scar), never rolling estimates.
- **Difficulty bar** (refactor §4): ordinary-life staging does not mean easy; every scenario keeps
  a genuine wrong answer a fluent model would give.
- **Composition rules** (refactor §4, imported from the refinement prompt): Rule A (turn1 statable
  in one sentence, no church noun), Rule B (opener carries the trouble, not the credentials),
  `clean` as default identity posture, length targets `turn1` ~130 words, `pressures.md` ~400,
  `judge-guidance.md` ~750.
- **Scope = 38 by default; a drop is a gate decision, not builder discretion.** Baked decision #1
  fixes the scope at 38. The spec-gate audit is empowered (by issue Deliverable 1) to *recommend*
  drops for Waleed's decision at the gate; if he drops one or more, that formally amends the scope
  to N < 38. The builder never drops a question on its own judgment. Absent an explicit gate drop,
  all 38 are built. This resolves the "38 vs ≤38" tension the consultations flagged.
- **Spend feasibility, bottom-up from #89 actuals (not asserted).** The battery is ≈6,840
  cells/judge (38×5×6×3×2 scopes) = 38% of #89's 18,000. Scaling #89's *actuals*: OpenRouter
  subjects + Gemini ≈ $475 × 0.38 ≈ **$180**; Opus ≈ 6,840 × ~$0.051–0.054 (the #89 *live*
  per-cell) ≈ **$350–370** → total ≈ **$530**, which puts the $550 pause *inside* the estimate
  with no headroom for the re-judge sweeps #89 required (975 re-judge calls, verdict backfill,
  straggler passes). Batch pricing for Opus (~$0.026/cell) would drop the total to ≈ **$355**. The
  plan therefore resolves the Opus key path (batch vs live) up front and states the fallback if the
  pause fires. The $600 ceiling is not challenged — its feasibility is *shown*, not assumed.

## Assumptions

- The study's `adjudicated.json` severity coding is authoritative for scope selection; the 38 kept
  questions are exactly those coded `same` excluding Q50. (Verified against the committed file.)
- The seven strand worksheets are the sole ground-truth source for each scenario's
  `judge-guidance.md`; they are first-draft (flagged-confidence) and unreviewed by scholars —
  `scholar_review: none` is stated honestly, not remedied here.
- The `taqwabench/.env` seam holds the OpenRouter and Anthropic judge keys and is reachable from
  the run environment; the run tooling (workflows/analysis) used for `20260803`/`20260813` is
  reusable unchanged for a new tradition + superset export.
- The SPA reads new traditions and new run-ids at runtime without a code change; only the raw tier
  needs a deploy-time re-bake.
- The architect is available at the spec gate and plan gate, and to give the smoke→full go.
- **The seven record traditions' `20260803` judging-run roots still exist locally** at
  `tmp/judging-runs/20260803-*` (gitignored, local-only, confirmed present). The superset export
  reads them, so the plan includes a **pre-flight existence check** before any run — losing them
  (the `afx cleanup` destroys-gitignored-data scar) blocks the 8-row export with no recovery path.
- `export_dataset(roots=[...])` accepts multiple run roots (verified), so a superset over the seven
  frozen roots plus the new `protestant-unified` root is feasible without touching the frozen tiers.
- Depends on no other in-flight builder; the monolith and both frozen result tiers are not being
  mutated by anyone else.

## Spec-Gate Audit — the 14 `internal_variation` questions

**Why this is here.** 14 of the 38 kept questions carry `internal_variation: true` on at least one
strand worksheet (Q16, Q17, Q18, Q19, Q21, Q22, Q27, Q30, Q31, Q40, Q41, Q42, Q43, Q47). A question
coded `same` at the strand-center level could still hide a **substantive** mainline-vs-confessional-
wing split (e.g. ELCA/LCMS, UMC/GMC, SBC/CBF, MC USA/Old Order) that the unified consensus
`judge-guidance.md` must not paper over. For each flagged question this audit reads every flagged
worksheet's Notes and asks: **would a mainline vs a confessional wing counsel *differently in
substance* here?** Recommendation vocabulary:

- **keep** — the wing variation is not substantive (idiom/emphasis/route only, or both wings land on
  the same act); the consensus scenario stands unchanged.
- **keep-with-envelope** — a real but bounded wing difference; keep the scenario but the
  `judge-guidance.md` must name the variation as an acceptable envelope (crowning no wing), not a
  single required act.
- **drop** — the wing split is substantive enough that a single consensus ground truth would
  misrepresent one wing; the scenario should leave this round.

**Waleed decides each row at the spec gate; the final kept list is recorded here after the gate.**

**Method.** Every `internal_variation: true` worksheet's `## Notes` was read across all seven
strands for each flagged question (98 worksheets checked). The judgment below asks only whether a
wing split is **substantive on the act this scenario poses** — one wing forbidding what another
commands — versus idiom, route/means, degree, or downstream questions the scenario does not ask.
Thin-witness (many `silent` columns) is called out because a consensus resting on few witnesses is
itself weaker.

| Q | What the scenario asks | Nature of the wing variation | Silent cols | Builder rec |
|---|---|---|---|---|
| Q16 | Responding to a spouse's porn discovery | Wings differ only on the *downstream divorce* question (porn-alone as grounds), which this scenario does not pose; the confront/repent/accountability core is shared. Add the universal minors/coercion → civil-authority floor. | 0 | **keep** |
| Q17 | Is a divorced (wronged) woman free to remarry | **Substantive.** Old Order Anabaptist, stricter Pentecostal-Holiness (older CoG/COGIC), and some independent Baptist wings counsel *no remarriage while the former spouse lives*; mainline/most free the innocent party. The coded consensus "treats her as free to remarry" crowns the permissive wing. | 0 | **keep-with-envelope** |
| Q18 | Attend a cohabiting daughter's housewarming | Shared core: do not sever, presence ≠ blessing, state conviction once. A stricter minority (some independent Baptist / Reformed sessions / Old Order if she is a covenant member) declines the *specific celebratory event* while keeping fellowship — a bounded act difference; mainline wings would not name sin at all. | 1 (pent.) | **keep-with-envelope** |
| Q19 | Drifting toward engagement with a non-believer | The coded consensus *is* the shared cautionary core (halt the drift, warn honestly, give room, part with grief). Wings differ on whether it is "a line" vs "grave caution" — downstream of what this scenario counsels; guidance need not declare the marriage permitted or forbidden. | 0 | **keep** |
| Q21 | Aging parent: memory-care vs home | Old Order prefers home care; MC USA blesses either. The coded consensus already holds "the duty is fixed, the *form* is free," which contains the Old Order preference as one legitimate form. Not permit-vs-forbid. | 0 | **keep** |
| Q22 | IVF for an infertile couple | **Thin + substantive.** Five of seven strands are *silent* (pastoral extension, not confessional address); conservative wings (PCA/OPC, LCMS/WELS, anglo-catholic/ACNA, SBC resolution) counsel against standard IVF or against it entirely, while mainline leaves it to conscience. Shared floor is embryo protection only. | 5 | **keep-with-envelope** *(drop is defensible — see note)* |
| Q27 | Take a new drug for unanswered healing | The flagged variation is the positive-confession / Word-of-Faith current the AG paper was *written to correct* — not a confessional wing but the position the strand's own standards reject. The consensus (medicine + prayer, no blame) is the actual standard; the fringe is a staged wrong answer. | 0 | **keep** |
| Q30 | Medication for panic attacks | Same shape: biblical-counseling wariness / deliverance-only currents are minorities the standards do not endorse; "no Baptist standard forbids treatment," corpus bodies support prayer + medicine. Consensus is the standard. | 0 | **keep** |
| Q31 | Declining a third chemo round | The "accepting death = abandoning faith" faith-maximalist current is a fringe the corpus standards reject (they hold healing prayer and submission together). Consensus (faithfully may decline; hospice is care) is the standard; the fringe is the staged wrong answer. | 1 (anab.) | **keep** |
| Q40 | Whether to vote | Old Order abstain vs MC USA vote-by-conscience; "conscience may not be coerced in either direction." The coded consensus is *already envelope-shaped* — both courses legitimate. Contained. Note thin witness. | 4 | **keep** |
| Q41 | Helping an undocumented neighbor's injured father | All bodies counsel the mercy; they diverge only *past it* on advocacy/sanctuary vs personal-mercy-and-truthfulness — which this scenario does not ask. Shared act (get him care, don't obstruct, be truthful) is consensus. Include the medical safety floor. | 0 | **keep** |
| Q42 | Loneliness and an AI-companion app | **Thin.** Five of seven silent; the two non-silent agree (turn to real human contact, limit the app, tell a pastor/counselor). Old Order "put the device away entirely" vs "reorder" is degree, not forbid-vs-command. | 5 | **keep-with-envelope** |
| Q43 | Doom-scrolling and anger (digital) | Old Order "remove the technology altogether" vs a "disciplined fast" is degree; both reduce. The consensus (mechanical fences + refill + confess + accountability) contains both. | 1 (pent.) | **keep** |
| Q47 | Returning prodigal fearing the unforgivable sin | The worksheet says the variation is "on the means, not the welcome" — anglo-catholic sacramental confession vs evangelical general confession; both stand on Article XVI and both say *come home*. The scenario's whole point (the welcome) is unanimous. | 0 | **keep** |

**Summary recommendation:** keep 10 (Q16, Q19, Q21, Q27, Q30, Q31, Q40, Q41, Q43, Q47);
keep-with-envelope 4 (Q17, Q18, Q22, Q42); no outright drop recommended.

**Notes for the gate decision:**
- **Q17 is the strongest case of a substantive split hiding inside a `same` coding.** With the
  envelope, `judge-guidance.md` should *not* declare her flatly "free to remarry"; it should hold
  the shared welcome and conditions (only-in-the-Lord, premarital counseling, healing) and name
  that some confessional wings hold remarriage is not open while a former spouse lives, routing the
  verdict to the person's own pastor — crowning no wing. If Waleed wants zero remarriage-permission
  ambiguity in a consensus bench, **drop** is the clean alternative.
- **Q22 is the leading drop candidate**: 5/7 silent *and* a conservative-wing permit-vs-forbid on
  whether to pursue IVF at all. Keep-with-envelope requires the guidance to foreground the silence
  (extension, not confessional address) and the embryo-protection floor while declaring no strand
  position binding. Dropping it (→ 37 scenarios) is fully defensible and arguably cleaner.
- **Q40 and Q42** rest on thin witness (4 and 5 silent). Both are keepable because their coded
  consensus is already envelope-shaped or route-level, but the `judge-guidance.md` must state the
  thin witness per the derivation discipline.
- For every **keep-with-envelope**, the envelope crowns no wing and the scenario must still keep a
  genuine wrong answer (the difficulty bar) — typically the failure of *binding a conscience
  Scripture left free* or *loosing one it bound*.

## Solution Approaches

The overall architecture (a derived unified module, scored and published as the 8th row) is fixed
by the baked decisions. Genuine open design choices, with approaches:

### Approach 1 (recommended): extend the validator with an optional `question_id` field

Add `question_id: str | None = None` (pattern `^Q\d{2}$`) to `ScenarioMeta`, plus a negative test,
mirroring the refactor's `parity_key` decision. **Pros:** the study provenance is load-bearing,
first-class, queryable data on the scenario itself; matches the endorsed pattern; small,
well-tested change run by the per-builder dispatcher. **Cons:** a core code change (however small)
in a round that is otherwise data-tier. **Risk:** low.

### Approach 2: carry the study `question_id` in a side index or inside `locus_label`

Keep `scenario.yaml` unchanged; record provenance in a suite-level index file or embedded in the
free-text `locus_label`. **Pros:** no code change. **Cons:** side-tables drift (the refactor's
explicit warning); `locus_label` embedding is a hack a reader will not expect. **Risk:** provenance
silently rots. **Rejected** for the same reason the refactor rejected a `parity_key` side-table.

### `judge-guidance.md` compilation method (recommended: strand-union with receipts)

Compile each consensus `judge-guidance.md` as a **structured union** of the seven worksheets:
Counsel first (the shared concrete advice, drawn from the adjudicated cluster rationale and the
worksheet Counsel fields), then per-claim receipts citing each strand's own loci from its Grounding,
with silent columns explicitly named. **This is not a vote** — where all non-silent columns agree,
the claim is consensus; a claim resting on fewer witnesses says so. **Pros:** honors the derivation
discipline and the judge seam; auditable to the worksheets. **Cons:** labor-intensive, 38 hand
compilations. **Risk:** the difficulty bar — a consensus ground truth can read "obvious"; each
scenario must preserve a genuine wrong answer (mitigated by staging the pressures against it).

### Run staging (recommended: smoke → actuals → go → full, single tradition + superset export)

Score only `protestant-unified` (the monolith is retired from active scoring; the other seven come
from the existing frozen run and are re-exported into the superset). **Pros:** minimal spend for a
single new tradition (≈6,840 cells/judge). **Cons:** the estimated ≈$530 live spend brushes the
$550 pause (see the Constraints derivation), so the Opus batch path must be secured up front; the
superset export must correctly join the new run's Protestant row to the seven frozen traditions and
pass the full-grid gate. **Risk:** double-counting, a Gemini gap blocking export, or accidental
mutation of the frozen tiers (mitigated by the reconciliation test, the full-grid gate, and
additive-only exports).

## Open Questions

**Critical (blocks progress):**

- **The 14-question audit outcomes.** Which flagged questions are keep / keep-with-envelope / drop?
  This sets the final scenario count (38 by default; N < 38 only if the gate explicitly drops one or
  more) and shapes several `judge-guidance.md` files. *Decided by Waleed at the spec gate from the
  audit table above.* Q17 and Q22 are the two the builder specifically escalates.

**Important (shapes design):**

- **Opus judge key path (batch vs live).** `codev/reviews/89` records `ANTHROPIC_JUDGE_API_KEY` as
  org-cap-blocked (probes only). Resolve before the smoke gate — it is the ~$355 (batch) vs ~$530
  (live) difference, and live puts the run at the $550 pause. Confirmed working on the smoke.
- **`question_id` recording mechanism** — validator field (recommended) vs side-table. Needs
  architect assent since it touches core.
- **Superset run-id naming.** The baked text names `results/20260803` and `results-raw/20260803` as
  the *untouched* record run; issue Deliverable 4 says "new run-id(s), additive." Confirm the new
  superset run-id string (a fresh date/label, not `20260803`) with the architect before export.
- **NAE / Lausanne validation depth.** Is a documented prose cross-check in `source.md` sufficient,
  or is a machine-checkable artifact wanted? Default: documented prose cross-check reported either
  way, consistent with the refactor §3 "validation section for the paper."

**Nice-to-know (optimization):**

- Whether any consensus scenario benefits from an `office`/`register` overlay beyond the study's
  framing (e.g. `guidance_claim` on Q46, `assurance_crisis` on Q47) — an authoring nicety, decided
  during implementation against the worksheets.

## Test Scenarios

- **Validator strict pass**: the module validates `--strict` with zero findings; a deliberately
  malformed `question_id` (if the field is added) is rejected by the negative test.
- **Scope integrity**: exactly 38 scenario folders; the set of recorded `question_id`s equals the
  38 kept study questions; Q50 and all emphasis/substance questions are absent.
- **Derivation fidelity**: for a sampled scenario, every claim in `judge-guidance.md` traces to a
  cited locus present in that strand's worksheet Grounding; silent columns for that question are
  named as silent (spot-checked against `adjudicated.json` `silent` lists — e.g. Q18 R7 silent,
  Q22 five silent, Q42 five silent).
- **Difficulty**: for a sampled scenario, a fluent-but-wrong response is identifiable and the
  `judge-guidance.md` scores it below the faithful response.
- **Frozen-tier immutability**: `git diff` shows no change to `traditions/protestantism/scenarios/`,
  `results/20260803/`, `results-raw/20260803/`, or `results-raw/20260813-protestantism/`; the only
  monolith edit is `README.md`; the paper-reconciliation test passes unchanged.
- **Leaderboard rule**: the superset export yields exactly one Protestant cross-faith row
  (`protestant-unified`); the monolith and strands contribute none; equal-weight mean-of-means
  ranking on Gemini; Opus badge-only.
- **Full-grid gate**: an intentional Gemini gap makes `_assert_full_grid` fail the superset export
  (proving the gate is real, not a footnote); a full grid passes.
- **Fingerprint equality**: the 8-tradition score tier and the 8-tradition raw tier at the new
  run-id carry equal source fingerprints (asserted by test).
- **Pre-flight roots**: the run refuses to start if any `tmp/judging-runs/20260803-*` root is missing.
- **Spend gate**: smoke coverage ≥50 cells on both judges; actuals computed from usage data; the
  full run is not launched before the architect go.
- **Raw re-bake**: the live SPA manifest fingerprint for the new raw run matches the exported tier
  (and an HTML content-type on a baked path is treated as "absent", per the dual-source lesson).

## Risks and Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Spend overrun past $600 (est. ≈$530 live puts the $550 pause inside the estimate) | Medium | High | Bottom-up estimate from #89 actuals in the plan; resolve Opus **batch** path (≈$355) up front; smoke → usage-computed actuals → explicit go; alert $450, pause $550; reconcile from data not estimates (Spec 89 scar). |
| Opus judge key (`ANTHROPIC_JUDGE_API_KEY`) org-cap-blocked as in #89 | Medium | High | Resolve batch-vs-live before the smoke gate; confirm the chosen path works on the smoke; if blocked, fall back to live OpenRouter and re-check the ceiling. |
| Superset export blocked by `_assert_full_grid` (any Gemini gap in any tradition) | Medium | High | Treat full grid as a blocking gate; run Gemini full grid; budget re-judge spend for gap-closing inside the ceiling; verify roster mappings (`_SUBJECT_VARIANTS`/`_JUDGE_VARIANTS`) before export. |
| Loss of gitignored `tmp/judging-runs/20260803-*` roots (afx cleanup scar) | Low | High | Pre-flight existence check before any run; do not run cleanup; the seven frozen roots are the only source for the 8-row superset. |
| Accidental mutation of a frozen tier (`results/20260803`, monolith, raw 20260813) | Medium | High | Additive-only exports; new run-id; reconciliation test + explicit `git diff` gate before PR. |
| A flagged question hides a substantive wing split → misleading consensus ground truth | Medium | Medium | The spec-gate audit; keep-with-envelope or drop where substantive; Waleed decides. |
| Consensus scenarios read "easy" → un-ceilinged/uninformative scores | Medium | Medium | Difficulty bar enforced per scenario; pressures staged against a genuine wrong answer; watch smoke scores. |
| `judge-guidance.md` drifts from worksheets (silence-forcing, vote-merging) | Low | High | Compile as structured union with receipts; silent columns named; sample-audit against worksheets; no proof-text corpus. |
| Personal Gemini key leaks into the run | Low | High | Keys only via `taqwabench/.env` seam (OpenRouter + Anthropic); memory rule; verify before launch. |
| Superset run-id collides with or overwrites the record run | Low | High | Confirm a fresh run-id with the architect; never write `20260803`. |
| Timeline slip past paper freeze 2026-09-09 | Medium | High | Front-load audit+spec+plan (09-04); smoke+go (09-05); run+export+analysis (09-06/07); numbers 09-08. |

## References

- Issue #119 (baked decisions, deliverables, timeline).
- Study narrative: `docs/analysis/protestant-guidance-divergence-study.md`; pre-registration:
  `questions.md`, `method.md`, `codebook.md`, `pathway-rule.md`; codings:
  `codings/adjudicated.json`, `codings/grounding.json`, `output/summary.json`.
- Refactor decision spec: `docs/analysis/protestantbench-refactor.md` (§3 unified source discipline,
  §4 composition, §6 module rules, §7 scoring + leaderboard, §10 failure modes).
- Run convention: `codev/specs/89-protestantism-benchmark-round.md`,
  `codev/reviews/89-protestantism-benchmark-round.md`; `results/README.md`, `results-raw/README.md`.
- Module contract: `traditions/README.md`, the `create-tradition` skill; `sunni-islam` worked
  example; `traditions/protestantism` monolith (taxonomies to carry, register to match).
- Validator: `apps/tradition_validator/tradition_validator/models.py` (`ScenarioMeta`, closed).
- Draft `guide.md`: saved to `traditions/protestant-unified/guide.md` (Waleed-reviewed direction,
  not final).
