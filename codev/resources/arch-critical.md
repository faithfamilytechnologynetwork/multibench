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
- `apps/multibrowser/` is the team-standard **frontend SPA** (Vite/React19/TS/Tailwind4/HeroUI/TanStack) that **browses the corpus by reading GitHub at runtime** (client-side TanStack Query: git-trees + `raw`, SHA-pinned); deployed on **Railway as a static site**; bakes no tradition data (new traditions appear without redeploy); read-only, display-first.
- **Multi-language repo** (Python `uv` validator + JS/Vite SPA); porch's implement/review tests-check is a **per-builder dispatcher** `.codev/checks/test.sh` that runs only the suite of each app a builder touched (registry: validator→`uv … pytest`, multibrowser→`pnpm -C apps/multibrowser test`; +1 line/app). Per-phase consult is `["codex","claude"]` (`porch.consultation.models`).
- **Results datasets** are a drop-in committed `results/<run-id>/` tier the SPA reads at runtime like traditions (manifest + per-tradition shards, scores+metadata only, single-digit MB), produced by `analysis export` (reuses the canonical aggregator). The `/results` leaderboard ranks **Gemini-only** (mean of per-tradition means, reconciles with the paper); **Opus is a badged validation layer, never re-ranks**. Contract: Spec 49 / `results/README.md`.
- **Raw-results tier** `results-raw/<run-id>/` (Spec 51 / `results-raw/README.md`): per-scenario gz shards of transcripts+verdicts (~126 MB/run), produced by `analysis export-raw` (reuses #49 loaders; both tiers stamp an equal **source fingerprint**). Served **dual-source** — a same-origin **baked** bundle (primary; `railway up --no-gitignore`) with the committed GitHub tier as authoritative fallback. The raw viewer (`/results/$runId/$groupId/$itemId`) is **catalog-generic** (scale/ramp/axes/subjects/items in the catalog, no MB vocab) so a non-MB catalog (AFB #54) rides it unchanged; **numeric scores + catalog ramp, no band names**.

## Map of arch.md (consult when…)
- System purpose & shape — consult when orienting to what MultiBench measures and why it is multi-tradition.
- Tradition module format — consult when authoring or changing a tradition or any of its files.
- Universal core — framings & pressures — consult when touching framings, pressures, or cross-tradition comparability.
- The judge seam — consult when working on judging, or tempted to add a proof-text corpus.
- The judging & analysis workflows — consult when working on a scoring run or on cross-tradition report/CIs/figures.
- tradition_validator — consult when changing a validation rule or the validator CLI.
- Repository layout — consult when deciding where new code or data belongs.
- Toolchain & protocol environment — consult when porch checks/consults misbehave or tests will not run.
