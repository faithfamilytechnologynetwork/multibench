# Review 7: multibrowser — browse & explore MultiBench traditions

| | |
|---|---|
| **Issue** | #7 |
| **Spec** | [codev/specs/7-jaleesbrowser-browse-explore-m.md](../specs/7-jaleesbrowser-browse-explore-m.md) |
| **Plan** | [codev/plans/7-jaleesbrowser-browse-explore-m.md](../plans/7-jaleesbrowser-browse-explore-m.md) |
| **App** | `apps/multibrowser/` |
| **Tests** | 89 vitest (offline) + a real build & static-server smoke; `tsc --noEmit` clean |

## What was built

A **pure client-side React SPA** at `apps/multibrowser/` (the team-standard stack: Vite 6 +
React 19 + TS + Tailwind 4 + HeroUI v3 + TanStack Router/Query, `react-markdown` + `rehype-sanitize`)
that **reads the MultiBench tradition corpus from GitHub at runtime in the browser** and deploys on
**Railway as a static site**. It browses tradition index → tradition → scenario; renders each
scenario's turn-1, the six pressures (canonical order), the judge-guidance, and the framings
context; and filters/slices the scenario set by taxonomy tag, `identity_signal`, and source locus,
all deep-linkable. It is **read-only**, **display-first** (imperfect content → inline notices),
**no-hardcoded-taxonomy** (axes from each manifest; verified across all 5 real traditions, 2–5 axes
each), and carries an **inert results-ready seam** for the judging workflow (#8).

Built in 6 git-committed phases on one branch: offline parsing core → GitHub/TanStack-Query data
layer → app shell + router + index + UI primitives → tradition page + filtering + progressive
hydration → scenario detail + results seam → Railway deploy + README.

## How it went

**Three architecture pivots before a line of code.** The spec/plan were taken to approval three
times: (v0) a Python static-site generator over local files (approved + planned, then rejected);
(v1) a Python Flask live web app + GitHub data layer (specced, rejected pre-approval); (v2) this
pure-frontend SPA. Each pivot re-ran spec/plan with 3-way consultation. The corpus-browsing goal,
display-first posture, no-hardcoded-taxonomy, and the inert #8 seam carried across all three; only
the delivery/stack changed. **Lesson: keep the spec's *intent* sections (features, posture, format)
separable from its *delivery* sections so a stack pivot is a rewrite of the latter, not both.**

**The GitHub-as-runtime-data-layer design held up.** Verified against the live repo before
speccing: the recursive git-trees API returns the whole tree in one call; `raw.githubusercontent`
is off the API rate budget; both endpoints are CORS-enabled. The client-side rate limit (60/hr
unauth, possibly NAT-shared, no safe token) drove the cache design: SHA-pin the tree (≈1 call per
snapshot), fetch all content via raw, poll the commit SHA gently with `refetchInterval` +
`refetchOnWindowFocus:"always"`, serve-stale-with-banner on 403.

**Per-phase 3-way consults caught real bugs**, not just nits: a cold-start rate-limit endless
spinner; `staleTime` mistaken for a poll (it doesn't refetch); unbounded fetch (no timeout);
unknown-tag-value validation missing; `?pillars=bogus` filtering to zero rows instead of fail-soft.
All fixed with tests.

## Architecture Updates

Applied to the hot-tier governance docs (`codev/resources/{arch,lessons}-critical.md`), which also
regenerate into CLAUDE.md/AGENTS.md:

- **arch-critical.md** — added: *"`apps/multibrowser/` is the team-standard frontend SPA (Vite/
  React19/TS/Tailwind4/HeroUI/TanStack) that browses the corpus by reading GitHub at RUNTIME
  (client-side TanStack Query: git-trees + raw, SHA-pinned); deployed on Railway as a static site;
  bakes no data (new traditions appear without redeploy); read-only."* and *"porch's implement/
  review tests-check is a per-builder DISPATCHER (`.codev/checks/test.sh`) that runs only the suite
  of each app a builder touched (registry: tradition_validator→pytest, multibrowser→pnpm test);
  add an app = one registry line."* (Displaced/condensed weaker entries to respect the cap.)

## Lessons Learned Updates

- **lessons-critical.md** — added: *"HeroUI **v3** is provider-less — there is no `HeroUIProvider`
  (only I18nProvider/ToastProvider/useTheme); wire styling via `@import "@heroui/styles"`, don't add
  a v2-era provider."* and *"A client-side GitHub data layer is unauthenticated (60/hr per IP, may be
  NAT-shared, no safe token): SHA-pin the tree (1 call/snapshot), fetch content via `raw` (off the
  API budget), poll the commit SHA gently, and serve stale + a banner on 403."*

### Other lessons (cold / this review)

- **Separate spec intent from delivery** so a stack pivot rewrites only the delivery half (3 pivots
  here).
- **Verify a data layer against the real source before speccing** — the tree-in-one-call,
  raw-off-budget, and CORS facts were load-bearing and only confirmable against live GitHub.
- **`staleTime` ≠ polling** in TanStack Query — freshness needs `refetchInterval` / `"always"`.
- **A global porch check needs a dispatcher, not a guarded `&&`-chain** — the `&&`/`||` form also
  masks real failures; a per-builder registry is the clean shape (thanks codev:architect).
- **"Tests pass" ≠ "it works"** — the live-GitHub node smoke and the real build + `serve -s dist`
  deep-link smoke caught what mocked unit tests couldn't.

## Deviations from the plan (all architect-approved)

- **`serve -s dist`** for Railway (not `vite preview`): `vite` is a devDep and may be absent at
  runtime; `serve` is a small runtime dep with SPA history fallback. Verified by a real
  static-server smoke.
- **Code-based TanStack Router** (not file-based/router-plugin): no codegen, explicit, fully
  testable; same deep links.
- **HeroUI v3 provider-less** wiring (the plan's "HeroUIProvider" was v2-era).

## Follow-ups

- **#8 (judging) results layer:** v1 ships only the inert seam (`Scenario.results?`, `loadResults→
  none`, reserved `ResultsRegion`). Bind the concrete `ScenarioResults` to #8's output once its
  schema firms up — coordinate directly with the spir-8 builder (per architect).
- **Verify phase:** deploy to Railway and confirm the live site lists all 5 traditions from GitHub,
  freshness without redeploy, and rate-limit resilience.
- **COULD:** light/dark theme; a shared rate-limit banner in the shell (page-local today, reactive);
  persisted query cache.
