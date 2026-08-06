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
