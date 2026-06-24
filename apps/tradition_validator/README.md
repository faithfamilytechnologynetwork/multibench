# tradition_validator

Validates a MultiBench **tradition** module against the canonical file-based format
(prose in Markdown, metadata in small YAML, a tiny `scenarios/index.json`). The format
contract is documented in [`../../traditions/README.md`](../../traditions/README.md) and
Spec 1 (`codev/specs/1-traditions-folder-layout-spec-.md`).

Discovery and validation are **mechanical**: the validator reads the same files an author
writes, fails fast, and reports **located, actionable** errors — it never guesses or
"fixes."

## Install

Run from this package directory:

```bash
cd apps/tradition_validator
uv sync
```

## Usage

From `apps/tradition_validator/`:

```bash
uv run python -m tradition_validator validate <tradition-dir>
uv run python -m tradition_validator validate-all <traditions-dir>
```

Or from the repo root, target the package with `--project` (the tradition path is then
relative to the repo root):

```bash
uv --project apps/tradition_validator run python -m tradition_validator validate traditions/sunni-islam
```

Options:

| Option | Effect |
|---|---|
| `--strict` | Escalate warnings to errors (non-zero exit on any warning). |
| `--format text\|json` | Human report (default) or machine-readable findings. |

Exit codes: `0` when clean (no errors, and under `--strict` no warnings); `1` when
validation finds problems — including when the given path is not a directory, which
`validate` reports as a located finding; `2` for an invocation error (a bad `--format`
value, or — for `validate-all` — a missing/empty traditions directory).

## What it checks

- **Structure** — all required files/dirs present.
- **Manifest** (`tradition.yaml`) — closed + strictly-typed schema; `id` is a slug and
  equals the directory name; `scenario_id_pattern` compiles; taxonomies well-formed.
- **Index ⟺ folders** — `scenarios/index.json` matches the `scenarios/*/` folders exactly.
- **Each scenario** — `scenario.yaml` (id == folder, matches the pattern, unique; tags cover
  every declared axis with declared values); `turn1.md` and the `judge-guidance.md`
  **seam** non-empty; `pressures.md` carries all six core pressures, each non-empty.
- **Prose** — `README.md` / `source.md` / `guide.md` non-empty.
- **Safety** — UTF-8 only; YAML via safe-load (no code execution); symlink/`..` escapes
  rejected; oversized/malformed files yield a located error, not a traceback.

### Error-report shape (`--format json`)

```json
{ "tradition": "<path>", "ok": false,
  "findings": [ {"severity": "error", "file": "<path>", "path": "<field|null>", "message": "..."} ] }
```

(`validate-all` wraps these as `{ "ok": <bool>, "traditions": [ ... ] }`.)

## Porting a tradition from JaleesBench (one-time)

`port_jaleesbench.py` is a one-time migration that generates `traditions/sunni-islam/`
(in the canonical scenario-folder layout) from a staged JaleesBench source tree (it
`ast`-parses the source — no code execution):

```bash
# stage the source (gitignored), e.g. via gh api into tmp/jaleesbench-source/
uv --project apps/tradition_validator run python -m tradition_validator.port_jaleesbench \
    --source tmp/jaleesbench-source --out traditions/sunni-islam
```

## Develop

```bash
cd apps/tradition_validator
uv run pytest
```
