# Plan 1 — Rebuttal to iteration-1 3-way plan review

**Reviews:** Claude **APPROVE**, Gemini **COMMENT**, Codex **REQUEST_CHANGES** — all HIGH.

**Disposition:** every point **ACCEPTED and incorporated**. No disagreements. Phase
structure unchanged; five targeted edits. Mapping also in the plan's Expert Review section.

## Codex REQUEST_CHANGES (4)
1. **README.md/source.md non-empty validation not an explicit deliverable** (spec §8.2
   check 9) → added a Phase-3 deliverable + tests asserting empty `README.md`/`source.md`
   each → located error.
2. **Phase 4 omitted `traditions/sunni-islam/README.md`** (required, §5.1/M2) → added a
   finalized, conformant `README.md` to Phase 4's generated deliverables.
3. **No phase said the sunni-islam README is finalized from its stub** → Phase 4 now
   states the porter replaces the "to port" stub with a non-empty conformant overview
   before acceptance (Phase 5 may further polish).
4. **T15 "oversized" handling had no concrete approach** → defined a `MAX_FILE_BYTES`
   size guard in `core.py`/`loaders.py` (Phase 3): files over the cap → located error
   instead of being read in; truncated YAML/JSON → located parse error.

## Gemini COMMENT (3) — also incorporated
1. **README.md/source.md non-empty** (same as Codex #1) → done.
2. **Guide-text fetch source underspecified** → Phase 4 now explicitly fetches
   `jaleesbench/jaleesbench/prompts.py` (extract `GUIDE` → `guide.md`, `STATED` → confirm
   `adherent_noun`) and `mapping.py` (`PILLARS`/`HEARTS` → `taxonomies`), alongside
   `probes.json`.
3. **Pydantic strict also rejects unquoted int ids** (`id: 123`/`001`) → noted in Phase 2.

## Claude APPROVE
No changes requested — confirmed full spec coverage, sound tech choices, all 19 test
scenarios assigned, ready for implementation.
