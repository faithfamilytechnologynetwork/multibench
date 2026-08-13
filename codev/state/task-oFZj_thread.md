# task-oFZj — multibrowser `/raw/$runId` landing UI tweaks

Standalone task (no porch project). Three UI tweaks from Waleed to the raw-explorer landing
(`RawRunPage`, shipped in #54/PR80), plus the data change tweak #2 requires.

## What changed
1. **Single column** — the item list is now `flex flex-col` (was a `sm:grid-cols-2 lg:grid-cols-3`
   grid).
2. **Full question text** — labels wrap (`break-words`, `min-w-0 flex-1`) and no longer `truncate`.
   The landing loads only the manifest (never shards), so the full text must live in
   `catalog.items[].label`. Removed the ≤80-char word-boundary `…` cap in `export_afb._label`
   (now just whitespace-collapse) and **regenerated** `results-raw/afb-20260808/manifest.json`.
   Verified byte-for-byte: shards unchanged, both fingerprints unchanged — **only 45 labels
   un-truncated**. Source of truth is the committed `experiments/54_afb_before_after/data/collection.json`
   (confirmed it reproduces the old manifest exactly before the change).
3. **One list, not two** — dropped the separate `RawPresets` card block. Now a single list of every
   item; items the catalog's presets flag (the export-computed "biggest movers", e.g. AFB's
   `|Δ| dpo vs base`) are emphasized in place (left accent + weight) and carry a **badge per preset**
   (the preset's own label). Highlighted items deep-link with the preset entry's exact
   a/b/scope/conditions (the curated before/after); plain items keep the first-two-subjects default.

Stayed **catalog-generic**: highlights derive from `catalog.presets`, no AFB vocab or hardcoded
threshold in the SPA. `RawPresets` component kept (still used by `ResultsPage` for the MB score tier).

## Decisions
- **In-place highlight, catalog item order** (not highlighted-first). The spec asked to highlight the
  movers and leave everything else "normal" — visual emphasis, not reordering. Highlighted-first
  would be a trivial follow-up if preferred.
- **Badge = preset label** (there is no per-item numeric delta in the catalog — the entry label is
  `ID · question`, and the delta magnitude is only implied by the preset's ranking). The preset
  label ("Omission → repair (|Δ| dpo vs base)") is the catalog's own delta descriptor.

## Verification
- `pnpm -C apps/multibrowser test` → 308 passed. `tsc --noEmit` clean.
- `pytest test_export_afb.py` → 22 passed (rewrote `test_item_label_truncation` →
  `test_item_label_full_text`).
- Updated `rawRun.test.tsx`: the old `presets` two-list assertion → asserts one merged list with
  AFB-001 highlighted (badge present) and AFB-002 plain (no badge).

Deploy handled by Waleed after merge.
