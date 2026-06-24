# Spec 1 — Revision brief (architect → builder)

*Received 2026-06-23T23:38:51Z at the spec-approval gate. User-reviewed. Saved here
verbatim as the source of the iteration-2 restructure.*

The user reviewed the spec at the spec-approval gate. Incorporate ALL changes below.

## ⭐ TOP PRIORITY (the user's explicit approval condition)
**Move the format to a file-based Markdown structure — NOT big JSON files.** The
user "really hates large JSON." Prose lives in `.md` (human-readable); structured
metadata lives in small machine-readable files. The design goal is **both human-
and machine-readable.** The architect will NOT approve the spec gate unless this
is genuinely honored.

## Changes

1. **Rename tradition `islam` → `sunni-islam`** (Riyāḍ al-Ṣāliḥīn / al-Nawawī is a
   Sunni source). `id: sunni-islam`, dir `traditions/sunni-islam/`, `display_name:
   Sunni Islam`. Rename the existing `traditions/islam/` stub and update the README
   link on the branch. Keep the `JLS-` probe id scheme.

2. **Framings & pressures → UNIVERSAL / core**, not per-tradition. The six pressure
   types and three framings live in core, defined once. Remove `pressures`,
   `framings`, `pressures.json`, and the override machinery from the per-tradition
   contract. Rationale: cross-tradition comparability — every tradition is tested
   against the SAME pressures/framings. The only faith-specific remainder stays
   local: `adherent_noun` (for the stated-framing template) in `tradition.yaml`;
   `guide.md` (guided framing); per-probe pressure text.

3. **Probes become FOLDERS, prose in Markdown** (the headline change):
   ```
   traditions/sunni-islam/
     tradition.yaml      # id, display_name, construct, canonical_source, adherent_noun,
                         #   maintainers, scholar_review, taxonomies, probe_id_pattern
     README.md  source.md  guide.md
     probes/
       index.json        # lightweight: list of probe folders + bank schema_version
       JLS-001/
         probe.yaml          # id, tags{...}, source_locus, locus_label, identity_signal
         scenario.md         # turn-1 scenario (prose)
         judge-guidance.md   # the judge anchor (the old §5.5 "seam")
         pressures.md        # one `## <pressure>` section per CORE pressure
   ```
   - Per-probe metadata in `probe.yaml` (machine); prose in `.md` (human).
   - `pressures.md` uses one heading per core pressure; validator checks all present.
   - Discovery: glob `probes/*/`; `index.json` lists folders and the validator
     checks index ⟺ folders match (drift = error). No monolithic probes.json.

4. **Remove `source_map.json` entirely** (overkill). Keep `source_locus`/
   `locus_label` as plain probe metadata; drop the map file and its integrity check.

5. **Remove ALL multilingual support.** Drop `languages`, language variants, and
   `translations`. Single language. (Consistent with how JaleesBench actually judged
   — the embedded English anchor.)

6. **Remove `proof_texts.json` corpus.** Redundant now that each probe's
   `judge-guidance.md` is the anchor. Source material = `source.md` (prose) +
   per-probe `judge-guidance.md`.

## Net effect on the validator
Drop language-parity, source-map integrity, and corpus checks. Add: probes/ folder
structure, `probe.yaml` schema, `pressures.md` heading-coverage against the core
pressure set, and index⟺folders drift. The "seam" gets stronger: `judge-guidance.md`
per probe is unambiguously the judge's binding.

## Process
- Revise the spec to reflect all of the above.
- Re-run your 3-way consult on the revised spec (per your gate note).
- Return to the spec-approval gate.

## On approval (from the user)
- The user has PRE-APPROVED the direction and the plan, **contingent on the
  file-based md structure being honored** — the architect verifies that, then
  approves the spec gate (and plan gate). No separate plan sign-off wait.
- **DELIVERABLE:** once the spec is finalized/approved, **open a PR that includes
  the spec** so the user can share it with others. Continue plan + implementation
  on the same branch/PR (the PR grows).

Questions → message the architect.
