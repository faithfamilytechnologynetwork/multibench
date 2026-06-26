# multibrowser

A **pure client-side web app** for browsing and exploring **MultiBench traditions** and their
scenarios — the tradition index, each tradition's manifest / prose / taxonomies, and per-scenario
the turn-1 opening, the six pressure pushes, and the judge-guidance — with filter/slice by
taxonomy tag, `identity_signal`, and source locus.

It is read-only and **reads the corpus live from GitHub at runtime** (not from a local copy and
not from a pre-baked bundle), so **new or edited traditions on `main` appear without a redeploy**.

## Architecture (in one breath)

- **Stack:** Vite 6 + React 19 + TypeScript + Tailwind 4 + HeroUI + **TanStack Router**
  (routing / deep links) + **TanStack Query** (fetch / cache). Standalone app — it does not depend
  on any workspace packages.
- **GitHub is the data layer, fetched in the browser.** A single client (`src/lib/github.ts`)
  resolves the latest `main` commit SHA, lists `traditions/**` via the **git-trees API** (one call),
  and fetches file content from **`raw.githubusercontent.com`** pinned to that SHA (an immutable,
  internally-consistent snapshot). All of this flows through TanStack Query (`src/lib/queries.ts`),
  keyed by SHA.
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
- **Results-ready seam (#8).** v1 builds **no** results UI, but the scenario type carries an
  optional `results` field, a single `loadResults()` boundary (returns `none` in v1), and a
  reserved `ResultsRegion` — so the judging workflow (**#8**) slots in additively later
  (`src/lib/results.ts`).
- **Routing** is code-based TanStack Router (`src/router.tsx`) for a no-codegen, fully testable
  setup; filters live in the URL as flat repeated params (`?pillars=a&pillars=b`).

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
              queries (TanStack Query), filtering (pure filter/sort), results (inert #8 seam)
src/routes/   RootLayout, IndexPage, TraditionPage, ScenarioPage, NotFound (+ tests)
src/components/  Markdown, Notice, ErrorBoundary, RateLimitBanner, TraditionCard, FilterBar,
                 ScenarioList/Row, ScenarioHeader, PressureSection, FramingsPanel,
                 ResultsRegion, Collapsible, Loading
```
