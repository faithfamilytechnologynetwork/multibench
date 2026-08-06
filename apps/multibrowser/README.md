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

- **Dense leaderboard** (jaleesbrowser-style, Spec 55) — one row per subject, the whole picture at a
  glance. Cross-tradition standings = the **mean of per-tradition means**, ranked on the full-grid
  **Gemini** judge; reconciles with the paper's standings to displayed precision.
  - **Headline columns** — **First-response / Post-pressure / Δ (steadfastness)** on the paper's
    published slice (the first framing, i.e. unstated); Δ is the matched-cell steadfastness read from
    the shard, **not** post − initial.
  - **Framing columns** — one post-pressure column per framing (unstated/stated/guided); the
    Post-pressure headline equals the first-framing column by definition.
  - **Per-tradition heat strip** — a `scoreColor` square per tradition (manifest order) in each row;
    its non-null mean *is* the Post-pressure column. Color is never the only encoding — each square
    carries an accessible label with the tradition and its value (or "no data" for an uncovered one).
  - **Sortable** by any numeric column (ascending/descending); a **canonical rank** column persists
    while sorted (it never re-numbers). Nulls sort last.
- **Pressure selector** (deep-linkable) — reframes the **whole table** (headline, framing columns,
  strip, and rank) to one of the six pressures or the pooled `"all"` (the default).
- **Drill-down** — click a subject (or deep-link `?expanded=`) for a **dense per-tradition table**
  (First/Post/Δ + framings + coverage `n/N`, `—/N` where the post numerator is absent).
- **Judge selector** — points the **drill-down** at **Opus** (the validation judge) where Opus data
  exists, badged `sample n/N`. It **never re-ranks or recolors** the board; ranking/strip stay Gemini.
- **Deep-linkable state** — run, pressure, judge, **column sort**, and **expanded subjects** all live
  in the URL; the bare `/results` link carries no default params.
- Display-first: a malformed/missing manifest or shard, unknown vocab, or a dropped tradition
  renders an inline notice — never a blank page.

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
  setup; corpus filters and results selection live in the URL as flat params
  (`?pillars=a&pillars=b`, `?pressure=flattery&sort=post.desc&expanded=claude-sonnet-5`).

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

`railway.json` pins this. The data stays live from GitHub at runtime, so this is **not** a
data-baking static build — new traditions appear without redeploying.

## Layout

```
src/lib/      constants, model, parse (tolerant parsers), github (fetch boundary),
              queries (TanStack Query), filtering (pure filter/sort), results (inert #8 seam),
              resultsModel (results manifest/shard parsers), resultsSelection (explorer deep-link
              model), leaderboard (mean-of-means standings), scoreColor (diverging palette)
src/routes/   RootLayout, IndexPage, TraditionPage, ScenarioPage, ResultsPage, NotFound (+ tests)
src/components/  Markdown, Notice, ErrorBoundary, RateLimitBanner, TraditionCard, FilterBar,
                 ScenarioList/Row, ScenarioHeader, PressureSection, FramingsPanel,
                 ResultsRegion, Collapsible, Loading
```
