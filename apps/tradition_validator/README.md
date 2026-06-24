# tradition_validator

Validates a MultiBench **tradition** module against the canonical file-based
format (prose in Markdown, metadata in small YAML, a tiny `probes/index.json`).
See `codev/specs/1-traditions-folder-layout-spec-.md` for the contract.

> Stub — full usage docs land in the documentation phase. Current capability:
> structure-only validation (required files/dirs present).

## Install

Run from this package directory (`apps/tradition_validator/`):

```bash
cd apps/tradition_validator
uv sync
```

## Usage

From `apps/tradition_validator/`:

```bash
uv run python -m tradition_validator validate <tradition-dir>
uv run python -m tradition_validator validate-all <traditions-dir>
# options: --strict (warnings become errors), --format text|json
```

Or from the repo root, target the package explicitly with `--project` (paths to the
tradition are then relative to the repo root):

```bash
uv --project apps/tradition_validator run python -m tradition_validator validate traditions/sunni-islam
```
