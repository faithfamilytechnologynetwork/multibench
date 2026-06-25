# Plan: multibrowser — browse & explore MultiBench traditions (frontend SPA)

## Metadata
- **ID**: plan-2026-06-25-multibrowser-spa
- **Status**: implemented & reviewed (PR #13, 2026-06-25)
- **Specification**: [codev/specs/7-jaleesbrowser-browse-explore-m.md](../specs/7-jaleesbrowser-browse-explore-m.md) (v2, frontend SPA)
- **Created**: 2026-06-25
- **Supersedes**: the Approach-A (Python static-site) plan and the implied Flask plan — both rejected.

## Executive Summary

Implements the **v2 spec**: a **pure client-side React SPA** at `apps/multibrowser/`, mirroring
`cluesmith/shannon/apps/web`'s stack, that reads the tradition corpus **from GitHub at runtime in
the browser** (via TanStack Query) and deploys on **Railway as a static site**. No Python, no
server, no tradition data in the bundle.

The build splits into an **offline core** (types + tolerant parsers — pure functions, fully
unit-testable with no network) → a **data layer** (the GitHub fetch boundary + TanStack Query
hooks, tested with a mocked `fetch`) → **UI** (routing, index, tradition list + filtering,
scenario detail). Every phase is verified with **vitest** offline (the GitHub client is mocked —
the suite never hits the network).

### Real data to build/test against (verified 2026-06-25)

`main` has **5 traditions, all `validate-all --strict` clean**, with **diverse, manifest-declared
taxonomy axes** — the no-hardcoded-axes design must handle all of them:

| tradition | id pattern | scenarios | taxonomy axes (count) |
|---|---|---|---|
| sunni-islam | `^JLS-\d{3}$` | 140 | pillars, hearts (2) |
| eastern-christianity | `^BZ-\d{3}$` | 106 | passions, virtues, economia, register (4) |
| judaism | `^MSR-\d{3}$` | 40 | middot, virtues, middle_path, domain, register (5) |
| buddhism | `^BUD-\d{3}$` | 40 | defilements, cultivations, path_factor, middle_way, register (5) |
| taoism | `^TAO-\d{3}$` | 40 | departures, te, pivot, register (4) |

Axis **names, counts (2–5), and value sets differ per tradition**; `register`/`virtues` recur with
*different* values. Fixtures mirror these shapes; the filter UI builds axis controls **purely from
the manifest**. (Also verified: `api.github.com` sends `access-control-allow-origin: *` and
CORS-exposes `X-RateLimit-Remaining`/`Reset`; unauth limit 60/hr.)

### Plan-level decisions (resolving the spec's deferred questions)

- **Package manager: pnpm** (matches shannon); **standalone** app — concrete pinned versions, **no
  `@shannon/*` deps**, and only the **core web stack** (exclude shannon's Tauri/Sentry/oRPC/auth).
- **Routing: TanStack Router file-based** via `@tanstack/router-plugin` (mirrors shannon).
- **YAML in browser: `js-yaml`** (pinned) for `tradition.yaml`/`scenario.yaml`.
- **Markdown: `react-markdown` + `rehype-sanitize`** (no `rehype-raw` → no raw HTML), styled with
  `@tailwindcss/typography` (`prose`).
- **Cache/freshness (I1):** `useLatestSha` uses **`refetchInterval` default 300000 ms**
  (`VITE_SHA_POLL_MS`) + `refetchOnWindowFocus`/`refetchOnReconnect`, `refetchIntervalInBackground:
  false`; SHA-pinned tree/content queries `staleTime: Infinity`, long `gcTime`. `persistQueryClient`
  = COULD, not v1.
- **Cold-load concurrency:** fire all `scenario.yaml` `raw` fetches through TanStack Query
  (off-budget; browser-throttled per-host), **progressively hydrate** rows with HeroUI skeletons +
  a "loaded N/total" indicator. No extra concurrency lib in v1.
- **Deploy (I3): `vite preview --host 0.0.0.0 --port $PORT`** on Railway (SPA history fallback).
- **Tests:** `vitest` + `@testing-library/react` + `jsdom`; the GitHub client is injected/mocked so
  the suite is fully offline.

### Key dependencies (concrete pins, mirroring shannon's versions)

`react@^19`, `react-dom@^19`, `vite@^6`, `typescript@^5`, `@vitejs/plugin-react@^4`,
`@tailwindcss/vite@^4`, `tailwindcss@^4`, `@tailwindcss/typography@^0.5`, `tailwind-merge@^3`,
`@heroui/react@^3`, `@heroui/styles@^3`, `@tanstack/react-router@^1.141`,
`@tanstack/router-plugin@^1.141`, `@tanstack/react-query@^5`, `react-markdown@^10`,
`rehype-sanitize@^6`, `lucide-react@^0.546`, `zod@^3`, `zustand@^5`, `js-yaml@^4`; dev:
`vitest@^3`, `@testing-library/react@^16`, `jsdom`, `@types/*`.

## Success Metrics
- [ ] All spec §9 acceptance criteria met (browse index→tradition→scenario; filter/slice; six-
      pressure layout; judge-guidance + turn-1; deep links + SPA fallback).
- [ ] **No tradition data baked** into the bundle; corpus fetched **client-side** from GitHub.
- [ ] **No-hardcoded-axes**: the filter UI works across all 5 real traditions' axis shapes (2–5 axes).
- [ ] **Freshness**: a new commit's content appears on an open page within the SHA `refetchInterval`
      (or focus/reconnect) — no redeploy.
- [ ] **Resilience**: 403/outage → banner + last cached data; error boundary prevents blank crashes;
      no token in the bundle.
- [ ] **Display-first**: every §5.5 degradation row renders an inline notice, never crashes.
- [ ] Tests pass offline: `pnpm test` (`vitest run`) in `apps/multibrowser`; types clean (`tsc --noEmit`).
- [ ] README documents dev/test/build, `VITE_*` config, and Railway deploy.

## Phases (Machine Readable)

```json
{
  "phases": [
    {"id": "phase_1", "title": "Scaffold (Vite/React/TS standalone) + constants + types + tolerant parsers (offline core)"},
    {"id": "phase_2", "title": "GitHub client + TanStack Query data layer (caching, freshness, rate-limit) — mocked-fetch tests"},
    {"id": "phase_3", "title": "App shell: providers, TanStack Router, tradition index, shared UI primitives (Markdown/Notice/ErrorBoundary/RateLimitBanner/Skeleton)"},
    {"id": "phase_4", "title": "Tradition page: manifest-driven scenario list + filtering.ts (zod search params) + progressive hydration"},
    {"id": "phase_5", "title": "Scenario detail: turn-1, six pressures, judge-guidance, framings + inert results-ready seam"},
    {"id": "phase_6", "title": "Railway static deploy config + README + polish; flag the porch JS test-check override"}
  ]
}
```

## Target app layout (standalone; built across phases)

```
apps/multibrowser/
  package.json  pnpm-lock.yaml  tsconfig.json  tsconfig.node.json
  vite.config.ts            # plugin-react, @tailwindcss/vite, router-plugin, vitest config (P1/P3)
  index.html  .env.example  README.md
  src/
    main.tsx                # mount: HeroUIProvider + QueryClientProvider + RouterProvider + ErrorBoundary (P3)
    styles.css              # tailwind + heroui (P1/P3)
    lib/
      constants.ts          # PRESSURES, FRAMINGS, IDENTITY_SIGNALS, STATED_TEMPLATE, file names, normalizeHeading (P1)
      model.ts              # types: Notice, TaxonomyAxis, Manifest, Tradition(+prose), Scenario(+results?), ScenarioResults (P1)
      parse.ts              # tolerant parsers → model + notices (P1)
      github.ts             # the ONE GitHub fetch boundary: latestSha/tree/raw, zod-validate, 403/error + rate headers (P2)
      queries.ts            # TanStack Query hooks: useLatestSha/useTree/useRawFile + derived useTraditions/useTradition/useScenario (P2)
      filtering.ts          # pure filter/sort + zod search-param schema (P4)
      results.ts            # inert results-ready seam: loadResults() -> none (P5)
    routes/                 # file-based (router-plugin): __root, index, t.$traditionId, t.$traditionId.$scenarioId, notFound (P3-5)
    components/             # TraditionCard, TraditionHeader, TaxonomyAxes, ScenarioList, ScenarioRow, FilterBar,
                            #   ScenarioDetail, PressureSection, JudgeGuidance, FramingsPanel, ResultsRegion,
                            #   Markdown, Notice, ErrorBoundary, RateLimitBanner, Skeleton (P3-5)
    test/                   # fixtures (5-axis-shaped traditions, good + malformed + Arabic), test utils (QueryClient wrapper, fake GitHub) 
    **/*.test.ts(x)         # colocated vitest tests
```

## Phase Breakdown

### Phase 1: Scaffold + constants + types + tolerant parsers (offline core)
**Dependencies**: None

#### Objectives
- Stand up the standalone Vite/React/TS app (builds + vitest runs) and the **offline parsing core**:
  format constants, the typed model, and **tolerant parsers** that turn raw file strings into the
  model with **inline notices** — pure functions, no network, no UI.

#### Deliverables
- [ ] `package.json` (standalone, pinned deps above; scripts `dev`/`build`/`serve`/`test`/`check-types`),
      `tsconfig*.json`, `vite.config.ts` (react + tailwind + vitest jsdom), `index.html`,
      `src/styles.css`, a minimal `src/main.tsx` rendering a placeholder (so `vite build` works).
- [ ] `src/lib/constants.ts`: `PRESSURES` (6, canonical order), `FRAMINGS`, `IDENTITY_SIGNALS`,
      `STATED_TEMPLATE`, file/dir names (`scenarios`, `index.json`, `scenario.yaml`, `turn1.md`,
      `judge-guidance.md`, `pressures.md`, `tradition.yaml`, `scenario_id_pattern`),
      `normalizeHeading` (trim→lower→spaces/hyphens→`_`).
- [ ] `src/lib/model.ts`: `Notice`, `TaxonomyAxis`, `Manifest`, `Tradition` (manifest + prose
      {readme,source,guide} + scenarios + notices), `Scenario` (id, tags, source_locus, locus_label,
      identity_signal, turn1, judgeGuidance, pressures{canonical→text|null}, notices, **`results?:
      ScenarioResults` — absent in v1**), forward-declared `ScenarioResults`.
- [ ] `src/lib/parse.ts`: `parseManifest` (tolerant — unknown keys → notice not throw; axes read
      generically), `parseIndex`, `parseScenarioMeta`, `parsePressures` (6 canonical via
      `normalizeHeading`; missing/extra → notice), `proseOrNotice`. **No hardcoded axis names.**
- [ ] `src/test/fixtures/`: small traditions mirroring the **5 real axis shapes** (2–5 axes) + a
      good one with **Arabic** content + malformed variants (bad manifest, missing prose, missing/
      extra pressure, unknown tag, index/folder drift inputs); `src/lib/parse.test.ts`.

#### Implementation Details
- Mirror shannon's TS/Vite conventions (strict TS, `@vitejs/plugin-react`, `@tailwindcss/vite`).
- Parsers are pure (input: file strings/objects → output: model fragment + notices); the
  drift/union logic operates on `(indexList, folderList)` so it's testable without GitHub.

#### Acceptance Criteria
- [ ] `pnpm build` (vite build) and `pnpm check-types` succeed; `pnpm test` runs.
- [ ] Good fixtures parse with **zero** notices; each malformed fixture yields exactly its expected
      notice(s) and never throws; pressures normalize across heading variants; axes come from the
      manifest (a 5-axis fixture parses all 5).
- [ ] All Phase-1 tests pass.

#### Test Plan
- **Unit (vitest)**: each parser; pressures normalization; manifest tolerance; index/folder drift
  (union/orphan/ghost) at the data level; Arabic round-trip.
- **Manual**: none (no UI yet).

#### Rollback / Risks
Revert the phase commit. **Risk**: Tailwind 4 / vite config drift → mitigate by mirroring shannon's
`vite.config.ts`.

---

### Phase 2: GitHub client + TanStack Query data layer
**Dependencies**: Phase 1

#### Objectives
- The **single GitHub fetch boundary** + the TanStack Query hooks implementing SHA-pinned caching,
  the `refetchInterval` freshness model, and rate-limit/error handling — all tested with a **mocked
  `fetch`** (offline).

#### Deliverables
- [ ] `src/lib/github.ts`: `latestSha(repo,ref)` (`/commits/{ref}`), `tree(repo,sha)` (recursive
      git-trees; **on `truncated:true`, fall back to per-directory listing** to still enumerate
      `traditions/*/…` — §6 N-trunc), `raw(repo,sha,path)` (`raw.githubusercontent.com`).
      `zod`-validate responses; detect `403` + read `X-RateLimit-Remaining`/`Reset`; bounded
      timeouts; **takes an injectable `fetch`** for tests. **No token.**
- [ ] `src/lib/queries.ts`: `useLatestSha` (`refetchInterval` `VITE_SHA_POLL_MS`≈5min +
      focus/reconnect, not in background), `useTree(sha)` (`staleTime: Infinity`), `useRawFile(sha,
      path)` (`staleTime: Infinity`); derived `useTraditions()` (tree + each `tradition.yaml`),
      `useTradition(id)` (manifest + prose + each `scenario.yaml`, progressive; **when `index.json`
      is missing/invalid, derive the scenario set from the tree's `scenarios/*/` folders + a notice**,
      via the P1 drift/union logic), `useScenario(tid,sid)` (its 4 files). All keyed by SHA.
- [ ] Tests (`github.test.ts`, `queries.test.ts`) with mocked `fetch` + a `QueryClientProvider`
      wrapper: sha→tree→raw flow; SHA-keyed caching; **freshness** (SHA change → new snapshot fetch);
      **rate-limit** (403 → rate-limit state surfaced); **error/timeout** → fallback; `raw` URL shape;
      **`truncated:true` → per-directory fallback enumerates the full set**; **`index.json`
      missing/invalid → scenario set derived from tree folders (with notice)**.

#### Acceptance Criteria
- [ ] With mocked GitHub, `useTraditions`/`useTradition`/`useScenario` resolve to the correct model;
      a changed SHA triggers a refetch keyed by the new SHA; a 403 surfaces a rate-limit state with
      the reset time; network error degrades (no throw to the UI).
- [ ] `truncated:true` falls back to per-directory listing (full set enumerated); a missing/invalid
      `index.json` derives the scenario set from the tree's folders with a notice.
- [ ] Suite makes **no real network calls**. All Phase-2 tests pass.

#### Test Plan
- **Unit/integration (vitest, mocked fetch)**: client methods; query hooks via `renderHook` +
  QueryClient; cache key behavior; 403/error paths.

#### Rollback / Risks
Revert the phase commit; P1 intact. **Risk**: TanStack Query test ergonomics → use a fresh
`QueryClient` per test with retries off.

---

### Phase 3: App shell + routing + tradition index + UI primitives
**Dependencies**: Phase 2

#### Objectives
- Wire the providers and **TanStack Router** (file-based), build the **tradition index** page, and
  the shared **UI primitives** (sanitized Markdown, Notice, ErrorBoundary, RateLimitBanner, Skeleton).

#### Deliverables
- [ ] `src/main.tsx`: `HeroUIProvider` + `QueryClientProvider` + `RouterProvider`, wrapped in a
      top-level **ErrorBoundary** (render errors → notice, never blank).
- [ ] `vite.config.ts`: add `@tanstack/router-plugin`; `src/routes/__root.tsx` (layout + banner slot
      + `<Outlet/>`), `src/routes/index.tsx` (`/` → `useTraditions` → `TraditionCard` grid),
      `notFound`.
- [ ] `src/components/`: `Markdown` (`react-markdown` + `rehype-sanitize`, `prose`), `Notice`,
      `ErrorBoundary`, `RateLimitBanner` (shows reset time from §2's exposed headers), `Skeleton`,
      `TraditionCard`. HeroUI + Tailwind theme set up in `styles.css`.
- [ ] Tests: `Markdown` sanitization (a `<script>`/`onclick` fixture renders inert) + Arabic
      survives; index route renders cards from a mocked `useTraditions`; rate-limit banner shows on
      the rate-limit state; ErrorBoundary catches a thrown child.

#### Acceptance Criteria
- [ ] `/` lists the (mocked) traditions as cards with metadata + links; a rate-limit state shows the
      banner while keeping cached data; a thrown render error shows the boundary notice, not a blank
      page; markdown is sanitized and Unicode-correct.
- [ ] All Phase-3 tests pass; `tsc --noEmit` clean.

#### Test Plan
- **Component/route (testing-library)** with mocked queries; **unit** for Markdown sanitization.
- **Manual**: `pnpm dev`, eyeball `/` against the real GitHub data (real-user path).

#### Rollback / Risks
Revert the phase commit; data layer intact. **Risk**: HeroUI v3 + Tailwind 4 setup → mirror shannon's
provider/styles wiring.

---

### Phase 4: Tradition page — scenario list, filtering, progressive hydration
**Dependencies**: Phase 3

#### Objectives
- `/t/$traditionId`: manifest header, prose, **manifest-driven** taxonomy axes + **FilterBar**, the
  scenario list with **filtering/sorting** (pure `filtering.ts`, zod search params) and **progressive
  hydration**.

#### Deliverables
- [ ] `src/lib/filtering.ts`: `searchSchema` (zod; repeated-param arrays per axis + identity_signal,
      `locusMin`/`locusMax` inclusive/one-sided, `q`, `sort`), `applyFilters(scenarios, selection)`
      (**OR-within-axis, AND-across-axes**, identity, locus range, free-text; **incomplete rows**
      excluded by any positive filter, present unfiltered; `source_locus`-missing sorts last),
      `sortScenarios`. **No hardcoded axes** — operates over whatever axes the manifest declares.
- [ ] `src/routes/t.$traditionId.tsx` (`validateSearch: searchSchema`; **an unknown `traditionId`
      not in the discovered set → in-SPA 404**), `src/components/`:
      `TraditionHeader`, `TaxonomyAxes` (renders each manifest axis + values), `FilterBar` (controls
      generated **from the manifest axes** — handles 2–5 axes), `ScenarioList`/`ScenarioRow`
      (progressive: skeleton rows until each `scenario.yaml` resolves; "loaded N/total"), result counts.
- [ ] Tests: `filtering.test.ts` (**exhaustive**, run across **multiple real axis shapes** incl. the
      5-axis judaism/buddhism and 2-axis sunni-islam — OR/AND, identity, locus edges, free-text, sort,
      ghost/stub rows); route test: filters update the URL search params and the rendered list+counts;
      FilterBar builds controls from a 5-axis manifest; **an unknown `traditionId` → in-SPA 404**.

#### Acceptance Criteria
- [ ] The tradition page renders the manifest, prose, axes, and the scenario list; the **FilterBar is
      generated from the manifest** and works for a 2-axis and a 5-axis tradition; filtering
      (OR-within/AND-across/identity/locus/search) + sort update **deep-linkable search params** with
      live counts; rows hydrate progressively with skeletons.
- [ ] All Phase-4 tests pass.

#### Test Plan
- **Unit (vitest)**: `filtering.ts` exhaustively over real axis shapes + incomplete rows.
- **Component/route**: filter interactions ⇄ URL ⇄ rendered list; progressive hydration states.
- **Manual**: `pnpm dev`, filter a real 5-axis tradition.

#### Rollback / Risks
Revert the phase commit; P1–P3 intact. **Risk**: search-param ⇄ UI sync bugs → keep `filtering.ts`
pure and the URL the single source of truth; test the pure layer hard.

---

### Phase 5: Scenario detail + inert results-ready seam
**Dependencies**: Phase 4

#### Objectives
- `/t/$traditionId/$scenarioId`: lay out turn-1, the six pressures (canonical order), judge-guidance,
  the framings context, and the **reserved (inert) results region**; prev/next; display-first notices.

#### Deliverables
- [ ] `src/lib/results.ts`: `loadResults(scenario)` → **none** (v1) — the single seam #8 will feed.
- [ ] `src/routes/t.$traditionId.$scenarioId.tsx` (**an unknown `scenarioId` not in the tradition's
      discovered scenario set → in-SPA 404**), `src/components/`: `ScenarioHeader` (id, locus,
      identity_signal, tag chips), `PressureSection` (6 in canonical order; missing → notice),
      `JudgeGuidance` (HeroUI accordion, collapsible), `FramingsPanel` (Stated instantiated with
      `adherent_noun`; Guided→guide.md; Unstated note; six-pressure glosses), `ResultsRegion`
      (renders nothing / "no judgement results yet" when results absent), `Markdown` for prose;
      prev/next in declared order.
- [ ] Tests: scenario detail renders all parts in order for a good fixture; a malformed scenario
      (missing pressure / empty section / unknown tag) shows inline notices, not a crash; the
      results region is **empty/inert**; framings show the instantiated Stated template; **an unknown
      `scenarioId` → in-SPA 404**.

#### Acceptance Criteria
- [ ] A scenario page shows turn-1, the six pressures (canonical order), judge-guidance, framings, and
      metadata; malformed content → inline notices; **results region renders empty (no scores/bands/
      verdicts markup in v1)**; prev/next navigate in declared order.
- [ ] All Phase-5 tests pass.

#### Test Plan
- **Component/route (testing-library)** over good + malformed fixtures; assert six-pressure order,
  notice rendering, inert results region, framings instantiation.
- **Manual**: `pnpm dev`, open a real scenario (incl. one with Arabic judge-guidance).

#### Rollback / Risks
Revert the phase commit; P1–P4 intact.

---

### Phase 6: Railway deploy + README + polish
**Dependencies**: Phase 5

#### Objectives
- Make it **deployable on Railway as a static site**, document everything, and polish; flag the porch
  JS test-check.

#### Deliverables
- [ ] Deploy: `package.json` `serve` = `vite preview --host 0.0.0.0 --port $PORT`; a `railway.json`/
      `Procfile` (build = `pnpm build`, start = `serve`); **`vite.config.ts` `base: '/'`** (the Vite
      default — **absolute** asset URLs so nested routes like `/t/sunni-islam/JLS-001` resolve
      `/assets/…` correctly; a relative `base: './'` would break deep-link asset loading on a
      root-served SPA, so it is explicitly **not** used); confirm SPA history fallback;
      `.env.example` (`VITE_MULTIBENCH_REPO`, `VITE_MULTIBENCH_REF`, `VITE_SHA_POLL_MS`).
- [ ] `README.md`: dev (`pnpm dev`), test (`pnpm test`), `check-types`, build, env config, **Railway
      deploy**, the GitHub-data-layer + freshness + rate-limit notes, and the **#8 results-ready seam**.
- [ ] Polish: empty/loading/error states; light/dark = COULD; final a11y pass on HeroUI components.
- [ ] **porch JS check note:** `.codev/config.json` `porch.checks.tests` is Python `pytest`;
      multibrowser is vitest. At this point I will **ping the architect** to set a JS-appropriate
      override (e.g. `pnpm --dir apps/multibrowser test` / `vitest run`) so `porch done` verifies this
      app. (Per architect: the override is an implement-time step.)
- [ ] Tests: a build smoke (the bundle has no tradition data); a deep-link/route smoke (SPA fallback
      path resolves); README commands accurate.

#### Acceptance Criteria
- [ ] `pnpm build` produces `dist/` with **no tradition data**; `vite preview` serves it with **deep
      links working** (SPA fallback); README is accurate and copy-pasteable; full suite green; types clean.
- [ ] All Phase-6 tests pass. (Actual Railway deploy + real-data run happen in **Verify**.)

#### Test Plan
- **Unit/build**: bundle-has-no-data scan; route/deep-link smoke.
- **Manual**: `pnpm build && pnpm serve`, open a deep link; (Railway deploy in Verify).

#### Rollback / Risks
Revert the phase commit; `build` (P1–P5) remains the runnable core. **Risk**: porch JS check blocks
`porch done` → mitigated by the architect-coordinated override (above).

## Dependency Map
```
P1 (offline core) → P2 (data layer) → P3 (shell+index) → P4 (tradition+filter) → P5 (scenario+seam) → P6 (deploy+README)
```
Strictly linear; each phase independently committable + vitest-testable. **Phases ship as git commits
within a single PR** (per the issue's PR strategy); the PR opens during/after P6.

## Risk Analysis
| Risk | P | I | Mitigation |
|---|---|---|---|
| Client-side rate limit (60/hr unauth, NAT-shared, no token) | M | M | SHA-pinned snapshot (tree ~1/snapshot); content via off-budget `raw`; conservative `refetchInterval` (~5min) + focus/reconnect; keep-cached + banner on 403 (reset time from CORS-exposed headers); proxy = future-only |
| No-hardcoded-axes must handle 5 diverse traditions (2–5 axes) | M | M | FilterBar/TaxonomyAxes built purely from the manifest; `filtering.ts` axis-agnostic; tests run over multiple real axis shapes |
| porch tests-check is Python `pytest` (blocks `porch done`) | H | M | Anticipated; architect-coordinated `.codev/config.json` vitest override at implement (P6) — ping then |
| HeroUI v3 + Tailwind 4 setup friction | M | L | Mirror shannon/apps/web's provider + vite + styles wiring |
| Tradition cold-load = 100–140 raw fetches | M | L | Off-budget `raw`; browser-throttled; progressive hydration + skeletons; cached per SHA |
| Markdown safety | L | M | `react-markdown` w/o raw HTML + `rehype-sanitize`; tested inert |
| Branch behind `main` (5 traditions added) | L | L | App reads GitHub at runtime (local data unused by the app); **rebase onto `main` before implement / in Verify** |

## Validation Checkpoints
1. **After P2**: data layer resolves the model from mocked GitHub; freshness + 403 + error paths green.
2. **After P4**: filtering works over a 2-axis and a 5-axis real tradition; deep-linkable; progressive.
3. **Before "done" (P6)**: real-user path — `pnpm dev`/`pnpm build && pnpm serve` against the live 5
   traditions on GitHub; deep links + SPA fallback; results seam inert; full suite + types green.
4. **Verify (post-merge)**: deploy on Railway; confirm the live site lists all 5 traditions from GitHub,
   freshness (edit on `main` appears without redeploy), and rate-limit resilience.

## Documentation Updates Required
- [ ] `apps/multibrowser/README.md` (P6).
- [ ] Consider a pointer from `traditions/README.md` / repo root to the hosted browser (Review, if warranted).
- [ ] Arch/lessons hot-tier via `update-arch-docs` (Review) if a durable fact emerges (e.g. "multibrowser
      reads the corpus client-side from GitHub; it's the team's standard SPA stack").

## Notes
- **Three prior architectures** (Python SSG, Flask, this SPA) — this plan is the SPA's; the old plan
  was banner-marked SUPERSEDED and is fully replaced here.
- **#8 (judging) coordination:** v1 ships only the inert results seam (`results?` type field +
  `loadResults→none` + reserved `ResultsRegion`). Concrete `ScenarioResults` binds to #8's output —
  a follow-up coordinated **directly with the spir-8 builder** once #8's spec firms up (per architect).
- **Rebase:** the app doesn't consume local `traditions/` (it fetches GitHub at runtime), so planning
  didn't require a rebase; I'll rebase onto `main` before/at implement and in Verify.

### Implemented deviations from the spec (ARCHITECT-APPROVED, recorded for the PR CMAP)
- **Railway serve = `serve -s dist -l $PORT`** (not the spec's `vite preview`). `vite` is a
  *devDependency*, so it may be pruned/absent at runtime; `serve` is a small **runtime** dependency
  with SPA history fallback — robust for Railway. The spec listed `serve -s dist` as the sanctioned
  alternative. Verified: `serve -s dist` + a curl'd deep link returns `index.html` (fallback works).
- **Code-based TanStack Router** (not file-based/router-plugin): avoids the codegen/`routeTree.gen.ts`
  step, keeps routes explicit, fully unit-testable with a memory history; same library + deep links.
- **HeroUI v3.2.1 is PROVIDER-LESS** — there is no `HeroUIProvider` export (only
  `I18nProvider`/`ToastProvider`/`useTheme`); styling comes from `@import "@heroui/styles"`. The
  plan's "HeroUIProvider" wording was HeroUI-v2-era; the mandated reference `shannon/apps/web` (v3)
  also mounts no such provider. The wiring is correct for v3.
All three were explicitly approved by the architect ("Both flagged deviations — code-based routing;
serve -s dist — are reasonable; I'll review them at the PR integration CMAP").

## Plan Consultation

**SPA plan consult — Codex: REQUEST_CHANGES · Claude: APPROVE.** Claude APPROVE ("complete spec
coverage; verified codebase claims; sound TanStack Query architecture; clean phase decomposition").
Codex's two points — both folded in:
1. **`base: './'` would break deep-link asset loading** on a root-served SPA → changed Phase 6 to
   **`base: '/'`** (absolute asset URLs so `/t/…/…` nested routes resolve `/assets/…`), with the
   rationale noted.
2. **Spec-mandated fallbacks weren't explicitly owned/tested** → assigned each to a phase with tests:
   **`truncated:true` → per-directory fallback** (P2 github.ts + test), **`index.json` missing/invalid
   → derive scenarios from tree folders** (P2 queries + test), **unknown `traditionId`/`scenarioId` →
   in-SPA 404** (P4 / P5 routes + tests).

(Run manually: porch had carried the plan-iteration counter to its ceiling from the rejected
Approach-A plan, so it wouldn't issue a fresh consult task; this consult reviewed the current SPA
plan directly — same as the v2 spec.)

## Change Log
| Date | Change | Reason | Author |
|------|--------|--------|--------|
| 2026-06-25 | Initial SPA plan (replaces superseded Approach-A plan) | v2 frontend spec approved | builder spir-7 |
| 2026-06-25 | Plan consult folded in (Codex RC / Claude APPROVE): `base:'/'` fix; explicit phase ownership + tests for truncated / index-fallback / unknown-id-404 | Consultation feedback | builder spir-7 |
