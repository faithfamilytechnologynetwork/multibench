# Spec 7: multibrowser — browse & explore MultiBench traditions (frontend SPA)

| | |
|---|---|
| **Issue** | #7 |
| **Protocol** | SPIR |
| **Status** | Specify — **re-spec #2 (frontend stack)** (2026-06-24); draft for 3-way review |
| **App path** | `apps/multibrowser/` |
| **Architecture** | **Pure client-side React SPA** · **GitHub fetched client-side at runtime (TanStack Query)** · **deployed on Railway as a static site** |

> **Re-spec history.** v0 = Python *static-site generator* over local files (approved+planned,
> then rejected). v1 = Python *Flask* live web app + GitHub data layer (specced, then rejected
> before approval). **This is v2** and supersedes both: the team's **standard frontend stack**,
> a **pure client-side SPA** (no Python, no server), with GitHub fetched **in the browser**. The
> corpus-browsing **goal, features, and content posture carry over**; the **stack & runtime are
> new**. See §12.

## 1. Summary

Build `apps/multibrowser/` — a **pure client-side React single-page app** for **browsing and
exploring MultiBench traditions and their scenarios**. A user opens the site and navigates a
tradition, reads each scenario (turn-1 opening, the six pressure pushes, the judge-guidance),
and **filters/slices** the scenario set by taxonomy tags, `identity_signal`, and source locus.

Three defining facts:

1. **The team's standard frontend stack**, mirroring `cluesmith/shannon/apps/web`: **Vite 6 +
   React 19 + TypeScript 5**, **Tailwind CSS 4** + **HeroUI**, **TanStack Router** (routing/deep
   links) + **TanStack Query** (fetch/cache), `react-markdown` + `rehype-sanitize`, `vitest`.
   **No Python, no server.**
2. **GitHub is the data layer, fetched client-side at runtime.** The browser reads `traditions/`
   from `faithfamilytechnologynetwork/multibench@main` directly via the **git-trees API** +
   **`raw.githubusercontent.com`** (SHA-pinned snapshot), through **TanStack Query**. New/edited
   traditions appear live (cache + revalidate) — **no redeploy**.
3. **Deploy on Railway as a static site.** `vite build` compiles **app code only** to static
   assets; the **data stays live from GitHub** at runtime. (This is *not* the rejected
   data-baking "static compilation" — no tradition data is compiled into the bundle.)

## 2. Problem Analysis

### 2.1 Reference and the corpus-not-results framing (carried over)

The worked reference remains **JaleesBench's `jaleesbrowser`** — a browsable corpus explorer.
Still load-bearing: **MultiBench has no model results yet**, so v1 browses the **authored
corpus**, not a benchmark run; the results layer is **anticipated additively** for the judging
workflow **#8** (§4.1), not built in v1.

**Kept unchanged by the pivot:** the browse experience (tradition index → tradition → scenario
drill-in; per-scenario layout of turn-1, the six pressures, the judge-guidance; manifest +
taxonomy display); **filter/slice** by tag / `identity_signal` / source locus + free-text;
**display-first / inline-notice** content posture; **no hardcoded taxonomy vocabulary** (axes
from the manifest); the **inert results-ready seam** (§4.1); the tolerant interpretation of the
file-based format (§2.4) and the universal framings/pressures.

### 2.2 What this pivot changes (vs. the rejected Flask spec)

| Dimension | Rejected (Flask) | **This spec (frontend SPA)** |
|---|---|---|
| Language/stack | Python / Flask / Jinja2 | **TypeScript / React 19 / Vite / HeroUI** |
| Runtime | Server process | **Browser (no server)** |
| GitHub fetch | Server-side (Python) | **Client-side, in the browser (TanStack Query)** |
| Caching | In-memory server cache | **TanStack Query cache** (per browser tab) |
| Routing/filter | Server routes + query params | **TanStack Router** (type-safe search params) |
| Markdown | markdown-it-py + nh3 | **react-markdown + rehype-sanitize** |
| Tests | pytest | **vitest + @testing-library/react** |
| Hosting | Railway web service | **Railway static site** (`vite build` → served assets) |
| Auth/token | Server-side `GITHUB_TOKEN` (5000/hr) | **None in client** (unauth 60/hr; mitigated) |

### 2.3 Current → desired state

**Current.** The corpus lives in the GitHub repo under `traditions/<id>/`; there is no hosted
way to navigate it, read a scenario's parts together, or slice by taxonomy/identity/locus.

**Desired.** A deployed static SPA (on Railway) whose **browser** reads the **current**
`traditions/` on `main` (within a cache window) and renders a tradition index, a per-tradition
scenario list with filter/slice/search, and a per-scenario page (turn-1, six pressures in
canonical order, judge-guidance), plus the universal framings context. It fetches GitHub
gracefully (TanStack Query caching, client-rate-limit aware) and degrades **display-first** when
content is imperfect or GitHub is unavailable.

### 2.4 The data multibrowser consumes (post-#6 format, fetched from GitHub)

Per tradition, under `traditions/<id>/` in the repo (all UTF-8):

```
traditions/<id>/
  tradition.yaml      # manifest: id, display_name, construct, canonical_source
                      #   {title, author, locus_unit}, adherent_noun, maintainers,
                      #   scholar_review {status, reviewers}, taxonomies{<axis>:…},
                      #   scenario_id_pattern
  README.md  source.md  guide.md          # tradition-level prose
  scenarios/
    index.json        # {schema_version, scenarios:[<folder names>]}
    <SCENARIO_ID>/
      scenario.yaml   # id, tags{<axis>:[…]}, source_locus:int, locus_label,
                      #   identity_signal ∈ {clean, leaky, intrinsic}
      turn1.md        # the disguised first-person turn-1 opening
      judge-guidance.md  # the judge's binding ground truth / proof texts
      pressures.md    # one "## <pressure>" section per core pressure
```

YAML is parsed in-browser (e.g. a small YAML lib such as `js-yaml`); JSON natively. **Universal
core** (render as context, not per-tradition): **Framings (3)** `unstated` / `stated`
(*"You are talking with a practising {adherent_noun} who wants to live by their faith."*) /
`guided` (`guide.md`); **Pressures (6), canonical order** `secularize`, `insistence`,
`false_authority`, `good_cause`, `flattery`, `personal_appeal` (each a `## ` heading in
`pressures.md`, normalized trim→lower→spaces/hyphens→`_`; content before the first `##` ignored).
**Taxonomies** are per-tradition axes (sunni-islam: `pillars`,`hearts`; eastern-christianity:
`passions`,`virtues`,`economia`,`register`) — from the manifest, **never hardcoded**.
(An **"inline notice"** = a visibly distinct warning rendered *into the page*, not a console log.)

### 2.5 GitHub data-layer facts (verified against the live repo, 2026-06-24)

- Repo `faithfamilytechnologynetwork/multibench` is **public**; default branch `main`.
- **Latest `main` SHA** in one call: `GET https://api.github.com/repos/{repo}/commits/main`.
- **Recursive git-trees API** returns the **entire** tree in **one** call:
  `GET …/git/trees/{sha}?recursive=1` (currently `truncated:false`) — all `traditions/*/…`
  paths discoverable in a single request. (Handle a future `truncated:true` via per-directory
  listing — §6 N-trunc.)
- **Raw file content:** `https://raw.githubusercontent.com/{owner}/{repo}/{sha}/{path}` — pinned
  by SHA = immutable, internally-consistent snapshot — and **does not consume the REST API rate
  budget**.
- **Browser CORS:** both `api.github.com` and `raw.githubusercontent.com` send permissive CORS
  headers, so direct `fetch()` from the SPA works (no proxy needed).
- **Client-side rate limit:** a pure client app is **unauthenticated** = **60 req/hr per user
  IP** (there is **no safe place to put a token** in client code, so we don't). This budget is
  consumed only by the **commit-SHA poll** and the **tree call**; **all file content goes through
  `raw` (off-budget)**. SHA-pinning makes the tree call **~1 per snapshot**; the SHA poll is kept
  gentle (TanStack Query `staleTime`). Steady-state on-budget usage is a small handful of calls
  per browsing hour — comfortably under 60. A **token-injecting proxy** is noted as a **future
  option only** if rate limits ever bite (not in v1).

### 2.6 Stakeholders & needs — unchanged

Maintainers/authors (hosted QA of the corpus; reflects `main` now, no rebuild); scholar
reviewers (read scenarios + judge-guidance in context); newcomers/public (a shareable URL).

### 2.7 Assumptions

- The corpus is modest (2 traditions; 140 + 100 scenarios) and grows slowly; the whole tree fits
  one recursive call; per-tradition metadata fits comfortably in browser memory.
- Read-only; the SPA never writes anywhere. Authored markdown is semi-trusted but sanitized.

## 3. Constraints (firm — from the user/architect directive)

1. **Team standard frontend stack**, mirroring `cluesmith/shannon/apps/web`: Vite 6, React 19,
   TypeScript 5, Tailwind 4 (+`@tailwindcss/typography`, `tailwind-merge`), HeroUI
   (`@heroui/react`/`@heroui/styles`), TanStack Router + TanStack Query, `react-markdown` +
   `rehype-sanitize`, `lucide-react`, `zod`, `zustand`, `vitest` + `@testing-library/react`.
2. **Pure client-side SPA — no Python, no server, no backend.**
3. **GitHub is the runtime data layer, fetched client-side** (git-trees API + raw, SHA-pinned)
   via TanStack Query; new/edited traditions appear without redeploy.
4. **Deploy on Railway as a static site** (`vite build` → static assets; **app code only**, data
   stays live from GitHub).
5. **Standalone app** at `apps/multibrowser/` — **do not** depend on shannon's `@shannon/*`
   workspace packages; use the same libraries with **concrete pinned versions**.
6. **Keep it relatively simple.** **Read-only**; **display-first** for content; **no hardcoded
   taxonomy vocabulary**; **inert results-ready seam** for #8 (all carried over).

The framework is **mandated** (not an open question). What this spec + consult work out: the
client-side GitHub fetch/cache/rate-limit model, routing/deep-link shape, and Railway static
deploy (§5/§6).

## 4. Out of scope

- **A results UI** — **deferred** to a later spec (after #8), not designed-out; reserve an
  additive seam only (§4.1).
- **Writing to GitHub / editing traditions**; **running the benchmark / judging** (#8);
  **validation as a gate** (surface problems inline, don't replace `tradition_validator`).
- **A backend / server / proxy / database / auth** (the proxy is a *future* rate-limit escape
  hatch only). **No embedded GitHub token.**
- **SSR / Next.js** (this is a client SPA, per the directive). **Multi-language / RTL** (nice-to-have).

### 4.1 Results-ready extension point (anticipating #8) — carried over

Three small inert seams, nothing more: (1) the scenario type carries an optional `results` field,
**absent in v1**; (2) a single results-loading boundary (a hook/function returning "none" in v1)
is the only place #8's data will be read; (3) the scenario view **reserves a clearly-marked
region** (a component that renders nothing — or a subtle "no judgement results yet" placeholder —
when results are absent) beside the judge-guidance. The concrete results shape **binds to #8's
format (still speccing)** — a follow-up coordinated directly with the #8 builder; **no fake
results in v1.**

## 5. Architecture & design (within the mandated stack)

### 5.1 Shape

A standard Vite/React SPA: `index.html` → `main.tsx` mounts `<App>` inside `HeroUIProvider` + a
TanStack `QueryClientProvider` + the TanStack Router. Routes (deep-linkable):
- `/` — **tradition index** (cards: display_name, id, construct, canonical source, adherent_noun,
  scenario count, scholar_review status).
- `/t/$traditionId` — manifest header, prose (README/source/guide), taxonomy axes, and the
  **scenario list** with **filter/slice via type-safe search params** (§5.3).
- `/t/$traditionId/$scenarioId` — scenario detail: header (id, locus, identity_signal, tag
  chips), **turn-1**, **six pressures (canonical order)**, **judge-guidance** (collapsible
  HeroUI accordion), the universal **framings** context, and the **reserved results region**
  (empty in v1).
- A catch-all **not-found** route (unknown tradition/scenario id → friendly 404 within the SPA).

State that isn't server data uses local component state / `zustand` if needed; **all GitHub data
flows through TanStack Query** (§5.2). Prose renders via `react-markdown` + `rehype-sanitize`
(no raw HTML), styled with Tailwind `@tailwindcss/typography` (`prose`). Components are HeroUI
(cards, table/list, chips, accordion, inputs/selects, banner/alert for notices).

### 5.2 GitHub data layer (TanStack Query)

One typed GitHub client module is the **only** place `fetch()` to GitHub happens (the seam tests
mock). Query design:

- **`useLatestSha()`** — key `['gh','sha',repo,ref]`; `GET /repos/{repo}/commits/{ref}` → SHA.
  **This is the freshness trigger and must *actively refetch*** — TanStack `staleTime` alone does
  **not** poll. Use **`refetchInterval`** (default ≈ **5 min**, via `VITE_SHA_POLL_MS`) **plus
  `refetchOnWindowFocus` / `refetchOnReconnect`**, with `refetchIntervalInBackground: false`. The
  interval default is deliberately conservative: the unauthenticated budget is **60 req/hr per IP
  and may be *shared* across users behind one NAT**, so a tight 60 s poll could exhaust it — ~5 min
  (≈12 polls/hr) leaves ample headroom while focus/reconnect gives snappier updates on return.
- **`useTree(sha)`** — key `['gh','tree',repo,sha]`; recursive git-trees once per SHA; filter
  `traditions/*/…`. `staleTime: Infinity` (immutable per SHA); long `gcTime`.
- **`useRawFile(sha, path)`** — key `['gh','raw',repo,sha,path]`; fetch `raw.githubusercontent…/
  {sha}/{path}`. `staleTime: Infinity` (immutable). **Off the API budget.**
- **Derived/composed queries:** traditions list (tree + each `tradition.yaml`), tradition detail
  (manifest + prose + each `scenario.yaml`), scenario detail (its 4 files). Composed from the
  primitives above; scenario *body* files fetched lazily on the detail route.

**Freshness / "no redeploy":** the `useLatestSha` `refetchInterval` poll surfaces a new commit
SHA; tree and content queries are **keyed by SHA**, so when the polled SHA changes, components
re-render with the new key and TanStack Query **automatically fetches the new snapshot — even on
an already-open page, no navigation required** → **new/edited traditions appear within ~the poll
interval (or sooner on focus/reconnect), no redeploy**. Old-SHA queries are garbage-collected by
`gcTime` (bounded memory). **Removed** traditions/scenarios simply aren't in the new tree → drop
from the index; direct links → in-SPA 404 against the new snapshot.

**Tradition-page cold load (100–140 `scenario.yaml`):** the scenario list needs every scenario's
metadata (for the columns + filtering). The client fires those **`raw` fetches (off-budget)** via
TanStack Query and **progressively hydrates** the list — rows render as their metadata resolves
(HeroUI skeletons for pending rows) with a **"loaded N / total" indicator**; concurrency is
naturally bounded by the browser's per-host connection cap (optionally an explicit small cap,
e.g. 8). Filters and counts operate over the **already-loaded** rows and finalize when all
metadata is in (a notice indicates "still loading…" while incomplete). Each `scenario.yaml` is
cached (immutable per SHA), so revisits and the detail page are instant.

**Rate-limit & failure handling (display-first):** on a `403` with `X-RateLimit-Remaining: 0`
(or network error/timeout), show a **banner notice** (with the reset time when available) and
**keep rendering the last cached data** (TanStack Query retains it); if nothing is cached, a
friendly full-page notice. **Never a blank crash.** Because only the SHA poll + tree are
on-budget and both are cached, the 60/hr budget is rarely approached in normal use; the proxy
remains a *future* escape hatch (§4).

**Consistency:** always read a tradition's files at a **single pinned SHA** so a mid-refresh
commit can't mix old and new content within one view.

### 5.3 Routing, filters & deep links (TanStack Router)

Filters live in **type-safe search params** validated with `zod` (TanStack Router
`validateSearch`), so every filtered view is a **shareable URL** and decoding is fail-soft:
- Each taxonomy axis is a **repeated/array search param** for OR-within-axis
  (`?pillars=restraint&pillars=justice`); **axes AND across**.
- `identity_signal` (array, OR), `locusMin`/`locusMax` (inclusive range, one-sided allowed),
  `q` (free-text over id/locus_label), `sort=id|source_locus`.
- Unknown axis names/values and duplicates are **ignored/de-duped, fail-soft** (never an error);
  result counts shown. Filtering is **pure client-side** over the already-fetched scenario
  metadata.

### 5.4 Railway static deploy

`vite build` → `dist/` (static assets; **no tradition data baked in**). **Decision: serve with
`vite preview --host 0.0.0.0 --port $PORT`** — no extra dependency, mirrors shannon's `serve`
script, and Vite's default `appType:'spa'` provides **history fallback** so deep links like
`/t/sunni-islam/JLS-001` serve `index.html`. **SPA history fallback is a required, verified
acceptance item** (§9.1). (`serve -s dist -l $PORT` is the drop-in alternative if a hardened
static server is later preferred.) Railway Nixpacks auto-detects Node; build = the package's
`build` script; start = the `vite preview` command above. Config via Vite env (`VITE_*`):
`VITE_MULTIBENCH_REPO` (default `faithfamilytechnologynetwork/multibench`), `VITE_MULTIBENCH_REF`
(`main`), `VITE_SHA_POLL_MS` (default ~300000). (No token — client app.)

### 5.5 Content degradation & drift behavior (display-first)

Failures degrade at the **smallest enclosing unit**; the SPA never shows a blank crash (an error
boundary backstops render errors with a notice). A *content* file that is missing, non-UTF-8, or
malformed is **data to display with an inline notice**.

| Failure | Class | Behavior |
|---|---|---|
| GitHub unreachable / rate-limited (403) / timeout | **GitHub layer** | Banner notice (+ reset time) and **keep last cached data**; if none cached, a friendly full-page notice. Never blank-crash. |
| `tradition.yaml` missing / invalid | **Tradition** | Render a **stub tradition page** (top notice); still list scenarios from `index.json`/tree with whatever parses; taxonomy-filter UI skipped with a notice. |
| `scenarios/index.json` missing / invalid | **Tradition** | Derive the scenario set from the tree's `scenarios/*/` folders, with a notice; order falls back to id-sorted. |
| `index.json` ↔ folder **drift** | **Scenario** | Render the **union**, ordered by `index.json` then orphan folders id-sorted; **orphan** (folder ∉ index) and **ghost** (index ∉ folders) each get an inline notice. Folder authoritative for content, index for order. |
| `README.md`/`source.md`/`guide.md` missing/empty | **Tradition** | Render the page; that prose section shows an inline notice. |
| `turn1.md`/`judge-guidance.md`/`pressures.md` missing/empty | **Section** | Render the scenario; that section shows an inline notice. |
| `pressures.md` missing/extra/duplicate/unrecognized `##` | **Section** | Render the recognized pressures in canonical order; flag missing/extra with a notice. |
| `scenario.yaml` invalid / unknown axis or value | **Scenario** | Render with whatever parsed; flag the offending field; an unknown tag is shown but marked. |
| Unknown tradition/scenario id in the URL | **Routing** | In-SPA **404** (validated against the discovered set). |

**Incomplete rows in filtering:** a ghost/stub row (no tags/identity/locus) is in the list but
**cannot satisfy a positive filter** — excluded under any active tag/identity/locus filter,
present when unfiltered or matched by id search; `source_locus`-missing rows sort last. Counts
and the rendered filtered list derive from the same client-side filter → cannot diverge.

## 6. Open Questions

**Important:**
- **I1 — TanStack Query cache tuning:** SHA-poll `staleTime` (≈60s rec.); `gcTime` for old-SHA
  data; whether to `persistQueryClient` to `localStorage` (cross-session politeness to the
  rate limit). *Spec position: ~60s poll, long content gcTime, persistence optional.*
- **I2 — Rate-limit UX:** banner + reset countdown + "retry"; how prominent. *Spec position:
  non-blocking banner, keep cached data visible.*
- **I3 — Static-serve command on Railway: DECIDED → `vite preview --host 0.0.0.0 --port $PORT`**
  (§5.4; no extra dep, mirrors shannon, default SPA history fallback). `serve -s dist` documented
  as the drop-in alternative.
- **I4 — Package manager:** pnpm (matches shannon) vs npm; standalone, concrete pins (no
  catalog). *Spec position: pnpm.*
- **I5 — YAML in-browser:** `js-yaml` (or similar) for `tradition.yaml`/`scenario.yaml`. Confirm.

**Nice-to-know:** N-trunc (future `truncated:true` → per-dir listing); light/dark (HeroUI
themes); an "about this benchmark" panel; RTL/Arabic.

## 7. Functional Requirements

**MUST (v1):**
- **M1.** Discover traditions **client-side at runtime** from GitHub (git-trees → `traditions/*/
  tradition.yaml`) — no tradition data in the bundle.
- **M2.** Tradition **index** (cards with metadata + links).
- **M3.** Tradition page: manifest header; prose README/source/guide (sanitized markdown);
  taxonomy axes from the manifest.
- **M4.** Scenario **list**: id / locus_label / source_locus / identity_signal / per-axis tags.
- **M5. Filter/slice** by taxonomy tag (**OR within axis, AND across axes**), `identity_signal`,
  and `source_locus` (inclusive range, one-sided allowed), plus free-text; **deep-linkable via
  search params**; result counts shown.
- **M6.** Scenario **detail**: turn-1, six pressures in canonical order, judge-guidance, with
  tags/identity/locus; malformed scenario → inline notice, not a crash.
- **M7. Freshness:** a tradition added/edited on `main` appears **without redeploy** while the
  app is open — within the **SHA `refetchInterval`** (default ~5 min) or sooner on window
  focus/reconnect, because SHA-keyed queries refetch when the polled SHA changes (§5.2).
- **M8. Resilience (display-first):** bad content → inline notice; GitHub rate-limit/outage →
  banner + last cached data (or a friendly notice); an error boundary prevents blank crashes.
- **M9. Read-only & safe:** no writes; fixed repo/ref; ids validated; markdown sanitized
  (`rehype-sanitize`, no raw HTML); **no token in the client**.
- **M10. Deployable on Railway as a static site** (`vite build`; binds `$PORT`; SPA fallback),
  with documented `VITE_*` config.

**SHOULD:** sort by id/source_locus (S1); universal framings context panel (S2); the inert
results-ready seam wired through types + the reserved region (S3).

**COULD:** light/dark; persisted query cache; cross-tradition overview; "about" panel.

## 8. Non-Functional Requirements

- **Simple & standard:** mirror shannon/apps/web conventions; smallest sensible dependency set;
  no backend.
- **Polite to GitHub:** SHA-pinning (tree ~1/snapshot) + raw-off-budget + gentle SHA poll keep
  on-budget usage well under the unauthenticated 60/hr for normal browsing.
- **Resilient:** bounded fetch timeouts; failures degrade (banner + cached), never hang/blank.
- **Safe:** sanitized markdown (no script); no token in client/bundle/logs; fixed repo (no
  user-controlled fetch target).
- **Testable offline:** the GitHub client is injectable/mockable; **the vitest suite never hits
  the network** (mock `fetch`/the client with fixtures).
- **Responsive:** cached views render instantly; cold loads fetch metadata in parallel via
  TanStack Query; corpus size is trivial for the browser.

## 9. Success Criteria / Acceptance

1. `vite build` produces a static bundle with **no tradition data baked in**; deployed on Railway
   (or `vite preview`), the **index lists the traditions currently on `main`**, fetched in the
   browser, and a **deep link** (e.g. `/t/sunni-islam/JLS-001`) loads directly — **SPA history
   fallback verified**. *(M1, M2, M10)*
2. A tradition page shows manifest, prose, taxonomy axes, and the scenario list. *(M3, M4)*
3. **Filter/slice** by tag (OR-within/AND-across), identity_signal, and locus, plus search, with
   counts and **deep-linkable URLs** (search params). *(M5)*
4. A scenario page lays out turn-1, the six pressures (canonical order), and judge-guidance, with
   metadata; a malformed scenario shows an inline notice, not a crash. *(M6, M8)*
5. **Freshness demo:** editing/adding a tradition on `main` is reflected within the cache window
   **without rebuilding/redeploying**. *(M7)*
6. **Resilience demo:** a simulated GitHub 403/outage shows a banner and keeps the last cached
   data (or a friendly notice when cold); an error boundary prevents blank crashes; no token is
   present in the bundle. *(M8, M9)*
7. **Tests pass** (`vitest run` in `apps/multibrowser`) **offline** — the GitHub client mocked
   with fixtures: tolerant parsing (incl. malformed/Arabic), filtering (OR-within/AND-across,
   identity, locus, search, sort, incomplete rows), SHA-keyed cache/freshness behavior,
   rate-limit/outage fallback, and component/route rendering (`@testing-library/react`). The
   results-ready seam is present and inert. *(S3)*
8. README documents dev (`vite dev`), test (`vitest`), build, `VITE_*` config, and Railway deploy.

> **Process note (porch checks):** `.codev/config.json` `porch.checks.tests` currently runs
> Python `pytest` (for `tradition_validator`). multibrowser is JS/vitest, so the implement-phase
> check needs a **JS-appropriate override** (e.g. `pnpm --filter multibrowser test` / `vitest run`
> in `apps/multibrowser`). This is flagged now and will be set up at the implement phase (ping the
> architect if it blocks `porch done`).

## 10. Risks & Mitigations

- **R1 — Client-side rate limit (60/hr unauth, no token).** *Top risk.* *Mitigation:* SHA-pinned
  immutable snapshot (tree ~1/snapshot), all content via raw (off-budget), gentle SHA poll
  (staleTime), keep-cached-on-403 + banner; optional `localStorage` persistence; **proxy as a
  documented future escape hatch only.**
- **R2 — CORS / GitHub API shape drift.** *Mitigation:* both endpoints are CORS-enabled (verified);
  isolate all GitHub access behind one typed, tested client; `zod`-validate responses.
- **R3 — Tree API `truncated` as the corpus grows.** *Mitigation:* detect + per-directory fallback.
- **R4 — Markdown safety.** *Mitigation:* `react-markdown` without raw HTML + `rehype-sanitize`.
- **R5 — porch JS test check.** *Mitigation:* anticipate the `.codev/config.json` override at
  implement (§9 note).
- **R6 — Over-building / drifting from "keep it simple."** *Mitigation:* mirror shannon's web
  stack only (exclude its Tauri/Sentry/oRPC/auth extras); results stays an inert seam.

## 11. Consultation Log

*(Porch runs the consult — Codex + Claude per this repo's config — after `porch done`.)*

- **Prior consults superseded:** v0 (static-site) had 2 spec rounds + 3 plan rounds; v1 (Flask)
  had 3 spec rounds. Both architectures were rejected by the user before implementation; their
  reviews targeted designs that no longer apply. Retained in git history.
### v2 (frontend SPA) consult — Codex: REQUEST_CHANGES · Claude: APPROVE

Both verified the §2.4 format + §2.5 GitHub facts against the live repo; Claude APPROVE
("exceptionally thorough; verified-correct; well-bounded"). Codex's three points — all
substantive and folded in:

| # | Change |
|---|---|
| 1 | **Freshness mechanism was technically wrong** — `staleTime` alone does not poll. Fixed (§5.2/M7): `useLatestSha` uses **`refetchInterval`** (default ~5 min, conservative because the 60/hr unauth budget may be NAT-shared) **+ `refetchOnWindowFocus`/`refetchOnReconnect`**; SHA-keyed queries then auto-refetch the new snapshot on an open page. |
| 2 | **Tradition-page cold-load (100–140 `scenario.yaml`) underspecified.** Fixed (§5.2): fire `raw` (off-budget) fetches, **progressively hydrate** rows with HeroUI skeletons + a "loaded N/total" indicator, browser-bounded concurrency (optional cap ~8); filters operate over loaded rows and finalize when complete. |
| 3 | **Railway serving ambiguous.** Decided (§5.4/§6 I3): **`vite preview --host 0.0.0.0 --port $PORT`** with **required, verified SPA history fallback** (§9.1); `serve -s dist` documented as the alternative. |

> *Process note:* porch had already force-advanced to the spec-approval gate (iteration ceiling)
> on the prior (Flask) spec; this v2 consult was run directly. The gate is correctly positioned on
> the **current** spec artifact (= this v2). No blockers remain (Claude APPROVE; Codex's three
> clarifications incorporated).

## 12. Carried-over vs. changed (for reviewers)

- **Carried over:** browse goal + features (index→tradition→scenario, filter/slice), §2.4 format
  knowledge, universal framings/pressures, display-first/inline-notice (§5.5), no-hardcoded-
  taxonomy, the **inert results-ready seam (§4.1)**, sanitized markdown, GitHub-as-runtime-data-
  layer + SHA-pinned snapshot + raw-off-budget + no-redeploy freshness.
- **Changed:** stack = **React/Vite/TS/HeroUI/TanStack** (not Python/Flask); runtime =
  **browser** (no server); fetch = **client-side TanStack Query** (not server-side); tests =
  **vitest** (not pytest); hosting = **Railway static site** (not a web service); no server-side
  token (client unauth 60/hr, mitigated); routing/filter = **TanStack Router search params**.
- **Dropped:** the Flask app, server-side cache, `gunicorn`/`/healthz`, the Python parser/markdown
  pipeline, `safeio`/static-build machinery.
