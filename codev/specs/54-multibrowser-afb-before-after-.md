# Specification: multibrowser — AFB before/after explorer (vanilla Gemma vs MultiWeights responses)

<!--
SPEC vs PLAN BOUNDARY:
This spec defines WHAT and WHY. The plan defines HOW and WHEN.
Implementation phases, file-by-file edits, code, and ordering live in codev/plans/54-*.md.
-->

## Metadata
- **ID**: spec-2026-08-08-multibrowser-afb-before-after
- **Status**: draft
- **Created**: 2026-08-08

## Clarifying Questions Asked

A spec did not pre-exist; the issue body plus an architect correction (issue #54 comment,
2026-08-06, and a direct `afx` instruction 2026-08-08) answer the load-bearing questions. No
questions were put back to the user — the corrections below *are* the answers, and the
remaining uncertainties are captured under **Open Questions** for consultation.

- **Q: Does per-item AFB response text already exist on disk (issue body says "saved #48 outputs, zero new spend")?**
  A: **No — this is superseded.** Per the architect: `eval_afb_probes.py` discards responses
  after judging (persists `{id, score}` only), #48's raw outputs died with its worktree, and #58
  evaluated only the full-grid head. **#54 requires a dedicated collection run** with a script
  change to persist response text (and Terra judging for the scores alongside). Budget ~$25–35,
  pre-authorized by Waleed. This is a **baked decision** (see Constraints).
- **Q: Which three subjects?**
  A: `base` = `google/gemma-4-31B-it`; `sft` = `mb-sft-guided` (stage-1 SFT adapter); `dpo` =
  `mb-sft-dpo` — the **#48 shipped incumbent**, NOT #58's scaling-null `mb-dpo-full`.
- **Q: Which condition(s)?** A: **cold** (question verbatim). Faith-context is optional and low-value
  (the paper/#48 found it near-saturated) — out of scope for the launch catalog.
- **Q: Which judge / scale?** A: `gpt-5.6-terra` via OpenRouter, the AFB official `scoring_prompt.json`
  **0–4** religious-representation scale — catalog-declared, NOT the MultiBench −1…+1 ramp.
- **Q: Does this require viewer code changes (issue says "not a viewer change")?**
  A: **A small, in-scope one, yes** — see Current State / Approach 1. The raw viewer's render, model,
  parser, and color paths are already fully catalog-generic and AFB-ready; the *only* MultiBench
  coupling that blocks a raw-only AFB catalog is run **discovery**, which enumerates `results/`
  scores manifests only. This is exactly the genericity-verification the issue asked for.

## Problem Statement

The #48 "MultiWeights" result — that judge-filtered context distillation on MultiBench's guided
data moves gemma-4-31b from **omitting** religion (AFB mean ≈ 0, "meaningful-or-deeper" ≈ 1%) to
**including** it as a live perspective (score ≥ 2 ≈ 27%) without over-application — currently
exists only as **distribution tables and aggregate figures**. A reader cannot *see* the omission
and its repair: there is no way to read, for a given ordinary-life question, the flat secular
answer from vanilla Gemma beside the fine-tuned answers that actually name a religious perspective,
each with the judge's 0–4 score and rationale.

MultiBench already ships a **raw-results viewer** (Spec 51, live on `main`) whose contract is
explicitly **catalog-generic** — the score scale, color ramp, subjects, judges, condition axes,
grouping axis, scopes, and items are all *declared by the catalog*, with no MultiBench vocabulary
baked into the render path. The AFB before/after view is precisely the "second catalog type" that
contract was designed to carry. The problem is (a) the underlying per-item response text **does not
exist anywhere** and must be collected, and (b) a raw-only catalog (one with no `results/` scores
tier) is currently **undiscoverable** in the SPA.

## Current State

**The evidence is invisible.** Today a reader of the MultiWeights work sees:
- `experiments/48_multiweights_omissive_bias/figures/afb_distribution.pdf` — a distribution figure.
- Aggregate numbers in the #48 spec/review (mean, P≥1/2/3 per checkpoint).
- No per-item responses. `eval_afb_probes.py` (both #48 and #58 copies) computes a Terra 0–4 score
  per response and **discards the response text**, persisting `{id, score}` only. #48's raw eval
  outputs were lost with its worktree; #58 ran the lean battery on the full-grid head alone.

**The instrument is in-repo (MIT).** `experiments/48_multiweights_omissive_bias/data/input/afb/`
holds the vendored AllFaith Benchmark Religious-Representation instrument: `questions.jsonl` (150
items, fields `{id, question}` — *no category field*), `scoring_prompt.json` (the official 0–4
judge template + `{rationale, score}` JSON contract), `LICENSE` (MIT, © CEFE-AI), `SOURCE.md`.

**The model-serving stack exists.** `experiments/58/modal/serve_gemma_eval.py` serves the base
model plus LoRA adapters as named models on one Modal vLLM endpoint (`base`, `sft`, `dpo`). Both
adapters live on the Modal volume `gemma-dpo`: `mb-sft-guided` and `mb-sft-dpo` (the incumbent,
never overwritten) — alongside #58's `mb-dpo-full`. The script's `dpo=` module currently points at
`mb-dpo-full`; the #54 collection run must serve **`mb-sft-dpo`** as the `dpo` subject.

**The export machinery exists and is generic.** `workflows/analysis/analysis/export_raw.py`
(Spec 51) writes `results-raw/<run-id>/{manifest.json, <group>/<item>.json.gz}` with: per-shard
gzip (mtime=0, sorted keys → byte-stable re-export), size ceilings (≤ 1 MB/shard, ≤ 200 MB/run,
validated before any write), and two `sha256` fingerprints. Its manifest builder is already
catalog-generic (declares `scale{min,center,max}`, `ramp`, `subjects`, `judges`, `conditionAxes`,
`groupBy`, `scopes`, `items`, `presets`). **But its input model is MultiBench-specific** — it reads
judging-run roots (`report.json` + `sittings.jsonl`, framings × pressures × traditions). An AFB
collection run has a completely different input shape.

**The viewer render path is already AFB-ready; discovery is not.** Verified against
`apps/multibrowser/`:
- Generic and correct for AFB with **no change**: the catalog schema/parser (`lib/rawModel.ts`
  reads `scale/ramp/subjects/judges/conditionAxes/groupBy/scopes/items`, no −1..+1 or
  tradition/framing/pressure literals), score-bounds validation against `catalog.scale`, the
  generic two-slope color ramp (`lib/rampColor.ts` `catalogScoreColor`, 0/2/4 works), and the grid
  + controls that iterate the catalog's axes/subjects/judges/scopes/groupBy.
- The **one blocker**: run **discovery** (`lib/queries.ts` `resultsRunIds` + `loadResultsRuns`)
  enumerates only `results/<id>/manifest.json` (the scores tier). A `results-raw/<id>/` with no
  `results/<id>/` counterpart yields **zero** run IDs, so **nothing in the SPA ever links to it**
  (the raw route itself renders fine from a hand-typed deep link, and its cross-tier fingerprint
  lookup already tolerates a `null` — a raw-only run needs no scores fingerprint).
- Non-blocking MB seams to respect: `corpus.ts` `CORPUS_GROUP_KEY = "tradition"` (an AFB
  `groupBy.key ≠ "tradition"` simply renders no judge-guidance/corpus cross-link — graceful);
  `rawModel.ts` `RESERVED_AXIS_KEYS = {a, b, scope, judge}` (AFB's condition-axis key must avoid
  these); `RAW_SUPPORTED_SCHEMA_VERSION = 1` (the AFB manifest must stamp `schema_version: 1`).

## Desired State

A reader visits the multibrowser SPA, reaches an **AFB before/after** run through a first-class
in-app entry point (no hand-typed URL), and for any of the 150 AFB cold-condition questions sees
the three checkpoint responses side by side — **vanilla Gemma-4-31B**, **SFT (mb-sft-guided)**, and
**SFT+DPO (mb-sft-dpo)** — each labeled with its **GPT-5.6-Terra 0–4** score and rationale, colored
by a catalog-declared 0–4 ramp (numeric scores, no band names). Curated presets surface the most
legible before/after contrasts (e.g. the questions where omission is most clearly repaired). The
whole view rides the existing #51 raw viewer; the only viewer code added is the minimal
discovery/entry-point generalization that lets a raw-only catalog be found.

Underneath: a **new `results-raw/<afb-run-id>/`** drop-in catalog (committed, single-digit MB) whose
`manifest.json` declares the AFB scale/ramp/subjects/judge/condition/grouping/items, produced by a
**sibling export command** that reuses #51's shard/fingerprint/size-ceiling/determinism machinery.
The per-item responses+verdicts collected by the (one-time, ~$25–35) run are **preserved durably in
the repo** so the spend is never repeated and the export is reproducible.

## Stakeholders
- **Primary Users**: readers of the MultiWeights paper / MultiBench browser — researchers,
  CEFEAI collaborators, and reviewers who want to *see* the omission→repair on concrete items.
- **Secondary Users**: the MultiBench team (this is the paper's companion artifact; the paper's
  repo/browser links should point at it once live).
- **Technical Team**: this builder (spir-54); the architect (approvals, spend authorization,
  running/holding the Modal endpoint + keys).
- **Business Owners**: Waleed (pre-authorized the ~$25–35 regen; owns publication scope).

## Success Criteria
- [ ] A dedicated collection run produces, for **all 150 AFB items × 3 subjects (base, sft, dpo)**
      in the **cold** condition, the **response text** and a **GPT-5.6-Terra 0–4** score + rationale.
- [ ] That collection output is **preserved durably in the repo** (committed), so re-export needs
      no re-spend and #48's "raw outputs died with the worktree" loss is not repeated.
- [ ] A `results-raw/<afb-run-id>/` catalog exists as a **drop-in** (`manifest.json` + per-item gz
      shards) produced by a **sibling export command** that reuses #51's shard writer, size ceilings,
      gzip determinism, and fingerprinting (byte-stable re-export from the same input).
- [ ] The catalog **validates against the #51 schema** (`schema_version: 1`; scale/ramp/subjects/
      judges/conditionAxes/groupBy/scopes/items present; condition-axis key avoids the reserved set)
      and **loads in the current raw viewer** with the 0–4 scale and ramp, subjects = the three
      checkpoints, and 150 items — with **no change to the render/model/parser/color code**.
- [ ] The AFB run is **discoverable and reachable in the SPA through a first-class in-app entry
      point** (not a hand-typed URL), via the minimal discovery generalization.
- [ ] The side-by-side view shows, per item, the three responses with their numeric Terra scores +
      rationales; curated preset(s) surface the clearest before/after contrasts.
- [ ] **Licensing discipline** holds: AFB instrument stays MIT-attributed (`SOURCE.md`/`LICENSE`);
      our responses/judgments are ours to publish (`CC-BY-4.0` in the catalog); the shipped tier
      excludes usage/raw/timestamps, same allowlist discipline as #51.
- [ ] The touched apps' test suites pass via the per-builder dispatcher (`.codev/checks/test.sh`):
      `workflows/analysis` (pytest) and `apps/multibrowser` (pnpm test).
- [ ] Documentation updated: `results-raw/README.md` (second-catalog example / discovery note),
      the AFB run's provenance, and the paper's companion-artifact link plan.

## Constraints

### Baked Decisions (architect — do not relitigate)
Copied verbatim from the issue #54 comment (2026-08-06) and the architect instruction (2026-08-08):
- **A dedicated collection run is required** — per-item AFB response text does not exist anywhere.
  `EVAL_MODELS=base,sft,dpo-incumbent` through the eval endpoint, with a script change to **persist
  response text**, and **Terra judging** for the scores alongside.
- **`dpo-incumbent` = `mb-sft-dpo`** (the #48 shipped incumbent), not #58's `mb-dpo-full`.
- **Budget ~$25–35**, pre-authorized by Waleed (within the earmarked regen allowance).
- **Keys: OpenRouter + Anthropic only. NEVER Waleed's personal keys.** The Terra judge runs via
  OpenRouter; the Modal endpoint uses Modal auth, not a personal API key.
- **Build on the #51 viewer + generic contract** (live on `main`) — this is a **second catalog
  type**, not a viewer rewrite. (Verification found one small, in-scope discovery gap; see below.)
- **Rides the #51 GENERIC contract**: subjects/items/condition-axes/score-scale/ramp all
  catalog-declared, jaleesbrowser-style. Judge is Terra 0–4 (catalog-declared), **not** the −1..+1
  ramp. **Numeric scores + catalog ramp, no band names.**
- **Same exclusions discipline as #51**: no usage/raw/timestamps in the shipped tier.

### Technical Constraints
- Multi-language repo: Python `uv` (`workflows/analysis`) + JS/Vite SPA (`apps/multibrowser`).
  Tests run through the per-builder dispatcher `.codev/checks/test.sh` (registry entries per app).
- Byte-stable re-export must hold within the pinned `workflows/analysis` toolchain (gzip mtime=0,
  sorted keys) — export from `uv --project workflows/analysis`.
- Catalog must stamp `schema_version: 1`; condition-axis key ∉ `{a, b, scope, judge}`;
  `groupBy.key ≠ "tradition"` forgoes the corpus/judge-guidance cross-link (acceptable for AFB).
- The client GitHub data layer is unauthenticated (rate-limited); discovery additions must not
  multiply API calls (enumerate from the already-walked git-tree, don't add per-run listing calls).

### Business Constraints
- One-time spend ~$25–35, already authorized; no recurring cost. No time estimates (AI-age).
- Publication scope: AFB items are MIT (attribution required); our responses/judgments are
  publishable under CC-BY-4.0. This is the MultiWeights paper's companion artifact.

## Assumptions
- The Modal `gemma-dpo` volume still carries `mb-sft-guided` and `mb-sft-dpo` adapters intact
  (#58 notes: incumbent "never overwritten"). **Verify before spending** (samplability/serving smoke).
- The eval endpoint can serve all three subjects on one deployment (base + two LoRA modules), as
  `serve_gemma_eval.py` already does — with `dpo` repointed to `mb-sft-dpo`.
- Terra (`openai/gpt-5.6-terra`) remains available on OpenRouter and honors the 0–4 JSON contract.
- The AFB instrument's vendored copy is authoritative; the launch catalog uses **cold** only.
- #51 is on `main` and its render path is unchanged since the genericity verification above.

## Solution Approaches

### Approach 1: Dedicated collection run → sibling AFB exporter → drop-in `results-raw/` catalog → minimal viewer discovery generalization (RECOMMENDED)

**Description**: Four load-bearing pieces, no viewer render rewrite.
1. **Collect** per-item responses + Terra 0–4 verdicts for the 3 subjects × 150 cold items via the
   Modal eval endpoint (serving `mb-sft-dpo` as `dpo`), persisting the **response text** (the script
   change) and each judgment's `{score, rationale}`. Preserve the collection output durably in-repo.
2. **Export** with a **sibling command** (e.g. `analysis export-afb`) that reuses #51's shard writer,
   size ceilings, gzip determinism, and fingerprinting, but takes the AFB collection output as input
   and emits an AFB-flavored generic catalog (scale 0–4; subjects = 3 checkpoints; judges = [terra];
   single condition axis `cold`; single scope; `groupBy` = an AFB grouping; 150 item shards).
3. **Drop in** the committed `results-raw/<afb-run-id>/` — appears in the browser by data, not code.
4. **Generalize discovery**: add a sibling to `resultsRunIds` that enumerates
   `results-raw/<id>/manifest.json` from the already-walked git-tree, merge raw-only runs into the
   run list, and add a first-class in-app entry point linking into `/results/$runId/$groupId/$itemId`.

**Pros**:
- Maximally reuses #51 (contract, exporter machinery, render path) — smallest true delta.
- Honors every baked decision; the viewer change is the minimal generalization the genericity
  mandate implies, not a bespoke AFB view.
- Durable preservation of the one-time spend; deterministic, drop-in, no redeploy for data.

**Cons**:
- Requires real infra work (Modal endpoint spin-up, adapter verification) and the ~$25–35 spend.
- Introduces a second exporter code path (sibling command) to maintain.
- The discovery generalization touches the SPA's data layer (small, but must not inflate API calls).

**Estimated Complexity**: Medium · **Risk Level**: Medium (spend + live-serving verification).

### Approach 2: Force the AFB catalog through the existing `results/` scores tier (rejected)

Emit a `results/<afb-run-id>/` scores manifest too, so existing discovery finds it. **Rejected**:
the `results/` leaderboard (`ResultsPage`) is MultiBench-specific (Gemini-only mean-of-means,
"Steadfastness (Δ)", framings) and would misrender an AFB run; it also reintroduces a scores tier
AFB doesn't need and a cross-tier fingerprint with nothing to reconcile. Worse fit than a small
discovery generalization.

### Approach 3: Bespoke AFB page/route (rejected)

A dedicated `/afb` React view purpose-built for 3-column before/after. **Rejected**: duplicates the
already-generic raw viewer, violates the "second catalog type, not a viewer change" baked decision,
and forks the render path the #51 contract exists to keep single.

### Approach 4: Reuse `export-raw` directly by faking MultiBench roots (rejected)

Shoehorn the AFB collection into `report.json`/`sittings.jsonl` shapes so `export-raw` consumes it
unchanged. **Rejected**: brittle impedance-matching against a schema built for framings × pressures ×
traditions; a clean sibling command that shares the *writer* (not the *reader*) is simpler and safer.

## Open Questions

### Critical (Blocks Progress)
- [ ] **Where is the collection output preserved, and in what shape?** The #48 scar ("raw outputs
      died with the worktree") makes durable preservation a hard requirement. Options: commit a
      small intermediate collection JSON (reproducible export input) **and/or** treat the committed
      `results-raw/` shards (which already carry response text + verdicts) as the sole source of
      record. Recommendation: commit both the compact intermediate *and* the tier, so a future
      catalog-shape change re-exports with zero re-spend. Confirm at consult.
- [ ] **Adapter/endpoint availability before spend.** Must verify `mb-sft-dpo` + `mb-sft-guided`
      are intact on the `gemma-dpo` volume and the endpoint serves all three subjects, *before*
      authorizing the run. Who spins up / holds the Modal endpoint and provides the OpenRouter key?

### Important (Affects Design)
- [ ] **Grouping axis (`groupBy`) for 150 items.** `questions.jsonl` has no category field; the
      paper's Inner Life / Relationships / Worldview split is not in the vendored data. Options:
      (a) a single AFB group; (b) vendor/derive the category mapping to group by category. A single
      group is simplest and honors "no MB vocab"; category grouping is more legible but needs extra
      data. **Recommend (a) for launch**, category as a follow-up.
- [ ] **Score ramp semantics for 0–4.** AFB is arguably *sequential* (0 none → 4 predominant), and
      the thesis target is calibration to **1–2**, not maximization (4 = over-application). The
      catalog declares the ramp regardless; decide sequential vs. a center-highlighted ramp and the
      `scale.center` value. Recommend a sequential 0→4 ramp with `center` chosen to read
      "omission (low) → representation (high)" without implying 4 is best.
- [ ] **`verdict.summary` handling.** #51 verdicts carry an always-present direction `summary`; the
      AFB judge returns only `{rationale, score}`. Confirm the viewer tolerates an absent/derived
      summary (map `rationale`→display, omit `summary`), or the sibling exporter synthesizes one.
- [ ] **Scope + condition modeling.** AFB is single-turn, single-condition (cold). Model as one
      `scope` and a single-value `conditionAxes` entry (key ∉ reserved set), which the generic grid
      renders. Confirm the single-value axis renders cleanly (no empty-control artifacts).
- [ ] **Cross-tier `fingerprint` field.** A raw-only AFB catalog has no `results/` partner; the
      viewer already tolerates a `null` cross-tier fingerprint. Decide whether to still stamp a
      self-consistent `fingerprint` (harmless) or omit it, keeping `content_fingerprint` for
      baked-vs-GitHub coherence.

### Nice-to-Know (Optimization)
- [ ] Baked deploy bundle for the AFB shards (same `railway up --no-gitignore` path as #51) — likely
      unnecessary given the tiny size, but confirm the baked-first/GitHub-fallback path treats a
      small AFB tier correctly.
- [ ] Whether to also collect the faith-context condition later (a second condition-axis value) —
      out of scope now (saturated/low-value), but the axis leaves room.

## Performance Requirements
- **Catalog size**: single-digit MB committed (150 items × 3 short responses + verdicts) — far under
  the #51 ceilings (≤ 1 MB/shard, ≤ 200 MB/run); still validated before write.
- **Viewer load**: side-by-side item view interactive on a normal connection; discovery must add
  **no** new GitHub API calls per run (enumerate from the already-walked tree).
- **Determinism**: byte-identical re-export from the same collection input under the pinned toolchain.
- **Collection cost**: ~$25–35 total, one-time.

## Security Considerations
- **Credentials**: OpenRouter + Anthropic funded keys only; **never** personal keys. No key material
  committed; the eval endpoint stays keyless/short-lived on an obscure Modal URL (as #48/#58).
- **License compliance**: AFB items are MIT — ship `SOURCE.md` + `LICENSE` attribution; do not
  relicense. Our responses/judgments ship CC-BY-4.0 (catalog `license`).
- **Data hygiene / privacy**: the shipped tier excludes usage/raw/timestamps (the #51 allowlist);
  AFB questions are the published instrument (WildChat-derived but the vendored public set).

## Test Scenarios

### Functional Tests
1. **Happy path**: export the AFB collection → `results-raw/<afb-run-id>/manifest.json` + 150 shards;
   catalog validates against the #51 schema; loads in the raw viewer showing 3 subjects, 0–4 scores.
2. **Determinism**: re-export from the same committed collection input → byte-identical shards +
   identical `content_fingerprint`.
3. **Discovery/reachability**: the AFB run appears in the SPA's run list and a first-class in-app
   link reaches `/results/$runId/$groupId/$itemId` — no hand-typed URL.
4. **Before/after legibility**: a known item (base scores 0, dpo scores ≥ 2) renders three responses
   with the correct numeric scores + rationales and correct ramp colors.
5. **Edge — reserved axis key / schema version**: a catalog with a reserved condition-axis key or a
   wrong `schema_version` fails soft with a notice (regression guard for genericity assumptions).

### Non-Functional Tests
1. **Size-ceiling guard**: exporter aborts before any write if a shard/run would exceed the ceilings.
2. **No-API-call-inflation**: discovery generalization adds runs from the walked tree without extra
   GitHub requests (verified in the data-layer test).
3. **Cross-tier tolerance**: raw-only run with `null` scores fingerprint loads without a false notice.

## Dependencies
- **External Services**: Modal (vLLM eval endpoint + `gemma-dpo` volume); OpenRouter (Terra judge);
  GitHub raw + git-trees (SPA runtime data layer); Railway (SPA host).
- **Internal Systems**: Spec 51 raw viewer + `results-raw/` contract (live on `main`); the #51
  export machinery in `workflows/analysis` (shard writer, fingerprints, ceilings); the #48/#58 eval
  harness (`serve_gemma_eval.py`, `eval_afb_probes.py`) as the collection starting point.
- **Libraries/Frameworks**: `workflows/analysis` (`uv`, pytest); `apps/multibrowser`
  (Vite/React19/TS/Tailwind4/HeroUI/TanStack, pnpm).
- **Data/Instrument**: AFB-150 MIT instrument (`questions.jsonl`, `scoring_prompt.json`, `LICENSE`,
  `SOURCE.md`) currently under `experiments/48_multiweights_omissive_bias/data/input/afb/`.

## References
- Issue #54 (body + 2026-08-06 data-source-correction comment) and the 2026-08-08 architect instruction.
- Spec 51 — `codev/specs/51-multibrowser-raw-results-brows.md`; `results-raw/README.md` (generic
  catalog contract, dual-source, fingerprints, retention).
- Spec 49 — `results/` scores tier / aggregator reuse.
- Spec 48 — `codev/specs/48-multiweights-omissive-bias.md` (AFB instrument, recipe, checkpoints).
- #58 — `experiments/58_multiweights_full_grid_dpo/notes.md` (incumbent `mb-sft-dpo` vs scaling-null
  `mb-dpo-full`; `gemma-dpo` volume contents; serve script).
- Viewer genericity trace (this spec's Current State): `lib/rawModel.ts`, `lib/rampColor.ts`,
  `lib/queries.ts` (`resultsRunIds`/`loadResultsRuns`), `lib/corpus.ts`, `src/router.tsx`.

## Risks and Mitigation
| Risk | Probability | Impact | Mitigation Strategy |
|------|------------|--------|-------------------|
| Adapters missing/altered on the `gemma-dpo` volume | Low | High | Verify + serving smoke BEFORE authorizing spend; escalate to architect if absent. |
| Collection output lost again (worktree death) | Med | High | Commit the collection output durably as export input-of-record; treat committed `results-raw/` as preservation. |
| Spend overrun beyond ~$35 | Low | Med | Cold-only, 150×3 items, concurrency-bounded; reconcile actual spend against usage, stop at ceiling, no faith-context. |
| Viewer assumes a scores tier / non-null fingerprint | Low | Med | Verified null-tolerant; add a regression test for the raw-only path. |
| Genericity gap beyond discovery surfaces mid-build | Low | Med | Each found seam is small (reserved keys, groupBy, summary) — fix in the exporter/catalog, surface to architect if a render change is implied. |
| 0–4 ramp mis-signals "4 is best" (over-application) | Med | Low | Choose ramp/center to read low→high representation, not "higher = better"; numeric scores, no band names. |
| Terra JSON contract drift | Low | Med | Fail-fast on non-conforming judge output (validate `{score∈0..4, rationale}`), retry bounded, no fallback scoring. |

## Expert Consultation
<!-- Populated by porch's 3-way consultation (Codex, Claude per per-phase config) after this draft. -->
**Date**: (pending) · **Models Consulted**: (per `porch.consultation.models` = codex, claude)
**Sections Updated**: (to be filled after consultation)

## Approval
- [ ] Technical Lead Review
- [ ] Product Owner Review
- [ ] Stakeholder Sign-off
- [ ] Expert AI Consultation Complete

## Notes
- **Deviation surfaced for the architect**: the issue frames #54 as "not a viewer change." Genericity
  verification confirms the render/model/parser/color paths need **no** change, but a **small
  discovery generalization + one in-app entry point** *is* required for a raw-only catalog to be
  reachable. This is consistent with #51's genericity mandate (and the issue's own
  "verify the genericity requirement covers…" ask), but it is a real, in-scope SPA code change — not
  a pure data drop-in. Flagged rather than silently absorbed.
- **`dpo` = `mb-sft-dpo`** everywhere in this catalog — the serve script's `dpo=` module must be
  repointed from `mb-dpo-full` for the collection run.
- The companion-artifact link from the MultiWeights paper's repo/browser should be added once the
  run is live (Review-phase follow-up).
