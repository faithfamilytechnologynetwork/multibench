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
