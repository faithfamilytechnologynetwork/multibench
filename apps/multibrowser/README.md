# multibrowser

A **pure client-side web app** for browsing and exploring **MultiBench traditions** and their
scenarios — the tradition index, each tradition's manifest / prose / taxonomies, and per-scenario
the turn-1 opening, the six pressure pushes, and the judge-guidance — with filter/slice by
taxonomy tag, `identity_signal`, and source locus.

It is read-only and **reads the corpus live from GitHub at runtime** (not from a local copy and
not from a pre-baked bundle), so **new or edited traditions on `main` appear without a redeploy**.

It also hosts a **Results explorer** (`/results`) over committed judging-run datasets (see below).

## Results explorer (`/results`)

Browses `results/<run-id>/` datasets the same runtime way it reads the corpus (SHA-pinned git-trees
+ `raw`), so a newly committed run appears **without a redeploy** — the data contract and export
command live in [`results/README.md`](../../results/README.md).

- **Leaderboard** — cross-tradition standings = the **mean of per-tradition means**, ranked on the
  full-grid **Gemini** judge; reconciles with the paper's standings to displayed precision.
- **Selectors** (all deep-linkable): **framing** (unstated/stated/guided), **metric**
  (first-response / post-pressure / **steadfastness** = full − turn1), **pressure** (six + "all").
- **Judge selector** — points the **per-tradition drill-down** at **Opus** (the validation judge)
  where Opus data exists, badged `sample n/N`. It **never re-ranks** the board; Opus stated/guided
  is only a sample, so ranking always stays Gemini.
- Display-first: a malformed/missing manifest or shard, unknown vocab, or a dropped tradition
  renders an inline notice — never a blank page.

## Raw-results browser (`/results/$runId/$groupId/$itemId`, #51)

The evidence behind the scores: per-scenario **transcripts + judge verdicts**, read from the
[`results-raw/<run-id>/`](../../results-raw/README.md) tier (per-scenario gzip shards, lazy-loaded).
Reached by drilling in from `/results` → a tradition → a scenario's live **ResultsRegion** link.

- **Cell-score grid** — subjects × condition-tuples, chips colored by the **catalog-declared** ramp
  for the selected **judge + scope**; the grid *is* the navigation (click a chip → that cell).
- **A/B compare** — pin a second subject to see two transcripts + verdict sets side by side.
- **Presets** — export-computed curated deep links (Models split / Judges differed / Steadfastness
  cliff), each a shareable URL that may target another scenario.
- **Deep links** — the full view state (run, group, item, A/B, condition axes, scope, judge) lives
  in the URL. **No band names** — numeric scores + the catalog ramp only.
- **Catalog-generic** (issue #54): scale, ramp, subjects, judges, condition **axes**, grouping axis,
  and items are all catalog-declared, so a non-MultiBench catalog (e.g. the AFB 0–4 explorer) rides
  the same viewer with zero component changes. The view is also independent of the `results/` score
  tier — that's consulted only for an optional cross-tier coherence fingerprint.
- **Dual-source** (see below): served baked-first (same-origin), GitHub-committed tier as the
  authoritative fallback; fail-soft notices throughout.

## Architecture (in one breath)

- **Stack:** Vite 6 + React 19 + TypeScript + Tailwind 4 + HeroUI + **TanStack Router**
  (routing / deep links) + **TanStack Query** (fetch / cache). Standalone app — it does not depend
  on any workspace packages.
- **GitHub is the data layer, fetched in the browser.** A single client (`src/lib/github.ts`)
  resolves the latest `main` commit SHA, lists `traditions/**` **and `results/**`** via the
  **git-trees API** (one call; the truncation fallback walks both dirs), and fetches file content
  from **`raw.githubusercontent.com`** pinned to that SHA (an immutable, internally-consistent
  snapshot). All of this flows through TanStack Query (`src/lib/queries.ts`), keyed by SHA — so
  both the corpus and committed `results/<run-id>/` datasets are read the same way.
- **Freshness without redeploy.** `useLatestSha` polls the commit SHA on an interval
  (`VITE_SHA_POLL_MS`, default 5 min) plus on window focus/reconnect. When the SHA changes, the
  SHA-keyed queries automatically refetch the new snapshot — even on an already-open page.
- **No token.** A client app can't keep a secret, so requests are unauthenticated (60 req/hr per
  IP). Only the SHA poll and the one tree call are on-budget; **all file content via `raw` is off
  the API rate budget**, and a 403 shows a non-blocking banner while keeping cached data on screen.
- **Display-first.** Imperfect content (a missing prose file, a malformed manifest, a missing
  pressure, index↔folder drift) renders with an inline **notice** rather than crashing; an error
  boundary backstops any render error. Taxonomy axes are read **from each manifest** — nothing is
  hardcoded, so 2-axis and 5-axis traditions both work.
- **Results explorer (#49).** The `/results` explorer reads committed `results/<run-id>/` datasets
  at runtime (see the section above and [`../../results/README.md`](../../results/README.md)). The
  run shown defaults to the newest by `generated_at`; a specific run can be pinned with `?run=<id>`.
  The **per-scenario** `ResultsRegion` seam (optional `Scenario.results`, `loadResults()` → `none`)
  remains inert — the explorer is a separate route-level feature, not that seam.
- **Routing** is code-based TanStack Router (`src/router.tsx`) for a no-codegen, fully testable
  setup; corpus filters and results selectors live in the URL as flat params
  (`?pillars=a&pillars=b`, `?framing=stated&metric=steadfastness`).

## Develop

```bash
cd apps/multibrowser
pnpm install
pnpm dev            # http://localhost:5173
pnpm test           # vitest — fully offline (the GitHub client is mocked; no network)
pnpm check-types    # tsc --noEmit
pnpm build          # production static bundle -> dist/ (app code only; NO tradition data baked in)
pnpm preview        # serve the built bundle locally
```

## Configuration (build-time `VITE_*`)

| Var | Default | Meaning |
|---|---|---|
| `VITE_MULTIBENCH_REPO` | `faithfamilytechnologynetwork/multibench` | Repo to read `traditions/` from. |
| `VITE_MULTIBENCH_REF` | `main` | Branch/ref to read. |
| `VITE_SHA_POLL_MS` | `300000` | SHA poll interval (ms). Conservative for the unauthenticated rate limit. |

See `.env.example`. There is no runtime/server config and **no token**.

## Deploy on Railway (static site)

Point a Railway service at this directory (`apps/multibrowser`). It uses Nixpacks:

- **build:** `pnpm install` + `pnpm build` → `dist/` (app code only).
- **start:** `pnpm start` → `serve -s dist -l $PORT` — a static server with **SPA history
  fallback**, so deep links like `/t/sunni-islam/JLS-001` resolve to the app.

`railway.json` pins this. The corpus + `results/` score tier stay live from GitHub at runtime, so
new traditions/runs appear **without redeploying**.

### Baking the raw tier (#51 dual-source)

The `results-raw/` tier is served from **two public sources of identical gz content**: the
SHA-pinned **GitHub committed tier** (authoritative + fallback) and a **same-origin baked bundle**
(the fast primary — no GitHub rate limits). To refresh the baked copy:

```bash
apps/multibrowser/scripts/bake-and-deploy.sh <run-id> <run-root>...
```

This exports the gz raw tier into `public/data-raw/` (gitignored — deploy-only, never committed)
and runs `railway up --no-gitignore` (Railway honors `.gitignore` by default, so the baked dir must
be force-uploaded; `.railwayignore` re-excludes `node_modules`/`dist`). Vite copies `public/` into
`dist/`, so it's served same-origin at `/data-raw/<run-id>/`.

**Trade-off:** unlike the corpus/score tiers, the **baked** copy refreshes only on
`bake-and-deploy` — the **GitHub** copy still updates live on commit and is the fallback. **Partial
rate-limit immunity:** the baked-first fast path is chosen after a small GitHub read of the run's
coherence fingerprint, so immunity applies to the heavy per-scenario shards, not that one manifest
read.

## Layout

```
src/lib/      constants, model, parse (tolerant parsers), github (fetch boundary),
              queries (TanStack Query), filtering (pure filter/sort), results (deprecated #8 seam),
              resultsModel/resultsSelection/leaderboard/scoreColor (the #49 score explorer),
              rawModel (generic raw contract + parsers), rawSource (dual-source resolver + gunzip
              sniff), rawSelection (raw-view deep-link state), rampColor (catalog-generic ramp) [#51]
src/routes/   RootLayout, IndexPage, TraditionPage, ScenarioPage, ResultsPage,
              RawResultsPage (#51), NotFound (+ tests)
src/components/  Markdown, Notice, ErrorBoundary, RateLimitBanner, TraditionCard, FilterBar,
                 ScenarioList/Row, ScenarioHeader, PressureSection, FramingsPanel,
                 ResultsRegion (live #51 drill-in), Collapsible, Loading
scripts/      bake-and-deploy.sh (#51 raw-tier bake + deploy)
```
