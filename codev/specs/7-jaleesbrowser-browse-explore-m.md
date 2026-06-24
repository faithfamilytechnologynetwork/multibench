# Spec 7: multibrowser — browse & explore MultiBench traditions

| | |
|---|---|
| **Issue** | #7 |
| **Protocol** | SPIR |
| **Status** | Spec-approved 2026-06-24; **amended post-approval** (architect-directed — see §11): app renamed `jaleesbrowser`→`multibrowser`; results reframed "cut"→"anticipated/additive (#8)". |
| **App path** | `apps/multibrowser/` |
| **Depends on** | #6 (probe→scenario rename, in-flight) — see Risks |

## 1. Summary

Build `apps/multibrowser/` — a **read-only browser/explorer for MultiBench traditions and
their scenarios**. A user can navigate a tradition, read each scenario (the turn-1 opening,
the six pressure pushes, the judge-guidance), see the manifest/taxonomy metadata, and
**filter/slice** the scenario set by taxonomy tags, `identity_signal`, and source locus.

The worked reference is **JaleesBench's `jaleesbrowser`** (github.com/iaser-ai/jaleesbench):
a static, zero-install, deep-linkable explorer. We adapt its *browsing/viewer spirit* to a
different subject (see §2.1): MultiBench has, **today**, no collected model results to
compare — so **v1 browses the authored corpus**, not a benchmark run. Judgement results
(per-scenario scores / bands / verdicts) are coming from the **judging workflow (#8, in
parallel)**; v1 does **not** build a results UI, but its data model and page structure
**reserve a clean, additive extension point** so #8's output slots in later without a
rewrite (§4 / §4.1).

## 2. Problem Analysis

### 2.1 The reference, and how MultiBench differs (load-bearing)

JaleesBench's `jaleesbrowser` is a Vite/React static SPA on GitHub Pages whose entire job is
to compare **model-vs-model RESULTS**: pick Model A and Model B, a pressure and a framing,
and read their two responses side by side with per-judge verdicts and band scores. It is fed
by a Python `export_web.py` that pre-computes a score matrix + per-probe gzip shards.

**MultiBench #7's v1 is not that — yet.** Today MultiBench has only the **authored tradition
format** — `traditions/<id>/` — and no collected model responses, judgments, or scores. The
judging workflow **(#8) is being built in parallel** and **will** produce per-scenario
judgement results (scores / bands / verdicts, anchored to each scenario's `judge-guidance.md`).
So the posture is **"corpus now, results-ready"**:

- **v1 browses the authored content and its metadata** — the catalog → drill-in explorer,
  rich markdown prose, taxonomy-driven filter/slice, deep-linkable views, and the
  static/zero-install/deterministic build — all adapted from the reference.
- **v1 does NOT build a results UI.** JaleesBench's score-matrix / model-selectors /
  verdict-bands / shard machinery is **deferred**, not designed-out: there is no data to
  populate it until #8 lands.
- **But the design anticipates results additively.** The data model carries an optional,
  unpopulated per-scenario `results` slot; the scenario page reserves a clearly-marked region
  where scores/bands/verdicts will render; and a small **`ResultsSource` seam** (a no-op
  returning "none" in v1) is the single place #8's output gets wired in. When #8 ships, the
  results layer slots in **without a rewrite** (§4.1).

This dual framing is the most important design fact in this spec. A reviewer who assumes
"clone JaleesBench's results browser" will over-build a UI with no data; a reviewer who reads
"results are out of scope" too literally will paint the data model into a corner that forces a
rewrite when #8 lands. **v1 = corpus browser; structure = results-ready.**

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

### 2.4 The data multibrowser consumes (POST-RENAME format)

Per the issue, the spec targets the **post-rename vocabulary** landing in #6. The mapping
from the format on `main` today (old) to what multibrowser reads (new):

| Concept | OLD (on `main` today) | NEW (target — #6) |
|---|---|---|
| Per-scenario dir | `probes/<PROBE_ID>/` | `scenarios/<SCENARIO_ID>/` |
| Index file | `probes/index.json` (`{schema_version, probes:[…]}`) | `scenarios/index.json` (`{schema_version, scenarios:[…]}`) |
| Per-scenario metadata | `probe.yaml` | `scenario.yaml` |
| Turn-1 prose | `scenario.md` | `turn1.md` |
| Manifest id-pattern key | `probe_id_pattern` | `scenario_id_pattern` |
| Judge seam | `judge-guidance.md` | `judge-guidance.md` (unchanged) |
| Pressure pushes | `pressures.md` | `pressures.md` (unchanged) |

Files multibrowser reads per tradition (all UTF-8):

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
  `good_cause`, `flattery`, `personal_appeal`. (Throughout, an **"inline notice"** means a
  visually distinct warning block rendered *into the HTML page*, never a console log.) In
  `pressures.md` each is a `## ` heading,
  normalized (trim → lowercase → spaces/hyphens→`_`); content before the first `##` is
  intro/ignored.
- **Taxonomies** are per-tradition tag axes (e.g. Sunni Islam: `pillars` applies_to
  `scenario`, `hearts` applies_to `response`), each with a declared `values` set. The browser
  reads axes from the manifest and uses them to build filters — it must **not** hardcode any
  axis name or value (Sunni Islam is one instance; other traditions declare their own).

### 2.5 Assumptions

- The dataset is small and local: one tradition ≈ 140 scenarios of small markdown files;
  there are a handful of traditions. No DB, pagination-at-scale, or streaming is needed.
- multibrowser reads the live files under `traditions/` (a path argument); it does not
  require a pre-computed export the way JaleesBench does.
- Authored markdown is semi-trusted (repo content), but rendering still sanitizes/escapes as
  defense-in-depth, and never executes embedded code.

## 3. Constraints (firm — from the issue; do not relitigate in the spec)

The issue has no formal `## Baked Decisions` heading, but states these as firm directives;
they are treated as fixed. The **delivery approach** is *explicitly left open* for this spec +
3-way consultation to decide (§5).

1. **Read-only.** multibrowser MUST NOT create, modify, move, or delete anything under
   `traditions/`. It only reads.
2. **Python conventions.** Python + `uv`; **Typer** for any CLI (per repo + global prefs).
   No `src/` import prefix; run via `python -m`.
3. **Location.** The app lives at `apps/multibrowser/` (its own uv package, like
   `apps/tradition_validator/`).
4. **Post-rename vocabulary.** Spec and build against `scenarios/` / `scenario.yaml` /
   `turn1.md` / `scenario_id_pattern` / `scenarios/index.json`. Rebase onto `main` after #6
   merges (§9 Risks).
5. **No fallbacks / fail-loud at the boundaries** (global dev principle): when *invoked*
   wrongly (bad path, missing tradition) fail clearly. Distinct from *display* tolerance —
   see the resolved open question §6/§8 on display-first reading of imperfect content.

## 4. Out of scope

- **A results UI / results rendering — DEFERRED to a later spec, not designed-out.** v1 does
  not build model-response views, scoring, judge verdicts-of-models, band ladders,
  model-vs-model comparison, or a score matrix — there is no data until **#8** lands. But per
  §2.1 / §4.1 the data model and page structure **reserve an additive extension point** for
  per-scenario judgement results; this is the deliberate difference from "ignore results
  entirely." (Building the actual results UI is the later spec's job.)
- **Running the benchmark / judging workflow** (collection, judging, normalization) — that is
  #8's job; multibrowser only *consumes* #8's eventual output, additively.
- **Authoring or editing** traditions/scenarios (that is `create-tradition` + the validator).
- **Validation as a gate** — multibrowser is not a second validator; it may *surface* obvious
  problems inline (e.g. "missing pressure: flattery") but it does not replace
  `tradition_validator` and does not exit-fail on content defects.
- **Multi-language / RTL** (traditions are single-language; a nice-to-have, §6).
- **Auth, multi-user, a database, write-back, server-side persistence.**

### 4.1 Results-ready extension point (anticipating #8)

The judging workflow (#8) is speccing in parallel; multibrowser must consume its output
**additively** later. v1 builds exactly three small, inert seams — and nothing more:

1. **Data model:** `Scenario` carries an optional `results: ScenarioResults | None`, **`None`
   in v1** (no results data exists). `ScenarioResults` is a thin forward-declared shape — not
   populated, and not rendered with real data, in v1.
2. **Loader seam:** a single `ResultsSource` boundary (e.g. `load_results(scenario) -> None` in
   v1) is the **only** place #8's output is read. When #8 ships, this one function changes;
   nothing else in the loader does. (Mirrors the reference's praised `DataSource` seam.)
3. **Render reservation:** the scenario template includes a clearly-marked, currently-empty
   results region (a partial that renders nothing — or a subtle "no judgement results yet"
   placeholder — when `results is None`). When data exists, that region renders scores / bands
   / verdicts beside the `judge-guidance` seam they are anchored to.

**Coordination with #8 (open, tracked).** The concrete `ScenarioResults` schema is **not fixed
in this spec** — it binds to #8's result format, which is still being specced. multibrowser
commits only to the *seam shape* (optional per-scenario slot + single load boundary + reserved
render region); the field-level schema binding is a **follow-up** once #8's schema stabilizes
(Verify / next spec, not v1). v1 ships with the seam present and returning `None`. This keeps
v1 honest (no fake results) while guaranteeing the later integration is purely additive.

## 5. Solution Exploration (delivery approach — the open decision)

All approaches share the same **core** (a tolerant reader/model over the post-rename format,
reusing the validator's pydantic schemas where strictness is acceptable) and differ only in
the **presentation/runtime shell**. The decision is which shell to build for v1.

### Approach A — Python static-site generator (Typer `build`/`serve`) — **RECOMMENDED**

A Typer CLI that reads `traditions/` and renders a **self-contained static site** (server-
side-generated HTML via Jinja2; one page per tradition and per scenario; a small embedded
`index.json` + vanilla-JS for client-side filter/search; no JS framework). `multibrowser
build --out dist/` emits the site; `multibrowser serve` builds + serves it locally
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

`multibrowser serve` runs a small server that reads `traditions/` live; filtering is
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
every firm constraint (Python/uv/Typer, read-only, `apps/multibrowser/`), reproduces the
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
  `models.py`, or vendor a lean read-model in multibrowser? *Lean toward: reuse the pydantic
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
- **M6.** Render the **scenario list** as a table/list with columns: id, `locus_label`,
  `source_locus`, `identity_signal`, and per-axis tags. The list is the **union** of
  `scenarios/index.json` entries and the `scenarios/*/` folders, **ordered by `index.json`**
  (the tradition's declared order) with any **orphan folders** (present on disk, absent from
  the index) appended in id-sorted order. Divergence is surfaced, not fatal (display-first,
  §8): an **orphan** (folder ∉ index) renders with an inline notice; a **ghost** (index entry
  with no folder) renders as a stub row carrying an inline notice. The **folder** is
  authoritative for content; the **index** is authoritative for declared order.
- **M7. Filter/slice** the scenario list by: each **taxonomy tag** (per axis), **identity_signal**
  (`clean`/`leaky`/`intrinsic`), and **source_locus** (value or range); plus **free-text
  search** over id / locus_label. **Filter semantics: OR within a single axis** (a scenario
  matches if it carries *any* selected value of that axis), **AND across axes** (it must match
  every axis that has an active selection); free-text search ANDs with the rest. *(This is the
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
  scenario is addressable (its own page / deep link). **Prev/next follows the tradition's
  default declared order** (the M6 order: `index.json`, then orphan folders) so each static
  scenario page has stable, deterministic neighbors; filtered/sorted-view navigation is a
  client-side enhancement layered on top and does not change the canonical page links.

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
  parseable content. This is the deliberate split from the validator's fail-fast posture.

- **Degradation scope — what fails loud vs. degrades to a notice** (resolves the Codex/Claude
  fail-soft-vs-fail-loud question). Failures degrade at the **smallest enclosing unit**;
  **only invocation-level failures abort the process** (non-zero exit). A *content* file that
  is unreadable, non-UTF-8, oversized, or malformed is **data to display as a notice**, never
  a process abort:

  | Failure | Class | Behavior |
  |---|---|---|
  | Bad/missing root path; root has **no** `traditions/*/tradition.yaml`; output dir not writable | **Invocation** | Fail loud, non-zero exit, clear message. |
  | `tradition.yaml` missing / invalid / schema-violating | **Tradition** | Render a tradition **stub page** with a top-of-page notice; still list scenarios from folders/index with whatever metadata is parseable; skip manifest-derived UI (taxonomy filters) with a notice. Do **not** abort the build. |
  | `scenarios/index.json` missing / invalid | **Tradition** | Fall back to folder globbing for the scenario set, with a notice; declared order is then id-sorted. |
  | `index.json` ↔ folder divergence (orphan/ghost) | **Scenario** | Union + per-row inline notice (M6). |
  | `turn1.md` / `judge-guidance.md` / `pressures.md` missing, empty, non-UTF-8, or oversized | **Section** | Render the scenario page; that section shows an inline notice in place of content. |
  | `pressures.md` missing / extra / duplicate / unrecognized `## ` heading | **Section** | Render the recognized pressures in canonical order; flag the missing/extra ones with an inline notice. |
  | `scenario.yaml` invalid / unknown tag axis or value | **Scenario** | Render the page with whatever parsed; flag the offending field; an unknown tag is shown but marked. |

- **Data model:** reuse the validator's pydantic schemas as the *shape* reference, but wrap
  reads so a single bad file degrades to a notice rather than aborting the page (the validator
  is `extra="forbid"` + `strict=True`, so a tolerant wrapper or a separate lenient read-model
  is required — not direct strict reuse). Import-dependency on `tradition_validator` vs. a
  small vendored read-model is a **Plan** decision (I1); the spec fixes only the *posture*.

- **Security / safe rendering** (resolves Codex #5 / Claude path-containment & CDN notes):
  - **Path containment + size cap.** multibrowser **replicates the validator's containment
    guard** — reject symlinks and `..` escapes outside the tradition root — and the
    `MAX_FILE_BYTES` (5 MiB) read cap; an oversized/escaping file is a located notice, not a
    traceback or a read outside the tree.
  - **Output escaping.** Template rendering uses **autoescape on**; all authored markdown is
    rendered through a sanitizing pipeline (raw HTML off + sanitizer) so embedded HTML cannot
    inject script; any data embedded as JSON (the client filter index) is **safely
    serialized** (JSON-encoded, `</` escaped) and any query-string filter state restored
    client-side is **validated and escaped** before use — fail-soft to defaults on bad input.
  - **Self-contained output.** The generated site references **no external CDN/network**
    (CSS/JS/fonts are local); it works fully offline. (Non-functional, §10.)

- **Format names isolated** in one module/constants so the post-rename target — including the
  specific `scenario.md` → `turn1.md` file rename, which is the least obvious of #6's renames
  and must be confirmed against #6's actual implementation at rebase — is a one-file edit (C2).
- **No hardcoded taxonomy/axis vocabulary** in the UI shell; axes and values come from the
  manifest (the reference's "genericity lives in the viewer" lesson).

## 9. Risks & Mitigations

- **R1 — #6 vocabulary dependency — ✅ RESOLVED (2026-06-24).** #6 merged into `main` (PR #9,
  commit `31620e2`) plus follow-ups (#10); the new vocabulary (`scenarios/`, `scenario.yaml`,
  `turn1.md`, `scenario_id_pattern`, `index.json` key `scenarios`) is live for **both**
  `sunni-islam` (140) and the new `eastern-christianity` (100), and **this branch has been
  rebased onto `main`** — so multibrowser now plans/implements against real renamed data. The
  format on disk was verified to match the `constants.py` mapping. (Format names remain
  isolated in one constants module for future-proofing per C2.) *Originally the top risk;
  retained here for history.*
- **R2 — Over-building toward JaleesBench's results UI.** Mitigated by §2.1/§4 making the
  "no results data" reframing explicit and cutting all score/compare features.
- **R3 — Markdown rendering of Arabic / diacritics / proof-text citations** in
  judge-guidance/turn1. *Mitigation:* choose a Unicode-correct renderer (I3), include
  Arabic-bearing fixtures in tests.
- **R4 — Scope creep into validation.** Mitigated by §4: surface, don't gate.

## 10. Success Criteria / Acceptance

A reviewer can, from a clean checkout (post-#6-rename data, or the synthetic fixtures):

1. Run a single documented command (`uv --project apps/multibrowser run python -m
   multibrowser …`) and reach a browsable tradition index. *(M1, M2)*
2. Open a tradition and see its manifest, prose (README/source/guide), and taxonomy axes.
   *(M3–M5)*
3. See all scenarios in a list and **filter/slice by taxonomy tag, identity_signal, and
   source locus**, plus free-text search, with live result counts. *(M6, M7)*
4. Open any scenario and read — clearly separated — its turn-1 opening, its six pressures in
   canonical order, and its judge-guidance, with its tags/identity_signal/locus shown; a
   malformed scenario renders with an inline notice rather than crashing. *(M8, M9)*
5. Confirm **nothing under `traditions/` was written** during any operation — verified by a
   **fixture-tree snapshot invariant** (hash every path under the tradition root before and
   after both `build` and `serve`, assert identical). *(M10)*
6. Every view is reachable by a stable link, and **all generated inter-page links resolve**
   (tradition→scenario, prev/next, back-to-index) — no dangling links. *(M11)*
7. **Tests pass** (`uv --project apps/multibrowser run pytest`): unit tests for the
   tolerant reader (incl. malformed-content fixtures — missing/empty/non-UTF-8/oversized
   section files, an orphan and a ghost scenario, a missing/extra pressure, an unknown tag —
   and Arabic-bearing content) and the pressures/index parsing; an integration test that
   renders a fixture tradition end-to-end and asserts the six-pressure layout, the
   OR-within/AND-across filter results, **link integrity**, the **read-only tree-snapshot
   invariant**, and that **degraded content surfaces as inline notices** (per the §8 table)
   rather than crashing.
8. README documents install, the browse commands, and the #6 rebase note.

**Non-functional:** deterministic output (A: byte-stable build for unchanged input); the
generated site is **fully self-contained — no external CDN/network references** (works
offline); renders a 140-scenario tradition without noticeable lag; no network calls; UTF-8
throughout; no secrets/large data committed.

## 11. Consultation Log

*(Porch runs the consultation — Codex + Claude per this repo's config; Gemini's per-phase
consult cannot see the worktree here — after `porch done`.)*

### Post-approval amendments (2026-06-24, architect-directed — visible at plan-approval)

After the spec-approval gate, the architect relayed two user-directed changes. Both were
folded into this spec (and the plan) during the Plan phase; neither alters what v1 *builds*:

1. **Rename `jaleesbrowser` → `multibrowser`** (consistent with MultiBench naming). All app /
   package / module / doc references updated. *Note:* the porch project slug and the
   spec/plan/review **filenames** remain `7-jaleesbrowser-browse-explore-m.md` (porch state is
   keyed to that slug; renaming the files would break porch's checks and is not a manual edit).
   The reference project's own browser stays `JaleesBench's jaleesbrowser`.
2. **Results posture: "cut" → "anticipated/additive".** §2.1 and §4 reframed; new **§4.1**
   adds the results-ready extension point (optional `results` slot, `ResultsSource` seam,
   reserved render region) anticipating the judging workflow **#8**. v1 still builds **no**
   results UI; the change is structural readiness + #8 schema coordination, not new v1 surface.

*Re-gate judgment:* these do not change v1's build surface (rename is cosmetic; results
remain unbuilt in v1), so a separate spec re-gate is judged unnecessary — the amendments ride
to the human at the **plan-approval** gate. Flagged to the architect for confirmation.

### Iteration 1 (Codex: REQUEST_CHANGES · Claude: COMMENT — no blockers)

Both reviewers called the spec strong and well-bounded (the §2.1 "not JaleesBench's results
browser" reframing singled out as the highest-value content), and converged on the same set
of one-sentence sharpenings. All were incorporated:

| # | From | Change |
|---|---|---|
| 1 | Codex (substantive) | **Fail-soft vs fail-loud was internally inconsistent** (§3/§8 both listed "unreadable file"). Resolved with the §8 **degradation-scope table** classifying every failure as invocation (abort) / tradition / scenario / section, and fixing "unreadable content file" to degrade, not abort. |
| 2 | Codex + Claude | **`index.json` ↔ folder drift** policy: union, index-ordered, orphans appended; orphan/ghost each get an inline notice; folder authoritative for content, index for order (M6, §8). |
| 3 | Codex | **Prev/next order** defined: tradition default declared order for stable static pages (M9). |
| 4 | Codex | **Read-only made testable**: fixture-tree snapshot/hash invariant across `build` + `serve` (§10.5, §10.7). |
| 5 | Codex + Claude | **Output escaping / safe serialization**: autoescape, sanitized markdown, safe JSON embed, validated query-state restore (§8 Security). |
| 6 | Claude | **Filter semantics**: OR within axis, AND across axes (M7). |
| 7 | Claude | **Static link-integrity** test target (§10.6, §10.7). |
| 8 | Claude | **Path-containment + size-cap** explicitly required, not inherited-by-hope (§8 Security). |
| 9 | Claude | **Self-contained output** (no external CDN) as an explicit non-functional requirement (§10). |
| 10 | Claude | **"Inline notice"** defined once as a rendered HTML warning, not a console log (§2.4). |
| 11 | Claude | Noted that **`scenario.md`→`turn1.md`** is #6's least-obvious rename; flagged for confirmation at rebase (§8). |

Deferred to Plan (reviewers agreed these belong there): the `watchfiles`-vs-polling mechanism
for `serve --watch`; the import-dependency-vs-vendored-read-model choice (I1); the concrete
markdown-renderer + sanitizer pick (I3). Both reviewers endorsed Approach A over B and the
post-rename-with-synthetic-fixtures sequencing.
