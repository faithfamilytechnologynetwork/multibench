# arch-critical.md — Always-On System-Shape Facts (HOT tier)

<!-- HOT tier: capped facts + a bounded map of arch.md. Always injected into every porch
phase prompt and into CLAUDE.md/AGENTS.md. CAP: <=10 facts, <=12 map topics, <=35 lines.
To add a fact, DEMOTE a weaker one into arch.md (displacement). MAINTAIN polices the cap
and keeps the map in sync with arch.md's top-level sections.
STARTER: replace the examples below with YOUR project's facts and arch.md sections. -->

## Critical facts (consult before deciding)
- A **tradition** is a drop-in `traditions/<id>/` directory in the canonical **file-based** format (prose=Markdown, metadata=small YAML; only `probes/index.json` is JSON — no large JSON). Contract: Spec 1 / `traditions/README.md`.
- Core discovers traditions by globbing `traditions/*/tradition.yaml` and probes by `probes/*/`; adding a tradition adds a directory, never changes core.
- **Judge seam:** each probe's `judge-guidance.md` *is* the judge's binding ground truth — there is no separate proof-text corpus; don't reintroduce one.
- **Framings (unstated/stated/guided) + the six pressures are universal core**, identical across traditions; per-tradition only `adherent_noun`, `guide.md`, and per-probe `pressures.md`.
- `apps/tradition_validator/` is the mechanical gate for a tradition before workflows consume it; run from repo root via `uv --project apps/tradition_validator run python -m tradition_validator validate <dir>`.
- This is a **Python (uv) repo**; porch's implement/review checks are overridden for Python in `.codev/config.json` (`porch.checks`) and per-phase consult is `["codex","claude"]` (`porch.consultation.models`).

## Map of arch.md (consult when…)
- <Top-level arch.md section> — consult when <situation>.
- <List your arch.md's top-level sections here as the system grows; keep <=12, top-level only.>
