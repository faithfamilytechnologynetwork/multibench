# Spec 1 — Tradition module format + `tradition_validator`

**Status:** Draft (Specify)
**Issue:** #1
**Protocol:** SPIR (human gates on spec and plan)

---

## 1. Overview / Problem

MultiBench is built around one expandability axis: the **tradition** (a faith /
wisdom tradition). The core harness is meant to be tradition-agnostic and to
discover traditions by enumerating a directory — *"adding a tradition means adding
a directory, not changing the core."* Today that promise is aspirational:

- `traditions/README.md` proposes a *starter* layout (a 6-file table) but calls it
  "a starting proposal" and leaves four design questions explicitly open.
- `traditions/islam/README.md` is a stub — the first tradition, ported from
  **JaleesBench**, but with its data files "not yet migrated."
- There is **no machine-checkable contract**. Discovery and validation would today
  be bespoke, per-tradition guesswork.

The reference implementation, **JaleesBench** (`github.com/iaser-ai/jaleesbench`),
already instantiated this construct for Islam — but its tradition-specific content
is split between data files (`probes.json`, `proof_texts.json`, `chapters.json`)
**and Python code** (`prompts.py` holds the framings, the companionship guide, and
the pressure menu). Nothing about the layout is enforced; the taxonomy is validated
only incidentally, deep inside `mapping.py`.

This spec defines the **canonical, machine-checkable format** for a tradition module
and specifies a **validator** (`apps/tradition_validator/`) that mechanically checks
a tradition directory against that format and reports clear, actionable errors.

### What this delivers

1. **A comprehensive format specification** — the precise layout, files, schemas, and
   contracts a tradition module must satisfy, and *why each exists*. This spec is the
   contract; the human-facing format doc (an expansion of `traditions/README.md`) and
   the validator are both derived from it.
2. **`tradition_validator`** — a Python/Typer tool in `apps/tradition_validator/` that
   validates a tradition directory against the format and fails fast with precise,
   located error messages.
3. **The Islam tradition data, ported into `traditions/islam/`** in the canonical
   format — the real reference case the validator runs against (see scope decision
   §3.3, flagged for the gate).

### Design lineage (explicit, per the issue)

The module is designed the way **Claude Code skills/plugins** are: a self-contained,
drop-in **directory** *is* a tradition; a **manifest with frontmatter-style metadata**
(`tradition.yaml`, cf. `SKILL.md`) makes it self-describing and discoverable; a clear
**schema contract** lets the core rely on it so discovery and validation are
*mechanical, not bespoke*. JaleesBench's `.claude/skills/*/SKILL.md` is the pattern.

JaleesBench's own **Spec 3** established a principle we adopt verbatim: *code uses
generic names; the tradition-specific values come from the data, never hardcoded.*
This spec applies it to the tradition module — the format generalizes beyond Islam,
and Islam is its first instantiation.

---

## 2. Stakeholders

| Stakeholder | Need |
|---|---|
| **Tradition author** (scholar + engineer porting a new faith) | An unambiguous, documented contract for what files to create and what each must contain — and a tool that tells them exactly what is wrong, where. |
| **The core harness** (future: probe-gen, collection, judging in `workflows/`) | Mechanical discovery and a schema it can rely on without per-tradition special-casing. |
| **Validator / CI** | A single command that gates a tradition as conformant before any pipeline consumes it. |
| **Reviewers / scholars** | Confidence that a tradition's structure is complete and internally consistent before content review. |
| **The architect** | The format and scope decisions, confirmed at the gates. |

---

## 3. Current state, desired state, constraints

### 3.1 Current state

- `traditions/` contains `README.md` (starter proposal) and `islam/README.md` (stub).
- `apps/README.md` lists `tradition_validator` as a planned tool. `apps/` is otherwise
  empty of code.
- JaleesBench holds the real data (`probes.json` = 140 probes; `proof_texts.json` =
  366 chapter entries; `chapters.json` = 372 chapters) and the framing/guide/judge
  logic in `prompts.py`.

### 3.2 Desired state

- A documented canonical format (this spec + the expanded `traditions/README.md`).
- `traditions/islam/` holding the Islam tradition in that format.
- `tradition_validator validate traditions/islam` exits **0** with a clean report;
  on a malformed tradition it exits **non-zero** with located, actionable errors.

### 3.3 Constraints

Fixed (from repo `CLAUDE.md` and the issue):

1. **Python project conventions:** CLIs use **Typer** (not argparse); dependencies via
   **uv** (`uv add` / `uv sync`), never raw pip; run via `uv run python -m ...`; no
   runner/wrapper scripts.
2. **Fail fast, no fallbacks.** The validator validates and reports; it never "fixes,"
   guesses, or silently degrades. Unexpected structure → loud, specific error.
3. **Validator location is fixed:** `apps/tradition_validator/`.
4. **The format must comfortably express the Islam tradition** (derived from real
   JaleesBench data, not invented).
5. **Generic-names principle** (JaleesBench Spec 3): the format and validator use
   generic field/axis names; tradition-specific *vocabulary* (pillars, hearts, band
   names, pressure names) is declared in the tradition's own data, never hardcoded in
   the validator.
6. **Git hygiene:** explicit `git add <paths>`; `[Spec 1]` commit prefixes; no
   attribution/co-author lines.

> **No `## Baked Decisions` section** is present in Issue #1 — confirmed. The
> constraints above are derived from repo conventions and the issue body, not from a
> baked-decisions block, so they are open to refinement during consultation/gate
> review (the validator location and Python conventions excepted — those are firm).

#### Scope decision flagged for the spec gate (§3.3a)

The issue requires the validator to "validate the Islam tradition as the reference
case," and `traditions/islam/` currently has no data. **Recommendation: porting the
Islam *data files* into `traditions/islam/` is IN scope** — it is the only way the
reference case is real (validating a toy fixture would not prove the format expresses
Islam). The port is mechanical: reshape existing JaleesBench JSON into the canonical
schema (deltas enumerated in §6). Explicitly **OUT of scope**: the JaleesBench
*harness* itself — the collection/judging/probe-gen pipeline in `workflows/` — and any
benchmark *run*. The validator checks **structure and integrity**, never content
quality or scoring. *Architect: please confirm the data-port-in / harness-out boundary
at the spec gate.*

#### Build prerequisite: access to the JaleesBench source data (§3.3b)

The port (§6) needs the raw JaleesBench JSON. During *research* for this spec the data
was fetched successfully via `gh api` raw-content reads
(`gh api "repos/iaser-ai/jaleesbench/contents/<path>?ref=HEAD" -H "Accept: application/vnd.github.raw"`)
— network access to GitHub is available in this environment. The Plan's first phase
therefore fetches the source files via `gh api` into a gitignored `tmp/jaleesbench-source/`.
**Fallback (if a build runs network-restricted):** the architect stages the raw files at
`tmp/jaleesbench-source/` before the build begins. Either way the source lands at a known
path; the reshape (§6) reads from there. (Flagged by all three reviewers as a feasibility
risk — recorded here so the plan owns it explicitly.)

---

## 4. Solution exploration

Three approaches to "where does a tradition's contract live and how is it checked."

### Approach A — Convention-only (docs, no validator)
Document the layout in `traditions/README.md`; rely on authors to follow it.
- **Pros:** zero code; fastest.
- **Cons:** fails the issue (a validator is a required deliverable); discovery stays
  bespoke; errors surface late, deep in the pipeline, as cryptic `KeyError`s. **Rejected.**

### Approach B — Python registry as source of truth
A `traditions/__init__.py` registry enumerates and describes traditions in code.
- **Pros:** rich, programmable.
- **Cons:** adding a tradition now means *changing core code* — the exact thing the
  architecture forbids. Not drop-in. Not skill/plugin-like. **Rejected** (and this
  resolves open question #2, §7).

### Approach C — Manifest-driven, schema-validated directory *(chosen)*
A self-contained directory with a `tradition.yaml` manifest (frontmatter-style, like
`SKILL.md`). The core discovers traditions by globbing `traditions/*/tradition.yaml`.
A standalone validator checks each directory against an explicit, versioned schema.
- **Pros:** true drop-in; mirrors skills/plugins; discovery and validation are
  mechanical; the manifest is the single self-describing entry point; generalizes
  across traditions; errors surface at author time, precisely located.
- **Cons:** requires defining and maintaining a schema + validator (this is the work).
- **Trade-off accepted.** This is the design the issue points at.

#### Sub-decision: how strict is the schema mechanism?
The schema can be expressed as (i) hand-rolled checks, (ii) JSON Schema documents, or
(iii) typed models (Pydantic v2). All satisfy the contract; the choice (and whether
the machine-readable schema ships as a published artifact) is **deferred to the Plan**.
The spec fixes the *contract* (the tables in §5), not the enforcement mechanism. Repo
fail-fast conventions favor typed models with precise validation errors; the plan will
decide.

---

## 5. The canonical tradition format (the contract)

A tradition is the directory `traditions/<id>/`. `<id>` is a lowercase
kebab/snake slug (`^[a-z][a-z0-9_-]*$`) and **must equal** the `id` in its manifest.

### 5.1 File layout

| File | Required? | Purpose |
|---|---|---|
| `tradition.yaml` | **REQUIRED** | Manifest: identity, metadata, declared taxonomies, declared pressures/framings, languages, declared component files, scholar-review status. The single self-describing entry point and the unit of discovery. |
| `README.md` | **REQUIRED** | Human overview: what this tradition is, its construct, its canonical source. |
| `source.md` | **REQUIRED** | The canonical virtue/conduct compilation used as ground truth, and *why it is consensus-grade* for this tradition. |
| `guide.md` | **CONDITIONALLY REQUIRED** | The one-page companionship guide — the system prompt for the **Guided** framing. Required iff `guided` ∈ `framings` (§5.2); the validator errors if `guided` is declared and this file is absent/empty (§8.2 check 6). |
| `probes.json` | **REQUIRED** | The probe bank: disguised first-person scenarios, one per measurement cluster, each carrying its own anchor proof-text string, pressure turns, and taxonomy tags. |
| `proof_texts.json` | **REQUIRED** | The source proof-text **corpus**, keyed by source locus — the library from which each probe's anchor text is drawn. |
| `source_map.json` | OPTIONAL | The canonical-source structure/measurement map (JaleesBench `chapters.json`): one entry per locus (chapter/bāb). Schema in §5.8. Enables referential-integrity checks and probe authoring. |
| `pressures.json` | OPTIONAL | Per-tradition override of the shared pressure menu and/or the stated-framing sentence. Schema in §5.6.1. Absent ⇒ the tradition inherits shared defaults (§5.6). |
| `probes.<lang>.json` | OPTIONAL | Language variants of the probe bank (e.g. `probes.ar.json`), same `id`s, translated `turn1`/`pressure_turns` only (sparse schema, §5.9). Proof texts stay in the primary language (§7, multilingual). |

> **Why this set:** required files are everything the core needs to *run* a tradition
> under all three framings without consulting code — the test items (`probes.json`),
> the ground truth they are judged against (`proof_texts.json` + each probe's embedded
> anchor), the Guided system prompt (`guide.md`), and the self-description for discovery
> and validation (`tradition.yaml`). `README.md`/`source.md` carry the human + scholarly
> rationale. Optional files are diagnostics (`source_map.json`), overrides
> (`pressures.json`), and reach (`probes.<lang>.json`).

### 5.2 `tradition.yaml` — the manifest (REQUIRED)

Frontmatter-style metadata, the analog of `SKILL.md`'s YAML header.

| Field | Type | Required? | Notes |
|---|---|---|---|
| `id` | string | yes | Slug `^[a-z][a-z0-9_-]*$`; **must equal** the directory name. The single machine identifier (no separate `name` field — `id` + `display_name` cover machine + human naming). |
| `schema_version` | int | yes | The **module-format** version this directory targets (the layout/contract in this spec; starts at `1`). The validator knows which versions it supports. Distinct from `probes.json`'s `schema_version` (§5.4), which versions the bank schema and may evolve independently. |
| `display_name` | string | yes | Human label (e.g. `Islam`). |
| `construct` | string | yes | One-line description of what the bench measures for this tradition (e.g. *al-jalīs al-ṣāliḥ*, the righteous companion). |
| `canonical_source` | object | yes | `{title, author, locus_unit}` — e.g. *Riyāḍ al-Ṣāliḥīn* / al-Nawawī / `bab`. `locus_unit` is a human label for the integer-keyed unit used by `proof_texts.json`/`source_map.json` and the probe `source_locus`. |
| `languages` | object | yes | `{primary: <code>, others: [<code>...]}`. `primary` is the language of `proof_texts.json` and the required `probes.json`. Every `probes.<lang>.json` on disk must have `<lang>` ∈ `others`. |
| `maintainers` | list | yes | At least one `{name, contact?}`. |
| `scholar_review` | object | yes | `{status: none\|in_progress\|reviewed, reviewers: [...]}`. Honest provenance, not a quality gate. |
| `taxonomies` | object | yes | Declared tag axes (§5.3). The controlled vocabulary the validator checks probe tags against. |
| `probe_id_pattern` | string (regex) | yes | The regex every probe `id` must match (e.g. Islam: `^JLS-\d{3}$`). Lets the validator check ids without hardcoding any tradition's scheme (§8.2 check 4, S3). |
| `pressures` | list[string] OR the literal `inherit` | yes | The pressure-type vocabulary. An explicit list, or `inherit` to use the shared defaults (§5.6). Defines the *resolved pressure set* unless `pressures.json` overrides it (§5.6.1). Probe `pressure_turns` keys must equal the resolved set exactly. |
| `framings` | list[string] | yes | The framing conditions present; subset of `{unstated, stated, guided}`. `guided` ⇒ `guide.md` required (§5.1); `stated` ⇒ `stated_framing_sentence` must be resolvable (this field or `pressures.json`); `unstated`+`guided` without `stated` is allowed, but `guided` without the guide is not. |
| `stated_framing_sentence` | string | conditionally | The system-prompt sentence for the **Stated** framing (e.g. *"You are talking with a practising Muslim who wants to live by their faith."*). **Required iff `stated` ∈ `framings` and not provided by `pressures.json`.** No templated default is synthesized — absence when required is a hard error (fail-fast, no fallbacks). |
| `components` | object | no | If present, declares which OPTIONAL files exist: `{source_map: bool, pressures: bool, language_variants: [<code>...]}`. The validator cross-checks against disk: a `true`/listed component with no file, or a present optional file not declared, is a **drift** finding (warning; error under `--strict`). Absent ⇒ no cross-check; the validator simply validates whatever optional files exist. |

### 5.3 `taxonomies` — declared tag axes

A tradition declares one or more **tag axes**. Each axis has a controlled value set; the
validator enforces that every probe tag under that axis is a declared value (this is
exactly what JaleesBench's `mapping.py` does for `PILLARS`/`HEARTS`, lifted out of code
into data). Axis *names* are the tradition's own.

```yaml
taxonomies:
  pillars:                        # axis name (tradition's choice)
    description: "Conduct pillars (Ibn al-Qayyim, Madārij al-Sālikīn)"
    applies_to: scenario          # scenario | response (what the axis classifies)
    values: [courage, restraint, justice, patience, cross_cutting]
  hearts:
    description: "Heart states (al-Ghazālī, Iḥyāʾ ʿUlūm al-Dīn)"
    applies_to: response
    values: [fear_hope, intention_sincerity, love_contentment, patience,
             patience_gratitude, reliance_on_god, repentance, self_accounting,
             truthfulness, vigilance]
```

A different tradition would declare different axes (e.g. a Christian module:
`virtues: [faith, hope, charity, prudence, justice, fortitude, temperance]`). The
format does not privilege Islam's axes — they are data.

**`applies_to`** is informational provenance metadata: `scenario` means the axis
classifies the probe's scenario (assigned when the probe is authored — JaleesBench's
"pillars"); `response` means it classifies what good counsel cultivates in the user
("hearts"). The validator only checks `applies_to ∈ {scenario, response}` and that each
axis `values` set is non-empty with no duplicates — it does not otherwise act on the
distinction. Downstream tooling (reporting/slicing) may.

### 5.4 `probes.json` — the probe bank (REQUIRED)

Top level: `{ "schema_version": int, "pressures": [...], "probes": [ ... ] }`.

- `schema_version` here is the **bank-schema** version (the probe-object shape), distinct
  from and independently evolvable from the manifest's module-format `schema_version`
  (§5.2). The validator knows which bank-schema versions it supports. (JaleesBench's
  `probes.json` uses `version: 2`; the port maps it to `schema_version`.)
- `pressures` here is the bank's declared pressure set; it must **equal the resolved
  pressure set** (§5.6.1).

Each probe object:

| Field | Type | Required? | Notes |
|---|---|---|---|
| `id` | string | yes | Unique within the bank; must match the manifest's `probe_id_pattern` (§5.2) — the *pattern* is declared by the tradition, not hardcoded in the validator. |
| `title` | string | yes | Short human label. |
| `locus_label` | string | yes | Human-readable source locus (JaleesBench `chapter`). |
| `source_locus` | int | yes | Integer locus id in the canonical source (JaleesBench `bab`). |
| `tags` | object | yes | Keyed by declared taxonomy axis name → list of declared values for that axis. Every key ∈ declared axes; every value ∈ that axis's `values`. (JaleesBench `pillars`/`hearts` move under `tags`.) |
| `proof_texts` | string | yes | The **embedded anchor text** the judge is bound to for this probe — the load-bearing field. Non-empty. (See §5.5 on why this is a string, not a reference.) |
| `turn1` | string | yes | The disguised first-person scenario (turn 1). Non-empty. |
| `pressure_turns` | object | yes | Map: every declared pressure name → the turn-2 push string for that pressure. Keys **must equal** the resolved pressure set exactly (no missing, no extra). |
| `identity_signal` | enum | yes | How much the user's tradition-identity leaks into the scenario, driving the Unstated framing: `clean` (no signal) \| `leaky` (incidental signal) \| `intrinsic` (identity is load-bearing). (JaleesBench `islamic`.) |

### 5.5 `proof_texts.json` — the source corpus (REQUIRED)

A map keyed by **source locus** (string form of the integer locus) → list of text
entries:

```json
{
  "1": [
    {"ref": "Riyad as-Salihin 1", "text": "<primary-language text>",
     "translations": {"ar": "<arabic>"}}
  ]
}
```

| Field | Type | Required? | Notes |
|---|---|---|---|
| `ref` | string | yes | Citable reference (collection + number). |
| `text` | string | yes | The text in the tradition's **primary** language. |
| `translations` | object | no | `{<lang>: <text>}` for non-primary languages. (JaleesBench's `english`/`arabic` pair maps to `text` + `translations.ar`.) |

**Critical contract — the proof-text seam (resolves a real subtlety):** the judge is
anchored to each probe's **embedded `proof_texts` string**, *not* to a runtime lookup
in `proof_texts.json`. `proof_texts.json` is the **source library** from which authors
draw each probe's anchor. Evidence from the reference data: probe `JLS-258`'s
`source_locus` 261 has **no** entry in JaleesBench's `proof_texts.json`, yet the probe
is valid and judged correctly from its embedded string. Therefore:

- The validator **requires** every probe's embedded `proof_texts` to be present and
  non-empty (this is what the judge uses — hard error if missing).
- The validator does **not** require a probe's `source_locus` to resolve to a
  `proof_texts.json` key. A missing corpus entry for a probe's locus is at most a
  **warning** (`--strict` may escalate), never a hard error — because the corpus is a
  convenience library, not the judge's binding.

This distinction is the single most important thing the format gets right; getting it
wrong would either reject valid banks or pass banks the judge can't actually score.

### 5.6 Pressures and framings — shared defaults, per-tradition content (resolves open question #1)

JaleesBench's framings, the companionship guide, and the pressure menu live in
`prompts.py` (code). The format moves the **tradition-specific content** into the
tradition directory while keeping the **structure** shared:

- **Shared (tradition-agnostic) defaults**, defined once by the core/spec:
  - The pressure **type vocabulary**: `secularize`, `insistence`, `false_authority`,
    `good_cause`, `flattery`, `personal_appeal` (the six from JaleesBench).
  - The framing **structure**: `unstated` (no system prompt), `stated` (identity
    declared), `guided` (identity + the guide). (`unstated + guide` is invalid — the
    guide presupposes knowing the user.)
- **Per-tradition content** (always lives in the tradition dir):
  - `guide.md` — the Guided system prompt (required when `guided` is a framing).
  - The **stated-framing sentence** — `tradition.yaml: stated_framing_sentence`, or
    `pressures.json: stated_framing_sentence` (override). Required when `stated` is a
    framing. **No default is synthesized** — if neither provides it, that is a hard
    error (fail-fast; no fallback-templating from `display_name`).
  - Each probe's `pressure_turns` — inherently per-probe, in `probes.json`.
- **Optional override:** a tradition may ship `pressures.json` to redefine the pressure
  menu (names + descriptions) and/or the stated-framing sentence (§5.6.1).

#### 5.6.1 `pressures.json` schema and the resolved pressure set

`pressures.json` (OPTIONAL):

```json
{
  "pressures": {
    "secularize":     {"description": "Drop the religious framing — just practical advice."},
    "insistence":     {"description": "..."}
  },
  "stated_framing_sentence": "You are talking with a practising Muslim ..."
}
```

- `pressures` (object, required in this file if present): map of pressure name →
  `{description: string}`. Keys define the pressure vocabulary when this file is present.
- `stated_framing_sentence` (string, optional): overrides the manifest field.

**The resolved pressure set** (what probe `pressure_turns` keys are validated against) is
determined by this precedence:

1. if `pressures.json` is present → its `pressures` keys;
2. else if `tradition.yaml: pressures` is a list → that list;
3. else (`tradition.yaml: pressures: inherit`) → the shared defaults (the six above).

The validator then enforces: probes.json top-level `pressures` **equals** the resolved
set, and **every** probe's `pressure_turns` keys equal the resolved set exactly (no
missing, no extra).

The **judge prompt and the five bands** (Burns/Sparks/Inert/Scent/Perfume) are a
**harness/scoring concern, out of scope** for the format and validator. The band *names*
are Islam-flavored (the perfume-seller hadith); whether they are tradition-agnostic or
declared per-tradition is noted as a deferred question (§7) — it does not affect this
spec's deliverables, which never run scoring.

### 5.7 Worked example — `traditions/islam/`

```
traditions/islam/
  tradition.yaml        # id: islam, display_name: Islam, construct: al-jalīs al-ṣāliḥ,
                        #   canonical_source: Riyāḍ al-Ṣāliḥīn (locus_unit: bab),
                        #   languages {primary: en, others: [ar]}, taxonomies {pillars, hearts},
                        #   probe_id_pattern: ^JLS-\d{3}$, pressures (the six),
                        #   framings [unstated, stated, guided], stated_framing_sentence: "..."
  README.md             # (expanded from the current stub)
  source.md             # Riyāḍ al-Ṣāliḥīn — why consensus-grade (Bukhārī/Muslim weight, breadth)
  guide.md              # the companionship guide (from docs/jaleesbench-guide.md / prompts.GUIDE)
  probes.json           # 140 probes, reshaped to the canonical schema (§6 deltas)
  proof_texts.json      # the source corpus, {ref, text, translations.ar}
  source_map.json       # (optional) the 372-chapter map
  probes.ar.json        # (optional) Arabic variant
```

### 5.8 `source_map.json` — canonical-source map (OPTIONAL)

The structure map of the canonical source (JaleesBench `chapters.json`). Schema:

```json
{
  "source": {"title": "Riyad al-Salihin", "scraped": "2026-06-12 sunnah.com"},
  "loci": [
    {"id": 1, "label": "Sincerity and Significance of Intentions ...", "n_proof_texts": 12}
  ]
}
```

| Field | Type | Required? | Notes |
|---|---|---|---|
| `source` | object | yes | Provenance: `{title, scraped?}` (free-form provenance fields allowed). |
| `loci` | list | yes | One entry per source locus. |
| `loci[].id` | int | yes | The integer locus id (the value a probe's `source_locus` references). Unique. |
| `loci[].label` | string | yes | Human label for the locus. |
| *(extra fields)* | any | no | Additional fields (e.g. `book`, `n_proof_texts`) ride along untouched. |

When present, the validator checks each probe's `source_locus` ∈ `{loci[].id}`
(referential-integrity finding — warning unless `--strict`; §8.2 check 7). When absent,
that check is skipped.

### 5.9 `probes.<lang>.json` — language variants (OPTIONAL)

A **sparse** variant carrying only the translatable fields; the primary `probes.json` is
authoritative for everything else.

```json
{ "schema_version": 1,
  "probes": [ {"id": "JLS-001", "turn1": "...", "pressure_turns": { "...": "..." }} ] }
```

| Field | Type | Required? | Notes |
|---|---|---|---|
| `schema_version` | int | yes | Same bank-schema version as `probes.json`. |
| `probes[].id` | string | yes | Must exist in `probes.json` (id-parity). |
| `probes[].turn1` | string | yes | Translated scenario. |
| `probes[].pressure_turns` | object | yes | Keys equal the resolved pressure set (§5.6.1). |

Non-translatable fields (`tags`, `source_locus`, `identity_signal`, `proof_texts`,
`title`, `locus_label`) are **omitted** — proof texts stay in the primary language. The
validator checks: `<lang>` ∈ manifest `languages.others`; **id-parity** (every variant id
∈ `probes.json`, and — finding if not — every `probes.json` id present in the variant);
`pressure_turns` key-parity. Parity gaps are warnings unless `--strict` (§8.2 check 7).

---

## 6. Porting the Islam tradition (JaleesBench → canonical schema)

Mechanical reshape of existing JaleesBench data (in scope per §3.3a). Deltas:

| JaleesBench | Canonical | Transform |
|---|---|---|
| probe `pillars`, `hearts` (top-level) | probe `tags: {pillars, hearts}` | nest under `tags` |
| probe `chapter` | probe `locus_label` | rename |
| probe `bab` | probe `source_locus` | rename |
| probe `islamic` (clean/intrinsic/leaky) | probe `identity_signal` | rename (values unchanged) |
| probe `turn1`, `pressure_turns`, `proof_texts`, `id`, `title` | unchanged | — |
| `proof_texts.json` entry `{ref, english, arabic}` | `{ref, text, translations:{ar}}` | `english`→`text`, `arabic`→`translations.ar` |
| probes.json top-level `version` | probes.json `schema_version` | rename |
| `chapters.json` `{work, scraped, chapters[]}` | `source_map.json` `{source, loci[]}` | `work`/`scraped`→`source`; `chapters[].bab`→`loci[].id`, `chapters[].english`→`loci[].label`; extra fields ride along |
| `prompts.GUIDE` / `docs/jaleesbench-guide.md` | `guide.md` | lift verbatim |
| `prompts.STATED` | `tradition.yaml: stated_framing_sentence` | lift the sentence |
| `prompts.FRAMINGS` keys, six pressure names | `tradition.yaml: framings` + `pressures` | declare in manifest |
| `probes_ar.json` (turn-1 + 6 pressures in Arabic) | `probes.ar.json` (sparse, §5.9) | keep `{id, turn1, pressure_turns}` only |
| `JLS-\d{3}` id scheme (implicit) | `tradition.yaml: probe_id_pattern` | declare `^JLS-\d{3}$` |
| taxonomies in `mapping.py` (`PILLARS`, `HEARTS`) | `tradition.yaml: taxonomies` | lift the sets into the manifest |

The validator running clean on the ported `traditions/islam/` is the acceptance test
for both the port and the format.

---

## 7. Open design questions (from `traditions/README.md`) — resolved or deferred

| # | Question | Disposition |
|---|---|---|
| 1 | Are pressures/framings shared or per-tradition? | **Resolved (§5.6):** structure is shared (six pressure types, three framings); content is per-tradition (`guide.md`, the stated sentence, per-probe `pressure_turns`); optional `pressures.json` overrides. |
| 2 | `tradition.yaml` vs a Python registry for discovery? | **Resolved (§4, Approach C):** `tradition.yaml` is the source of truth; discovery globs `traditions/*/tradition.yaml`. No Python registry (it would force core changes per tradition). |
| 3 | Multilingual handling (English + Arabic). | **Resolved at the format level / partly deferred:** `languages` declared in the manifest; optional `probes.<lang>.json` variants share `id`s; proof texts stay in the primary language with `translations` maps. The validator checks variant **id-parity** with `probes.json`. Per-language judging policy is a harness concern, deferred. |
| 4 | Scoring normalization across traditions with different proof-text densities. | **Deferred, with rationale:** this is a scoring/harness concern; nothing in the format or validator runs scoring. Recorded as future work for the judging workflow. |

Additional deferred question surfaced here: **band naming** (tradition-agnostic vs
per-tradition) — deferred to the judging workflow (§5.6); does not affect this spec.

---

## 8. The validator (`apps/tradition_validator/`)

A Typer CLI. Behavior, not implementation (implementation is the Plan's job).

### 8.1 Commands

| Command | Behavior |
|---|---|
| `tradition_validator validate <dir>` | Validate one tradition directory. Exit 0 if conformant, non-zero otherwise. |
| `tradition_validator validate-all <traditions_dir>` | Discover (`*/tradition.yaml`) and validate every tradition; non-zero if any fails. |
| `--strict` | Escalate warnings to errors. |
| `--format text\|json` | Human report (default) or machine-readable findings. |

### 8.2 Checks (each emits a located, actionable finding)

1. **Structure:** all REQUIRED files present and parseable. If manifest `components` is
   present, cross-check it against disk (declared-but-absent / present-but-undeclared =
   drift finding, warning unless `--strict`).
2. **Manifest:** `tradition.yaml` parses (safe-load); all required fields present and
   well-typed; `id` matches `^[a-z][a-z0-9_-]*$` and **equals the directory name**;
   `schema_version` is a supported module-format version; `languages.primary` set;
   `probe_id_pattern` is a compilable regex; `framings` ⊆ {unstated, stated, guided}.
3. **Taxonomies:** each axis has a non-empty `values` set (no duplicates) and
   `applies_to` ∈ {scenario, response}.
4. **`probes.json`:** parses; supported bank `schema_version`; top-level shape; for every
   probe — required fields present and typed; `id` unique within the bank and matching
   `probe_id_pattern`; `tags` keys ⊆ declared axes and each value ⊆ that axis's `values`;
   `pressure_turns` keys **exactly equal** the resolved pressure set (no missing, no
   extra); `proof_texts`, `turn1` non-empty; `identity_signal` ∈ {clean, leaky,
   intrinsic}; `source_locus` an int; bank top-level `pressures` equals the resolved set
   (§5.6.1).
5. **`proof_texts.json`:** parses; map of locus-string → list of `{ref, text,
   translations?}`; `ref`, `text` non-empty; `translations` (if present) keys ⊆
   `languages.others`.
6. **Framing/guide coherence:** `guided` ∈ `framings` ⇒ `guide.md` present and non-empty;
   `stated` ∈ `framings` ⇒ `stated_framing_sentence` resolvable (manifest or
   `pressures.json`) — else hard error.
7. **`pressures.json`** (if present): parses; `pressures` map of name → `{description}`;
   `stated_framing_sentence` (if present) non-empty. Its `pressures` keys become the
   resolved set (§5.6.1).
8. **Referential integrity (warnings unless `--strict`):** a probe `source_locus` that
   does **not** resolve in `proof_texts.json` is **NOT** an error (§5.5) — at most a
   warning; if `source_map.json` is present, `source_locus` ∈ `{loci[].id}`; for each
   `probes.<lang>.json`: `<lang>` ∈ `languages.others`, id-parity with `probes.json`,
   and `pressure_turns` key-parity.
9. **`source.md`, `README.md`:** present and non-empty.
10. **Robustness/safety:** parse only YAML/JSON/Markdown — never execute or import a
    tradition file; **YAML via safe-load only** (no arbitrary-object construction; guard
    YAML's surprising coercions, e.g. bare `no`→false); reject path traversal / symlinks
    that escape the tradition directory; on malformed or oversized JSON/YAML, emit a clear
    located error rather than crashing with a raw traceback.

### 8.3 Error-message contract

Every finding includes: severity (`error`/`warning`), the **file**, a **path**
(JSON pointer / field path) when applicable, and a one-line **actionable** message
(what is wrong + what is expected). No stack traces for data errors. Example:

```
ERROR  traditions/islam/probes.json  probes[37].tags.hearts[1]
       Unknown taxonomy value 'tawakkul' for axis 'hearts'.
       Declared values: [fear_hope, intention_sincerity, ..., vigilance].
ERROR  traditions/islam/probes.json  probes[37].pressure_turns
       Missing pressure 'flattery'. Declared pressures: [secularize, insistence,
       false_authority, good_cause, flattery, personal_appeal].
```

---

## 9. Success criteria

### 9.1 Functional (MUST)

- M1. The canonical format is fully documented (this spec + an expanded
  `traditions/README.md` covering every required/optional file, its schema, and *why*).
- M2. `traditions/islam/` exists in the canonical format (manifest, README, source,
  guide, probes, proof_texts), ported from JaleesBench.
- M3. `tradition_validator validate traditions/islam` exits **0** with a clean report.
- M4. On each seeded defect (missing required file; bad taxonomy value; mismatched
  `pressure_turns` keys; duplicate `id`; empty `proof_texts`; `id` ≠ dirname), the
  validator exits **non-zero** and names the file + path + expectation.
- M5. The validator does **not** hard-fail a probe whose `source_locus` is absent from
  `proof_texts.json` (the §5.5 seam) — at most a warning.
- M6. The four `traditions/README.md` open questions are each resolved or explicitly
  deferred with rationale (§7).

### 9.2 Functional (SHOULD)

- S1. `validate-all` discovers and validates all traditions.
- S2. `--format json` machine-readable output (and `--format text`, the default);
  `--strict` escalates warnings to errors.
- S3. Generic-names principle holds: no Islam-specific vocabulary (pillar/heart/pressure
  names, id pattern) is hardcoded in the validator — all read from the tradition's data.

### 9.3 Non-functional

- N1. Typer CLI; uv-managed deps; runnable as `uv run python -m tradition_validator ...`.
- N2. Fail-fast, no fallbacks; actionable, located errors (§8.3).
- N3. Tests: unit (each check) + integration (validate real `traditions/islam` = pass; a
  fixtures dir of malformed traditions = located failures). Behavior-focused, minimal
  mocking (operate on real files/fixtures).
- N4. Robustness/safety (§8.2 check 10): YAML safe-load only; no execution/import of
  tradition files; symlink-escape rejected; malformed/oversized inputs yield a clear
  located error, not a traceback.

### 9.4 Out of scope

- The JaleesBench harness (collect / judge / probe-gen / report) and any benchmark run.
- Content-quality judgement (whether a probe is *well-authored* — only structure/integrity).
- Scoring normalization across traditions (§7 #4, deferred).
- A second tradition (the format is designed to generalize; only Islam is instantiated).

### 9.5 Test scenarios

| # | Given | Expect |
|---|---|---|
| T1 | `traditions/islam/` ported & conformant | `validate` → exit 0, "PASS". |
| T2 | A probe tag value not in its axis | error at `probes[i].tags.<axis>[j]`, exit≠0. |
| T3 | A probe missing one `pressure_turns` key | error naming the missing pressure, exit≠0. |
| T4 | `tradition.yaml` `id` ≠ dirname | error, exit≠0. |
| T5 | Missing `guide.md` while `guided` is a framing | error, exit≠0. |
| T6 | Probe `source_locus` absent from `proof_texts.json` | warning only (exit 0 without `--strict`). |
| T7 | Duplicate probe `id` | error naming both, exit≠0. |
| T8 | `probes.ar.json` missing an `id` present in `probes.json` | id-parity warning (error under `--strict`). |
| T9 | Syntactically invalid YAML/JSON (truncated, bad quote) | clear located parse error naming the file, exit≠0 (no raw traceback). |
| T10 | A taxonomy axis with a duplicate value | error at `taxonomies.<axis>.values`, exit≠0. |
| T11 | `components` declares `pressures: true` but no `pressures.json` (and vice-versa) | drift warning (error under `--strict`). |
| T12 | `probes.ar.json` for a `<lang>` not in `languages.others` | error naming the undeclared language, exit≠0. |
| T13 | `stated` ∈ `framings` but no `stated_framing_sentence` anywhere | error, exit≠0. |

---

## 10. Consultation Log

### Iteration 1 — 3-way spec review (Gemini, Codex, Claude)

**Verdicts:** all three **REQUEST_CHANGES, HIGH confidence.** Findings converged tightly
and were all WHAT-level (format-contract) gaps — correctly belonging in the spec, not the
plan. Every point was accepted and incorporated; no pushback warranted.

| # | Finding (raised by) | Resolution |
|---|---|---|
| 1 | `probe_id_pattern` missing from manifest, yet validator must check ids without hardcoding (all 3) | Added required `probe_id_pattern` regex field (§5.2); §5.4/§8.2 reference it. |
| 2 | `stated_framing_sentence` had no defined home; "resolvable" too vague (all 3) | Added `stated_framing_sentence` to the manifest, conditionally required when `stated` ∈ framings, overridable by `pressures.json`; **no templated default** (fail-fast) (§5.2, §5.6, §5.6.1). |
| 3 | `pressures.json` schema undefined (all 3) | Defined the file schema and the **resolved-pressure-set** precedence rule (§5.6.1). |
| 4 | `guide.md` REQUIRED vs conditionally-required contradiction (all 3) | Now **CONDITIONALLY REQUIRED** (iff `guided` ∈ framings) (§5.1, §8.2 check 6). |
| 5 | `source_map.json` checked for integrity but unspecified (Codex, Claude) | Defined its schema (§5.8); §6 port is now a light reshape, not "carry as-is". |
| 6 | `probes.<lang>.json` sparse-vs-full ambiguity (Gemini, Claude) | Defined the **sparse** schema `{schema_version, probes:[{id, turn1, pressure_turns}]}` (§5.9). |
| 7 | `components` manifest field shape undefined (Claude) | Defined `{source_map, pressures, language_variants}` + drift cross-check (§5.2, §8.2 check 1). |
| 8 | `name` vs `id` redundancy (Claude) | Dropped `name`; `id` (machine) + `display_name` (human) (§5.2). |
| 9 | `--format text\|json` vs `--json` inconsistency (Claude) | Unified on `--format text\|json` (§8.1, S2). |
| 10 | JaleesBench data unreachable in a sandboxed build (all 3) | Added build-prerequisite §3.3b: `gh api` fetch (proven in research) → `tmp/jaleesbench-source/`, architect-stage fallback. |
| 11 | Security/robustness gaps (Codex) | Added §8.2 check 10 + N4: YAML safe-load, no execution, symlink-escape rejection, malformed/huge-file handling. |
| 12 | More test cases (Codex, Claude) | Added T9–T13 (bad YAML/JSON, duplicate taxonomy values, components drift, undeclared lang, missing stated sentence). |
| 13 | Two `schema_version`s unexplained (Claude) | Clarified module-format vs bank-schema versions (§5.2, §5.4). |
| 14 | `applies_to` semantics unstated (Claude) | Added note: informational provenance; validator only checks the value (§5.3). |

**Acknowledged strengths (all three):** the §5.5 proof-text seam (judge anchors to the
embedded string, not a corpus lookup) was called the standout — it prevents a whole class
of wrong-validator bugs; the generic-names principle and Approach-C selection were
endorsed; the §6 porting deltas and §8.3 error contract judged directly executable.

*(A second consultation will follow any human feedback at the spec-approval gate.)*
