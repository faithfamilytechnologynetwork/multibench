# spir-51 — multibrowser raw-results browser (transcripts + verdicts)

## Phase: Specify (strict mode, porch-driven)

### 2026-08-06 — kickoff + reference deep-read
Architect handed a rich pre-spec brief (issue #51 + 2 architect comments + taqwabench
retro). Read all of it plus the real reference code before drafting.

**Reference (jaleesbench) — read verbatim:**
- `export_web.py`: `index.json` catalog + one deterministic-gzip shard per probe
  (compresslevel 9, mtime=0 → byte-identical). Shard cell = {subject, conditions,
  transcript[{role,content}], verdicts[]}. Flat row-major score blob + presets in index.
- `apps/jaleesbrowser/src/datasource.ts:70-84`: **magic-byte gunzip sniff** (0x1f 0x8b)
  — carry verbatim (double-gzip ambiguity across hosts).
- retro: split catalog (small/stable) from scores (big/churny); stamp contractVersion
  in BOTH catalog AND every shard; judge axis in matrix; fetch-at-runtime (not commit
  60MB baked); jsDelivr consideration; ship a `--limit` dev fixture; NO band names
  (jaleesbench's Burns/Perfume ladder does NOT port — MultiBench is numeric −1..+1).

**#49 seams in THIS repo (build ON these):**
- `results/<run-id>/` scores tier (manifest + per-tradition shards), read at runtime.
- `workflows/analysis/analysis/export_results.py`: loaders — `read_run_root`,
  `resolve_judgments` (v2 overlay + Opus-alias dedup + later-ts winner), subject/judge
  alias maps, `JUDGE_UI` (gemini full_grid / opus sample). **Raw tier MUST reuse these**
  so raw & score tiers never disagree. `analysis export` CLI already exists (cli.py:108).
- SPA: inert `ResultsRegion.tsx` + `results.ts::loadResults` (returns null today) =
  the per-scenario seam to make live. `github.ts` raw+SHA-pin fetch boundary.
  `resultsModel.ts` (fail-soft parse, SUPPORTED_SCHEMA_VERSION, isSafePathSegment).
  `scoreColor.ts` (−1..+1 diverging ramp, no band names).

**Real data (derived format from data, not docs):**
- `tmp/judging-runs/20260803-merged/<tradition>/sittings.jsonl` (transcripts,
  ~110MB/tradition) + `judgments.jsonl`. Opus roots (`*-unstated-opus`,
  `*-framings-opus-sample`) have judgments ONLY (no sittings) → **transcript source =
  the full-grid Gemini merged run; verdicts = all roots resolved.**
- Sitting keys: subject, tradition, scenario_id, pressure, framing, context_prefix,
  turns[{role,content}], + attempts/usage/ts (EXCLUDE). `context_prefix` carries the
  stated/guided "what the model was told" text (None for unstated; stated ~109 chars,
  guided ~6.5KB).
- Judgment keys: subject, scenario_id, pressure, framing, judge, scope, score,
  direction, rationale, + raw/usage/ts/sitting_key (EXCLUDE raw/usage/ts/sitting_key).
- **Score is ALREADY on −1..+1** (SCORES={-1,-0.5,0,0.5,1}) — no −2..+2 rescale needed
  (differs from jaleesbench). Ship verdict score as-is; scoreColor consumes it directly.

**Test dispatcher** already registers both `workflows/analysis` and `apps/multibrowser`
— touching both apps runs both suites. Good.

Next: draft spec → commit → **ping architect BEFORE the gate** (taqwabench offered a
cross-workspace pre-gate spec review).

### 2026-08-06 — three reviews in (iter 1), all converge → major spec revision
- **taqwabench cross-workspace** (architect-arranged, authoritative): APPROVE w/ 1 defect
  + rulings. DEFECT: determinism self-contradiction → ban wall-clock ENTIRELY, identity =
  run-id + deterministic SOURCE FINGERPRINT (hash over resolved-judgments stream);
  fingerprint stamped in BOTH tiers' manifests + checked equal per run-id (makes "cannot
  disagree" checkable). RULED (a) sibling `export-raw`; (b) context_prefix = per-shard
  `contexts` pool keyed by framing. Adds: shard enum manifest-declared (never trees API);
  export-time fail-loud on a resolved judgment with no full-grid sitting. PROMOTE
  steadfastness-cliff preset into spec.
- **Codex CMAP** REQUEST_CHANGES: determinism/timestamp; run-id missing from deep-link
  state; presets not testable (need score/scope/threshold/cap/sort/tie-break/sparse-Opus);
  perf ceilings unspecified; agreement test mathematically misstated (cell mean ≠
  cross-scenario slice mean); licensing needs actionable rule (allowlist, not "sanitize
  if sensitive"); name the preserved parity fields.
- **Claude CMAP** REQUEST_CHANGES (measured against real data — caught my factual errors):
  (1) SIZE WRONG — per-scenario shard 161–300 KB gz (median ~221), Gemini grid ~110–130
  MB gz, tier ~110–150 MB w/ Opus — NOT 30–80 MB (2–4×). (2) FACTUAL: `framings-opus-
  sample` DOES have sittings.jsonl (verified) — only `unstated-opus` lacks them; must rule
  which sittings win. (3) transcript↔verdict join: #49 loaders read judgments ONLY (no
  sitting loader) → transcript reading is NEW code; subject spellings differ across roots
  (verified) → key transcripts by NORMALIZED subject, unmatched verdict = loud fail. (4)
  run-id missing from view state. (5) entry-point ambiguous (ResultsRegion is 1-line
  inline; A/B is a full view). (6) minor: #49 tier=184KB not "single-digit MB"; Opus
  judgments=42,711; placeholder string literally says "bands" (must edit).

**Rulings I'm baking into iter 2:** transcript source = EXCLUSIVELY the full-grid
(report.json) merged run; other roots' sittings ignored. Sittings keyed by normalized
subject; unmatched verdict = abort. No wall-clock in raw tier; fingerprint identity.
sibling `export-raw`; per-shard contexts pool keyed by framing. New run+scenario-scoped
route for the full raw view; ResultsRegion becomes a live in-page entry. Corrected sizes
(~110–150 MB gz/run) — flagging to Waleed at gate as a repo-weight decision (4× the
issue estimate). Field allowlist replaces vestigial sanitization (scenario corpus already
public in traditions/). Presets fully specified. Agreement test = field-level equality +
independent aggregate recompute + fingerprint equality.

### 2026-08-06 — pre-gate amendment: catalog-genericity (issue #54, Waleed)
Architect relayed a new requirement (issue #54, the AFB before/after explorer): the #51 raw
contract + viewer must be GENERIC enough that a non-MultiBench catalog rides the same viewer
with zero component changes. #54 ships an AFB 0–4 catalog (vanilla Gemma vs fine-tuned,
GPT-5.6-Terra judge) as a SECOND catalog type — not a viewer change. Requirement (not new
#51 scope):
1. score scale + color ramp = catalog-declared data (not hardcoded −1..+1 / scoreColor
   constant). MultiBench catalog ships the scoreColor stops on (−1,0,+1), no rung labels;
   AFB ships 0–4 + its own ramp. Optional labels = schema affordance MB declines.
2. items + grouping axis = catalog-declared (NOT tradition→scenario shaped). On-disk
   <tradition>/<scenario> nesting is MB's realization of a generic <group>/<item>
   convention; shard paths manifest-declared.
3. subjects = catalog-declared (not the leaderboard set).
Genericity check: raw zod schemas + raw-view components contain NO tradition/scenario
literals and NO −1..+1 ramp constant — all in data. (#49 score/leaderboard tier stays
MB-specific; genericity binds the NEW #51 raw contract that #54 reuses.) My design is
already ported from jaleesbrowser's generic contract, so this is cheap to absorb; main
watch-item is not importing scoreColor's hardcoded constant in the raw view (read the ramp
from the catalog). Folded into Baked Decision 13 + Desired-State ruling + criteria + tests
+ risk. Re-committing; gate re-queues for Waleed.

### 2026-08-06 — pre-gate amendment 2: dual-source data (Waleed resolves repo-weight)
Waleed resolved the repo-weight Critical open question with a DUAL-SOURCE architecture:
- **Committed GitHub compressed tier** (per-scenario gz shards, as specced) = AUTHORITATIVE
  + FALLBACK. Waleed explicitly OK'd this committed weight (~110–150 MB gz/run).
- **Railway baked bundle** = the deploy (`railway up`, from the local machine so NOT
  constrained by what's committed) additionally bakes the FULL UNCOMPRESSED export into the
  static bundle (same-origin /data-style) = PRIMARY when present.
Resolution rule: baked-first (fast, no rate limits / API budget), GitHub-fallback; the
SOURCE FINGERPRINT decides coherence; a Notice when serving fallback. Identical slimmed
CONTENT both sources (allowlist applies to BOTH — both public); "full" = uncompressed in
bundle vs gz on GH, same fingerprint. Elegant: the magic-byte gunzip sniff we already carry
means uncompressed baked (.json, no 0x1f8b) and GH .gz go through ONE client code path.
Deploy-flow trade (disclosed): refreshing the BAKED copy = re-export + railway up (no longer
appears without a deploy); GH fallback still updates live on commit.
Folded into Baked Decision 14 + Desired-State ruling + criteria + tests 16/17 + risks +
closed the repo-weight open question. LICENSE SPDX still OPEN (flagged). Re-committing; gate
re-queues for Waleed — now ONE decision left at the gate (license id).

### 2026-08-06 — pre-gate amendment 3: license resolved
Waleed: dataset.license = CC-BY-4.0 (SPDX). Closes the last open decision. (#54's AFB items
are MIT — that's #54's concern; #51's MultiBench corpus/responses/judgments = CC-BY-4.0.)
Folded into Baked Decision 7 + criteria + security + open questions + approval. NO open
decisions remain for the spec-approval gate — ready for Waleed's word.

### 2026-08-06 — spec-approval gate APPROVED by Waleed → Plan phase
Spec approved (all decisions resolved: genericity #54, dual-source, CC-BY-4.0). Drafted the
plan (codev/plans/51-...) — 6 phases, producer→consumer ordered:
1. Raw export core (pure transform): new normalized sitting reader (full-grid only) + reuse
   #49 verdict loaders + join w/ orphan-abort + shard/catalog build + shared fingerprint.
2. Writer + `export-raw` CLI + presets + fingerprint into results/ manifest (additive #49) +
   committed launch dataset + results-raw/README.
3. SPA generic zod contract + dual-source resolver (baked-first/GH-fallback, fingerprint
   coherence) + gunzip sniff verbatim + version checks + dev fixture.
4. Raw view route: transcripts + verdicts w/ catalog-declared ramp (generic interpolator,
   NOT scoreColor constant) + live ResultsRegion entry + drill-down; edit "bands" string.
5. A/B compare + deep-link URL state (incl run-id) + preset navigation.
6. Railway baked-bundle deploy wiring + docs + arch-doc updates.

Resolved the 2 flagged plan decisions: (a) context_prefix = per-shard `contexts` keyed by
framing (measured ~2-3KB gz/shard, negligible); (b) sibling `export-raw` Typer command
reusing #49 loaders + new sitting reader + shared fingerprint helper. Also decided NOT to
drop results/ generated_at (default-run selection needs it; only ADD fingerprint). plan
checks pass (6 phase ids). Committing; plan-phase consult next, then plan-approval gate →
Waleed.

### 2026-08-06 — plan iter-1 reviews (Codex + Claude), both REQUEST_CHANGES → revise
Both converge; Claude verified against codebase (+ Railway docs) and found real defects:
- **Generic-contract contradiction**: Phase-1 cells emit literal framing/pressure fields vs
  Phase-3 "no such literals". FIX: adopt jaleesbench generic `conditionAxes` (catalog-
  declared) + cells `conditions: Record<string,string>`; schemas/components iterate axes,
  never hardcode names. Prohibition = no hardcoded MB axis names/enums, dynamic keys OK.
- **Fingerprint NOT additive**: build_manifest only sees aggregated TraditionExport;
  build_tradition_export discards resolve_judgments (line 370). Must thread ONE shared
  global-stream hash fn through BOTH exporters (same input shape) or the invariant silently
  fails. resultsModel.ts must expose fingerprint (currently strips unknown).
- **Railway deploy BROKEN** (Claude, sourced): `railway up` respects .gitignore by default →
  gitignored public/data-raw never uploads → primary source silently never ships. FIX:
  `railway up --no-gitignore` + `.railwayignore` (re-exclude node_modules/dist).
- **Baked size WRONG**: bake is UNCOMPRESSED; measured ratio ~3.7× → ~400-550 MB baked,
  ~1 GB in image after public/→dist/. Waleed's "uncompressed" directive predates this.
  FLAGGING to architect/Waleed; RECOMMEND baking the GZ shards same-origin instead (~115MB,
  same speed/no-rate-limit, reuses the gunzip sniff we already carry). Measure in Phase 2.
- isSafePathSegment rejects '/' but shard paths are <group>/<item>.json.gz → need multi-
  segment safe-relpath validator (Py + TS).
- build_scenario_shard needed titles/taxonomy from traditions/ but corpus-root not passed →
  DROP title/taxonomy from shard; item labels live in the CATALOG (id-based for MB); SPA
  enriches MB context from its existing tradition/scenario query via a (group,item) adapter.
  Removes the corpus-root dependency.
- URL ownership: run/group/item = ROUTE PATH params; A/B/framing/pressure/scope = validated
  SEARCH (route validateSearch zod, NOT searchParams.ts alone).
- Memory: build_raw_corpus holds 430MB sittings in RAM. Stream per-tradition (build→
  serialize→gzip→hold compressed bytes→write after full validation); ~115MB buffered.
- Split presets into their own phase (Phase 2 was oversized).
- Fixture in src/test/ (NOT public/data-raw, which collides w/ bake + slows deploy.test's
  real pnpm build). --limit fixture can't be fingerprint-coherent → injectable expected
  fingerprint for the baked-coherent test.
- Bake = separate predeploy script (NOT in `pnpm build`) so deploy.test's build is unaffected.
Revised plan → 8 phases. Sending architect an afx flag on the baked-representation (gz vs
uncompressed / ~1GB image) decision.

### 2026-08-06 — Railway spir-51 test project deleted (architect-directed)
A Railway project `spir-51` (ID 47f5e095-6392-4947-aa76-12835e52aab5, workspace Haadi) had
been created + linked to this worktree by the plan-review consult's Railway verification —
NOT a builder-authorized action. Architect directed deletion. I verified first (railway
status showed it linked, empty: Service None / no resources — matched the description), then
`railway delete --project <id> --yes` (accepted, exit 0), `railway unlink --yes` (worktree
now unlinked). Authoritative confirmation: a re-delete by ID returns "Project not found" and
`railway status` = no linked project. `railway list` still shows it — Railway deletion is
SCHEDULED/async, list purges on a lag. RULE GOING FORWARD (architect): any Railway/external-
account action goes through the architect FIRST. gz-baked also APPROVED by architect (encoding
is implementation; measurement settles it) — folding into the plan revision.

### 2026-08-06 — plan revised (8 phases) + rebuttal → plan-approval gate
Revised plan committed (f3af4bf) folding in both plan reviews; rebuttal written. gz-baked
approved by architect; Railway test project deleted + confirmed by architect. plan checks
pass (8 phase ids). Reached plan-approval gate → STOP, awaiting Waleed. Not approving.

### 2026-08-06 — IMPLEMENT phase_1 done: raw export core (pure transform)
Wrote workflows/analysis/analysis/export_raw.py + tests/test_export_raw.py (12 tests, all
green; full analysis suite 125 green). Implements:
- read_full_grid_sittings: NEW sitting reader over the report.json-bearing run only; keys by
  NORMALIZED subject; drops harness fields (attempts/usage/ts/model); rejects dup identity +
  conflicting context_prefix; context_prefix null→None (verified unstated=null).
- build_raw_corpus/build_tradition_raw: reuse read_run_root+resolve_judgments for verdicts;
  join to full-grid transcripts; ABORT on orphan verdict, out-of-universe sitting, ambiguous
  (2 report-bearing roots). Resolve once per tradition, reuse for global fingerprint stream.
- Generic shard (schema_version, contexts pool keyed by framing, cells w/ conditions:{framing,
  pressure}, transcript, verdicts) + generic catalog (scale/ramp from colors.STOPS, subjects,
  judges w/ fullGrid flag, conditionAxes, contextAxis, groupBy, manifest-declared items,
  fingerprint). No title/taxonomy in shard (no corpus-root dep).
- source_fingerprint(resolved): sha256 over sorted (subj,scenario,pressure,framing,judge,
  scope,score,direction,rationale) — shared helper; Phase 2 wires it into export_results.
- Verdict = allowlisted {judge(UI key),scope,score,summary(=direction),rationale?}.
Next: porch done → verify (codex+claude consult) → phase_2.

### 2026-08-06 — phase_1 APPROVED (3 consult iters) → phase_2
phase_1 ✓ (Claude APPROVE, Codex issues all resolved over iters 1-3). Real-data smoke passed
(buddhism 52×90, eastern-christianity 106×90, both judges). Now on phase_2: fingerprint
cross-tier plumbing + streaming writer + export-raw CLI + size measurement. Deferred-from-
phase_1 memory items land here: per-tradition judgment reads (drop raw/usage) + streaming
catalog so peak memory is bounded (Claude measured 1.87GB with whole-root reads).
Plan: put source_fingerprint in a neutral analysis/fingerprint.py (both exporters import it,
no circular dep); thread resolved stream through export_results.build_manifest.

### 2026-08-06 — IMPLEMENT phase_2 built: writer + CLI + fingerprint plumbing
- analysis/fingerprint.py (NEW): shared source_fingerprint + fingerprint_line/combine_
  fingerprint (both tiers use it; no circular dep). Tuple = (tradition,subject,scenario,
  pressure,framing,judge,scope,score,direction,rationale).
- export_results (#49 additive): TraditionExport carries fingerprint_lines (lightweight, not
  full dicts); build_manifest stamps the combined fingerprint. Kept generated_at (default-run
  selection needs it) — its fingerprint is wall-clock-independent (test proves it).
- export_raw: per-tradition streaming reads (drop raw/usage at read) replacing whole-root
  read_run_root — bounds memory; deterministic streaming write_dataset (gz lvl9 mtime=0,
  validate-all-sizes-before-write, prune stale, multi-seg safe-relpath); --limit fixture.
- cli.py: `analysis export-raw` command.
- MEASURED real export (all 3 roots): 519 scenarios, 126.2MB gz total, max shard 533KB,
  median 233KB, p99 401KB. Ceilings RAISED to per-shard 1MB / per-run 200MB (real max 545KB
  → the initial 512KB ceiling correctly ABORTED before any write; validate-before-write works).
  Peak RSS 1.66GB (was ~1.9GB) — streaming caps it to one tradition + compressed buffer;
  acceptable for a one-off batch export. Raw manifest fingerprint == results/ manifest
  fingerprint (cross-tier equality test).
- Tests: test_export_raw_writer.py (12) — determinism, ceilings (both, no partial tier),
  safe-path guards, --limit, prune, cross-tier fingerprint equality, wall-clock-independence,
  CLI. Full analysis suite 163 green.

### 2026-08-06 — phase_2 APPROVED (Codex+Claude); nits folded
Phase 2 approved both. Folded Claude's non-blocking nits: import _require_safe_segment from
export_results (no forked traversal guard); moved gzip import to top + dropped unused re;
removed misleading __all__; prune removes now-empty group dirs; added no-wall-clock manifest
assertion test. Deferred to Phase 4: document exporting toolchain (Python/zlib) in
results-raw/README (determinism is per-build). 159 tests green. Next: phase_3 (presets).

### 2026-08-06 — IMPLEMENT phase_3: presets (export-computed)
compute_presets() in export_raw: Models split (widest turn1 Gemini cross-subject spread),
Judges differed (full-scope |gemini-opus|>=1.0, contrast vs top-gemini subject), Steadfastness
cliff (biggest negative gemini full-turn1 drop). Each: deterministic sort, one-entry-per-
scenario dedup, cap 12, stable keys (preset:scenario), sparse-safe (skip missing judge/scope),
deep-link param maps {group,item,framing,pressure,scope,a,b?}. Accumulated from a compact
per-cell judge-score map (numbers only) during streaming (written scenarios only) — no extra
memory. Wired into catalog (build_catalog + write_dataset). Real data: all 3 presets, 12
entries each, sensible. 9 preset tests; full suite 168 green.

### 2026-08-06 — phase_3 iter-2: preset determinism + cross-tradition diversity
CORRECTION to my earlier "12 entries each, sensible" note: with the initial (magnitude,
scenario-lexicographic) tie-break, all 36 real preset entries landed in buddhism (hundreds of
scenarios tie at max spread → alphabetical pick). Fixed: (1) group added to all sort keys +
canonical _PRESSURE_ORDER/_FRAMING_ORDER (Codex determinism); (2) _dedup now ROUND-ROBINS
across groups (sorted group order) so a preset is a curated CROSS-tradition view. Verified:
all 3 presets now span all 7 traditions. This refines the spec's fixed "(scenario,pressure,
framing) tie-break" — flagging the architect (serves the spec's curation goal; both reviewers
required it). Added cross-group diversity+determinism tests + write_dataset-emits-presets +
--limit-confines-preset-entries tests. 176 green.

### 2026-08-06 — architect APPROVED round-robin (CMAP-required spec refinement)
Architect ruled round-robin approved; must be recorded in the REVIEW DOC (codev/reviews/51-*)
as a CMAP-required spec refinement WITH the real-data evidence (all-36-in-buddhism → spans 7
traditions). [TODO in Review phase.] Optional within-slot tie-break by "matched n" then
lexicographic: SKIPPED — needs coverage(n_judged) threaded into the compact preset cell map
(scores-only today), so NOT a one-liner; architect said one-liner-only. Noted here + will note
in review. Proceeding phases 4-8.

### 2026-08-06 — phase_4: committed launch dataset + README
Re-exported BOTH tiers for run 20260803 from the same roots so their committed fingerprints
MATCH (sha256:53c8ac98…): results/20260803/manifest.json gains `fingerprint` (+ new
generated_at; shards byte-stable) — safe for the live SPA (resultsModel z.object strips unknown
keys); results-raw/20260803/ = 519 gz shards, 126MB (uncompressed 449MB, ratio 3.56 → confirms
gz-baked ~4× smaller than uncompressed). Wrote results-raw/README.md (contract, layout,
allowlist, dual-source gz-baked, deploy-flow --no-gitignore, presets round-robin + conditions-
nested params, fingerprint, CC-BY-4.0, toolchain-determinism caveat, produce/refresh). Committed
results-raw/20260803 + README + results/20260803/manifest.json.

### 2026-08-06 — phase_4 APPROVED (both). Forward notes for phases 5-7:
- Catalog scopes label=id ("turn1"/"full"); consider friendly labels ("initial"/"post-pressure")
  in Phase 6 (manifest-only re-export). Subjects id==label is CORRECT per retro (canonical slugs).
- Subject ids contain "/" → Phase 7 deep-links MUST URL-encode; test a slashed id round-trip.
- Phase 5 zod schemas must be written against the COMMITTED shard/catalog shapes (shard-shape
  changes later would rewrite ~126MB history). Committed shapes are the contract now.

### 2026-08-06 — IMPLEMENT phase_5: SPA raw data layer
- rawModel.ts (NEW): GENERIC zod contract (catalog + shard) + tolerant parsers. Score is
  z.number().finite() (bounds from catalog.scale, NOT hardcoded −1..1 → genericity). No
  tradition/scenario/framing/pressure literals; conditions = Record<string,string>. isSafeRelPath
  (every component). Version-mismatch/unsafe-path/malformed → Notice, never throw. Verified a
  synthetic 0-4 AFB catalog parses with no code change.
- rawSource.ts (NEW): decodeGzText (magic-byte sniff 0x1f8b carried VERBATIM from jaleesbrowser
  + DecompressionStream feature-detect → DecompressionUnsupportedError, no polyfill); RawDataSource
  seam + BakedRawSource (same-origin) + GitHubRawSource (SHA-pinned); resolveRawSource (baked-first,
  fingerprint coherence via score-tier fingerprint, GitHub fallback + Notice on stale/absent).
- github.ts: added rawBytes() (ArrayBuffer for gz shards) + results-raw to WALK_DIRS.
- resultsModel.ts: tolerant optional `fingerprint` field (so raw view gets the authoritative
  score-tier fingerprint; pre-#51 manifests still parse).
- 17 rawData tests (parsers incl. 0-4 genericity, gunzip both cases, resolver baked/stale/absent,
  source impls). Full multibrowser suite 170 green; typecheck clean. Dev render fixture deferred
  to phase_6 (view tests).

### 2026-08-06 — phase_5 APPROVED (both) after 7 iters. Data layer hardened:
generic zod contract (0-4 AFB catalog parses unchanged); dual-source resolver (baked-first,
fingerprint coherence on BOTH paths, per-shard GitHub fallback gated on GitHub coherence);
fail-soft loaders (404/rate-limit/decompression/malformed/version); catalog-aware shard
consistency; cache-only-serializable (persistence-safe) + rawScenario/rawSource excluded from
localStorage persistence (quota); useRawScenario hook w/ fingerprint in key. Drift guards: real
committed catalog + .gz shard parse + results/↔results-raw/ fingerprint equality. 191 SPA tests.
Phase-6 carry-forwards: gate useRawScenario on expectedFingerprint!==null (avoid wasted GH fetch +
misleading flash); static genericity check must ignore comments; consider friendlier scope labels
in catalog (manifest re-export).

### 2026-08-06 — IMPLEMENT phase_6: raw view route + live ResultsRegion
- rampColor.ts (NEW): catalogScoreColor(scale, ramp, value) — generic two-slope interpolator over
  the CATALOG-declared scale+ramp (NOT scoreColor's hardcoded −1..1). Same score → different color
  under different scales (genericity proven in tests).
- routes/RawResultsPage.tsx (NEW) at /results/$runId/$groupId/$itemId: loads via useRawScenario
  (gated on runs-settled so the score-tier fingerprint is known before fetch); renders subject +
  per-conditionAxis selectors (generic, no hardcoded axes), the selected cell's context prefix +
  transcript (Markdown) + verdict cards (score colored by catalog ramp, Opus 'sample' badge).
  Fail-soft notices; NotFound on missing run.
- ResultsRegion.tsx: now a LIVE in-page entry — links to the raw view for the default results run
  (data-has-results); placeholder when no run; dropped the "bands" wording. ScenarioPage passes
  traditionId/scenarioId.
- router.tsx: added rawResultsRoute.
- Tests: MB render (transcript+verdicts), NON-MB 0-4 catalog render (genericity, no component
  change), live ResultsRegion link, rampColor (generic + null-neutral). scenario.test updated
  (no "bands"). 201 SPA tests green; tsc clean; deploy.test (real vite build) passes.
Note: #49 loadResults() inert seam (returns null; scenario.results) is now vestigial (ResultsRegion
no longer reads it) — flag for Review/simplify cleanup.

### 2026-08-06 — phase_6 iter-2: ResultsRegion link-only APPROVED by architect
Architect ruled option (a): ResultsRegion is a live LINK, no eager shard fetch (perf: a grid
needs the ~220KB shard on every scenario page; score tier has no per-scenario cell scores).
Made it CONTENTFUL from the run's score manifest ("N models × M conditions", no fetch).
REVIEW-DOC TODO: record this as a perf-driven plan deviation (220KB/page rationale + score-
tier-lacks-cell-scores). Also fixed: RawResultsPage shard-load-fail shows 'unavailable' (not
'No cell'); back-link to scenario/judge-guidance; /results→/t/<tradition> drill-path disclosed
in spec+plan. Multi-run: drill-link + ResultsRegion use defaultRunId (run not propagated) —
phase-7 deep-link item. 206 SPA tests.

### 2026-08-06 — phase_6 APPROVED; architect ruled option (b): ADD cell-score grid (phase_7)
Rationale (REVIEW-DOC): selector-only repeats the one-at-a-time pattern Waleed rejected in #49's
leaderboard; his preference is dense-at-a-glance (#55 board + heat strip + tooltip). The raw view
already holds the full shard → grid is fetch-free. Shape: subjects × (pressure×framing) chips
colored by the catalog ramp (judge-selectable + scope), each chip=cell score, click chip → that
cell's transcript+verdicts (grid IS the navigation; selectors/URL-state underneath). A/B = pin two
subjects from the grid. Phase-8 doc: baked-first needs a GitHub fingerprint read → partial
rate-limit immunity (document exactly). loadResults seam annotated deprecated (review/simplify TODO).

### 2026-08-06 — IMPLEMENT phase_7: cell-score grid + A/B + deep-links + presets
- rawSelection.ts: URL state (fail-soft) with GENERIC per-axis conditions (not hardcoded
  framing/pressure) — a=subject, b?, conditions:Record<axisKey,value>, scope, judge; each axis a
  flat search param; out-of-vocab → catalog defaults. Wired validateSearch on rawResultsRoute.
- RawResultsPage rewrite: cell-score GRID (subjects × condition-tuple product, chips colored by
  the catalog ramp for the selected judge+scope; click chip = navigate to that cell → the grid IS
  the navigation, per architect ruling); judge+scope pills; A/B compare (pin subject B → two
  CellDetail columns); presets rendered as deep-links (may target other scenarios); full view
  state in the URL.
- Tests: grid navigates, A/B two columns, deep-link write (via router.state.location.search) +
  restore, preset deep-link, generic 0-4 grid, rawSelection unit (defaults/fail-soft/round-trip/
  generic axes). 214 SPA tests green; tsc clean; deploy.test (real build) passes.

### 2026-08-06 — phase_7 APPROVED (both, 2 iters). Grid+A/B+deep-links+presets done.
Non-blocking nits folded: preset Link spreads conditions FIRST so reserved keys win (matches
rawSelectionToSearch). Compare-B URL covered transitively. Dead loadResults seam annotated
(review/simplify TODO). Next: phase_8 (Railway gz-baked deploy wiring + deploy-test safety + docs
+ arch-docs). Phase-8 doc TODO: partial rate-limit immunity (baked coherence needs GH fingerprint).

### 2026-08-06 — IMPLEMENT phase_8: Railway gz-baked deploy wiring + docs + arch-docs
- apps/multibrowser/scripts/bake-and-deploy.sh: export-raw gz into public/data-raw + `railway up
  --no-gitignore`; .railwayignore (node_modules/dist); .gitignore public/data-raw/ (deploy-only).
- deploy.test guard: a normal build carries NO dist/data-raw (bake is deploy-only) + gitignored.
  VERIFIED manually: export-raw --limit → public/data-raw → pnpm build → dist/data-raw served;
  cleaned up (gitignored). Production `railway up` is architect-driven post-merge (wiring only here).
- README: raw-browser section + dual-source bake flow + partial-rate-limit-immunity note.
- arch-docs (update-arch-docs skill): +1 arch-critical fact (raw tier + dual-source, at cap 10);
  arch.md analysis-workflow raw-tier paragraph; lessons-learned +catalog-generic/fingerprint/
  gunzip-sniff/size-from-real-data/Railway-.gitignore/persist-quota. Hot lessons stayed at cap.
218 SPA + 177 analysis tests green.
REVIEW-DOC TODOs (Review phase): round-robin presets refinement; link-only ResultsRegion (220KB);
partial rate-limit immunity; loadResults dead-seam cleanup.

### 2026-08-06 — phase_8 iter-1 (deploy wiring + docs)
Ran `porch done 51` → 2-way impl consult on phase_8. **Codex REQUEST_CHANGES** (3 items),
all addressed + committed:
1. `bake-and-deploy.sh` interpolated an unvalidated `RUN_ID` into `rm -rf` → added
   `[[ RUN_ID =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]` guard before any deletion.
2. Script left `public/data-raw/` behind → conflicts with deploy.test's "no dist/data-raw"
   guard → added `trap 'rm -rf "$OUT"' EXIT` so the baked dir is always cleaned.
3. Doc drift: README said ResultsRegion "inert" (now: live drill-in, loadResults deprecated);
   lessons-learned said baked `.json` (now: both tiers ship `.gz`, one sniff path).
Green: check-types + deploy.test (6/6). **Claude iter-1 verdict still generating** — waiting
on the background consult; will re-consult (iter2) against the now-fixed committed state.

### 2026-08-06 — phase_8 iter-1 verdicts + iter-2 fixes
Both iter-1 verdicts in: **Codex REQUEST_CHANGES** (3 items, all fixed in iter-1 commit),
**Claude COMMENT** (verified bake→build→serve end-to-end; non-blocking but 4 real findings).
Folded Claude's findings (iter-2 commit):
1. `serve -s dist` answers a MISSING baked file with 200+index.html (SPA history fallback),
   so BakedRawSource's 404 check never fired in prod → misleading "baked unreadable" notice
   on every load until first bake. Now treat text/html as absent (catalog+shard) + tests.
2. `.railwayignore` mirrors `.gitignore` (add .vite/coverage/*.local) — `--no-gitignore`
   un-excludes everything else, so a stale cache/secret could ride along.
3. deploy-test guard now names the remediation; bake script asserts repo-root CWD.
4. Plan asked the deploy/gunzip/fingerprint/genericity lessons for the HOT tier; hot is at
   cap 10, so folded the Railway-`.gitignore` + serve-s traps into the SPA-data-layer hot
   entry (no net slot) — the rest stay in cold lessons-learned. Recording in the review.
Full suite green: check-types + vitest 219/219. Launching `porch done 51` (iter-2 consult).

### 2026-08-06 — phase_8 iter-2 consult
Learned the porch loop the hard way: `porch done`↔`porch next` is the build↔review handshake,
but the 2-way consult is a SEPARATE manual `consult` CLI step (writes the convention-named
`51-phase_8-iterN-{model}.txt`; porch parses the verdict into status.yaml). Wrote iter-2
context (iter-1 reviews + rebuttal) and ran the consults:
- **Codex: APPROVE** (was REQUEST_CHANGES) — deploy wiring + cleanup + ignore rules + docs
  all align, prior findings addressed.
- **Claude:** running in background (bz1pcnojo). Will record verdicts via porch on completion,
  then advance to Review phase (R) if both non-REQUEST_CHANGES.
