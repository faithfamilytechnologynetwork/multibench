---
name: create-tradition
description: Scaffold a new MultiBench tradition under traditions/<id>/ in the canonical file-based format (tradition.yaml + prose Markdown + one folder per scenario) and validate it with tradition_validator. Use this whenever you are creating, adding, porting, or authoring a new tradition (faith/wisdom tradition) for MultiBench, or when someone says "add a tradition", "create a tradition", or "scaffold a tradition". sunni-islam is the worked example to copy from.
---

# Create a MultiBench tradition

A tradition is a **self-contained, drop-in directory** under `traditions/`. It is
**file-based**: prose lives in Markdown, structured metadata in small YAML, and the only
JSON is a tiny `scenarios/index.json`. Discovery is mechanical (`traditions/*/tradition.yaml`),
and the final step is always: **run the validator until it passes.**

**Read first:** [`traditions/README.md`](../../../traditions/README.md) (the format doc)
and copy from the worked example [`traditions/sunni-islam/`](../../../traditions/sunni-islam/).
The authoritative contract is Spec 1 (`codev/specs/1-traditions-folder-layout-spec-.md`).

## Steps

### 1. Pick an id and create the directory
`<id>` is a lowercase slug (`^[a-z][a-z0-9-]*$`) and **must equal** the directory name
(e.g. `sunni-islam`). Create `traditions/<id>/`.

### 2. Write `tradition.yaml` (the manifest)
Small YAML; **unknown keys are rejected** and string fields are not coerced (don't write a
bare `no` where a string is meant). Fields:

```yaml
id: <id>                        # must equal the directory name
schema_version: 1
display_name: <Human Name>
construct: <one line: what this tradition measures>
canonical_source: {title: ..., author: ..., locus_unit: ...}
adherent_noun: <e.g. Muslim>    # feeds the universal Stated framing
maintainers: [{name: ..., contact: ...}]   # at least one
scholar_review: {status: none, reviewers: []}   # none | in_progress | reviewed
taxonomies:                     # your own tag axes; each value set non-empty, no dupes
  <axis>: {description: ..., applies_to: scenario|response, values: [...]}
scenario_id_pattern: '^...$'     # regex every scenario id (and folder name) must match
```

### 3. Write the tradition prose (all **non-empty**)
- `README.md` — overview of the tradition.
- `source.md` — the canonical source and **why it is consensus-grade**.
- `guide.md` — the one-page companionship guide (the Guided-framing system prompt).

### 4. Create the scenario bank
Make `scenarios/` with:
- `scenarios/index.json` — `{"schema_version": 1, "scenarios": ["<ID-1>", "<ID-2>", ...]}`. It
  must list **exactly** the scenario folders on disk (any mismatch is a drift error).
- One folder per scenario, named by its id (matching `scenario_id_pattern`).

### 5. Fill each scenario folder `scenarios/<ID>/`
- `scenario.yaml`:
  ```yaml
  id: <ID>                      # must equal the folder name
  tags:                         # every declared taxonomy axis present; values from that axis
    <axis>: [<value>, ...]
  source_locus: <int>
  locus_label: <human label>
  identity_signal: clean        # clean | leaky | intrinsic
  ```
- `turn1.md` — the turn-1 opening scenario (prose, non-empty).
- `judge-guidance.md` — **the judge's binding ground truth** for this scenario (the proof
  texts / direction). Required and non-empty — this is what the judge is anchored to.
- `pressures.md` — one `## ` section per **core pressure**, each non-empty. The six core
  pressures (use these exact headings):

  ```
  ## secularize
  ## insistence
  ## false_authority
  ## good_cause
  ## flattery
  ## personal_appeal
  ```

  Headings are normalized (lowercase, spaces/hyphens → `_`), so `## False authority` also
  works; content before the first `## ` is ignored.

## Notes
- **Framings and pressures are universal core** — you do NOT define them. You only supply
  `adherent_noun` (Stated), `guide.md` (Guided), and each scenario's `pressures.md` text.
- Every prose file and every `pressures.md` section must be **non-empty**.
- Single language: there is no multilingual support and no separate proof-text corpus.

## 6. Validate (the last step — fix until it passes)
Run from the repo root and resolve every finding until it exits 0:

```bash
uv --project apps/tradition_validator run python -m tradition_validator validate traditions/<id>
```

A clean run (`PASS`, exit 0) means the tradition conforms to the format and is ready for
the workflows that consume it.
