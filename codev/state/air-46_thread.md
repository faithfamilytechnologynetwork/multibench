# air-46 — multibrowser: scenario categorizations as badges + facet filters

Protocol: AIR (strict). Issue #46.

## Finding (post-recon)
Spec 7 (PR #7) already shipped most of this issue:
- Badges: `ScenarioRow` shows tags per-axis + identity chip; `ScenarioHeader` shows tags grouped by family + identity/locus chips. **DONE.**
- Facet filters: `FilterBar` has clickable axis toggles, OR-within/AND-across, URL round-trip, fail-soft bogus-value degrade (`filtering.ts`). **DONE** — but facets are **manifest-driven**.

## Real gaps vs issue #46
- **#3 data-driven discovery**: facets currently come from `manifest.taxonomies`, not "the scenarios actually loaded". Need scenario-derived family/value discovery; a tradition with no tags → no tag UI.
- **#4 counts**: no per-facet-value scenario count. Missing entirely.

## Plan
1. `filtering.ts`: add `Facet`/`Facets` + `computeFacets(rows, sel, order?)`. Discovery strictly from loaded rows' metas; per-value counts use faceted convention (exclude the value's OWN family from the active filter, so multi-select OR stays meaningful). Order values by manifest order when provided, extras appended.
2. `FilterBar.tsx`: prop `taxonomies` → `facets`. Render axis + identity groups from facets; show `value (count)`; omit families/identity absent from loaded scenarios. Keep button accessible-name = value (count in aria-hidden span) so existing role-name queries still pass. Identity becomes data-driven too (consistency + counts).
3. `TraditionPage.tsx`: compute facets from `entries` + selection; pass to FilterBar. `TaxonomyAxes` reference section stays manifest-driven (documents the controlled vocab).
4. URL validation (`parseSelection`) stays manifest-vocab-based — that IS the "existing degrade-to-no-filter" behavior the issue says to preserve.
5. Tests: computeFacets units in `filtering.test.ts`; rewrite the "FilterBar is manifest-driven" test to data-driven; add no-tags→no-UI + counts assertions.

## Done (implement phase)
- `filtering.ts`: `Facet`/`Facets` + `computeFacets(rows, sel, order?)` — scenario-derived discovery, own-axis-excluded counts, manifest-order sorting.
- `FilterBar.tsx`: facet-driven (was manifest-driven); per-value counts; identity now data-driven too; button accessible-name stays = value (count in aria-hidden span).
- `TraditionPage.tsx`: computes facets from loaded entries; `TaxonomyAxes` reference section stays manifest-driven; `parseSelection` URL validation unchanged (preserves fail-soft degrade).
- Tests: +7 (90→97). tsc clean, `vite build` clean, dispatcher `pnpm -C apps/multibrowser test` green.
- Prod LOC ~124 (<300 AIR budget). Badges (#1) + basic facet plumbing (#2) were already shipped by Spec 7; this PR adds #3 (data-driven discovery) + #4 (counts).
