# Plan: jaleesbrowser — browse & explore MultiBench traditions

## Metadata
- **ID**: plan-2026-06-24-jaleesbrowser
- **Status**: draft
- **Specification**: [codev/specs/7-jaleesbrowser-browse-explore-m.md](../specs/7-jaleesbrowser-browse-explore-m.md)
- **Created**: 2026-06-24

## Executive Summary

Implements the spec's **Approach A**: a Python (`uv` / **Typer**) **static-site generator**
at `apps/jaleesbrowser/` that reads `traditions/` **read-only** (post-rename #6 vocabulary)
and emits a self-contained, deep-linkable, offline static site for browsing traditions and
their scenarios — plus a `serve [--watch]` convenience. The package mirrors the sibling
`apps/tradition_validator/` flat-package layout.

The build splits into a **data layer** (tolerant, fail-soft reader → in-memory model) and a
**presentation layer** (Jinja2 render → static build → serve), so the data layer is fully
testable before any HTML exists. Verification throughout uses **synthetic post-rename
fixtures** (the #6 rename is not merged yet), and a final rebase-onto-`main` happens in the
Verify phase.

### Plan-level decisions (resolving the spec's deferred open questions)

- **I1 — data model: vendor a lean read-model; do NOT import `tradition_validator`.** The
  validator's pydantic schemas are `extra="forbid"` + `strict=True` (the wrong posture for
  display-first), and a path-dependency would couple two independent apps' build order (both
  reviewers flagged this). jaleesbrowser defines its own **`dataclass`-based** read-models in
  `model.py` and reads tolerantly. It mirrors the validator's *shapes* and reuses its
  *safety ideas* (path containment, 5 MiB cap) by re-implementing them locally.
- **I3 — markdown: `markdown-it-py` (raw-HTML disabled) + `nh3` sanitizer.** Unicode-correct
  (Arabic/diacritics in the corpus), actively maintained, same family as the reference's
  `markdown-it`. `nh3` (ammonia) is the modern successor to the deprecated `bleach`.
- **`serve --watch` mechanism: `watchfiles`.** Rust-backed, tiny API. Base `serve` uses only
  stdlib `http.server`; `--watch` adds the rebuild loop.

**Dependencies** (`pyproject.toml`): `typer`, `jinja2`, `markdown-it-py`, `nh3`, `pyyaml`,
`watchfiles`. Dev: `pytest`. (No `pydantic` — dataclasses keep reads deliberately tolerant.)

## Success Metrics
- [ ] All spec §10 acceptance criteria met (browse index→tradition→scenario; filter/slice by
      tag/identity_signal/locus; six-pressure layout; judge-guidance + turn-1 rendered).
- [ ] **Read-only invariant**: tradition tree byte-identical before/after `build` and `serve`.
- [ ] **Display-first**: every §8 degradation row renders an inline HTML notice, never crashes.
- [ ] **Self-contained**: generated site has no external CDN/network references (offline-clean).
- [ ] **Deterministic**: rebuilding unchanged input yields byte-identical output.
- [ ] **Link integrity**: all generated inter-page links resolve.
- [ ] Tests pass: `uv --project apps/jaleesbrowser run pytest`; no reduction in coverage.
- [ ] README documents install, commands, and the #6 rebase note.

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
apps/jaleesbrowser/
  pyproject.toml                # uv package (Phase 1)
  README.md                     # Phase 5
  jaleesbrowser/
    __init__.py  __main__.py    # Phase 1
    cli.py                      # Typer app; `build` (P4), `serve` (P5)
    constants.py                # post-rename names, PRESSURES, FRAMINGS, IDENTITY_SIGNALS, STATED_TEMPLATE (P1)
    model.py                    # dataclass read-models + Notice (P1/P2)
    safeio.py                   # path-containment + size-capped UTF-8 read (P1)
    loader.py                   # tolerant discover/load → model (P1 discovery+manifest, P2 scenarios)
    markdown.py                 # markdown-it-py + nh3 render-to-safe-HTML (P3)
    render.py                   # Jinja2 render of index/tradition/scenario (P3)
    site.py                     # build orchestration + filter-index JSON (P4)
    serve.py                    # http.server + optional watchfiles rebuild (P5)
    templates/                  # *.html.j2 (P3)
    assets/                     # styles.css (P3), filter.js (P4) — all local, no CDN
  tests/
    conftest.py  fixtures/      # synthetic post-rename traditions (good + malformed)
    test_safeio.py test_loader_discovery.py  # P1
    test_loader_scenarios.py                  # P2
    test_render.py                            # P3
    test_site.py                              # P4
    test_cli.py                               # P5
```

## Phase Breakdown

### Phase 1: Package scaffold + format constants + tolerant reader core
**Dependencies**: None

#### Objectives
- Stand up the `apps/jaleesbrowser/` uv package and the foundational data primitives:
  format constants, dataclass read-models, safe file I/O, tradition **discovery**, and
  **tolerant manifest** loading.

#### Deliverables
- [ ] `pyproject.toml` (deps above; `[project.scripts] jaleesbrowser = "jaleesbrowser.cli:app"`;
      pytest config) + `jaleesbrowser/__init__.py`, `__main__.py`, a minimal `cli.py` Typer app
      (so `python -m jaleesbrowser --help` works).
- [ ] `constants.py`: the **post-rename** names (`SCENARIOS_DIR="scenarios"`,
      `SCENARIO_META="scenario.yaml"`, `TURN1="turn1.md"`, `JUDGE="judge-guidance.md"`,
      `PRESSURES_FILE="pressures.md"`, `INDEX="scenarios/index.json"`,
      `ID_PATTERN_KEY="scenario_id_pattern"`), plus `PRESSURES` (6, canonical order),
      `FRAMINGS`, `IDENTITY_SIGNALS`, `STATED_TEMPLATE`, `MAX_FILE_BYTES=5*1024*1024`,
      `normalize_heading()`. **All format names live here only** (one-file edit at #6 rebase).
- [ ] `model.py`: `Notice(severity, scope, where, message)`, `TaxonomyAxis`, `Manifest`,
      `Tradition` (manifest + notices + scenarios), placeholder `Scenario` (filled in P2).
- [ ] `safeio.py`: `read_text(path, root)` → returns `(text|None, Notice|None)`: rejects
      symlink/`..` escapes outside `root`, enforces `MAX_FILE_BYTES`, UTF-8 only — fail-soft
      to a `Notice`, never a traceback. `load_yaml`/`load_json` wrappers (yaml.safe_load).
- [ ] `loader.py`: `discover(root)` globs `traditions/*/tradition.yaml`; `load_manifest()`
      tolerantly parses the manifest into `Manifest` (unknown keys → notice, not rejection;
      missing required → notice + stub).
- [ ] `tests/fixtures/`: one **good** post-rename tradition (small, ~3 scenarios, includes
      Arabic content) + malformed manifest variants; `tests/test_safeio.py`,
      `tests/test_loader_discovery.py`.

#### Implementation Details
- Mirror `tradition_validator` package conventions (flat package, `__main__`, Typer in `cli.py`).
- `safeio` re-implements the validator's `_within_root` containment and size cap locally
  (decision I1 — no cross-app import).
- Tolerant manifest: parse to dict; map known keys to `Manifest`; collect unknown/missing as
  `Notice`s on the tradition; never raise on content.

#### Acceptance Criteria
- [ ] `python -m jaleesbrowser --help` runs.
- [ ] `discover()` finds the fixture tradition(s); a bad/missing manifest yields a stub +
      notice (no exception).
- [ ] `safeio` rejects a symlink-escape and an oversized file with a located notice;
      round-trips UTF-8 incl. Arabic.
- [ ] All Phase-1 tests pass.

#### Test Plan
- **Unit**: `safeio` containment/size/UTF-8; `discover` globbing; manifest tolerance (unknown
  key, missing required, non-UTF-8 manifest).
- **Integration**: none yet (no rendering).
- **Manual**: `python -m jaleesbrowser --help`.

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
      judge_guidance, pressures{canonical→text|None}, notices).
- [ ] Fixtures: orphan, ghost, missing/extra pressure, non-UTF-8 section, oversized file,
      unknown tag, Arabic judge-guidance; `tests/test_loader_scenarios.py`.

#### Implementation Details
- One public entry, e.g. `load_tradition(path, root) -> Tradition` (manifest + scenarios +
  aggregated notices), and `load_all(root) -> list[Tradition]`.
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
      `_notice.html.j2`, `_framings.html.j2`. Scenario template lays out header (id, locus,
      identity_signal, tag chips), **turn-1**, **six pressures in canonical order**,
      **judge-guidance** (collapsible). Tradition template: manifest header, prose
      (README/source/guide), taxonomy axes, scenario table. Index: tradition cards.
      `_framings.html.j2`: Stated template instantiated with `adherent_noun`, Guided pointer,
      Unstated note, six-pressure glosses (S2).
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
- `jaleesbrowser build --out DIR`: write the full static site (index + per-tradition +
  per-scenario pages + assets), an embedded **filter-index JSON**, and **client-side
  filter/search** (OR-within-axis, AND-across-axes, free-text). Guarantee determinism,
  link-integrity, and read-only.

#### Deliverables
- [ ] `site.py`: orchestrate output paths (stable scheme: `index.html`,
      `<tradition>/index.html`, `<tradition>/<scenario_id>.html`), write pages, copy
      `assets/`, emit a per-tradition `filter-index.json` (scenarios × tags/identity_signal/
      locus/search-text), **safely serialized** (`</` escaped). Deterministic: sorted keys,
      stable ordering, no timestamps. **Writes only under `--out`.**
- [ ] `assets/filter.js`: vanilla JS reading the embedded index; OR-within/AND-across filters,
      identity_signal + locus-range filters, free-text search, live result counts; reflect
      active filters in the query string (S3), fail-soft restore. No framework, no CDN.
- [ ] `cli.py`: `build(traditions_root=Path("traditions"), out=Path("dist"))` Typer command;
      fail-loud on invalid root / no traditions / unwritable out (invocation class).
- [ ] `tests/test_site.py`.

#### Implementation Details
- Prev/next computed in **default declared order** (P2 order) for stable static links (M9).
- Link integrity: collect all emitted hrefs, assert each resolves to an emitted file.
- Read-only: snapshot-hash the traditions tree before/after `build`, assert identical.

#### Acceptance Criteria
- [ ] `build` on the good fixture emits index + tradition + one page per scenario; **all
      inter-page links resolve**.
- [ ] Re-running `build` on unchanged input is **byte-identical** (determinism).
- [ ] Tradition tree **unchanged** after build (snapshot invariant).
- [ ] No emitted file references an external CDN/URL.
- [ ] Filter-index JSON present and well-formed; (filter logic unit-tested where feasible, else
      asserted via the embedded data + a documented manual check).
- [ ] All Phase-4 tests pass.

#### Test Plan
- **Unit**: output-path scheme; filter-index construction (OR/AND membership precomputed or
  asserted); determinism (build twice, diff).
- **Integration**: full build of fixture → link integrity + read-only snapshot + no-CDN scan.
- **Manual**: open `dist/index.html` via `file://`, exercise filters/search/deep-links.

#### Rollback Strategy
Revert the phase commit; P1–P3 (data + render-to-string) remain usable and tested.

#### Risks
- **Risk**: client JS filter logic drifts from the spec's OR/AND semantics.
  **Mitigation**: precompute membership server-side into the index where possible; document
  and manually verify the JS path; keep logic minimal.
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
      (`uv --project apps/jaleesbrowser run python -m jaleesbrowser …`), the filter/slice
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
- [ ] Full suite green: `uv --project apps/jaleesbrowser run pytest`.

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
| #6 (probe→scenario rename) not merged; real data still old vocab | H | M | Build against post-rename; verify on synthetic fixtures; names isolated in `constants.py`; rebase + verify on real data in Verify phase |
| `scenario.md`→`turn1.md` is #6's least-obvious rename | M | M | Confirm against #6's actual impl at rebase; single-file fix in `constants.py` |
| Over-building toward a results UI | L | M | Spec §2.1/§4 reframing; no score/compare code anywhere |
| Markdown sanitizer strips Arabic/citations | M | M | Allow-list tuned; Arabic/citation fixtures assert survival |
| Client-side filter logic drift | M | L | Precompute membership server-side where feasible; minimal JS; manual verify |
| Non-deterministic output | M | L | Sort all emitted structures; build-twice determinism test |

### Schedule Risks
N/A — progress measured by completed phases, not time (per protocol).

## Validation Checkpoints
1. **After Phase 2**: data layer loads the good fixture clean and every malformed fixture with
   exactly its expected notices (no exceptions).
2. **After Phase 4**: full static build — link integrity, determinism, read-only snapshot,
   no-CDN — all green on the fixture.
3. **Before "done" (Phase 5)**: real-user path — `serve` and browse locally; full suite green.
4. **Verify phase (post-merge)**: rebase onto `main` after #6; run `build`/`serve` against the
   real `traditions/sunni-islam`; confirm the 140-scenario tradition renders + filters + stays
   read-only.

## Monitoring and Observability
N/A — a static-site generator / local CLI. "Observability" = the inline notices surfaced in
the rendered site and clear non-zero exits on invocation errors.

## Documentation Updates Required
- [ ] `apps/jaleesbrowser/README.md` (Phase 5).
- [ ] Consider a one-line pointer from `traditions/README.md` / `apps/README.md` to the browser
      (Review phase, if warranted).
- [ ] Arch/lessons hot-tier docs via the `update-arch-docs` skill (Review phase) if a durable
      system-shape fact emerges (e.g. "the browser reads display-first, the validator fail-fast").

## Post-Implementation Tasks
- [ ] Verify-phase rebase onto `main` + real-data run (above).
- [ ] (COULD, out of v1) GitHub Pages deploy workflow; light/dark theme; cross-tradition view.

## Expert Review
**Date**: (pending — porch runs Codex + Claude after `porch done`)
**Key Feedback**: _to be recorded._
**Plan Adjustments**: _to be recorded._

## Approval
- [ ] Expert AI Consultation Complete
- [ ] Human plan-approval gate

## Change Log
| Date | Change | Reason | Author |
|------|--------|--------|--------|
| 2026-06-24 | Initial plan | Spec 7 approved | builder spir-7 |

## Notes
- **Phases ship as git commits within a single PR** (per the issue's PR strategy), not as
  separate PRs; the PR opens during/after Phase 5 unless the architect requests an earlier one.
- The `#6` dependency is acknowledged and accepted per the issue's directive; it is the top
  risk and is handled by fixtures-now / rebase-in-Verify, with all format names isolated in
  `constants.py`.
