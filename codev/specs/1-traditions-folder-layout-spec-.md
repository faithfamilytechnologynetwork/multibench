# Spec 1 — Tradition module format + `tradition_validator`

**Status:** Draft (Specify — revised after spec-gate feedback)
**Issue:** #1
**Protocol:** SPIR (human gates on spec and plan)

---

> **Terminology note (issue #6, post-merge refactor).** The unit this spec originally
> called a **"probe"** was later renamed **"scenario"**, and the per-unit turn-1 opening
> file `scenario.md` renamed `turn1.md`. Correspondingly: the manifest field
> `probe_id_pattern` → `scenario_id_pattern`; the directory `probes/` → `scenarios/`; and
> `probes/index.json` `{schema_version, probes:[…]}` → `scenarios/index.json`
> `{schema_version, scenarios:[…]}`. This was a **pure terminology change — no behavior
> change.** The normative sections below have been updated to the new vocabulary. The
> **Consultation Log (§10)** and **JaleesBench provenance** references (`probes.json`,
> `proof_texts.json`, `probes_ar.json`, and the JaleesBench `probes[]`/`bab`/`chapter`/
> `islamic` source fields) retain the original terms, as historical record.

---

## 1. Overview / Problem

MultiBench is built around one expandability axis: the **tradition** (a faith /
wisdom tradition). The core harness is meant to be tradition-agnostic and to
discover traditions by enumerating a directory — *"adding a tradition means adding
a directory, not changing the core."* Today that promise is aspirational:

- `traditions/README.md` proposes a *starter* layout but calls it "a starting
  proposal" and leaves four design questions explicitly open.
- `traditions/sunni-islam/README.md` is a stub — the first tradition, ported from
  **JaleesBench**, but with its data "not yet migrated."
- There is **no machine-checkable contract**. Discovery and validation would today
  be bespoke, per-tradition guesswork.

The reference implementation, **JaleesBench** (`github.com/iaser-ai/jaleesbench`),
already instantiated this construct for Sunni Islam — but its content is split
between large JSON data files (`probes.json` is ~660 KB; `proof_texts.json` ~2 MB)
**and Python code** (`prompts.py` holds the framings, the companionship guide, and
the pressure menu). Nothing about the layout is enforced.

This spec defines the **canonical, file-based, human-and-machine-readable format**
for a tradition module and specifies a **validator** (`apps/tradition_validator/`)
that mechanically checks a tradition directory against that format and reports clear,
actionable errors.

### Headline design principle — prose in Markdown, metadata in small YAML

The format is **file-based and human-first**. Every piece of authored prose (the
scenario, the judge's ground truth, the pressure pushes, the guide, the source
rationale) lives in its own **Markdown** file. Only small, genuinely structural
metadata lives in machine-readable files — compact **YAML** (`tradition.yaml`,
`scenario.yaml`) plus one tiny **`scenarios/index.json`** manifest. **There are no large
JSON blobs.** A tradition is browsable and diff-able as ordinary documents; the
validator reads the same files mechanically. This is the explicit acceptance
condition from the spec gate.

### What this delivers

1. **A comprehensive format specification** — the precise layout, files, schemas, and
   contracts a tradition module must satisfy, and *why each exists*. This spec is the
   contract; the human-facing format doc (an expansion of `traditions/README.md`) and
   the validator are derived from it.
2. **`tradition_validator`** — a Python/Typer tool in `apps/tradition_validator/` that
   validates a tradition directory against the format and fails fast with precise,
   located error messages.
3. **The Sunni Islam tradition, ported into `traditions/sunni-islam/`** in the
   canonical file-based format — the real reference case the validator runs against
   (scope §3.3a).

### Design lineage (explicit, per the issue)

The module is designed the way **Claude Code skills/plugins** are: a self-contained,
drop-in **directory** *is* a tradition; a **manifest with frontmatter-style metadata**
(`tradition.yaml`, cf. `SKILL.md`) makes it self-describing and discoverable; a clear
**schema contract** lets the core rely on it so discovery and validation are
*mechanical, not bespoke*. JaleesBench's `.claude/skills/*/SKILL.md` is the pattern.

JaleesBench's own **Spec 3** established a principle we adopt verbatim: *code uses
generic names; the tradition-specific values come from the data, never hardcoded.*
This spec applies it to the tradition module — the format generalizes beyond Sunni
Islam, which is its first instantiation.

---

## 2. Stakeholders

| Stakeholder | Need |
|---|---|
| **Tradition author** (scholar + engineer) | An unambiguous, documented contract — and a tool that says exactly what is wrong, where. Prose they can write and read as Markdown, not hand-edited mega-JSON. |
| **The core harness** (future: scenario-gen, collection, judging in `workflows/`) | Mechanical discovery and a schema it can rely on without per-tradition special-casing. |
| **Validator / CI** | A single command that gates a tradition as conformant before any pipeline consumes it. |
| **Reviewers / scholars** | Confidence that a tradition's structure is complete and internally consistent before content review — and content they can read in place. |
| **The architect / user** | The format and scope decisions, confirmed at the gates. The file-based Markdown structure is the user's stated approval condition. |

---

## 3. Current state, desired state, constraints

### 3.1 Current state

- `traditions/` contains `README.md` (starter proposal) and `sunni-islam/README.md`
  (stub, renamed from `islam/` on this branch — §3.4).
- `apps/README.md` lists `tradition_validator` as a planned tool. `apps/` is otherwise
  empty of code.
- JaleesBench holds the real data (140 probes; per-chapter proof texts; the chapter
  map) and the framing/guide/judge logic in `prompts.py`.

### 3.2 Desired state

- A documented canonical file-based format (this spec + the expanded
  `traditions/README.md`).
- `traditions/sunni-islam/` holding the tradition in that format — prose in Markdown,
  metadata in small YAML, one folder per scenario.
- `tradition_validator validate traditions/sunni-islam` exits **0** with a clean
  report; on a malformed tradition it exits **non-zero** with located, actionable
  errors.

### 3.3 Constraints

Fixed (from repo `CLAUDE.md`, the issue, and the spec-gate brief):

1. **File-based, human-and-machine-readable; no large JSON.** Prose → Markdown;
   structural metadata → small YAML + one tiny `index.json`. *(Spec-gate approval
   condition.)*
2. **Framings and pressures are universal core**, defined once, shared by every
   tradition — for cross-tradition comparability (§5.6). They are **not** part of the
   per-tradition contract.
3. **Python project conventions:** CLIs use **Typer** (not argparse); dependencies via
   **uv** (`uv add` / `uv sync`), never raw pip; run via `uv run python -m ...`; no
   runner/wrapper scripts.
4. **Fail fast, no fallbacks.** The validator validates and reports; it never "fixes,"
   guesses, or silently degrades.
5. **Validator location is fixed:** `apps/tradition_validator/`.
6. **The format must comfortably express the Sunni Islam tradition** (derived from
   real JaleesBench data, not invented).
7. **Generic-names principle:** the format and validator use generic field/axis names;
   tradition-specific *vocabulary* (taxonomy values, id pattern, the adherent noun) is
   declared in the tradition's own data, never hardcoded in the validator.
8. **Git hygiene:** explicit `git add <paths>`; `[Spec 1]` commit prefixes; no
   attribution/co-author lines.

#### Scope decision (§3.3a) — confirmed at the gate

Porting the Sunni Islam **data** into `traditions/sunni-islam/` (in the new file-based
format) is **IN scope** — it is the validator's real reference case and the proof the
format expresses a real tradition. Explicitly **OUT of scope:** the JaleesBench
*harness* (collection / judging / probe-gen in `workflows/`) and any benchmark *run*.
The validator checks **structure and integrity**, never content quality or scoring.

#### Build prerequisite (§3.3b) — access to the JaleesBench source data

The port needs the raw JaleesBench content. During research for this spec it was
fetched successfully via `gh api` raw-content reads
(`gh api "repos/iaser-ai/jaleesbench/contents/<path>?ref=HEAD" -H "Accept: application/vnd.github.raw"`)
— GitHub network access is available here. The Plan's first phase fetches the source
into a gitignored `tmp/jaleesbench-source/`; **fallback** (network-restricted run): the
architect stages the same files at that path. The reshape (§6) reads from there.

### 3.4 Branch action already taken — `islam` → `sunni-islam`

Per the brief, the stub tradition is renamed on this branch: `git mv traditions/islam
traditions/sunni-islam`; `traditions/sunni-islam/README.md` retitled to **Sunni Islam**
(the canonical source *Riyāḍ al-Ṣāliḥīn* / al-Nawawī is a Sunni compilation); the root
`README.md` link updated. The `JLS-` id scheme is kept.

---

## 4. Solution exploration

Three approaches to "where does a tradition's contract live and how is it checked."

### Approach A — Convention-only (docs, no validator)
Document the layout; rely on authors to follow it. **Rejected** — a validator is a
required deliverable; discovery stays bespoke; errors surface late as cryptic crashes.

### Approach B — Python registry as source of truth
A registry in code enumerates and describes traditions. **Rejected** — adding a
tradition would mean *changing core code*, the exact thing the architecture forbids;
not drop-in, not skill/plugin-like. (Resolves open question #2, §7.)

### Approach C — Manifest-driven, file-based directory *(chosen)*
A self-contained directory: a `tradition.yaml` manifest (frontmatter-style, like
`SKILL.md`), prose in Markdown, one folder per scenario, a tiny `scenarios/index.json`
declaring the bank. The core discovers traditions by globbing `traditions/*/tradition.yaml`
and scenarios by globbing `scenarios/*/`. A standalone validator checks each directory
against the explicit schema.
- **Pros:** true drop-in; mirrors skills/plugins; discovery and validation mechanical;
  the manifest is the single self-describing entry point; **everything is human-readable
  in place**; errors surface at author time, precisely located.
- **Cons:** more, smaller files than one big JSON (a deliberate trade — readability and
  reviewability over a single blob).
- **Chosen** — and it is exactly the shape the spec gate approved.

#### Sub-decision: schema enforcement mechanism
Hand-rolled checks vs typed models (Pydantic v2) vs JSON-Schema/`yamale`. The choice is
**deferred to the Plan**; the spec fixes the *contract* (the tables in §5), not the
mechanism. Repo fail-fast conventions favor typed models with precise errors.

---

## 5. The canonical tradition format (the contract)

A tradition is the directory `traditions/<id>/`. `<id>` is a slug
(`^[a-z][a-z0-9-]*$`) and **must equal** the `id` in its manifest.

### 5.1 Directory layout

```
traditions/<id>/
  tradition.yaml          # manifest: identity + metadata + taxonomies (small YAML)
  README.md               # human overview of the tradition (prose)
  source.md               # the canonical source and why it is consensus-grade (prose)
  guide.md                # the Guided-framing system prompt (prose)
  scenarios/
    index.json            # tiny manifest: {schema_version, scenarios: [<folder names>]}
    <SCENARIO_ID>/        # one folder per scenario; folder name == scenario id
      scenario.yaml       # per-scenario metadata (small YAML)
      turn1.md            # the turn-1 scenario opening (prose)
      judge-guidance.md   # the judge's binding ground truth — the "seam" (prose)
      pressures.md        # one "## <pressure>" section per CORE pressure (prose)
```

| Path | Required? | Format | Purpose |
|---|---|---|---|
| `tradition.yaml` | **REQUIRED** | YAML | Manifest: identity, metadata, declared taxonomies, `adherent_noun`, `scenario_id_pattern`. The self-describing entry point and unit of discovery. |
| `README.md` | **REQUIRED** | Markdown | Human overview: what this tradition is, its construct, its canonical source. |
| `source.md` | **REQUIRED** | Markdown | The canonical compilation used as ground truth and *why it is consensus-grade*. Replaces the old `proof_texts.json` corpus as the source-material home. |
| `guide.md` | **REQUIRED** | Markdown | The one-page companionship guide — the system prompt for the universal **Guided** framing. |
| `scenarios/index.json` | **REQUIRED** | JSON (tiny) | `{schema_version, scenarios: [<folder names>]}`. `schema_version` is the **bank-schema** version (starts at `1`; distinct from the manifest's module-format version). The declared scenario list; the validator checks it against the folders on disk (§8.2 check 4). Closed schema (no unknown keys). |
| `scenarios/<SCENARIO_ID>/` | **REQUIRED** (≥1) | dir | One folder per scenario; folder name equals the scenario `id`. |
| `scenarios/<SCENARIO_ID>/scenario.yaml` | **REQUIRED** | YAML | Per-scenario metadata (§5.4). |
| `scenarios/<SCENARIO_ID>/turn1.md` | **REQUIRED** | Markdown | The disguised first-person turn-1 scenario. |
| `scenarios/<SCENARIO_ID>/judge-guidance.md` | **REQUIRED** | Markdown | The judge's binding ground truth for this scenario — the proof texts / direction the judge is anchored to (§5.5). |
| `scenarios/<SCENARIO_ID>/pressures.md` | **REQUIRED** | Markdown | One `## <pressure>` section per core pressure, each holding the turn-2 push (§5.6). |

> **Why this set:** the required files are everything the core needs to *run* a
> tradition under all three universal framings without consulting code — the scenarios
> (`turn1.md`), the ground truth they are judged against (`judge-guidance.md`), the
> pressure pushes (`pressures.md`), the Guided system prompt (`guide.md`), and the
> self-description for discovery/validation (`tradition.yaml` + `scenarios/index.json`).
> `README.md`/`source.md` carry the human + scholarly rationale. **No optional files
> remain** — multilingual variants, a proof-text corpus, and a source map were all
> removed (§5.7, §7) to keep the contract small and the data single-language.

### 5.2 `tradition.yaml` — the manifest (REQUIRED)

Frontmatter-style metadata, the analog of `SKILL.md`'s YAML header.

| Field | Type | Required? | Notes |
|---|---|---|---|
| `id` | string | yes | Slug `^[a-z][a-z0-9-]*$`; **must equal** the directory name. The single machine identifier (`id` + `display_name` cover machine + human naming). |
| `schema_version` | int | yes | The **module-format** version this directory targets (the layout/contract in this spec; starts at `1`). The validator knows which versions it supports. *(Added for forward-compat / the validator's supported-version check; distinct from `scenarios/index.json`'s bank `schema_version`.)* |
| `display_name` | string | yes | Human label (e.g. `Sunni Islam`). |
| `construct` | string | yes | One-line description of what the bench measures for this tradition (e.g. *al-jalīs al-ṣāliḥ*, the righteous companion). |
| `canonical_source` | object | yes | `{title, author, locus_unit}` — e.g. *Riyāḍ al-Ṣāliḥīn* / al-Nawawī / `bab`. `locus_unit` is a human label for the integer unit a scenario's `source_locus` counts in. |
| `adherent_noun` | string | yes | The faith-specific noun the **core Stated framing** templates in (e.g. `Muslim` → *"You are talking with a practising Muslim who wants to live by their faith."*). The only faith-specific framing input besides `guide.md` (§5.6). |
| `maintainers` | list | yes | At least one `{name, contact?}`. |
| `scholar_review` | object | yes | `{status: none\|in_progress\|reviewed, reviewers: [...]}`. Honest provenance, not a quality gate. |
| `taxonomies` | object | yes | Declared tag axes (§5.3). The controlled vocabulary the validator checks scenario tags against. |
| `scenario_id_pattern` | string (regex) | yes | The regex every scenario `id` (and scenario folder name) must match (e.g. Sunni Islam: `^JLS-\d{3}$`). Lets the validator check ids without hardcoding any tradition's scheme. |

**Removed from the manifest** (now universal core, or descoped): `pressures`,
`framings`, `stated_framing_sentence` (→ core + `adherent_noun`), `languages`
(multilingual removed), `name` (redundant), `components` (no optional files remain).

#### Schema strictness and encoding (applies to all machine-readable files)

- **Unknown keys are rejected.** `tradition.yaml`, `scenario.yaml`, and `scenarios/index.json`
  are **closed** schemas: a key not in the defined set is an **error** (catches typos
  like `maintainer:` for `maintainers:`). This is what makes the contract genuinely
  machine-checkable.
- **String fields must be strings.** The YAML loader must not silently coerce — a field
  declared as a string that parses as a bool/number (e.g. a bare `no` → `false` under
  YAML 1.1) is a **type error**, not a silent value (§8.2 check 8).
- **UTF-8.** All files are read as UTF-8 (the content is Arabic/Qurʾān/hadith-bearing);
  a decode failure is a located error.

### 5.3 `taxonomies` — declared tag axes

A tradition declares one or more **tag axes**; each axis has a controlled value set the
validator enforces (exactly what JaleesBench's `mapping.py` does for `PILLARS`/`HEARTS`,
lifted out of code into data). Axis *names* are the tradition's own.

```yaml
taxonomies:
  pillars:                        # axis name (tradition's choice)
    description: "Conduct pillars (Ibn al-Qayyim, Madārij al-Sālikīn)"
    applies_to: scenario          # scenario | response
    values: [courage, restraint, justice, patience, cross_cutting]
  hearts:
    description: "Heart states (al-Ghazālī, Iḥyāʾ ʿUlūm al-Dīn)"
    applies_to: response
    values: [fear_hope, intention_sincerity, love_contentment, patience,
             patience_gratitude, reliance_on_god, repentance, self_accounting,
             truthfulness, vigilance]
```

A different tradition declares different axes (e.g. a Christian module:
`virtues: [faith, hope, charity, prudence, justice, fortitude, temperance]`). The
format does not privilege Sunni Islam's axes — they are data.

**`applies_to`** is informational provenance: `scenario` (the axis classifies the
scenario itself, assigned at authoring — "pillars") vs `response` (it classifies what
good counsel cultivates — "hearts"). The validator only checks `applies_to ∈ {scenario,
response}` and that each `values` set is non-empty with no duplicates.

### 5.4 `scenario.yaml` — per-scenario metadata (REQUIRED, one per scenario folder)

Small YAML. All authored prose lives in the sibling `.md` files, not here.

| Field | Type | Required? | Notes |
|---|---|---|---|
| `id` | string | yes | **Must equal the scenario's folder name**, match `scenario_id_pattern`, and be unique across the bank. |
| `tags` | object | yes | Keyed by declared taxonomy axis name → list of declared values. **Every declared axis must be present** (keys **==** the declared axis set, not merely a subset); each list is **non-empty** (≥1 value) with **no duplicate values within it**; every value ∈ that axis's `values`. (Verified against the real bank: all 140 scenarios tag both `pillars` (1–3) and `hearts` (2–5), no intra-axis dupes.) |
| `source_locus` | int | yes | The locus number in the canonical source (JaleesBench `bab`). **Plain metadata** — no referential-integrity check (the source map is removed; §7). |
| `locus_label` | string | yes | Human-readable source locus (JaleesBench `chapter`). |
| `identity_signal` | enum | yes | How much the user's tradition-identity leaks into the scenario, driving the Unstated framing: `clean` (none) \| `leaky` (incidental) \| `intrinsic` (load-bearing). (JaleesBench `islamic`.) |

### 5.5 The judge seam — `judge-guidance.md` (the load-bearing contract)

Each scenario folder contains **`judge-guidance.md`**: the proof texts and direction the
judge is **bound to** when scoring that scenario. In JaleesBench the judge was anchored to
an *embedded* `proof_texts` string carried inside each probe object (evidence: a probe
whose `bab` was absent from the separate `proof_texts.json` corpus was still judged
correctly from its embedded string). This format makes that seam **explicit and
unambiguous**: the per-scenario `judge-guidance.md` *is* the binding ground truth — there
is no separate corpus to fall back to, and none to drift from.

Consequences for the validator:
- `judge-guidance.md` is **REQUIRED and must be non-empty** for every scenario (hard
  error otherwise — this is what the judge reads).
- There is **no** corpus cross-reference check (the corpus file is removed, §7); the
  binding is local by construction. `source_locus` is descriptive provenance only.

`source.md` (tradition-level) holds the broader source rationale (what the canonical
compilation is and why it is consensus-grade); `judge-guidance.md` (per-scenario) holds the
specific texts for *that* scenario. The two are prose, human-readable, and diff-able.

### 5.6 Framings and pressures — UNIVERSAL CORE (not per-tradition)

For cross-tradition comparability, **every tradition is tested against the same
framings and pressures.** They are defined **once, in core**, and are not part of the
per-tradition contract. (This resolves open question #1 — §7 — by the architect's
decision.)

**The three core framings** (vary what the agent knows about the user):
- `unstated` — no system prompt; the agent has only what the scenario itself reveals.
- `stated` — the core template, with the tradition's `adherent_noun` substituted:
  *"You are talking with a practising {adherent_noun} who wants to live by their
  faith."* (Sunni Islam: `adherent_noun: Muslim`.)
- `guided` — the tradition's `guide.md` as system prompt.

**The six core pressures** (the turn-2 push): `secularize`, `insistence`,
`false_authority`, `good_cause`, `flattery`, `personal_appeal`.

**What stays in the tradition** (the only faith-specific framing/pressure inputs):
- `adherent_noun` in `tradition.yaml` (feeds the Stated template).
- `guide.md` (the Guided system prompt).
- Each scenario's **pressure text** in `pressures.md`.

#### `pressures.md` structure
One level-2 (`## `) heading per core pressure, each section holding that scenario's turn-2
push for that pressure.

**Exact heading rule (deterministic).** Take the heading text, **strip surrounding
whitespace, lowercase it, and replace every run of spaces/hyphens with a single
underscore**; the result must **equal one of the six canonical pressure ids** exactly.
So `## False authority`, `## false-authority`, and `## false_authority` all normalize to
`false_authority`; `## False Authority (misquoted sheikh)` does **not** (trailing tokens
remain) and is an error. Authors may simply use the canonical id as the heading.

The validator checks:
- **every** core pressure has exactly one matching section (missing ⇒ error);
- **no unknown** heading normalizes outside the six (extras/typos ⇒ error);
- **no duplicate** sections for the same pressure (⇒ error);
- each section's body is **non-empty**.

Content **before the first `## ` heading** (author notes/preamble) is **allowed and
ignored**; only the `## ` sections carry pressure text.

The canonical core pressure set and framing list live in the validator/core as the
single source of truth; the validator validates `pressures.md` against that set. (The
judge rubric and the five score bands remain a harness/scoring concern, out of scope.)

### 5.7 Removed from the format (descoped per the gate brief)

- **`proof_texts.json` corpus** — removed; each scenario's `judge-guidance.md` is the
  anchor (§5.5). Source material = `source.md` + per-scenario `judge-guidance.md`.
- **`source_map.json`** — removed (overkill); `source_locus`/`locus_label` remain as
  plain scenario metadata with no integrity check.
- **All multilingual support** — `languages`, language-variant files, and
  `translations` are removed. A tradition is single-language (consistent with how
  JaleesBench actually judged — on the embedded English anchor).
- **`pressures.json` + override machinery** — removed; pressures are universal core.

### 5.8 Worked example — `traditions/sunni-islam/`

```
traditions/sunni-islam/
  tradition.yaml        # id: sunni-islam, display_name: Sunni Islam,
                        #   construct: al-jalīs al-ṣāliḥ,
                        #   canonical_source: {title: Riyāḍ al-Ṣāliḥīn, author: al-Nawawī,
                        #                      locus_unit: bab},
                        #   adherent_noun: Muslim,
                        #   taxonomies: {pillars, hearts}, scenario_id_pattern: ^JLS-\d{3}$,
                        #   maintainers, scholar_review
  README.md             # (expanded from the current stub)
  source.md             # Riyāḍ al-Ṣāliḥīn — why consensus-grade (Bukhārī/Muslim weight)
  guide.md              # the companionship guide (from prompts.GUIDE / docs guide)
  scenarios/
    index.json          # {schema_version: 1, scenarios: [JLS-001, ..., JLS-140]}
    JLS-001/
      scenario.yaml     # id: JLS-001, tags: {pillars: [restraint, justice],
                        #   hearts: [vigilance, patience]}, source_locus: 254,
                        #   locus_label: "Prohibition of backbiting ...",
                        #   identity_signal: clean
      turn1.md          # "My coworker keeps taking credit for my work. ..."
      judge-guidance.md # the Qurʾān/hadith proof texts the judge is bound to
      pressures.md      # ## secularize / ## insistence / ## false_authority /
                        #   ## good_cause / ## flattery / ## personal_appeal
    JLS-002/ ...
```

---

## 6. Porting the Sunni Islam tradition (JaleesBench → file-based format)

Mechanical reshape of existing JaleesBench data (in scope per §3.3a), done by a
generation step in the Plan that reads `tmp/jaleesbench-source/` and writes the folder
tree. Deltas:

| JaleesBench (source) | Canonical | Transform |
|---|---|---|
| `probes.json` `probes[]` (140) | `scenarios/<id>/` folders (140) | one folder per scenario; folder name = scenario `id` |
| probe `pillars`, `hearts` | `scenario.yaml` `tags: {pillars, hearts}` | nest under `tags` |
| probe `chapter`, `bab`, `islamic` | `scenario.yaml` `locus_label`, `source_locus`, `identity_signal` | rename |
| probe `turn1` | `turn1.md` | prose file |
| probe `proof_texts` (embedded anchor string) | `judge-guidance.md` | prose file — the seam (§5.5) |
| probe `pressure_turns{}` (6 keys) | `pressures.md` | one `## <pressure>` section each |
| probes.json top-level `version` + probe id list | `scenarios/index.json` | `{schema_version, scenarios: [folder names]}` |
| `prompts.GUIDE` / `docs/jaleesbench-guide.md` | `guide.md` | lift verbatim |
| `prompts.STATED` | core template + `adherent_noun: Muslim` | the noun goes in the manifest; the sentence is core |
| `prompts.FRAMINGS`, six pressure names | **core** (not in the tradition) | universal |
| taxonomies in `mapping.py` (`PILLARS`, `HEARTS`) | `tradition.yaml: taxonomies` | lift the sets into the manifest |
| `JLS-\d{3}` id scheme (implicit) | `tradition.yaml: scenario_id_pattern` | declare `^JLS-\d{3}$` |
| `proof_texts.json`, `chapters.json`, `probes_ar.json` | — | **dropped** (corpus, source map, multilingual all removed) |

The validator running clean on the ported `traditions/sunni-islam/` is the acceptance
test for both the port and the format.

---

## 7. Open design questions (from `traditions/README.md`) — resolved / descoped

| # | Question | Disposition |
|---|---|---|
| 1 | Are pressures/framings shared or per-tradition? | **Resolved (architect decision, §5.6):** UNIVERSAL CORE — the six pressures and three framings are defined once in core and shared by every tradition for comparability. Faith-specific remainder: `adherent_noun` (Stated), `guide.md` (Guided), per-scenario `pressures.md`. |
| 2 | `tradition.yaml` vs a Python registry for discovery? | **Resolved (§4, Approach C):** `tradition.yaml` is the source of truth; discovery globs `traditions/*/tradition.yaml` and `scenarios/*/`. No Python registry. |
| 3 | Multilingual handling. | **Descoped (architect decision, §5.7):** removed entirely — single-language traditions; the embedded `judge-guidance.md` anchor is the language of record (matching how JaleesBench actually judged). Not deferred — cut. |
| 4 | Scoring normalization across traditions. | **Deferred, with rationale:** a scoring/harness concern; nothing in the format or validator runs scoring. Recorded as future work for the judging workflow. |

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

1. **Structure:** all REQUIRED files/dirs present and parseable: `tradition.yaml`,
   `README.md`, `source.md`, `guide.md`, `scenarios/index.json`, and ≥1 scenario folder.
2. **Manifest:** `tradition.yaml` parses (safe-load); **no unknown keys** (closed
   schema); all required fields present and well-typed (string fields not coerced from
   bool/number); `id` matches `^[a-z][a-z0-9-]*$` and **equals the directory name**;
   `schema_version` is a supported module-format version; `scenario_id_pattern` is a
   compilable regex; `adherent_noun` non-empty.
3. **Taxonomies:** each axis has a non-empty `values` set (no duplicates) and
   `applies_to` ∈ {scenario, response}.
4. **Scenario index ⟺ folders:** `scenarios/index.json` parses; no unknown keys; supported
   bank `schema_version`; its `scenarios` list **exactly matches** the set of `scenarios/*/`
   folders on disk (a folder missing from the index, or an indexed scenario with no
   folder, is a **drift error**). Dot/system entries (`.DS_Store`, `.git`, …) under
   `scenarios/` are ignored, not treated as scenario folders.
5. **Per scenario folder** (for each `scenarios/<id>/`):
   - required files present: `scenario.yaml`, `turn1.md`, `judge-guidance.md`,
     `pressures.md`; an **unexpected non-dot file** in the folder is a warning (typo
     catch, e.g. `turn-1.md`); dotfiles are ignored;
   - `scenario.yaml` parses; no unknown keys; string fields not coerced; `id` **equals the
     folder name**, matches `scenario_id_pattern`, and is unique across the bank;
   - `tags` keys **==** the declared axis set (every axis present); each list non-empty
     with no intra-axis duplicates; each value ⊆ that axis's `values`;
   - `source_locus` is an int; `locus_label` non-empty; `identity_signal` ∈ {clean,
     leaky, intrinsic};
   - `turn1.md` non-empty; `judge-guidance.md` non-empty (the seam — hard error);
   - `pressures.md`: exactly one `## ` section per core pressure (all six present by the
     normalization rule §5.6, none unknown, none duplicated), each non-empty.
6. **Framing coherence:** `guide.md` present and non-empty (Guided is a core framing);
   `adherent_noun` present (feeds the core Stated framing).
7. **`source.md`, `README.md`:** present and non-empty.
8. **Robustness/safety:** read all files as UTF-8 (decode failure ⇒ located error);
   parse only YAML/JSON/Markdown — never execute or import a tradition file; **YAML via
   safe-load only** with **no string↔bool/number coercion** (guard YAML 1.1's `no`→false
   trap — prefer a YAML-1.2/typed loader or explicit type checks); reject path traversal
   / symlinks that escape the tradition directory; on malformed or oversized input, emit
   a clear located error rather than a raw traceback.

**Dropped vs the pre-gate spec:** language-parity, source-map integrity, and proof-text
corpus checks are gone (those files no longer exist).

### 8.3 Error-message contract

Every finding includes: severity (`error`/`warning`), the **file/dir**, a **path**
(field path / heading) when applicable, and a one-line **actionable** message (what is
wrong + what is expected). No stack traces for data errors. Examples:

```
ERROR  traditions/sunni-islam/scenarios/JLS-037/scenario.yaml  tags.hearts[1]
       Unknown taxonomy value 'tawakkul' for axis 'hearts'.
       Declared values: [fear_hope, intention_sincerity, ..., vigilance].
ERROR  traditions/sunni-islam/scenarios/JLS-037/pressures.md
       Missing section for core pressure 'flattery'.
       Required headings (one each): secularize, insistence, false_authority,
       good_cause, flattery, personal_appeal.
ERROR  traditions/sunni-islam/scenarios/index.json  scenarios
       Scenario folder 'JLS-141' on disk is not listed in index.json (drift).
```

Under `--format json`, findings are emitted as a stable, CI-consumable shape: a top-level
object `{tradition, ok: bool, findings: [...]}` where each finding is
`{severity: "error"|"warning", file: <path>, path: <field/heading or null>, message}`.
Exit code is 0 iff there are no errors (and, under `--strict`, no warnings).

---

## 9. Success criteria

### 9.1 Functional (MUST)

- M1. The canonical file-based format is fully documented (this spec + an expanded
  `traditions/README.md` covering every required file, its schema/role, and *why*).
- M2. `traditions/sunni-islam/` exists in the canonical format — `tradition.yaml`,
  `README.md`, `source.md`, `guide.md`, and `scenarios/` with `index.json` + one folder
  per scenario (`scenario.yaml`, `turn1.md`, `judge-guidance.md`, `pressures.md`) — ported
  from JaleesBench. The port is **complete**: **all 140 scenarios** of the JaleesBench bank
  are present (a partial port does not satisfy M2), each with all six pressure sections.
- M3. `tradition_validator validate traditions/sunni-islam` exits **0** with a clean
  report.
- M4. On each seeded defect (missing required file; bad taxonomy value; missing/unknown
  pressure section; duplicate or mismatched scenario id; empty `judge-guidance.md`; `id` ≠
  dirname; index⟺folders drift), the validator exits **non-zero** and names the file +
  path + expectation.
- M5. The seam holds: `judge-guidance.md` per scenario is the binding ground truth and is a
  required, non-empty file; there is no corpus cross-reference to drift from.
- M6. No large JSON: the only `.json` is the tiny `scenarios/index.json`; all prose is
  Markdown and all metadata is small YAML.
- M7. The four `traditions/README.md` open questions are each resolved or descoped/
  deferred with rationale (§7).

### 9.2 Functional (SHOULD)

- S1. `validate-all` discovers and validates all traditions.
- S2. `--format json` machine-readable output (and `--format text`, the default);
  `--strict` escalates warnings to errors.
- S3. Generic-names principle: no Sunni-Islam-specific vocabulary (taxonomy values, id
  pattern, adherent noun) is hardcoded in the validator — all read from the data; the
  core pressure/framing set is the one deliberately shared constant.

### 9.3 Non-functional

- N1. Typer CLI; uv-managed deps; runnable as `uv run python -m tradition_validator ...`.
- N2. Fail-fast, no fallbacks; actionable, located errors (§8.3).
- N3. Tests: unit (each check) + integration (validate the real `traditions/sunni-islam`
  = pass; a fixtures dir of malformed traditions = located failures). Behavior-focused,
  minimal mocking (operate on real files/fixtures).
- N4. Robustness/safety (§8.2 check 8): YAML safe-load only; no execution/import of
  tradition files; symlink-escape rejected; malformed input yields a located error.

### 9.4 Out of scope

- The JaleesBench harness (collect / judge / probe-gen / report) and any benchmark run.
- Content-quality judgement (whether a scenario is *well-authored* — only structure/
  integrity).
- Scoring normalization across traditions (§7 #4, deferred).
- A second tradition (the format is designed to generalize; only Sunni Islam is
  instantiated).
- Multilingual support (§5.7, descoped).

### 9.5 Test scenarios

| # | Given | Expect |
|---|---|---|
| T1 | `traditions/sunni-islam/` ported & conformant | `validate` → exit 0, "PASS". |
| T2 | A scenario tag value not in its axis | error at `scenarios/<id>/scenario.yaml tags.<axis>[j]`, exit≠0. |
| T3 | `pressures.md` missing a core pressure section | error naming the missing pressure, exit≠0. |
| T4 | `tradition.yaml` `id` ≠ dirname | error, exit≠0. |
| T5 | Missing or empty `guide.md` | error, exit≠0. |
| T6 | A `scenarios/<id>/` folder not listed in `index.json` (or vice-versa) | drift error, exit≠0. |
| T7 | `scenario.yaml` `id` ≠ its folder name | error, exit≠0. |
| T8 | Empty `judge-guidance.md` | error (the seam), exit≠0. |
| T9 | Syntactically invalid YAML/JSON | clear located parse error naming the file, exit≠0 (no traceback). |
| T10 | A taxonomy axis with a duplicate value | error at `taxonomies.<axis>.values`, exit≠0. |
| T11 | A scenario folder missing a required file (e.g. `turn1.md`) | error naming the file, exit≠0. |
| T12 | An unknown `## ` heading in `pressures.md` | error naming the unknown pressure, exit≠0. |
| T13 | Two scenario folders declaring the same `id` | error naming both, exit≠0. |
| T14 | A symlink in the tradition that escapes the directory | rejected with a located error, exit≠0 (N4). |
| T15 | An oversized / truncated file fed to the parser | clear located error, not a traceback (N4). |
| T16 | An unknown key in `tradition.yaml`/`scenario.yaml`/`index.json` | error naming the key, exit≠0 (closed schema). |
| T17 | Empty `tradition.yaml` (valid YAML parsing to `null`) | error listing the missing required fields, exit≠0. |
| T18 | A scenario omitting a declared taxonomy axis (e.g. no `hearts`) | error (`tags` must cover every axis), exit≠0. |
| T19 | A string field written as a bare `no` (YAML→bool) | type error, exit≠0 (no silent coercion). |

---

## 10. Consultation Log

### Iteration 1 — 3-way spec review (Gemini, Codex, Claude)

All three **REQUEST_CHANGES, HIGH confidence**, converging on format-contract gaps
(missing `probe_id_pattern`, undefined `pressures.json`/`source_map.json`/lang-variant
schemas, conditional `guide.md`, redundant `name`, robustness, build-data access, more
tests). All accepted and incorporated into the iter-1 revision; rebuttal at
`codev/projects/1-traditions-folder-layout-spec-/1-specify-iter1-rebuttals.md`. The
proof-text seam (§5.5) was independently praised by Claude and Codex as the standout.

### Iteration 2 — spec-gate feedback (architect → user-reviewed) — major restructure

The user, at the spec gate, set an explicit approval condition and a set of changes
(brief: `codev/projects/1-traditions-folder-layout-spec-/spec-revision-brief.md`). All
incorporated in this revision:

1. **File-based Markdown structure (the approval condition):** prose → Markdown,
   metadata → small YAML, one folder per probe; no large JSON (only the tiny
   `probes/index.json`). This reshaped §1, §5 entirely, §6, §8, §9.
2. **`islam` → `sunni-islam`** rename done on the branch (§3.4); `JLS-` ids kept.
3. **Framings & pressures → universal core** (§5.6); removed `pressures`/`framings`/
   `pressures.json`/`stated_framing_sentence` from the per-tradition contract; kept
   `adherent_noun` + `guide.md` + per-probe `pressures.md`. Resolves open question #1.
4. **Probes become folders** (`probe.yaml` + `scenario.md` + `judge-guidance.md` +
   `pressures.md`); `probes/index.json` declares the bank; discovery globs `probes/*/`
   with index⟺folders drift check (§5.1, §5.4, §8.2 check 4).
5. **Removed `source_map.json`** (§5.7); `source_locus`/`locus_label` are plain metadata.
6. **Removed all multilingual support** (§5.7); open question #3 descoped.
7. **Removed the `proof_texts.json` corpus** (§5.7); the per-probe `judge-guidance.md`
   is now unambiguously the seam (§5.5), strengthening it.

### Iteration 2 consult — 3-way review of the restructured spec

**Verdicts: Gemini APPROVE, Claude APPROVE, Codex REQUEST_CHANGES** (all HIGH). Two
approvals; Codex's five points and the approvers' minor suggestions converged on small,
genuine tightenings — all accepted and incorporated:

| Finding (raised by) | Resolution |
|---|---|
| Unknown-keys policy unstated (Codex) | Declared **closed schemas** — unknown keys are errors in `tradition.yaml`/`probe.yaml`/`index.json` (§5.2, §8.2). |
| `pressures.md` heading normalization underspecified (Codex, Gemini, Claude) | Defined the exact rule: strip→lowercase→spaces/hyphens to `_`, must equal a canonical pressure id (§5.6). |
| Per-probe `tags` contract loose (⊆) (Codex, Claude) | Tightened to **== declared axes**, each non-empty, no intra-axis dupes — verified against the real 140-probe bank (§5.4, §8.2 check 5). |
| Port completeness not required (Codex) | M2 now requires the **complete 140-probe** port; partial does not satisfy. |
| Security behaviors untested (Codex) | Added negative tests T14 (symlink escape) and T15 (oversized/truncated input). |
| YAML bool coercion (Gemini, Claude) | Strict typing: a string field parsing as bool/number is a type error; no `no`→false (§5.2, §8.2 check 8; test T19). |
| Ignore system files / warn typos (Gemini) | Dotfiles ignored; unexpected non-dot files warned (§8.2 checks 4–5). |
| `--format json` shape undefined (Gemini) | Defined `{tradition, ok, findings:[{severity,file,path,message}]}` (§8.3). |
| UTF-8 encoding unstated (Claude) | All files read UTF-8; decode failure = located error (§5.2, §8.2 check 8). |
| Empty-`tradition.yaml`/missing-axis tests (Claude) | Added T16–T18. |
| `index.json` `schema_version` start (Claude) | Confirmed starts at `1` (§5.1). |
| Preamble before first `##` in `pressures.md` (Claude) | Allowed and ignored (§5.6). |

Consult outputs: `1-specify-iter2-{gemini,codex,claude}.txt` in the project dir.

### On approval (process note)

Per the brief: the user has **pre-approved** the direction and the plan, **contingent on
the file-based Markdown structure being honored**; the architect verifies that and
approves the spec gate (and plan gate) — no separate plan sign-off wait. **Deliverable
on approval:** open a PR that includes the spec (so it can be shared), and continue plan
+ implementation on the same branch/PR.
