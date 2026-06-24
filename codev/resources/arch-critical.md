# arch-critical.md — Always-On System-Shape Facts (HOT tier)

<!-- HOT tier: capped facts + a bounded map of arch.md. Always injected into every porch
phase prompt and into CLAUDE.md/AGENTS.md. CAP: <=10 facts, <=12 map topics, <=35 lines.
To add a fact, DEMOTE a weaker one into arch.md (displacement). MAINTAIN polices the cap
and keeps the map in sync with arch.md's top-level sections. -->

## Critical facts (consult before deciding)
- A **tradition** is a drop-in `traditions/<id>/` directory in the canonical **file-based** format (prose=Markdown, metadata=small YAML; only `scenarios/index.json` is JSON — no large JSON). Contract: Spec 1 / `traditions/README.md`.
- Core discovers traditions by globbing `traditions/*/tradition.yaml` and scenarios by `scenarios/*/`; adding a tradition adds a directory, never changes core.
- **Judge seam:** each scenario's `judge-guidance.md` *is* the judge's binding ground truth — there is no separate proof-text corpus; don't reintroduce one.
- **Framings (unstated/stated/guided) + the six pressures are universal core**, identical across traditions; per-tradition only `adherent_noun`, `guide.md`, and per-scenario `pressures.md`.
- `apps/tradition_validator/` is the mechanical gate for a tradition before workflows consume it; run from repo root via `uv --project apps/tradition_validator run python -m tradition_validator validate <dir>`.
- This is a **Python (uv) repo**; porch's implement/review checks are overridden for Python in `.codev/config.json` (`porch.checks`) and per-phase consult is `["codex","claude"]` (`porch.consultation.models`).

## Map of arch.md (consult when…)
- System purpose & shape — consult when orienting to what MultiBench measures and why it is multi-tradition.
- Tradition module format — consult when authoring or changing a tradition or any of its files.
- Universal core — framings & pressures — consult when touching framings, pressures, or cross-tradition comparability.
- The judge seam — consult when working on judging, or tempted to add a proof-text corpus.
- tradition_validator — consult when changing a validation rule or the validator CLI.
- Repository layout — consult when deciding where new code or data belongs.
- Toolchain & protocol environment — consult when porch checks/consults misbehave or tests will not run.
