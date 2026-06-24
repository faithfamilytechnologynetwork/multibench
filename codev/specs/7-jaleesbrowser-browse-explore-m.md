# Spec 7: multibrowser — browse & explore MultiBench traditions (live web app)

| | |
|---|---|
| **Issue** | #7 |
| **Protocol** | SPIR |
| **Status** | Specify — **re-spec after architecture pivot** (2026-06-24); draft for 3-way review |
| **App path** | `apps/multibrowser/` |
| **Architecture** | **Live deployable web app** · **GitHub is the runtime data layer** · **deployed on Railway** |

> **Re-spec notice.** An earlier version of this spec (a Python *static-site generator* over
> *local* files — "Approach A") was approved and planned, then the user **fundamentally changed
> the architecture** before any code was written. This document supersedes it. The corpus-
> browsing **goal, features, and content posture carry over**; the **delivery architecture is
> new**. See §12 for what carried over vs. changed and the (now-invalidated) prior consults.

## 1. Summary

Build `apps/multibrowser/` — a **deployable, live web application** for **browsing and
exploring MultiBench traditions and their scenarios**. A user opens a URL and navigates a
tradition, reads each scenario (the turn-1 opening, the six pressure pushes, the
judge-guidance), and **filters/slices** the scenario set by taxonomy tags, `identity_signal`,
and source locus.

Two defining architectural facts:

1. **GitHub is the data layer, read at runtime.** multibrowser reads the tradition corpus
   **directly from the GitHub repository** `faithfamilytechnologynetwork/multibench`
   (`traditions/` on `main`) **via the GitHub API / raw content at request time** — *not* from
   a local filesystem and *not* from a pre-built bundle. **New or edited traditions on GitHub
   appear in the app without a redeploy** (within a short cache window).
2. **It deploys on Railway** as a normal long-running web service, kept **relatively simple**.

There is **no static-compilation/build step** and no checked-in data copy: the running service
*is* the product.

## 2. Problem Analysis

### 2.1 What carries over from the (worked) reference and the prior spec

The worked reference remains **JaleesBench's `jaleesbrowser`** (github.com/iaser-ai/jaleesbench)
— a browsable corpus/results explorer. As before (and still load-bearing): **MultiBench has no
model results yet**, so v1 browses the **authored corpus**, not a benchmark run; the results
layer is **anticipated additively** for the judging workflow **#8** (§4.1), not built in v1.

These remain unchanged by the pivot and are **kept**:
- The browse experience: **tradition index → tradition → scenario** drill-in; per-scenario
  layout of turn-1, the six pressures, and the judge-guidance; manifest + taxonomy display.
- **Filter/slice** the scenario set by taxonomy tag, `identity_signal`, and source locus, plus
  free-text search.
- **Display-first / inline-notice** content posture (render imperfect data with a visible
  notice, never crash on bad *content*).
- **No hardcoded taxonomy vocabulary** — axes and values come from each tradition's manifest.
- The **inert results-ready seam** for #8 (§4.1).
- The tolerant parsing of the file-based format (§2.4) and the universal framings/pressures.

### 2.2 What the pivot changes

| Dimension | Prior (invalidated) | **This spec** |
|---|---|---|
| Delivery | Static-site generator (`build`/`serve`) | **Live web service** (long-running) |
| Data source | **Local** `traditions/` files | **GitHub** repo at **runtime** (API / raw) |
| Freshness | Rebuild to update | **New traditions appear without redeploy** (cache TTL) |
| Filtering | Pre-baked index + client JS | **Server-side** over fetched+cached metadata (query params) |
| Hosting | GitHub Pages (static) | **Railway** (web service) |
| File safety | Local symlink/`..` containment | **GitHub-fetch safety** (fixed repo, validated ids, no SSRF) |
| Primary interface | Typer CLI | **HTTP routes** (a tiny CLI to run locally is fine) |

### 2.3 Current state vs desired state

**Current state.** The corpus lives in the GitHub repo under `traditions/<id>/`. To read it one
opens raw files on GitHub; there is no hosted way to navigate a tradition, read a scenario's
parts together, or slice by taxonomy/identity/locus.

**Desired state.** A deployed URL (on Railway) serves a browsable view that always reflects the
**current** `traditions/` on `main` (within a cache window): a tradition index, a per-tradition
scenario list with filter/slice/search, and a per-scenario page laying out the turn-1 opening,
the six pressures (canonical order), and the judge-guidance seam, plus the universal framings
context. It reads GitHub gracefully (caching, rate-limit aware) and degrades display-first when
content is imperfect or GitHub is unavailable.

### 2.4 The data multibrowser consumes (post-rename format, live from GitHub)

The format is the **post-#6 vocabulary** (merged; verified on `main`). Per tradition, under
`traditions/<id>/` in the repo (all UTF-8):

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

**Universal core (render as context, not per-tradition):**
- **Framings (3):** `unstated`, `stated` (template *"You are talking with a practising
  {adherent_noun} who wants to live by their faith."*), `guided` (the tradition's `guide.md`).
- **Pressures (6), canonical order:** `secularize`, `insistence`, `false_authority`,
  `good_cause`, `flattery`, `personal_appeal`. In `pressures.md` each is a `## ` heading,
  normalized (trim → lowercase → spaces/hyphens→`_`); content before the first `##` is ignored.
- **Taxonomies** are per-tradition axes (sunni-islam: `pillars`,`hearts`; eastern-christianity:
  `passions`,`virtues`,`economia`,`register`). Axes/values come **from the manifest** — never
  hardcoded. (Throughout, an **"inline notice"** = a visibly distinct warning block rendered
  *into the page*, not a console log.)

### 2.5 GitHub data-layer facts (verified against the live repo, 2026-06-24)

- The repo `faithfamilytechnologynetwork/multibench` is **public**; default branch `main`.
- The **latest `main` commit SHA** is one cheap call (`GET /repos/{repo}/commits/main`).
- The **recursive git trees API** returns the **entire** repo tree in **one** call
  (`GET /repos/{repo}/git/trees/{sha}?recursive=1`), currently `truncated: false` — so all
  `traditions/*/…` paths are discoverable in a single request. (Spec must handle a future
  `truncated: true` by falling back to per-directory listing — §6 N-trunc.)
- **Raw file content** is fetchable via `raw.githubusercontent.com/{owner}/{repo}/{sha}/{path}`
  (pinned by SHA = an immutable, internally-consistent snapshot) and **does not consume the
  REST API rate budget**.
- **Rate limits:** unauthenticated REST = 60/hr per IP; with a `GITHUB_TOKEN` = 5000/hr. With
  caching, steady-state API usage is ~1–2 calls per cache window (commit SHA + tree), so even
  the unauthenticated budget is comfortable; a token is recommended, not required.

### 2.6 Stakeholders & needs

- **Maintainers / authors** — a hosted way to QA the corpus and see a scenario's parts together;
  want it to reflect what's on `main` now, without asking anyone to rebuild/redeploy.
- **Scholar reviewers** — read scenarios + judge-guidance in context with clean prose rendering.
- **Newcomers / the public** — a shareable URL to explore what MultiBench tests.

### 2.7 Assumptions

- The corpus is modest (today 2 traditions; 140 + 100 scenarios) and grows slowly; the whole
  tree fits one recursive call; per-tradition metadata fits comfortably in memory.
- Read-only: multibrowser never writes to GitHub or anywhere persistent (no DB).
- Authored markdown is semi-trusted (repo content) but is still sanitized on render.

## 3. Constraints (firm — from the user/architect directive)

1. **Live web app — no static build step.** The running service is the product; no
   pre-compilation, no checked-in data bundle.
2. **GitHub is the runtime data layer.** Read `traditions/` from
   `faithfamilytechnologynetwork/multibench@main` via the GitHub API / raw content **at request
   time**; new/edited traditions appear **without redeploy** (within the cache window).
3. **Deploy on Railway.**
4. **Keep it relatively simple.** Prefer the smallest design that meets the above; avoid a DB,
   a queue, a build pipeline, or heavy frameworks unless justified.
5. **Python conventions** (uv; the repo is Python). App at `apps/multibrowser/`.
6. **Read-only**; **display-first** for content; **no hardcoded taxonomy vocabulary**;
   **inert results-ready seam** for #8 (all carried over).

The **web framework, fetch/cache/rate-limit design, and Railway deploy shape** are *open* for
this spec + 3-way consultation to decide (§5/§6).

## 4. Out of scope

- **A results UI** — **deferred** to a later spec (after #8), not designed-out; v1 reserves an
  additive seam only (§4.1).
- **Writing to GitHub / editing traditions** (that's `create-tradition` + the validator).
- **Running the benchmark / judging** (that's #8); multibrowser only *consumes* its output later.
- **Validation as a gate** — surface obvious content problems inline; do not replace
  `tradition_validator`.
- **Auth / users / a database / write-back / persistent storage** (the cache is in-memory).
- **Multi-language / RTL** (single-language corpus; nice-to-have).

### 4.1 Results-ready extension point (anticipating #8) — carried over

v1 builds exactly three small, inert seams and nothing more: (1) the scenario model carries an
optional `results` slot, **`None` in v1**; (2) a single results boundary (a `load_results(...)`
returning `None` in v1) is the only place #8's output will be read; (3) the scenario page
**reserves a clearly-marked region** that renders nothing (or a subtle "no judgement results
yet" placeholder) when results are absent, beside the judge-guidance the results anchor to. The
concrete results schema **binds to #8's format (still speccing)** — a follow-up, coordinated
directly with the #8 builder; v1 ships the seam returning `None`. **No fake results in v1.**

## 5. Solution Exploration

### 5.1 Web framework (the central "approach" decision)

All options share the same **core** (a GitHub data-layer client + cache, the tolerant parser
carried over from the prior spec, server-side filtering, Jinja2 templates, safe markdown) and
differ in the web shell.

- **Approach A — Flask + Jinja2 + gunicorn — RECOMMENDED.** A small, synchronous,
  server-rendered app; routes return HTML; filtering is server-side via query params; concurrent
  GitHub fetches (e.g., a tradition's many `scenario.yaml`) use a bounded thread pool; gunicorn
  on Railway is a one-line start command. *Pros:* simplest, maximal familiarity, matches "keep it
  relatively simple," trivial Railway deploy. *Cons:* concurrency for cold-cache bursts needs a
  thread pool (minor). **Complexity: low. Risk: low.**
- **Approach B — FastAPI + httpx (async) + uvicorn.** Async makes concurrent GitHub fetches
  elegant and scales many simultaneous users well. *Pros:* clean async fetch; modern. *Cons:*
  async adds conceptual overhead; once the cache is warm the async benefit is marginal for a
  read-mostly app. **Complexity: low–medium. Risk: low.** *Strongest alternative if fetch
  concurrency/latency dominates.*
- **Approach C — Streamlit / Dash.** Fast to stand up a data UI. *Cons:* opinionated UX, awkward
  for clean per-scenario URLs / deep links and custom prose layout; heavier; diverges from a
  normal deep-linkable web app. **Not recommended.**

**Decision: Approach A — Flask** (confirmed by the consult; neither reviewer advocated FastAPI).
It honors "keep it relatively simple," gives clean deep-linkable routes, and the GitHub-fetch
concurrency need is fully met by caching + a small bounded thread pool. **FastAPI+httpx (B)
remains the documented fallback** if fetch concurrency/latency ever dominates. Acceptance and
deploy wording (§5.4, §9) are therefore Flask-specific **by decision** (resolves the prior
§9.7-vs-C1 inconsistency).

### 5.2 GitHub data layer (fetch + cache + freshness)

A single **`GitHubSource`** boundary (the one place network I/O happens — the seam that tests
mock):
- **Resolve snapshot:** `latest_sha()` → `GET /repos/{repo}/commits/{ref}` (ref default `main`).
  Pin all subsequent reads to that SHA → an internally-consistent snapshot.
- **Discover:** `tree(sha)` → `GET …/git/trees/{sha}?recursive=1`; filter `traditions/*/…`.
  Handle `truncated: true` by per-directory fallback (§6).
- **Read files:** `raw(path, sha)` via `raw.githubusercontent.com/{owner}/{repo}/{sha}/{path}`
  (off the API budget; immutable per SHA). Contents-API is the fallback if raw is unavailable.
- **Auth:** optional `GITHUB_TOKEN` (Bearer) → 5000/hr + future private support; absent → 60/hr,
  fine with caching.
- **Conditional requests:** use `ETag`/`If-None-Match` on the commit/tree calls to avoid burning
  budget when nothing changed.

**Caching & freshness** (the mechanism behind "no redeploy"):
- An in-memory cache keyed by **commit SHA**. Content fetched per `(sha, path)` is immutable, so
  cached until the SHA changes.
- **Single live snapshot (bounded memory):** when a new SHA is confirmed, the prior SHA's cached
  data is **discarded** — the cache holds essentially one snapshot at a time, so memory does not
  grow across commits on Railway. A consequence: a **removed** tradition/scenario simply isn't in
  the next tree → it **drops from the index** on refresh and its direct links **404** against the
  new snapshot (no stale ghosts of deleted content).
- A short **TTL** (default e.g. 60s, configurable) gates how often `latest_sha()` is re-checked.
  On a request past the TTL, re-check the SHA; if it changed, the new snapshot is used (lazily,
  per accessed tradition) → **new/edited traditions appear within ~TTL, no redeploy**.
- **Cold-cache** for a tradition: fetch its `index.json` + `tradition.yaml` + prose + each
  `scenario.yaml` concurrently (bounded pool), cache, then serve. Scenario *body* files
  (`turn1.md`/`pressures.md`/`judge-guidance.md`) are fetched lazily on the detail page.

**Failure / rate-limit handling (display-first):** on GitHub error, rate-limit (403), or
timeout, **serve stale cache if available** with a visible banner notice; otherwise a clear,
friendly error page. Never crash; never block indefinitely (bounded timeouts).

**Security / SSRF:** the repo/ref are **fixed by config**, never user input. URL path components
(`<tradition_id>`, `<scenario_id>`) are **validated against the discovered set** before any
fetch; unknown ids → 404. No user input is interpolated into a GitHub path/URL → no traversal,
no SSRF.

### 5.3 Routes & UX (server-rendered, deep-linkable)

- `GET /` — tradition index (each: display_name, id, construct, canonical source, adherent_noun,
  scenario count, scholar_review status).
- `GET /t/<tradition_id>` — manifest header, prose (README/source/guide), taxonomy axes, and the
  **scenario list** with **filter/slice via query params** (`?<axis>=<val>&identity_signal=…&
  locus_min=…&locus_max=…&q=…&sort=id|source_locus`). Filters: **OR within an axis, AND across
  axes**; free-text over id/locus_label. Deep-linkable (the query string *is* the state).
- `GET /t/<tradition_id>/<scenario_id>` — scenario detail: header (id, locus, identity_signal,
  tag chips), **turn-1**, **six pressures in canonical order**, **judge-guidance** (collapsible),
  the universal **framings** context, and the **reserved results region** (empty in v1).
- `GET /healthz` — liveness for Railway (does not depend on GitHub being reachable).

### 5.4 Railway deploy shape

A normal web service (Flask, per §5.1): start `gunicorn multibrowser.app:app --bind 0.0.0.0:$PORT`.
Python deps via `pyproject`/`requirements.txt` (Railway nixpacks auto-detects), optionally a
`Procfile`/`railway.json`. Config via env: `GITHUB_TOKEN` (optional), `MULTIBENCH_REPO` (default
`faithfamilytechnologynetwork/multibench`), `MULTIBENCH_REF` (`main`), `CACHE_TTL_SECONDS`,
`PORT` (Railway-provided). `/healthz` as the health check.

### 5.5 Content degradation & drift behavior (display-first — restated for the GitHub-backed app)

This restores the prior spec's degradation contract, adapted to the live/GitHub model (the prior
review's main clarifications). Failures degrade at the **smallest enclosing unit**; only
**startup/config** failures fail the process. A *content* file that is missing, non-UTF-8,
oversized, or malformed is **data to display with an inline notice**, never a crash. GitHub-layer
failures degrade to stale-cache + banner (§5.2).

| Failure | Class | Behavior |
|---|---|---|
| Missing/invalid required env at startup (bad repo/ref) | **Startup** | Fail fast with a clear log; `/healthz` reports unhealthy. |
| GitHub unreachable / rate-limited (403) / timeout | **GitHub layer** | Serve **stale cache + banner** notice; if no cache, a friendly error page. Never crash; bounded timeouts. |
| `tradition.yaml` missing / invalid / schema-violating | **Tradition** | Render a **stub tradition page** (top notice); still list scenarios from `index.json`/folders with whatever metadata parses; manifest-derived UI (taxonomy filters) **skipped with a notice**. |
| `scenarios/index.json` missing / invalid | **Tradition** | Derive the scenario set from the tree's `scenarios/*/` folders instead, with a notice; declared order falls back to id-sorted. |
| `index.json` ↔ folder **drift** | **Scenario** | Render the **union**, ordered by `index.json` then orphan folders id-sorted; **orphan** (folder ∉ index) and **ghost** (index entry ∉ folders) each get an inline notice. Folder authoritative for content, index for order. |
| `README.md` / `source.md` / `guide.md` missing / empty / non-UTF-8 | **Tradition** | Render the page; that prose section shows an inline notice. |
| `turn1.md` / `judge-guidance.md` / `pressures.md` missing / empty / non-UTF-8 / oversized | **Section** | Render the scenario; that section shows an inline notice in place of content. |
| `pressures.md` missing / extra / duplicate / unrecognized `## ` heading | **Section** | Render the recognized pressures in canonical order; flag missing/extra with a notice. |
| `scenario.yaml` invalid / unknown axis or value | **Scenario** | Render with whatever parsed; flag the offending field; an unknown tag is shown but marked. |
| **Removed** tradition/scenario (gone from `main` after refresh) | **Snapshot** | Next refresh omits it → drops from the index; direct links **404** against the new snapshot; old-SHA cache discarded (§5.2). |

**Incomplete rows in filtering** (carried over): a row with missing metadata (ghost / stub) is in
the list but, having no tags/identity/locus, **cannot satisfy a positive filter** — excluded under
any active tag/identity/locus filter, present when unfiltered or matched by id search;
`source_locus`-missing rows sort **last**. Counts and the rendered filtered list both derive from
the same server-side filter, so they cannot diverge.

## 6. Open Questions

**Critical:**
- **C1 — Framework: DECIDED → Flask** (§5.1; confirmed by the consult — neither reviewer
  advocated FastAPI). FastAPI+httpx documented as the fallback only.
- **C2 — Fetch strategy:** raw-by-SHA (rec.) vs contents API; lazy per-page vs eager
  whole-tradition warming. *Spec position: raw-by-SHA, lazy-by-page with concurrent metadata fetch.*

**Important:**
- **I1 — Token required or optional?** *Spec position: optional (60/hr + caching suffices), token
  recommended for headroom.* Confirm acceptable.
- **I2 — Cache TTL & freshness target** (how fast must a new tradition appear?). *Spec position:
  ~60s default, configurable.*
- **I3 — Rate-limit/outage behavior:** serve-stale-with-notice (rec.) vs hard error. *Spec
  position: serve stale + banner; friendly error only when no cache.*
- **I4 — Filtering:** pure server-side query params (rec., simplest) vs a little client JS for
  snappier UX. *Spec position: server-side; optional progressive JS later.*
- **I5 — Data model reuse:** carry the prior spec's tolerant **dataclass** parser (rec.) vs adopt
  pydantic. *Spec position: reuse tolerant dataclasses (display-first needs leniency).*

**Nice-to-know:**
- **N-trunc** — handle a future `truncated: true` tree via per-directory listing.
- **N1** — light/dark theme; **N2** — a `/` "about this benchmark" panel; **N3** — RTL/Arabic.

## 7. Functional Requirements

**MUST (v1 acceptance):**
- **M1.** Discover traditions at runtime from GitHub (`traditions/*/tradition.yaml` via the tree
  API) — no local data copy.
- **M2.** Tradition **index** page (per-tradition metadata + links).
- **M3.** Tradition page: manifest header; prose README/source/guide (rendered markdown);
  taxonomy axes (from manifest).
- **M4.** Scenario **list** with columns id / locus_label / source_locus / identity_signal /
  per-axis tags.
- **M5. Filter/slice** the list by taxonomy tag (**OR within axis, AND across axes**),
  `identity_signal`, and `source_locus` (a range **inclusive on both ends**; one-sided — only
  `locus_min` or only `locus_max` — allowed), plus free-text search; deep-linkable via query
  string; result counts shown.
- **M6.** Scenario **detail**: turn-1, the six pressures in canonical order, judge-guidance, with
  tags/identity_signal/locus; a malformed scenario renders with an inline notice, not a crash.
- **M7. Freshness:** a tradition added/edited on `main` appears in the app **without a redeploy**
  (within the cache TTL).
- **M8. Resilience (display-first):** bad/missing content → inline notice; GitHub rate-limit /
  outage → serve stale cache with a banner, else a friendly error; never crash.
- **M9. Read-only & safe:** no writes anywhere; fixed repo/ref; ids validated (no SSRF/traversal);
  markdown sanitized; `/healthz` independent of GitHub.
- **M10. Deployable on Railway** with documented env config; binds `$PORT`.

**SHOULD:** sort by id/source_locus (S1); universal framings context panel (S2); the inert
results-ready seam wired through model + render (S3).

**COULD:** light/dark; cross-tradition overview; a tiny CLI to run locally (`multibrowser serve`)
for dev; ETag-driven conditional refresh tuning.

## 8. Non-Functional Requirements

- **Simple:** no DB/queue/build pipeline; smallest dependency set that works.
- **Resilient & bounded:** all GitHub calls have timeouts; failures degrade, never hang/crash.
- **Polite to GitHub:** caching + conditional requests keep steady-state API usage to ~1–2
  calls/TTL; works within the unauthenticated 60/hr budget for low traffic.
- **Safe:** sanitized markdown (no script execution); no SSRF; secrets only via env (no token in
  code/logs).
- **Offline-testable:** the GitHub layer is injectable; the **test suite never hits the network**.
- **Responsive:** warm-cache pages render without noticeable lag; cold-cache tradition load fetches
  metadata concurrently.

## 9. Success Criteria / Acceptance

1. Deployed on Railway (or run locally), the **index lists the traditions currently on `main`**;
   no tradition data is committed into `apps/multibrowser/`. *(M1, M2, M10)*
2. A tradition page shows manifest, prose, taxonomy axes, and the scenario list. *(M3, M4)*
3. **Filter/slice** by tag (OR-within/AND-across), identity_signal, and locus, plus search, with
   counts and deep-linkable URLs. *(M5)*
4. A scenario page lays out turn-1, the six pressures (canonical order), and judge-guidance, with
   metadata; a malformed scenario shows an inline notice, not a crash. *(M6)*
5. **Freshness demo:** editing/adding a tradition on `main` is reflected within the cache TTL
   **without redeploying**. *(M7)*
6. **Resilience demo:** simulated GitHub rate-limit/outage serves stale cache with a banner (or a
   friendly error when cold); the app never crashes; `/healthz` stays green. *(M8, M9)*
7. **Tests pass** (`uv --project apps/multibrowser run pytest`) **offline** — the `GitHubSource`
   is mocked with fixtures: tolerant parser (incl. malformed/Arabic), filtering
   (OR-within/AND-across, identity, locus, search, sort, incomplete rows), cache TTL +
   SHA-invalidation, rate-limit/outage fallback, and route handlers (Flask test client). The
   results-ready seam is present and inert (`results=None`, reserved region empty). *(S3)*
8. README documents local run, env config (repo/ref/token/TTL), and Railway deploy.

## 10. Risks & Mitigations

- **R1 — GitHub rate limits / outages.** *Mitigation:* SHA-pinned immutable cache + conditional
  requests + raw-content (off-budget) + serve-stale-with-notice; optional token for headroom.
- **R2 — Latency of many per-scenario fetches (cold cache).** *Mitigation:* fetch tradition
  metadata concurrently (bounded pool / async), lazy scenario bodies, cache aggressively.
- **R3 — Tree API `truncated` as the corpus grows.** *Mitigation:* detect and fall back to
  per-directory listing (N-trunc).
- **R4 — SSRF / path traversal via URL ids.** *Mitigation:* fixed repo/ref; validate ids against
  the discovered set; never interpolate raw user input into GitHub paths.
- **R5 — Over-building / drifting from "keep it simple."** *Mitigation:* Flask, in-memory cache,
  server-side filtering, no DB; results stays an inert seam.
- **R6 — Stale-cache confusion** (user sees old data). *Mitigation:* short TTL + a visible "as of
  commit <sha-short>" / "served from cache" indicator.

## 11. Consultation Log

*(Porch runs the consult — Codex + Claude per this repo's config — after `porch done`.)*

- **Prior consults (Approach A, now invalidated):** the spec went through 2 spec-review rounds
  and the plan through 3; all of that targeted the *static-site* architecture and is superseded
  by this re-spec. Retained in git history; not repeated here.

### Re-spec iteration (Codex: REQUEST_CHANGES · Claude: APPROVE — no blockers)

Both reviewers verified the §2.4 format + §2.5 GitHub facts against the live repo and called the
architecture sound; they converged on the same clarifications (the rewrite had dropped the prior
spec's degradation detail). All incorporated:

| # | From | Change |
|---|---|---|
| 1 | Codex (substantive) | **Degradation/drift behavior restated** for the GitHub-backed app — new **§5.5 table** (startup / GitHub-layer / tradition / scenario / section / snapshot), incl. index↔folder drift (union, orphan/ghost notices), missing prose, stub-tradition on bad manifest, missing scenario sections, and the incomplete-row filtering rule. |
| 2 | Codex + Claude | **Framework DECIDED → Flask** (C1 closed; §5.1; §5.4/§9 now consistently Flask). Resolves the §9.7-vs-C1 inconsistency. |
| 3 | Codex + Claude | **Removals / drift after refresh** specified (§5.2 + §5.5 Snapshot row): a removed tradition/scenario drops from the index and 404s on direct links against the new snapshot. |
| 4 | Claude | **Cache eviction / bounded memory** (§5.2): single live snapshot — old-SHA data discarded on new-SHA confirmation. |
| 5 | Claude | **`source_locus` range** inclusivity specified (M5): inclusive both ends; one-sided allowed. |

No blockers; Claude APPROVE, and Codex's REQUEST_CHANGES items are all one-paragraph
clarifications now folded in.

## 12. Carried-over vs. changed (quick reference for reviewers)

- **Carried over (unchanged intent):** browse goal + features (index→tradition→scenario,
  filter/slice), §2.4 format knowledge, universal framings/pressures, display-first/inline-notice,
  no-hardcoded-taxonomy, the tolerant dataclass parser, the **inert results-ready seam (§4.1)**,
  markdown-it-py + nh3 sanitized rendering.
- **Changed:** delivery = **live web service** (not static build); data = **GitHub at runtime**
  (not local files); filtering = **server-side** (not pre-baked client index); hosting =
  **Railway** (not GitHub Pages); file-safety = **GitHub-fetch safety** (not local containment);
  primary interface = **HTTP routes** (not a Typer CLI).
- **Dropped:** static `build`/`serve --watch`, the static `filter-index.json` + `filter.js`
  applier, local `safeio` path-containment, the SSG determinism/link-integrity machinery.
