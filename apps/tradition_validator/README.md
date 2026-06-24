# tradition_validator

Validates a MultiBench **tradition** module against the canonical file-based
format (prose in Markdown, metadata in small YAML, a tiny `probes/index.json`).
See `codev/specs/1-traditions-folder-layout-spec-.md` for the contract.

> Stub — full usage docs land in the documentation phase. Current capability:
> structure-only validation (required files/dirs present).

## Install

```bash
uv sync
```

## Usage

```bash
uv run python -m tradition_validator validate <tradition-dir>
uv run python -m tradition_validator validate-all <traditions-dir>
# options: --strict (warnings become errors), --format text|json
```
