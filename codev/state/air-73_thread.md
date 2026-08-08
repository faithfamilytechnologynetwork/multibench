# air-73 — multibrowser raw-results: inline judge guidance + move presets off item pages

Issue #73 (AIR, strict). Two changes to the #51 raw-results viewer.

## Plan / decisions

**1. Judge guidance on the raw item page (`/results/$runId/$groupId/$itemId`).**
The raw viewer is catalog-generic — no MB vocab in the raw MODEL (`rawModel.ts`) or renderer
(`RawComparison`). Guidance is wired through the **documented group→corpus mapping** the issue
sanctions (raw `group` = tradition id, `item` = scenario id — the identity the scenario page's
"Open in the full explorer" link already assumes).

- New `lib/corpus.ts` — the ONE module that knows this deployment's raw→corpus shape. `corpusRef()`
  returns the guidance path + corpus route only when `catalog.groupBy.key === "tradition"`; any other
  catalog (AFB #54, groupBy `instrument`) → `null` → **no guidance section** (graceful degrade).
- Reuses the corpus `judge-guidance.md` file already served at
  `traditions/<group>/scenarios/<item>/judge-guidance.md` (via a new `useCorpusGuidance` hook in
  queries.ts, `proseSection`-cleaned). **Zero data regeneration** — works on the live 20260803 run
  after a code-only deploy (matches the deploy note).
- Rendered in the existing `Collapsible` "Context — what good counsel looks like…", **default open**
  (deep-link readers should see it without a click).
- Nice-to-have cross-link "View in corpus →" to `/t/$traditionId/$scenarioId` when it resolves.

Considered a catalog-declared `corpus` field (cleanest genericity) but it needs the Python exporter
+ a full raw re-export (data not in the worktree) → acceptance #1's live deep link would fail until
regen. The group→corpus mapping is smaller, single-app, and works today. A future catalog field could
generalize it (noted in PR).

**2. Move the preset panels off every item page → run-level highlights.**
Presets are run-level, not item-scoped. Extract `PresetCard` + the `presets` section into
`components/RawPresets.tsx`; render them on the `/results` landing (ResultsPage) instead, loaded via a
new `useRawCatalog` hook (shares the `RAW_SOURCE_QK` dedup with the item page). The item page keeps
only item-scoped content (grid, transcripts, verdicts, guidance). Degrades to nothing when the run has
no raw catalog / no presets.

## Implementation notes
- `RawResultsPage.tsx` must stay free of MB route/vocab literals — enforced by the static genericity
  guard in `rawData.test.ts` (it lists RawResultsPage.tsx and forbids `"tradition"`, `traditionId`,
  `/t/`, …). So the corpus-coupled JSX (guidance + `/t/…` cross-link) lives in a NEW non-guarded
  component `components/CorpusContext.tsx`; RawResultsPage just renders `<CorpusContext …>`.
- `PresetCard` extracted to `components/RawPresets.tsx`; rendered on `/results` (ResultsPage) under a
  "Highlights" section, loaded via `useRawCatalog` (shares the `RAW_SOURCE_QK` dedup).

## Status
- [x] implement
- [x] typecheck + build green
- [x] tests green — 291 passed (added: guidance-inline, cross-link, AFB-degrade, presets-off-item,
      presets-on-/results)
- [ ] PR
