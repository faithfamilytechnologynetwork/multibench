# spir-7 — jaleesbrowser: browse & explore MultiBench traditions

Builder thread (cohort situational-awareness log). Issue #7, SPIR strict mode.

## 2026-06-23 — Specify phase started

**Goal**: an `apps/jaleesbrowser/` app to *browse and explore* MultiBench traditions
and their scenarios (read-only). Reference: JaleesBench's `jaleesbrowser` (iaser-ai/jaleesbench).

**Key research findings**:
- JaleesBench's `jaleesbrowser` is a **static TS/React (Vite) SPA** on GitHub Pages that
  browses **model-vs-model RESULTS** (scores, judge verdicts, side-by-side compare),
  fed by a Python `export_web.py` that emits `index.json` + lazy gzip per-probe shards.
- **Crucial divergence**: MultiBench #7 browses the **authored corpus** (scenarios,
  pressures, judge-guidance, taxonomy metadata) — there are NO model results to compare
  yet. Same *spirit* (static, zero-install, deep-linkable explorer), different *subject*.
  So JaleesBench's score-matrix / model-compare / shard machinery is largely irrelevant;
  we adapt the *browsing/viewer* experience, not the results-comparison.
- Repo is **Python (uv)**; sibling app `apps/tradition_validator/` is Typer + pydantic +
  pyyaml, flat-package layout, with a ready data model (`models.py`) + loaders (`loaders.py`).

**Firm constraints from the issue** (treated as baked, though no formal Baked-Decisions heading):
- Read-only: NEVER modify `traditions/` data.
- Python conventions (uv/Typer where CLI).
- App lives at `apps/jaleesbrowser/`.
- **Approach (web vs TUI vs static-site) is explicitly LEFT OPEN** for the spec + 3-way to decide.

**⚠️ #6 vocabulary dependency (critical risk)**:
- Issue says spec/build against POST-RENAME vocab: `scenarios/`, `scenario.yaml`,
  `turn1.md`, `scenario_id_pattern`, `scenarios/index.json`.
- But #6 (AIR, branch `builder/air-6`) is NOT merged AND the rename isn't even committed to
  its branch yet (diff vs main = only a status.yaml). Real data on main still uses OLD vocab
  (`probes/`, `probe.yaml`, `scenario.md`, `probe_id_pattern`).
- Plan: build against post-rename, verify with synthetic post-rename fixtures, isolate the
  format names in one constants module, rebase onto main after #6 merges. Documented as a risk.

Next: draft spec → `porch done 7` → porch runs 3-way consult → iterate → spec-approval gate.

## 2026-06-23 — Spec iter-1 consult done, feedback incorporated

Ran the 2-way consult (codex + claude; Gemini excluded by repo config). **Codex:
REQUEST_CHANGES, Claude: COMMENT — no blockers**, strong convergence. Both praised the §2.1
"this is NOT JaleesBench's results browser, there are no results to browse" reframing as the
key risk-killer. Incorporated all 11 sharpenings (see spec §11 Consultation Log table):
the substantive one was a real fail-soft/fail-loud inconsistency → added an explicit §8
**degradation-scope table** (invocation aborts; tradition/scenario/section degrade to inline
notices). Also nailed down: OR-within/AND-across filter semantics, index↔folder drift policy,
prev/next order, read-only tree-snapshot test, output escaping/path-containment/no-CDN, and
an "inline notice = rendered HTML warning" definition. Deferred to Plan: watch mechanism,
validator-import-vs-vendored-model, markdown renderer/sanitizer pick. Both endorsed Approach A
(Python static-site generator) over B and the post-rename-with-synthetic-fixtures sequencing.

Next: `porch next 7` → expect spec-approval gate (human). Will notify architect.

## 2026-06-24 — Spec-approval APPROVED; Plan phase (consult done + 2 architect changes folded)

Spec gate approved by human (architect relayed: "corpus-not-results reframing + Approach A
exactly right"). Wrote the implementation **plan** (5 strictly-linear phases: reader-core →
scenarios/notices → render → static-build → serve+README). Resolved the spec's deferred Plan
decisions: **I1** vendor dataclass read-model (don't import the strict validator); **I3**
`markdown-it-py`+`nh3`; **watch** = `watchfiles`.

Plan consult: **Codex REQUEST_CHANGES** (3 gaps: tradition prose loading M4; S1 sort;
stub-tradition-on-bad-manifest rendering) + **Claude APPROVE** (no blockers). All folded in.

**Two architect-directed changes folded into spec+plan mid-phase:**
1. **Rename `jaleesbrowser` → `multibrowser`** (app/package/module/docs). ⚠️ Kept the porch
   slug + spec/plan/review FILENAMES as `7-jaleesbrowser-browse-explore-m.md` (porch state is
   keyed to slug; renaming breaks porch checks). Reference project's own app stays `jaleesbrowser`.
2. **Results "cut" → "results-ready"** anticipating judging #8: three inert seams
   (`Scenario.results=None`; `load_results()→None`; reserved `_results.html.j2`) across P1–P3.
   **No results UI in v1.** Concrete `ScenarioResults` schema deferred to a #8-coordinated
   follow-up. Spec §2.1/§4 reframed + new §4.1; logged as post-approval amendment in spec §11.

**Re-gate judgment:** amendments don't change v1's build surface (rename cosmetic; results
unbuilt) → no separate spec re-gate; rides to human at plan-approval. Flagged to architect.

Next: rebuttal written → `porch done 7` → expect plan-approval gate. Notify architect +
coordinate with #8 (spir-8) on the eventual result schema.

## 2026-06-24 — Plan iter-2 consult + #6 MERGED → rebased onto main

Plan iter-2 consult: **Codex REQUEST_CHANGES** (one point: Phase-4 client-filter testing too
manual) + **Claude APPROVE** (all iter-1 gaps resolved, full spec coverage). Fixed Codex's
point by extracting filter/sort/query-state into a **pure-Python `filtering.py`** (the
authoritative semantics) with exhaustive `test_filtering.py`; JS reduced to a thin applier.
No spec-required behavior now rests on a manual check.

**#6/#9 MERGED on main** (commit 31620e2) + follow-up #10 — and per architect, **rebased
builder/spir-7 onto origin/main** (clean, 0 conflicts; my codev/* files don't overlap main's
traditions/ rename). Verified real post-rename data matches my `constants.py`:
`scenarios/` + `index.json` key `"scenarios"` + `scenario.yaml` + `turn1.md` +
`scenario_id_pattern`. **R1 (top risk) RESOLVED.** Bonus: a 2nd real tradition landed —
`eastern-christianity` (100 scenarios, BZ-### ids, axes passions/virtues/economia/register vs
sunni-islam's pillars/hearts) → now a real test of multi-tradition discovery + no-hardcoded-axes.

Plan + spec updated (R1 resolved, filtering.py, 2-tradition verification). Next: `porch done 7`
→ iter-3 consult → expect plan-approval gate (human). Then coordinate w/ #8 on result schema.

(Note: rebasing the already-pushed branch made the porch auto-push non-fast-forward → resolved
with `git push --force-with-lease` after confirming all 13 "dropped" remote commits were my own
pre-rebase spir-7 work, all replayed onto main. Local≡remote now.)

## 2026-06-24 — Plan iter-3 consult: Codex RC (2 pts) fixed, Claude APPROVE

Iter-3: **Codex REQUEST_CHANGES** (2 pts) + **Claude APPROVE**. Fixed both:
1. **Ghost/stub rows in filtering** were underspecified → added an explicit Phase-4 rule:
   `build_filter_index` emits an entry for every rendered row (ghost/stub get null/empty
   metadata); metadata-less rows can't satisfy a positive predicate (excluded under any active
   filter, present when unfiltered); `None` locus sorts last; counts≡rendered list (both from
   `apply_selection`). Stub-tradition: tag-axis UI skipped, identity/locus/search/sort still
   work. test_filtering covers a ghost + a no-axes tradition.
2. **Stale "manual verify" risk-table row** contradicting the filtering.py posture → updated to
   "automated test-of-record." Swept plan; remaining "manual" mentions are legit confirmatory steps.

Next: `porch done 7` → iter-4 consult (expect convergence) → plan-approval gate (human).

## 2026-06-24 — ⚠️ MAJOR ARCHITECTURE PIVOT (user-directed) → rolled back to SPECIFY

Plan-approval was APPROVED and I'd just entered Implement — then the user **fundamentally
changed the architecture**. HALTED before writing any code (only task placeholders + an
uncommitted config tweak, reverted). Ran `porch rollback 7 specify`.

**OLD (now invalidated):** Approach A = Python static-site generator over LOCAL files.
**NEW direction (user, via architect):**
- A **deployable LIVE web app** — NO static-compilation/build stage.
- **GitHub is the data layer**: read `traditions/` from `faithfamilytechnologynetwork/multibench@main`
  **at runtime** via GitHub API / raw content (NOT local FS, NOT a prebuilt bundle) — so
  new/edited traditions appear **without a redeploy**.
- **Deploy on Railway.** Keep it **relatively simple**.

**KEEP (still applies):** corpus-browse goal + features (index→tradition→scenario, filter/slice);
display-first/inline-notice posture; no hardcoded taxonomy vocab; inert results-ready seam (#8).
**DROP:** static build, `build`/`serve --watch`, filtering.py-as-static-index (filtering now
server-side), local safeio path-containment (no local FS).
**NEW to spec (with consultation):** Python web framework (Flask vs FastAPI), GitHub
fetch + caching + rate-limit/token handling, Railway deploy shape.

Plan: re-spec → spec consult (codex+claude) → spec-approval gate (architect brings to user).
spir-8 (#8) coordination: per architect, do it directly once #8's spec firms up; v1 inert seam stands.

Grounded the GitHub data layer against the REAL repo first: public; recursive git-trees API
returns the whole tree in ONE call (truncated:false) → clean discovery; raw.githubusercontent
fetch is off the API rate budget; token→5000/hr (60/hr unauth, fine w/ caching). Wrote the
new spec: Flask + Jinja2 + gunicorn on Railway; GitHubSource boundary (latest_sha→tree→raw,
SHA-pinned immutable snapshot); in-memory single-snapshot cache w/ TTL (~60s) → new traditions
appear w/o redeploy; serve-stale+banner on rate-limit/outage; server-side filtering; SSRF-safe
(fixed repo, ids validated). Old plan banner-marked SUPERSEDED.

## 2026-06-24 — Re-spec consult: Codex RC (3) fixed, Claude APPROVE → spec-approval gate next

Re-spec consult: **Codex REQUEST_CHANGES** (degradation/drift detail dropped in rewrite;
framework-decision inconsistency; removals unspecified) + **Claude APPROVE** (4 minor). Both
verified format+GitHub facts against the live repo. Fixed all: restored a **§5.5 degradation/
drift table** (startup/GitHub-layer/tradition/scenario/section/snapshot incl. index↔folder
drift, stub-tradition, incomplete-row filtering); **DECIDED Flask** (closed C1; §5.4/§9 now
Flask-consistent); specified **removals** (drop from index + 404 on next refresh) and
**bounded single-snapshot cache** (discard old-SHA data); **source_locus** range inclusive both
ends, one-sided allowed.

Next: `porch done 7` → expect spec-approval gate (human). Notify architect.

## 2026-06-24 — ⚠️ 2nd ARCHITECTURE PIVOT (user) → re-spec #2: FRONTEND SPA stack

Flask spec REJECTED at the gate (before approval). New direction: the team's **standard
frontend stack** — pure client-side SPA, **no Python**: Vite6 + React19 + TS5 + Tailwind4 +
HeroUI + TanStack Router/Query, react-markdown+rehype-sanitize, vitest. Mirror
`cluesmith/shannon/apps/web` (confirmed its package.json: HeroUI v3, Tailwind 4, TanStack
Router 1.141 / Query 5, react-markdown 10, rehype-sanitize 6, vite 6, vitest 3, react 19;
pnpm catalog). multibrowser = STANDALONE (no @shannon/* deps, concrete pins), excluding
shannon's Tauri/Sentry/oRPC/auth extras.

Architecture: **pure frontend SPA**; **GitHub fetched client-side at runtime via TanStack
Query** (git-trees + raw, SHA-pinned); **Railway STATIC-SITE deploy** (vite build = app code
only, data stays live from GitHub → NOT data-baking). Client rate limit = **60/hr unauth, NO
token in client** — mitigate w/ SHA-pinned snapshot (tree=1/snapshot), raw off-budget, gentle
SHA poll, keep-cached-on-403 + banner; proxy = FUTURE only. KEEP: browse features, display-
first/§5.5 degradation table, no-hardcoded-taxonomy, inert #8 seam.

⚠️ porch JS-check: `.codev/config.json` tests=pytest (python). multibrowser=vitest → will need
a JS override at IMPLEMENT (architect flagged; will ping then). Verified vs real repo: api +
raw both CORS-enabled; whole tree in 1 call; raw off-budget.

Re-spec #2 written. Next: porch rollback/redo consult cycle → re-consult (codex+claude) →
spec-approval gate. Architect brings to user.

porch mechanics note: porch had force-advanced to the spec-approval gate (iteration ceiling) on
the Flask spec; `porch rollback 7 specify` is refused ("cannot rollback to current phase") and
`porch done` from gate_pending just re-asserts the gate. So the gate is correctly pending on the
CURRENT spec artifact (now v2); I ran the v2 consult **manually** (codex+claude) — it reviews the
current spec file regardless. Gate stays pending for the human; no porch state hacking needed.

v2 consult: **Codex REQUEST_CHANGES** (3) + **Claude APPROVE**. Fixed all 3 — incl. a real bug I
made: TanStack `staleTime` doesn't poll → switched to `refetchInterval` (~5min default, NAT-
shared-60/hr-aware) + focus/reconnect refetch; SHA-keyed queries auto-refresh open pages.
Also specified tradition-page cold-load (progressive hydration, skeletons, "loaded N/total",
off-budget raw, browser-bounded concurrency) and DECIDED Railway serve = `vite preview --host
--port $PORT` w/ verified SPA history fallback. Spec §11 consultation log updated.

Gate is pending on v2 (porch spec-approval). Notified architect. Awaiting human approval. After
approval: rewrite the plan for the frontend SPA + set up the JS porch test-check.

## 2026-06-25 — v2 spec APPROVED → SPA plan written (6 phases)

Spec-approval APPROVED (architect: SPA frontend spec, shannon stack). Heads-up: **main now has 5
traditions** (sunni-islam 140, eastern-christianity 106, judaism 40, buddhism 40, taoism 40), all
validate-all --strict clean. Queried their axes via gh api (no rebase — SPA reads GitHub at
runtime, local data unused by the app): **diverse axes 2–5 per tradition** (pillars/hearts;
passions/virtues/economia/register; middot/virtues/middle_path/domain/register;
defilements/cultivations/path_factor/middle_way/register; departures/te/pivot/register) — strong
test of no-hardcoded-axes. Confirmed api.github.com sends ACAO:* and CORS-exposes
X-RateLimit-Remaining/Reset (banner can show reset time); unauth limit 60.

Plan = 6 linear phases: (1) scaffold + constants + types + tolerant parsers (offline core);
(2) GitHub client + TanStack Query data layer (mocked-fetch tests); (3) shell + router + index +
UI primitives; (4) tradition page + filtering.ts (zod search params) + progressive hydration;
(5) scenario detail + inert results seam; (6) Railway deploy + README + porch-JS-check flag.
Plan decisions: pnpm, file-based TanStack Router, js-yaml, react-markdown+rehype-sanitize,
refetchInterval ~5min (NAT-60/hr-aware), vite preview deploy, vitest+testing-library offline.

Next: porch done → plan consult (codex+claude) → plan-approval gate. Rebase onto main at implement.

SPA plan consult (run MANUALLY — porch carried the plan-iteration counter to its ceiling from the
rejected Approach-A plan, so it loops "fix issues" without issuing a consult task; consult reviews
the current plan file regardless): **Codex REQUEST_CHANGES (2) + Claude APPROVE**. Fixed both:
(1) `base:'./'` → **`base:'/'`** (relative base breaks deep-link asset loading on a root-served
SPA); (2) assigned the 3 spec fallbacks to phases+tests — truncated→per-dir (P2), index-missing→
folders (P2), unknown traditionId/scenarioId→in-SPA 404 (P4/P5). Plan §Plan-Consultation + rebuttal
recorded.

Next: `porch done 7` → plan-approval gate (force-advance at ceiling). Notify architect.
