# Plan: multibrowser — browse & explore MultiBench traditions

## Metadata
- **ID**: plan-2026-06-24-multibrowser
- **Status**: draft
- **Specification**: [codev/specs/7-jaleesbrowser-browse-explore-m.md](../specs/7-jaleesbrowser-browse-explore-m.md)
- **Created**: 2026-06-24

## Executive Summary

Implements the spec's **Approach A**: a Python (`uv` / **Typer**) **static-site generator**
at `apps/multibrowser/` that reads `traditions/` **read-only** (post-rename #6 vocabulary)
and emits a self-contained, deep-linkable, offline static site for browsing traditions and
their scenarios — plus a `serve [--watch]` convenience. The package mirrors the sibling
`apps/tradition_validator/` flat-package layout.

The build splits into a **data layer** (tolerant, fail-soft reader → in-memory model) and a
**presentation layer** (Jinja2 render → static build → serve), so the data layer is fully
testable before any HTML exists. Verification uses **synthetic fixtures** for the
malformed/degradation cases (which cannot be produced from the read-only real data) **and the
two real post-rename traditions** — `sunni-islam` (140) and `eastern-christianity` (100) — now
that **#6 has merged (PR #9, commit 31620e2) and this branch is rebased onto `main`**, so we
plan/implement against real renamed data rather than a hypothesised format.

### Plan-level decisions (resolving the spec's deferred open questions)

- **I1 — data model: vendor a lean read-model; do NOT import `tradition_validator`.** The
  validator's pydantic schemas are `extra="forbid"` + `strict=True` (the wrong posture for
  display-first), and a path-dependency would couple two independent apps' build order (both
  reviewers flagged this). multibrowser defines its own **`dataclass`-based** read-models in
  `model.py` and reads tolerantly. It mirrors the validator's *shapes* and reuses its
  *safety ideas* (path containment, 5 MiB cap) by re-implementing them locally.
- **I3 — markdown: `markdown-it-py` (raw-HTML disabled) + `nh3` sanitizer.** Unicode-correct
  (Arabic/diacritics in the corpus), actively maintained, same family as the reference's
  `markdown-it`. `nh3` (ammonia) is the modern successor to the deprecated `bleach`.
- **`serve --watch` mechanism: `watchfiles`.** Rust-backed, tiny API. Base `serve` uses only
  stdlib `http.server`; `--watch` adds the rebuild loop.

**Dependencies** (`pyproject.toml`): `typer`, `jinja2`, `markdown-it-py`, `nh3`, `pyyaml`,
`watchfiles`. Dev: `pytest`. (No `pydantic` — dataclasses keep reads deliberately tolerant.)

### Scope updates folded in (architect-directed, 2026-06-24)

- **Rename `jaleesbrowser` → `multibrowser`** throughout (app / package / module / docs). The
  porch project slug and the spec/plan/review **filenames** stay
  `7-jaleesbrowser-browse-explore-m.md` (porch state is keyed to that slug; renaming the files
  would break porch's checks). The reference project's own browser stays `JaleesBench's jaleesbrowser`.
- **Results-ready (anticipating #8) — without building a results UI in v1** (spec §4.1). Three
  small, inert seams are threaded through the phases below, and nothing more:
  - **P1/P2 data model:** `Scenario.results: ScenarioResults | None = None` (`None` in v1);
    `ScenarioResults` a thin forward-declared shape.
  - **P2 loader seam:** `load_results(scenario) -> None` — the single boundary #8's output will
    feed; v1 returns `None`.
  - **P3 render reservation:** a `_results.html.j2` partial that renders nothing (or a subtle
    "no judgement results yet" placeholder) when `results is None`.
  - **Coordination:** the concrete `ScenarioResults` schema binds to #8's format (still
    speccing) — deferred to a #8-coordinated follow-up; v1 fixes only the seam shape. **No fake
    results in v1.**

## Success Metrics
- [ ] All spec §10 acceptance criteria met (browse index→tradition→scenario; filter/slice by
      tag/identity_signal/locus; six-pressure layout; judge-guidance + turn-1 rendered).
- [ ] **Read-only invariant**: tradition tree byte-identical before/after `build` and `serve`.
- [ ] **Display-first**: every §8 degradation row renders an inline HTML notice, never crashes.
- [ ] **Self-contained**: generated site has no external CDN/network references (offline-clean).
- [ ] **Deterministic**: rebuilding unchanged input yields byte-identical output.
- [ ] **Link integrity**: all generated inter-page links resolve.
- [ ] **Tradition prose** (README/source/guide) rendered, each degrading to a notice if absent (M4).
- [ ] **Results-ready seams present and inert**: `Scenario.results=None`, `load_results→None`,
      reserved render region empty — **no results UI in v1** (spec §4.1).
- [ ] Tests pass: `uv --project apps/multibrowser run pytest`; no reduction in coverage.
- [ ] README documents install, commands, the #6 rebase note, and the #8 results-ready seam.

## Phases (Machine Readable)

```json
{
  "phases": [
    {"id": "phase_1", "title": "Package scaffold + format constants + tolerant reader core (discovery + manifest + safe-read)"},
    {"id": "phase_2", "title": "Scenario & section reading: index/folder drift, scenario.yaml, pressures parsing, notices"},
    {"id": "phase_3", "title": "Rendering layer: Jinja2 templates + safe markdown pipeline (views as HTML strings)"},
    {"id": "phase_4", "title": "Static-site build command + client-side filter/search + determinism & link integrity"},
    {"id": "phase_5", "title": "serve [--watch], README, and end-to-end CLI polish"}
  ]
}
```

## Target package layout (built across phases)

```
apps/multibrowser/
  pyproject.toml                # uv package (Phase 1)
  README.md                     # Phase 5
  multibrowser/
    __init__.py  __main__.py    # Phase 1
    cli.py                      # Typer app; `build` (P4), `serve` (P5)
    constants.py                # post-rename names, PRESSURES, FRAMINGS, IDENTITY_SIGNALS, STATED_TEMPLATE (P1)
    model.py                    # dataclass read-models + Notice (P1/P2)
    safeio.py                   # path-containment + size-capped UTF-8 read (P1)
    loader.py                   # tolerant discover/load → model (P1 discovery+manifest, P2 scenarios)
    markdown.py                 # markdown-it-py + nh3 render-to-safe-HTML (P3)
    render.py                   # Jinja2 render of index/tradition/scenario (P3)
    filtering.py                # pure filter/sort/query-state fns + filter-index builder (P4) — Python-tested semantics
    site.py                     # build orchestration + page writing (P4)
    serve.py                    # http.server + optional watchfiles rebuild (P5)
    templates/                  # *.html.j2 (P3)
    assets/                     # styles.css (P3), filter.js (P4) — all local, no CDN
  tests/
    conftest.py  fixtures/      # synthetic post-rename traditions (good + malformed)
    test_safeio.py test_loader_discovery.py  # P1
    test_loader_scenarios.py                  # P2
    test_render.py                            # P3
    test_filtering.py  test_site.py           # P4
    test_cli.py                               # P5
```

## Phase Breakdown

### Phase 1: Package scaffold + format constants + tolerant reader core
**Dependencies**: None

#### Objectives
- Stand up the `apps/multibrowser/` uv package and the foundational data primitives:
  format constants, dataclass read-models, safe file I/O, tradition **discovery**, and
  **tolerant manifest** loading.

#### Deliverables
- [ ] `pyproject.toml` (deps above; `[project.scripts] multibrowser = "multibrowser.cli:app"`;
      pytest config) + `multibrowser/__init__.py`, `__main__.py`, a minimal `cli.py` Typer app
      (so `python -m multibrowser --help` works).
- [ ] `constants.py`: the **post-rename** names (`SCENARIOS_DIR="scenarios"`,
      `SCENARIO_META="scenario.yaml"`, `TURN1="turn1.md"`, `JUDGE="judge-guidance.md"`,
      `PRESSURES_FILE="pressures.md"`, `INDEX="scenarios/index.json"`,
      `ID_PATTERN_KEY="scenario_id_pattern"`), plus `PRESSURES` (6, canonical order),
      `FRAMINGS`, `IDENTITY_SIGNALS`, `STATED_TEMPLATE`, `MAX_FILE_BYTES=5*1024*1024`,
      `normalize_heading()` (trim → lowercase → spaces/hyphens → `_`, matching the validator).
      **All format names live here only** (kept isolated for future-proofing; #6 is already
      merged, so these now match real data — verified: `index.json` inner key is `scenarios`,
      manifest key is `scenario_id_pattern`).
- [ ] `model.py`: `Notice(severity, scope, where, message)`, `TaxonomyAxis`, `Manifest`,
      `Tradition` (manifest + **prose: README/source/guide (text|None + notices)** + scenarios +
      aggregated notices), placeholder `Scenario` (filled in P2) including the **results-ready**
      `results: ScenarioResults | None = None` field, plus a thin forward-declared
      `ScenarioResults` shape (unpopulated in v1; spec §4.1).
- [ ] `safeio.py`: `read_text(path, root)` → returns `(text|None, Notice|None)`: rejects
      symlink/`..` escapes outside `root`, enforces `MAX_FILE_BYTES`, UTF-8 only — fail-soft
      to a `Notice`, never a traceback. `load_yaml`/`load_json` wrappers (yaml.safe_load).
- [ ] `loader.py`: `discover(root)` globs `traditions/*/tradition.yaml`; `load_manifest()`
      tolerantly parses the manifest into `Manifest` (unknown keys → notice, not rejection;
      missing required → notice + stub); `load_prose()` reads the tradition-level prose
      **`README.md` / `source.md` / `guide.md`** via `safeio`, each **display-first**: a
      missing / empty / non-UTF-8 / oversized prose file degrades to a `Notice` on the
      `Tradition`, never an abort (spec M4 + §8 tradition-scope rows).
- [ ] `tests/fixtures/`: one **good** post-rename tradition (small, ~3 scenarios, includes
      Arabic content) + malformed manifest variants + a **missing/empty prose** variant (e.g.
      absent `source.md`); `tests/test_safeio.py`, `tests/test_loader_discovery.py` (incl.
      prose-degradation → notice, no exception).

#### Implementation Details
- Mirror `tradition_validator` package conventions (flat package, `__main__`, Typer in `cli.py`).
- `safeio` re-implements the validator's `_within_root` containment and size cap locally
  (decision I1 — no cross-app import).
- Tolerant manifest: parse to dict; map known keys to `Manifest`; collect unknown/missing as
  `Notice`s on the tradition; never raise on content.

#### Acceptance Criteria
- [ ] `python -m multibrowser --help` runs.
- [ ] `discover()` finds the fixture tradition(s); a bad/missing manifest yields a stub +
      notice (no exception); a missing/empty tradition prose file (README/source/guide) yields
      a `Notice`, not an exception.
- [ ] `safeio` rejects a symlink-escape and an oversized file with a located notice;
      round-trips UTF-8 incl. Arabic.
- [ ] All Phase-1 tests pass.

#### Test Plan
- **Unit**: `safeio` containment/size/UTF-8; `discover` globbing; manifest tolerance (unknown
  key, missing required, non-UTF-8 manifest).
- **Integration**: none yet (no rendering).
- **Manual**: `python -m multibrowser --help`.

#### Rollback Strategy
Revert the phase commit; nothing else depends on it yet.

#### Risks
- **Risk**: over-coupling to validator internals. **Mitigation**: vendor locally (I1); only
  the *idea* is reused.

---

### Phase 2: Scenario & section reading (tolerant) — full content model
**Dependencies**: Phase 1

#### Objectives
- Complete the data layer: load the scenario set with **index↔folder drift** handling, the
  tolerant `scenario.yaml`, the prose sections, and **pressures parsing** — all producing
  the §8 notices.

#### Deliverables
- [ ] `loader.py`: `load_index()` (`scenarios/index.json`, tolerant; missing/invalid →
      folder-glob fallback + notice); scenario-set assembly = **union** of index + `scenarios/*/`,
      **index order then orphans id-sorted**; **orphan** (folder ∉ index) and **ghost** (index
      ∉ folder) each get a notice.
- [ ] `load_scenario()`: tolerant `scenario.yaml` (tags/identity_signal/source_locus/locus_label;
      unknown axis/value → render-but-flag); read `turn1.md` / `judge-guidance.md` (section
      notice if missing/empty/non-UTF-8/oversized).
- [ ] `parse_pressures()`: split `pressures.md` on `## ` headings, `normalize_heading`, map to
      the 6 canonical pressures **in canonical order**; missing/extra/duplicate/unrecognized →
      notice; content before first `##` ignored.
- [ ] Complete `Scenario` model (id, tags, source_locus, locus_label, identity_signal, turn1,
      judge_guidance, pressures{canonical→text|None}, notices, **`results=None`**).
- [ ] **Results seam (inert):** `load_results(scenario) -> ScenarioResults | None` returning
      **`None`** in v1 — the single boundary #8's output will later feed (spec §4.1);
      `Scenario.results` is populated from it (always `None` in v1). Nothing else reads results.
- [ ] Fixtures: orphan, ghost, missing/extra pressure, non-UTF-8 section, oversized file,
      unknown tag, Arabic judge-guidance; `tests/test_loader_scenarios.py`.

#### Implementation Details
- One public entry, e.g. `load_tradition(path, root) -> Tradition` (manifest + **prose** +
  scenarios + aggregated notices), and `load_all(root) -> list[Tradition]`. `Scenario.results`
  is filled from the inert `load_results` seam (always `None` in v1).
- Pressures map keeps canonical order regardless of file order; `None` value ⇒ render a notice
  in P3.

#### Acceptance Criteria
- [ ] The good fixture loads with **zero** notices; each malformed fixture loads with exactly
      the expected notice(s) and never raises.
- [ ] Drift fixtures produce the documented union/ordering with orphan/ghost notices.
- [ ] `parse_pressures` returns all six keys (missing → `None` + notice), canonical order.
- [ ] All Phase-2 tests pass; coverage not reduced.

#### Test Plan
- **Unit**: index fallback; union/order; orphan/ghost; per-section degradation; pressures
  normalization (`## False authority` / `false-authority` / `false_authority` all map);
  unknown-tag flagging.
- **Integration**: `load_tradition` on the good fixture → full populated model.
- **Manual**: load the fixture in a REPL, inspect notices.

#### Rollback Strategy
Revert the phase commit; Phase 1 remains intact and tested.

#### Risks
- **Risk**: pressures heading edge cases. **Mitigation**: reuse the validator's normalization
  rule; table-driven tests over heading variants.

---

### Phase 3: Rendering layer — Jinja2 templates + safe markdown
**Dependencies**: Phase 2

#### Objectives
- Turn a loaded `Tradition`/`Scenario` into **HTML strings**: the tradition index, a tradition
  view, and a scenario view — with safe markdown and inline-notice rendering. No file output
  or client JS yet (Phase 4).

#### Deliverables
- [ ] `markdown.py`: `render_markdown(text) -> safe_html` via `markdown-it-py` (raw HTML
      disabled) piped through `nh3` (allow-list). Unicode/Arabic preserved.
- [ ] `render.py`: `render_index(traditions)`, `render_tradition(t)`, `render_scenario(t, s,
      prev, next)` returning HTML strings via Jinja2 (`autoescape=True`).
- [ ] `templates/`: `base.html.j2`, `index.html.j2`, `tradition.html.j2`, `scenario.html.j2`,
      `_notice.html.j2`, `_framings.html.j2`, **`_results.html.j2`**. Scenario template lays out
      header (id, locus, identity_signal, tag chips), **turn-1**, **six pressures in canonical
      order**, **judge-guidance** (collapsible), and the **reserved results region** —
      `_results.html.j2`, which renders **nothing** (or a subtle "no judgement results yet"
      placeholder) when `scenario.results is None` (always, in v1) and is the slot #8's
      scores/bands/verdicts will fill (spec §4.1). Tradition template: manifest header, prose
      (README/source/guide, each degrading to its notice if absent), taxonomy axes, scenario
      table. **Stub-tradition rendering:** when the manifest is invalid/missing, the tradition
      page still renders — a top-of-page notice, the scenario list from folders/index, and
      manifest-derived UI (taxonomy filters) **skipped with a notice** (spec §8 tradition row).
      Index: tradition cards. `_framings.html.j2`: Stated template instantiated with
      `adherent_noun`, Guided pointer, Unstated note, six-pressure glosses (S2).
- [ ] `assets/styles.css` (local; notice styling = visually-distinct warning block).
- [ ] `tests/test_render.py`.

#### Implementation Details
- A `Notice` renders via `_notice.html.j2` as a visible warning block (spec definition).
- Tag chips/filters read axes **from the manifest** (no hardcoded vocabulary).
- Markdown sanitized centrally so no template bypasses it; everything else autoescaped.

#### Acceptance Criteria
- [ ] Scenario HTML contains all six pressure labels in canonical order; a `None` pressure
      renders a notice block, not a blank.
- [ ] A `<script>`-bearing markdown fixture renders **inert** (sanitized); a `{{`-bearing
      manifest field is escaped (autoescape).
- [ ] Notices render as visible HTML warning blocks.
- [ ] Index/tradition/scenario render without error for the good fixture and for malformed
      fixtures (notices shown).
- [ ] **Stub-tradition**: an invalid-manifest fixture still renders a tradition page (top
      notice + scenario list + taxonomy-UI-skipped notice), no crash.
- [ ] **Reserved results region** renders empty (or the placeholder) for every v1 scenario
      (`results is None`); no scores/bands/verdicts markup is emitted in v1.
- [ ] All Phase-3 tests pass.

#### Test Plan
- **Unit**: `render_markdown` sanitization + Arabic round-trip; each renderer's structure
  (assert presence of labels/sections/chips).
- **Integration**: render a full fixture tradition's index+tradition+all scenarios to strings.
- **Manual**: write one rendered scenario to a temp file, eyeball in a browser.

#### Rollback Strategy
Revert the phase commit; data layer (P1/P2) unaffected.

#### Risks
- **Risk**: sanitizer strips legitimate content (e.g. Arabic, footnote markup).
  **Mitigation**: allow-list tuned + Arabic/citation fixtures asserting content survives.

---

### Phase 4: Static-site build + client-side filter/search
**Dependencies**: Phase 3

#### Objectives
- `multibrowser build --out DIR`: write the full static site (index + per-tradition +
  per-scenario pages + assets) and an embedded **filter-index**, with the filter/sort/
  query-state **semantics implemented as pure, automatically-tested Python** and the client JS
  as a thin applier. Guarantee determinism, link-integrity, and read-only.

#### Deliverables
- [ ] **`filtering.py` — the authoritative filter/sort/query-state semantics as pure Python
      functions** (this resolves the iter-2 "client behavior must be *automatically* tested"
      gap; Codex offered "a Python-side reference implementation checked against generated
      filter-index cases" as an acceptable path — this is it):
  - `build_filter_index(tradition) -> dict`: the per-tradition data the site embeds (per
    scenario: per-axis tag membership, `identity_signal`, `source_locus`, lowercased
    `search_text`). Deterministic (sorted keys/order).
  - `apply_selection(index, selection) -> list[id]`: **OR-within-axis, AND-across-axes**, plus
    identity_signal, `source_locus` range, and free-text — the single source of truth for the
    spec's filter semantics.
  - `sort_ids(index, key) -> list[id]`: by `id` or `source_locus` (S1).
  - `encode_selection` / `decode_selection`: Selection ⇄ query string, round-trippable and
    **fail-soft** to defaults on bad input (S3).
- [ ] `assets/filter.js`: a **thin applier** of the embedded index that mirrors
      `apply_selection` / `sort_ids` / `decode_selection` over the precomputed membership — so
      the JS surface stays minimal and the *semantics* live in the Python-tested reference. (No
      JS test toolchain is added; the JS mirrors a documented, Python-verified contract.)
      OR-within/AND-across tag filters, identity_signal, `source_locus` range (min/max inputs),
      free-text, sort, live result counts; active filters+sort reflected in the query string,
      fail-soft restore. No framework, no CDN.
- [ ] `site.py`: orchestrate output paths (stable scheme: `index.html`,
      `<tradition>/index.html`, `<tradition>/<scenario_id>.html`), write pages, copy `assets/`,
      embed each tradition's `build_filter_index(...)` output, **safely serialized** (`</`
      escaped). Deterministic: sorted keys, stable ordering, no timestamps. **Writes only under
      `--out`.**
- [ ] `cli.py`: `build(traditions_root=Path("traditions"), out=Path("dist"))` Typer command;
      fail-loud on invalid root / no traditions / unwritable out (invocation class).
- [ ] `tests/test_filtering.py` (**exhaustive, automated**) + `tests/test_site.py`.

#### Implementation Details
- **Suggested intra-phase order** (this is the densest phase): output-path scheme →
  page-write orchestration → filter-index JSON → `filter.js` (filters + **sort** + search) →
  CLI `build` wiring → tests.
- Prev/next computed in **default declared order** (P2 order) for stable static links (M9).
- **Sort (S1)** by `id`/`source_locus` is a client-side reordering of the filtered set; the
  static page order (prev/next) is unaffected.
- **Filtering of incomplete rows (ghost + stub-tradition) — keeps rendered list ≡ filtered
  results ≡ counts:** `build_filter_index` emits an entry for **every rendered row**, including
  **ghost** (index-only, no folder) and stub-tradition rows, with **null/empty** metadata
  (`tags={}`, `identity_signal=None`, `source_locus=None`, `search_text=id`). In
  `apply_selection`, a row with missing metadata **cannot satisfy a positive predicate**: any
  active tag-axis (OR-within), identity_signal, or `source_locus`-range filter **excludes** it
  (it matches none); with **no active filter** (or a free-text query matching its id) it
  appears. `sort_ids` always orders by `id`; for `source_locus`, `None` sorts **last**
  (deterministic). Because both the counts and the rendered filtered list derive from
  `apply_selection` over the same index, they cannot diverge. **Stub-tradition** (invalid
  manifest → no declared axes): the tag-axis filter UI is skipped with a notice, but
  identity_signal / locus / free-text / sort still operate over each scenario's own
  `scenario.yaml` (independent of the manifest). `test_filtering.py` covers a ghost row and a
  no-axes (stub) tradition explicitly.
- Link integrity: collect all emitted hrefs, assert each resolves to an emitted file.
- Read-only: snapshot-hash the traditions tree before/after `build`, assert identical.

#### Acceptance Criteria
- [ ] `build` on the good fixture emits index + tradition + one page per scenario; **all
      inter-page links resolve**.
- [ ] Re-running `build` on unchanged input is **byte-identical** (determinism).
- [ ] Tradition tree **unchanged** after build (snapshot invariant).
- [ ] No emitted file references an external CDN/URL.
- [ ] **Filter/sort/query-state semantics are automatically tested in `filtering.py`** —
      `apply_selection` (OR-within/AND-across, identity_signal, locus-range, free-text),
      `sort_ids`, and `encode∘decode` round-trip are covered by `test_filtering.py` against
      generated cases over both real axis shapes; **no spec-required behavior rests on a manual
      check.** The embedded index is the same `build_filter_index` output the tests exercise.
- [ ] All Phase-4 tests pass.

#### Test Plan
- **Unit (automated, primary)**: `test_filtering.py` — exhaustive `apply_selection` /
  `sort_ids` / `encode∘decode` over generated selections on both traditions' axis shapes,
  including OR-within/AND-across, locus-range edges, free-text, malformed-query→defaults, **and
  incomplete rows (a ghost row + a no-axes stub tradition): excluded by any active positive
  filter, present when unfiltered, `None` locus sorts last**.
- **Unit**: output-path scheme; determinism (build twice, diff).
- **Integration**: full build of fixture + the two real traditions → link integrity +
  read-only snapshot + no-CDN scan.
- **Manual (confirmatory only, not the test of record)**: open `dist/index.html` via `file://`,
  exercise filters/search/deep-links to confirm the JS applier matches the Python reference.

#### Rollback Strategy
Revert the phase commit; P1–P3 (data + render-to-string) remain usable and tested.

#### Risks
- **Risk**: client JS filter logic drifts from the spec's OR/AND semantics.
  **Mitigation**: the semantics live in the **Python-tested `filtering.py` reference**; the JS
  is a thin applier of its precomputed membership over a documented contract; keep JS logic
  minimal so drift surface is tiny.
- **Risk**: non-determinism from dict/set ordering. **Mitigation**: sort everything emitted.

---

### Phase 5: `serve [--watch]`, README, end-to-end CLI polish
**Dependencies**: Phase 4

#### Objectives
- Add the `serve` convenience (build + local `http.server`, optional `--watch` rebuild),
  finalize the README, and round out CLI ergonomics/tests.

#### Deliverables
- [ ] `serve.py`: build then serve `--out` over stdlib `http.server` on a chosen port;
      `--watch` re-runs `build` on changes under the traditions root via `watchfiles`.
      Serving is read-only over the built dir; **never writes under `traditions/`**.
- [ ] `cli.py`: `serve(traditions_root, out, port, watch=False)` Typer command.
- [ ] `README.md`: install (`uv sync`), `build`/`serve` usage from repo root
      (`uv --project apps/multibrowser run python -m multibrowser …`), the filter/slice
      feature summary, and the **#6 rebase note** (built against post-rename vocab; run against
      real `traditions/` only after #6 merges + rebase).
- [ ] `tests/test_cli.py`: `--help` for all commands; `build` smoke via Typer `CliRunner`;
      `serve` smoke (build path) asserting pages exist + read-only snapshot invariant; bad-root
      fails loud (non-zero exit).

#### Implementation Details
- `--watch` loop isolated so the base `serve` has no hard `watchfiles` runtime cost when off.
- Reuse Phase-4 `build`; `serve` adds no new rendering logic.

#### Acceptance Criteria
- [ ] `serve` (no watch) builds and serves; a fetched tradition/scenario page returns expected
      content (via test client or a localhost request in-test).
- [ ] Bad invocation (missing root) exits non-zero with a clear message.
- [ ] README commands are accurate and copy-pasteable.
- [ ] Full suite green: `uv --project apps/multibrowser run pytest`.

#### Test Plan
- **Unit**: CLI arg wiring; watch-loop guard.
- **Integration**: `CliRunner` build+serve smoke; read-only invariant on the serve path.
- **Manual**: `… serve` and browse locally (real-user-path check before calling done).

#### Rollback Strategy
Revert the phase commit; `build` (P4) remains the shippable core.

#### Risks
- **Risk**: `watchfiles` flakiness in CI. **Mitigation**: keep `--watch` untested-in-CI or
  test the rebuild function directly (not the OS watcher); base `serve` is the tested path.

## Dependency Map
```
Phase 1 (reader core) ──→ Phase 2 (scenarios/notices) ──→ Phase 3 (render) ──→ Phase 4 (build) ──→ Phase 5 (serve + README)
```
Strictly linear: each phase builds on the prior and is independently committable/testable.

## Resource Requirements
- **Environment**: Python ≥3.11 + `uv` (as `apps/tradition_validator`). No services, DB, or
  network. **Infrastructure**: none (static output). **External systems**: none.

## Integration Points
- **Internal**: reads `traditions/<id>/` (post-rename format) read-only; conceptually parallel
  to `apps/tradition_validator` but does **not** import it (I1). No other coupling.

## Risk Analysis
### Technical Risks
| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| ~~#6 not merged~~ — **RESOLVED**: #6 merged (PR #9, `31620e2`) + follow-ups (#10); branch **rebased onto `main`** | done | M | Real post-rename data confirmed on disk (`scenarios/`, `scenario.yaml`, `turn1.md`, `scenario_id_pattern`, `index.json` key `scenarios`) and matches `constants.py`; build/implement against real data + the renamed validator |
| ~~`scenario.md`→`turn1.md` least-obvious rename~~ — **confirmed on real data** (`scenarios/<id>/turn1.md` exists) | done | — | `constants.py` already targets `turn1.md` |
| #8 result schema still speccing; multibrowser must consume it later | M | M | v1 fixes only the seam shape (optional `results` slot + `load_results` boundary + reserved region); defer field-level schema binding to a #8-coordinated follow-up; **no fake results in v1** |
| Over-building toward a results UI | L | M | Spec §2.1/§4 reframing; no score/compare code anywhere |
| Markdown sanitizer strips Arabic/citations | M | M | Allow-list tuned; Arabic/citation fixtures assert survival |
| Client-side filter logic drift | M | L | Semantics live in the **Python-tested `filtering.py`** reference; JS is a thin applier of its precomputed membership over a documented contract — the test-of-record is **automated**, not manual |
| Non-deterministic output | M | L | Sort all emitted structures; build-twice determinism test |

### Schedule Risks
N/A — progress measured by completed phases, not time (per protocol).

## Validation Checkpoints
1. **After Phase 2**: data layer loads the good fixture clean and every malformed fixture with
   exactly its expected notices (no exceptions).
2. **After Phase 4**: full static build — link integrity, determinism, read-only snapshot,
   no-CDN — all green on the fixture.
3. **Before "done" (Phase 5)**: real-user path — `serve` and browse locally; full suite green;
   confirm the results-ready seams are present and **inert** (`results=None`, empty reserved region).
4. **During Implement (real data — #6 already merged + rebased)**: run `build`/`serve` against
   the real `traditions/sunni-islam` (140) **and** `traditions/eastern-christianity` (100,
   different axes: `passions`/`virtues`/`economia`/`register`) — confirms multi-tradition
   discovery, no-hardcoded-axes, the 140/100-scenario render + filter, and read-only. The
   Verify phase re-confirms on the integrated `main`.

## Monitoring and Observability
N/A — a static-site generator / local CLI. "Observability" = the inline notices surfaced in
the rendered site and clear non-zero exits on invocation errors.

## Documentation Updates Required
- [ ] `apps/multibrowser/README.md` (Phase 5).
- [ ] Consider a one-line pointer from `traditions/README.md` / `apps/README.md` to the browser
      (Review phase, if warranted).
- [ ] Arch/lessons hot-tier docs via the `update-arch-docs` skill (Review phase) if a durable
      system-shape fact emerges (e.g. "the browser reads display-first, the validator fail-fast").

## Post-Implementation Tasks
- [ ] Verify-phase rebase onto `main` + real-data run (above).
- [ ] (COULD, out of v1) GitHub Pages deploy workflow; light/dark theme; cross-tradition view.

## Expert Review

**Plan iteration 1 (2026-06-24) — Codex: REQUEST_CHANGES · Claude: APPROVE.** Both verified the
plan against the codebase and called the phase decomposition, the data/presentation split, and
the I1/I3 decisions sound. Claude found no blockers; Codex raised three concrete coverage gaps —
all accepted and folded in:

- **Tradition prose (README/source/guide) loading/degradation was unassigned (M4).** → Added
  `load_prose()` to Phase 1 loader, prose fields on `Tradition`, a missing-prose fixture, and
  acceptance/test coverage (display-first degradation).
- **S1 sorting (by id / source_locus) not planned.** → Added explicit sort to Phase 4
  `filter.js` deliverable, implementation details, and acceptance/test.
- **Stub-tradition-on-invalid-manifest rendering only implicit.** → Made explicit in the Phase 3
  templates deliverable (top notice + scenario list + taxonomy-UI-skipped notice) with an
  acceptance criterion + test.

Claude's non-blocking notes also folded in: `source_locus` range UI = min/max numeric inputs; a
suggested intra-phase ordering for the dense Phase 4; the `watchfiles` Rust-wheel note (already
mitigated by keeping `--watch` off the tested path).

**Plan Adjustments (architect-directed, same revision):** app renamed `jaleesbrowser` →
`multibrowser`; results posture moved from "cut" to "results-ready" — three inert seams
(`Scenario.results=None`, `load_results→None`, reserved `_results.html.j2`) threaded through
P1–P3, anticipating #8, with **no results UI built in v1**.

**Plan iteration 2 (2026-06-24) — Codex: REQUEST_CHANGES (one point) · Claude: APPROVE.** Claude
confirmed all iter-1 gaps resolved and every spec requirement covered. Codex's sole remaining
point: Phase 4's filter/query-state testing was "unit-tested where feasible / documented manual
check" — too weak for a spec-required acceptance path. **Resolved** by extracting the
filter/sort/query-state semantics into a pure-Python **`filtering.py`** (the authoritative,
exhaustively `test_filtering.py`-covered reference — exactly Codex's suggested "Python-side
reference checked against generated filter-index cases"), with the client JS reduced to a thin
applier of its precomputed membership. No spec-required behavior now rests on a manual check.

**Real-data rebase (2026-06-24):** #6 merged on `main` (PR #9 `31620e2` + #10) mid-Plan; per
the architect, **rebased this branch onto `main`** so plan/implement run against real renamed
data. Verified on disk that the format matches `constants.py` (`scenarios/`, `scenario.yaml`,
`turn1.md`, `scenario_id_pattern`, `index.json` key `scenarios`). R1 (the top risk) is resolved;
a **second real tradition** `eastern-christianity` (100 scenarios, axes `passions`/`virtues`/
`economia`/`register`) now exercises multi-tradition discovery + no-hardcoded-axes for real.

## Approval
- [ ] Expert AI Consultation Complete
- [ ] Human plan-approval gate

## Change Log
| Date | Change | Reason | Author |
|------|--------|--------|--------|
| 2026-06-24 | Initial plan | Spec 7 approved | builder spir-7 |
| 2026-06-24 | Plan iter-1 review folded in (Codex REQUEST_CHANGES / Claude APPROVE): prose loading, S1 sort, stub-tradition rendering + minor notes | Consultation feedback | builder spir-7 |
| 2026-06-24 | Rename → `multibrowser`; results posture → results-ready (inert seams for #8) | Architect-directed | builder spir-7 |
| 2026-06-24 | Plan iter-2: added `filtering.py` (Python-tested filter/sort/query-state semantics) resolving Codex's "client behavior must be automatically tested" gap | Consultation feedback | builder spir-7 |
| 2026-06-24 | #6 merged → **rebased branch onto `main`**; R1 resolved; now verifying against 2 real traditions (sunni-islam 140 + eastern-christianity 100) | Architect-directed | builder spir-7 |

## Notes
- **Phases ship as git commits within a single PR** (per the issue's PR strategy), not as
  separate PRs; the PR opens during/after Phase 5 unless the architect requests an earlier one.
- The `#6` dependency is **now resolved**: #6 merged (PR #9, commit `31620e2`) + follow-ups
  (#10), and this branch is **rebased onto `main`**. Real data is post-rename and matches
  `constants.py`; format names remain isolated there for future-proofing. There are now **two**
  real traditions to verify against (`sunni-islam` 140; `eastern-christianity` 100).
- **#8 (judging) coordination:** v1 ships only the results seam (optional `results` slot +
  `load_results` boundary + reserved render region), all inert. The concrete `ScenarioResults`
  schema is a follow-up bound to #8's output once its format stabilizes — tracked, not built in
  v1. A coordination note to the #8 effort (via the architect) is sent so the seam matches #8's
  eventual shape.
