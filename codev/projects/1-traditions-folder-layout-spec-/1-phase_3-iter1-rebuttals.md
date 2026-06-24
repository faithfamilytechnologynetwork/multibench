# Phase 3 (probes) — Rebuttal to iteration-1 impl review

**Reviews:** Codex **REQUEST_CHANGES** (HIGH), Claude **COMMENT** (HIGH). All points
ACCEPTED and fixed.

## Codex REQUEST_CHANGES (2)
1. **Symlink-escape guard incomplete** — `tradition.yaml`, `probe.yaml`, and
   `probes/index.json` were loaded *without* the root-containment check that Markdown
   reads already had, so a symlinked machine-readable file outside the tradition could be
   parsed (violates spec N4). **Fixed:** added `_guard_within` before every YAML/JSON load
   (manifest, index, probe.yaml). New test `test_symlinked_machine_file_escape_rejected`
   symlinks `probe.yaml` outside the tradition and asserts the escape error.
2. **Promised prose/guide tests missing.** **Fixed:** added `test_prose.py` covering empty
   `README.md`, empty `source.md`, missing `guide.md` (T5), and empty `guide.md`.

## Claude COMMENT (4)
1. **T5 (missing/empty guide.md)** → added in `test_prose.py`.
2. **T13 (two folders, same id)** → added `test_duplicate_probe_id` (second folder's
   probe.yaml claims `JLS-001`; asserts the "duplicate probe id" error).
3. **Empty README.md/source.md tests** → added in `test_prose.py`.
4. **`search` vs `fullmatch`** for `probe_id_pattern` → switched to `fullmatch`, so an
   author's unanchored pattern still requires the whole id to match (the Islam pattern is
   already anchored; behavior unchanged for it).

Suite: **66 tests pass** (was 60).
