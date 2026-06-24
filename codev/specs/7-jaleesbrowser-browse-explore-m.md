# Spec 7: jaleesbrowser — browse & explore MultiBench traditions

| | |
|---|---|
| **Issue** | #7 |
| **Protocol** | SPIR |
| **Status** | Specify (draft for 3-way review) |
| **App path** | `apps/jaleesbrowser/` |
| **Depends on** | #6 (probe→scenario rename, in-flight) — see Risks |

## 1. Summary

Build `apps/jaleesbrowser/` — a **read-only browser/explorer for MultiBench traditions and
their scenarios**. A user can navigate a tradition, read each scenario (the turn-1 opening,
the six pressure pushes, the judge-guidance), see the manifest/taxonomy metadata, and
**filter/slice** the scenario set by taxonomy tags, `identity_signal`, and source locus.

The worked reference is **JaleesBench's `jaleesbrowser`** (github.com/iaser-ai/jaleesbench):
a static, zero-install, deep-linkable explorer. We adapt its *browsing/viewer spirit* to a
fundamentally different subject (see §2.1): MultiBench has, today, **no model results to
compare** — jaleesbrowser browses the **authored corpus**, not a benchmark run.

## 2. Problem Analysis

### 2.1 The reference, and how MultiBench differs (load-bearing)

JaleesBench's `jaleesbrowser` is a Vite/React static SPA on GitHub Pages whose entire job is
to compare **model-vs-model RESULTS**: pick Model A and Model B, a pressure and a framing,
and read their two responses side by side with per-judge verdicts and band scores. It is fed
by a Python `export_web.py` that pre-computes a score matrix + per-probe gzip shards.

**MultiBench #7 is not that.** At this point MultiBench has only the **authored tradition
format** — `traditions/<id>/` — and no collected model responses, judgments, or scores. So:

- The thing to browse is the **authored content and its metadata**, not results.
- JaleesBench's score-matrix / model-selectors / verdict-bands / shard machinery is **out of
  scope** — there is nothing to populate it.
- What we keep from the reference is the **explorer experience**: a catalog → drill-in flow,
  rich markdown rendering of authored prose, taxonomy-driven filtering, deep-linkable views,
  and a static/zero-install/deterministic build philosophy.

This reframing is the most important design fact in this spec. A reviewer who assumes
"clone JaleesBench's browser" will over-build a results UI with no data behind it.

### 2.2 Current state vs desired state

**Current state.** Traditions are authored as file trees under `traditions/<id>/`. The only
tool that reads them is `apps/tradition_validator/` (a fail-fast mechanical gate). To *read*
a tradition today you open raw `.md`/`.yaml` files in an editor — there is no way to see a
scenario's turn-1, its six pressures, and its judge-guidance together, nor to slice the 140
scenarios by tag / identity_signal / locus.

**Desired state.** A maintainer runs one command and gets a browsable view: a tradition
index, a per-tradition scenario list with filter/slice/search, and a per-scenario page that
lays out the turn-1 opening, the six pressure pushes (in canonical order), the judge-guidance
seam, and the scenario's taxonomy tags / identity_signal / source locus — plus the universal
framings context (the Stated template instantiated with `adherent_noun`, and the Guided
`guide.md`). Read-only: it never writes to `traditions/`.

### 2.3 Stakeholders & needs

- **Tradition authors / porters** — QA a tradition while building it: "do all 140 scenarios
  have all six pressures? which are `leaky`? what does scenario JLS-072's judge-guidance
  actually bind to?" Needs fast slicing and side-by-side reading of a scenario's parts.
- **Scholar reviewers** — read scenarios + judge-guidance in context to assess fidelity to
  the canonical source; need clean prose rendering and locus labels, not YAML.
- **Maintainers / newcomers** — understand the benchmark's shape (taxonomies, framings,
  pressures, identity_signal distribution) before contributing.
- **The public (secondary)** — if hosted, a shareable way to explore what MultiBench tests.

### 2.4 The data jaleesbrowser consumes (POST-RENAME format)

Per the issue, the spec targets the **post-rename vocabulary** landing in #6. The mapping
from the format on `main` today (old) to what jaleesbrowser reads (new):

| Concept | OLD (on `main` today) | NEW (target — #6) |
|---|---|---|
| Per-scenario dir | `probes/<PROBE_ID>/` | `scenarios/<SCENARIO_ID>/` |
| Index file | `probes/index.json` (`{schema_version, probes:[…]}`) | `scenarios/index.json` (`{schema_version, scenarios:[…]}`) |
| Per-scenario metadata | `probe.yaml` | `scenario.yaml` |
| Turn-1 prose | `scenario.md` | `turn1.md` |
| Manifest id-pattern key | `probe_id_pattern` | `scenario_id_pattern` |
| Judge seam | `judge-guidance.md` | `judge-guidance.md` (unchanged) |
| Pressure pushes | `pressures.md` | `pressures.md` (unchanged) |

Files jaleesbrowser reads per tradition (all UTF-8):

```
traditions/<id>/
  tradition.yaml      # manifest: id, display_name, construct, canonical_source
                      #   {title, author, locus_unit}, adherent_noun, maintainers,
                      #   scholar_review {status, reviewers}, taxonomies{<axis>:…},
                      #   scenario_id_pattern
  README.md           # human overview (prose)
  source.md           # canonical source + why it is consensus-grade (prose)
  guide.md            # the Guided-framing system prompt (prose)
  scenarios/
    index.json        # {schema_version, scenarios:[<folder names>]}
    <SCENARIO_ID>/
      scenario.yaml   # id, tags{<axis>:[…]}, source_locus:int, locus_label,
                      #   identity_signal ∈ {clean, leaky, intrinsic}
      turn1.md        # the disguised first-person turn-1 opening (prose)
      judge-guidance.md  # the judge's binding ground truth / proof texts (prose)
      pressures.md    # one "## <pressure>" section per core pressure (prose)
```

**Universal core (not per-tradition; render as context):**
- **Framings (3):** `unstated` (no system prompt), `stated` (core template *"You are talking
  with a practising {adherent_noun} who wants to live by their faith."*), `guided` (the
  tradition's `guide.md`).
- **Pressures (6), canonical order:** `secularize`, `insistence`, `false_authority`,
  `good_cause`, `flattery`, `personal_appeal`. In `pressures.md` each is a `## ` heading,
  normalized (trim → lowercase → spaces/hyphens→`_`); content before the first `##` is
  intro/ignored.
- **Taxonomies** are per-tradition tag axes (e.g. Sunni Islam: `pillars` applies_to
  `scenario`, `hearts` applies_to `response`), each with a declared `values` set. The browser
  reads axes from the manifest and uses them to build filters — it must **not** hardcode any
  axis name or value (Sunni Islam is one instance; other traditions declare their own).

### 2.5 Assumptions

- The dataset is small and local: one tradition ≈ 140 scenarios of small markdown files;
  there are a handful of traditions. No DB, pagination-at-scale, or streaming is needed.
- jaleesbrowser reads the live files under `traditions/` (a path argument); it does not
  require a pre-computed export the way JaleesBench does.
- Authored markdown is semi-trusted (repo content), but rendering still sanitizes/escapes as
  defense-in-depth, and never executes embedded code.

## 3. Constraints (firm — from the issue; do not relitigate in the spec)

The issue has no formal `## Baked Decisions` heading, but states these as firm directives;
they are treated as fixed. The **delivery approach** is *explicitly left open* for this spec +
3-way consultation to decide (§5).

1. **Read-only.** jaleesbrowser MUST NOT create, modify, move, or delete anything under
   `traditions/`. It only reads.
2. **Python conventions.** Python + `uv`; **Typer** for any CLI (per repo + global prefs).
   No `src/` import prefix; run via `python -m`.
3. **Location.** The app lives at `apps/jaleesbrowser/` (its own uv package, like
   `apps/tradition_validator/`).
4. **Post-rename vocabulary.** Spec and build against `scenarios/` / `scenario.yaml` /
   `turn1.md` / `scenario_id_pattern` / `scenarios/index.json`. Rebase onto `main` after #6
   merges (§9 Risks).
5. **No fallbacks / fail-loud at the boundaries** (global dev principle): when *invoked*
   wrongly (bad path, missing tradition) fail clearly. Distinct from *display* tolerance —
   see the resolved open question §6/§8 on display-first reading of imperfect content.

## 4. Out of scope

- **Anything results-shaped**: model responses, scoring, judge verdicts-of-models, band
  ladders, model-vs-model comparison, a score matrix. (No such data exists in MultiBench yet;
  this is the core JaleesBench feature we intentionally drop.)
- **Running the benchmark / judging workflow** (collection, judging, normalization).
- **Authoring or editing** traditions/scenarios (that is `create-tradition` + the validator).
- **Validation as a gate** — jaleesbrowser is not a second validator; it may *surface* obvious
  problems inline (e.g. "missing pressure: flattery") but it does not replace
  `tradition_validator` and does not exit-fail on content defects.
- **Multi-language / RTL** (traditions are single-language; a nice-to-have, §6).
- **Auth, multi-user, a database, write-back, server-side persistence.**

## 5. Solution Exploration (delivery approach — the open decision)

All approaches share the same **core** (a tolerant reader/model over the post-rename format,
reusing the validator's pydantic schemas where strictness is acceptable) and differ only in
the **presentation/runtime shell**. The decision is which shell to build for v1.

### Approach A — Python static-site generator (Typer `build`/`serve`) — **RECOMMENDED**

A Typer CLI that reads `traditions/` and renders a **self-contained static site** (server-
side-generated HTML via Jinja2; one page per tradition and per scenario; a small embedded
`index.json` + vanilla-JS for client-side filter/search; no JS framework). `jaleesbrowser
build --out dist/` emits the site; `jaleesbrowser serve` builds + serves it locally
(`http.server`) with an optional `--watch` rebuild.

- **Pros:** Stays in the repo's language (Python/uv/Typer) with **zero Node toolchain**;
  mirrors JaleesBench's static / zero-install / deterministic / deep-linkable philosophy and
  is GitHub-Pages-hostable the same way; deterministic output diffs cleanly; reuses the
  validator's pydantic model; the static artifact *is* the shareable deliverable.
- **Cons:** A build step sits between editing data and seeing it (mitigated by `serve
  --watch`); client-side filtering needs a little hand-written vanilla JS over an embedded
  index.
- **Complexity:** Medium. **Risk:** Low.

### Approach B — Python live web app (Flask/FastAPI + Jinja2)

`jaleesbrowser serve` runs a small server that reads `traditions/` live; filtering is
server-side query-params re-rendering templates (no client JS needed).

- **Pros:** No build step / always live; dynamic filtering "just works" without JS; simplest
  *interaction* model for an internal tool.
- **Cons:** Not static / not zero-install / not directly GitHub-Pages-hostable (diverges from
  the reference's defining property); needs a running process; "shareable" becomes "run my
  server," not "open a link."
- **Complexity:** Low–Medium. **Risk:** Low. *Strongest alternative if interactivity and
  zero-build-friction outweigh static hosting.*

### Approach C — Python TUI (Textual / Rich)

A terminal explorer.

- **Pros:** Pure Python, fast, lives where the developer already is, no browser.
- **Cons:** Not shareable / not hostable; weaker for rendering long markdown prose and the
  six-pressure layout; narrower audience; diverges most from the static-explorer reference.
- **Complexity:** Medium. **Risk:** Medium (TUI markdown/layout fiddliness).

### Approach D — TypeScript/React static SPA (clone JaleesBench's stack)

Rebuild the reference's Vite/React app for tradition content.

- **Pros:** Maximal fidelity to the reference; richest client interactivity; same hosting story.
- **Cons:** Introduces a **Node/TS toolchain into a Python repo** (the only other app is
  Python); most of the cloned machinery (score matrix, model compare, shards) has no data to
  drive it, so it is over-built; two languages to maintain.
- **Complexity:** High. **Risk:** Medium–High (toolchain + over-engineering).

### Recommendation

**Approach A (Python static-site generator with an optional `serve --watch`).** It honors
every firm constraint (Python/uv/Typer, read-only, `apps/jaleesbrowser/`), reproduces the
reference's static/zero-install/deep-linkable/deterministic spirit, reuses the validator's
data model, and avoids both a second language (D) and a hard dependency on a running process
(B). The `serve --watch` convenience closes most of B's live-editing gap. **The 3-way
consultation is explicitly asked to pressure-test A vs B** (the genuine trade-off is
static-hostable-deliverable vs zero-build-live-interaction).

## 6. Open Questions

**Critical (blocks design):**
- **C1 — Delivery approach:** confirm Approach A (static SSG) over B (live Flask). *Spec
  position: A; consultation to validate.*
- **C2 — #6 sequencing:** build against post-rename now and verify on synthetic fixtures
  (spec position), vs wait for #6, vs support both vocabularies via an auto-detect adapter.
  *Spec position: post-rename only, names isolated in one constants module; rebase after #6.*

**Important (affects design):**
- **I1 — Data-model reuse:** depend on the `tradition_validator` package's pydantic
  `models.py`, or vendor a lean read-model in jaleesbrowser? *Lean toward: reuse the pydantic
  schemas but read **tolerantly** (display-first) rather than fail-fast — decided in §8.*
- **I2 — Reading posture:** the browser must render even an *imperfect* / in-progress
  tradition (a missing pressure, an unknown tag), surfacing problems as inline notices rather
  than refusing to render. (Contrast the validator's fail-fast.) *Spec position: yes,
  display-first; invocation errors still fail loud per §3.5.*
- **I3 — Markdown renderer:** `markdown-it-py` vs `python-markdown` vs `mistune`, plus
  sanitization (e.g. `bleach`/`nh3`). *Pick one in Plan; must escape raw HTML, render the
  Arabic/diacritics in the corpus correctly, and not execute code.*
- **I4 — Cross-tradition exploration:** v1 = per-tradition browse only, or also a
  cross-tradition taxonomy/identity_signal overview? *Spec position: per-tradition for v1; a
  top-level tradition index is in; cross-tradition slicing is COULD.*

**Nice-to-know (optimization):**
- **N1 — GitHub Pages deploy** workflow (as JaleesBench has) — COULD, not v1-blocking.
- **N2 — Light/dark theme, deep-link URL state for active filters** — SHOULD where cheap.
- **N3 — RTL / Arabic-aware** rendering of judge-guidance — COULD.

## 7. Functional Requirements

Adapted from the reference's *browsing* features (catalog → drill-in, filtering, deep links),
re-pointed at authored content. **MUST** = v1 acceptance; **SHOULD** = strongly wanted;
**COULD** = stretch.

### 7.1 Discovery & tradition index
- **M1.** Discover traditions by globbing `traditions/*/tradition.yaml` under a given root
  (default `traditions/`, overridable).
- **M2.** Render a **tradition index**: per tradition show `display_name`, `id`, `construct`,
  `canonical_source` (title / author / locus_unit), `adherent_noun`, scenario count, and
  `scholar_review.status`; link into each tradition.

### 7.2 Tradition view
- **M3.** Render the manifest header (display_name, construct, canonical source, adherent_noun,
  maintainers, scholar_review).
- **M4.** Render the tradition prose — `README.md`, `source.md`, `guide.md` — as formatted
  markdown (each reachable; `guide.md` labeled as the Guided-framing system prompt).
- **M5.** Show the **taxonomy axes**: for each axis its `description`, `applies_to`, and
  `values` (read from the manifest; never hardcoded).
- **M6.** Render the **scenario list** (from `scenarios/index.json`, cross-checked against the
  `scenarios/*/` folders) as a table/list with columns: id, `locus_label`, `source_locus`,
  `identity_signal`, and per-axis tags.
- **M7. Filter/slice** the scenario list by: each **taxonomy tag** (per axis), **identity_signal**
  (`clean`/`leaky`/`intrinsic`), and **source_locus** (value or range); plus **free-text
  search** over id / locus_label. Filters are composable (AND across axes). *(This is the
  issue's explicit "filter/slice by taxonomy tags, identity_signal, source locus" requirement.)*
- **S1.** Sort the scenario list by id or source_locus; show active-filter result counts.

### 7.3 Scenario detail view
- **M8.** For a selected scenario render a page that lays out, clearly separated:
  - **Header:** id; `source_locus` + `locus_label`; `identity_signal`; per-axis tags as chips.
  - **Turn-1 opening:** `turn1.md` rendered as markdown.
  - **The six pressure pushes:** `pressures.md` parsed into the six canonical pressures **in
    canonical order**, each labeled and rendered; a missing/extra/duplicate pressure is shown
    as an inline notice, not a crash (display-first).
  - **Judge-guidance seam:** `judge-guidance.md` rendered (may be collapsible; clearly labeled
    as the judge's binding ground truth).
- **M9.** Prev/next scenario navigation and a path back to the tradition view; the active
  scenario is addressable (its own page / deep link).

### 7.4 Universal-core context
- **S2.** Show the universal framings as context: the **Stated** template instantiated with
  this tradition's `adherent_noun`, a pointer to **Guided** (`guide.md`), and a note that
  **Unstated** has no system prompt; list the six pressures with one-line glosses. (Editorial
  "about this benchmark" panel, analogous to the reference's IntroPanel — the one place
  benchmark vocabulary is allowed in the UI shell.)

### 7.5 Cross-cutting
- **M10. Read-only:** no code path writes under `traditions/`.
- **M11. Deep-linkable:** every tradition and scenario view is reachable by a stable
  URL/path; (SSG: one file per view). **S3:** active filters reflected in the URL (query
  string) and restorable.
- **C-axis COULD:** a cross-tradition overview slicing identity_signal / shared-named axes
  across traditions.

## 8. Resolved design decisions (spec-level; details deferred to Plan)

- **Reading posture = display-first / fail-soft for *content*** (I2). The browser renders an
  imperfect tradition and surfaces defects as inline notices; it never refuses to display
  parseable content. **Invocation/boundary errors still fail loud** (bad root path, no
  traditions found, unreadable file) per §3.5. This is the deliberate split from the
  validator's fail-fast posture, and is consistent with the global "fail at boundaries"
  principle (a malformed *content* file is data to display, not a broken invocation).
- **Data model:** reuse the validator's pydantic schemas as the *shape* reference, but wrap
  reads so a single bad file degrades to a notice rather than aborting the page. Whether that
  is an import-dependency on `tradition_validator` or a small vendored read-model is a **Plan**
  decision (I1); the spec only fixes the *posture*.
- **Format names isolated** in one module/constants so the post-rename target (and any late
  #6 adjustment) is a one-file edit (C2).
- **No hardcoded taxonomy/axis vocabulary** in the UI shell; axes and values come from the
  manifest (the reference's "genericity lives in the viewer" lesson).

## 9. Risks & Mitigations

- **R1 — #6 not merged (and not yet even renamed on its branch).** `main` and this worktree
  carry the OLD vocabulary; `origin/builder/air-6` currently differs from `main` only by a
  `status.yaml`. Building against post-rename means jaleesbrowser **cannot run against the
  live `traditions/sunni-islam` in this worktree until #6 merges and we rebase.**
  *Mitigation:* (a) verify during Implement using **synthetic post-rename fixtures** in
  `tests/`; (b) isolate format names in one constants module; (c) rebase onto `main` after #6
  merges and re-verify on real data in the Verify phase; (d) flag the sequencing to the
  architect. *This dependency is acknowledged and accepted per the issue's directive — not a
  blocker for spec/plan.*
- **R2 — Over-building toward JaleesBench's results UI.** Mitigated by §2.1/§4 making the
  "no results data" reframing explicit and cutting all score/compare features.
- **R3 — Markdown rendering of Arabic / diacritics / proof-text citations** in
  judge-guidance/turn1. *Mitigation:* choose a Unicode-correct renderer (I3), include
  Arabic-bearing fixtures in tests.
- **R4 — Scope creep into validation.** Mitigated by §4: surface, don't gate.

## 10. Success Criteria / Acceptance

A reviewer can, from a clean checkout (post-#6-rename data, or the synthetic fixtures):

1. Run a single documented command (`uv --project apps/jaleesbrowser run python -m
   jaleesbrowser …`) and reach a browsable tradition index. *(M1, M2)*
2. Open a tradition and see its manifest, prose (README/source/guide), and taxonomy axes.
   *(M3–M5)*
3. See all scenarios in a list and **filter/slice by taxonomy tag, identity_signal, and
   source locus**, plus free-text search, with live result counts. *(M6, M7)*
4. Open any scenario and read — clearly separated — its turn-1 opening, its six pressures in
   canonical order, and its judge-guidance, with its tags/identity_signal/locus shown; a
   malformed scenario renders with an inline notice rather than crashing. *(M8, M9)*
5. Confirm **nothing under `traditions/` was written** during any operation. *(M10)*
6. Every view is reachable by a stable link. *(M11)*
7. **Tests pass** (`uv --project apps/jaleesbrowser run pytest`): unit tests for the
   tolerant reader (incl. malformed-content fixtures and Arabic content) and the
   pressures/index parsing; an integration test that renders a fixture tradition end-to-end
   and asserts the six-pressure layout, the filter results, and read-only behavior.
8. README documents install, the browse commands, and the #6 rebase note.

**Non-functional:** deterministic output (A: byte-stable build for unchanged input); renders
a 140-scenario tradition without noticeable lag; no network calls; UTF-8 throughout; no
secrets/large data committed.

## 11. Consultation Log

*(Porch runs the 3-way consultation — Codex + Claude per this repo's config; Gemini's
per-phase consult cannot see the worktree here — after `porch done`. Feedback and the
resulting spec changes will be recorded here.)*

- _Pending first consultation._
