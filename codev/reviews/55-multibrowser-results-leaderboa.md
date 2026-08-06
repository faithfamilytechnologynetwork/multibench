# Review: multibrowser /results leaderboard v2 — jaleesbrowser-style dense table, multi-faith

- **Spec**: [codev/specs/55-multibrowser-results-leaderboa.md](../specs/55-multibrowser-results-leaderboa.md)
- **Plan**: [codev/plans/55-multibrowser-results-leaderboa.md](../plans/55-multibrowser-results-leaderboa.md)
- **Status**: implementation complete (4 phases), PR pending
- **Date**: 2026-08-06

## What was built

A **UI + client-aggregation** rewrite of the `/results` leaderboard presentation, replacing #49's
selector-driven one-slice table with the jaleesbrowser dense-table model, extended with MultiBench's
tradition dimension. The #49 data tier (`results/<run-id>/` shards + manifest), the Python exporter,
and the `computeStandings` core are **unchanged and reused** — no export change.

- **Dense board** (one row per subject): First-response / Post-pressure / Δ (steadfastness) headline
  columns on the paper's published slice (first framing), plus one post-pressure column per framing.
- **Per-tradition heat strip** (the multi-faith upgrade): a `scoreColor` square per tradition whose
  non-null mean *is* the Post column, built from `computeStandings`'s own `contributions` (reconciles
  by construction). Accessible (`role="img"` + label; dashed empty cell for uncovered traditions).
- **Sortable** numeric columns with a **persistent canonical rank**; **pressure** reframes the whole
  table (headline + framing columns + strip + rank); **judge selector** repoints only the drill-down
  to Opus (badged, never re-ranks/recolors); **dense per-tradition drill-down** (`—/N` when a Post
  numerator is absent). Run / pressure / judge / sort / expansion are all deep-linkable.

### Phases
1. **Client aggregation** (pure lib) — `computeLeaderboardRows` / `sortRows` / `subjectDrilldownRows`,
   the `Slice` decouple, subject-id column join, structural Gemini-only ranking.
2. **Dense sortable table + URL state** — new selection model (sort + expanded; framing/metric → columns),
   run selector, retained #49 drill-down via a `Slice` literal.
3. **Multi-faith layer** — heat strip, drill-down upgraded to the dense per-tradition table,
   URL-encoded keyboard expansion, accessibility.
4. **Docs + cleanup + verify** — READMEs reconciled to v2, removed the app-dead `subjectTraditionValues`,
   a11y polish, build + preview smoke.

Final: `pnpm -C apps/multibrowser test` → **179 tests green**; `check-types` clean; production bundle
builds; preview serves `/results`.

## #49 supersession (architect action at merge)

This **supersedes the #49 leaderboard presentation**. When this PR merges:
- **Close #49** — its presentation is replaced by this dense-table v2.
- **Retire #49's parked `verify-approval` gate** — it was held pending this successor.

Both are **architect actions** flagged here (the builder does not close #49 or touch its gate).

## Plan exception — pre-merge live smoke deferred to post-merge Verify (architect, 2026-08-06)

The plan's Phase 4 called for a **manual local-preview browser click-through against the real GitHub
runtime**. A headless builder cannot drive a real browser, so the architect **granted an explicit plan
exception**: the pre-merge live click-through is **deferred to the post-merge Verify phase**, and the
following automated evidence is **accepted** in its place:

- The **20-test `results.test.tsx` integration suite** exercises every board interaction (sort +
  persistent rank, whole-table pressure reframe, run switch, heat strip, dense drill-down, keyboard
  expansion + URL round-trip, deep-link restore, judge invariance) against a **byte-faithful GitHub
  fetch stand-in**.
- `pnpm build` succeeds and `pnpm preview` serves the `/results` shell.
- The **real GitHub runtime data path is verified live** — at `main` SHA `7f2c34c` the recursive
  git-tree (non-truncated) lists all 8 `results/20260803/` files and both `manifest.json` (5 subjects,
  7 traditions) and a shard fetch + parse via `raw`. This is the exact runtime dependency the deployed
  board executes.

**Acceptance criterion for #55 (recorded per the architect):** #55 is accepted only on **Waleed's
approval of the live leaderboard's look-and-feel after the post-merge `railway up`**. Until he confirms
it looks right, **both issue #55 and the parked #49 `verify-approval` gate stay open**. Any changes he
requests are **follow-up iterations on the open issue, not scope creep**.

## Integration review — codex REQUEST_CHANGES overruled (architect, 2026-08-06)

The architect's integration CMAP on PR #59 was **gemini + claude APPROVE; codex REQUEST_CHANGES
OVERRULED**. Codex's concern was that the single `k/N` "traditions contributing" count could diverge
per column (a tradition covered for one column but not another), making one count misleading.

**Overrule rationale (recorded):** the **#50 "earned full_grid" invariant** precludes per-column
coverage divergence — a judge either covers a shard's entire grid or is excluded from that shard
wholesale, so whole-shard exclusion is **uniform across all columns**. The Post-slice strip's non-null
count therefore equals every other column's count, and a single `k/N` is correct. This dependency is
now documented at the derivation site in `ResultsPage.tsx` (revisit to a per-column count only if that
invariant is ever relaxed to allow partial per-column coverage).

## Architecture Updates

**No hot-tier `arch-critical.md` change is warranted** — and that is the point worth recording. #55 is a
**presentation rewrite**; the system-shape facts are unchanged:

- The results data tier (`results/<run-id>/` shards + manifest, `analysis export`) is untouched — no
  export change.
- The always-on fact "the `/results` leaderboard ranks **Gemini-only** … Opus is a badged validation
  layer, never re-ranks" (Spec 49) still holds exactly; #55 made that invariant **structural**
  (`computeLeaderboardRows` takes no judge) rather than merely conventional.

So the `arch-critical.md` "Results datasets" fact stays as-is; the only thing that changed is the
*presentation* (a dense sortable table vs the #49 selector strip), which is UI detail, not a hot-tier
system-shape fact. The `results/README.md` and `apps/multibrowser/README.md` (cold/reference docs) were
updated to the v2 presentation as part of Phase 4.

## Lessons Learned Updates

The strongest durable lesson from this work — a candidate the architect may want in the hot
`lessons-critical.md` (it is cross-cutting for **every** multibrowser builder, not just #55):

> **A pure-type break ships green here.** The porch tests-check runs only `pnpm -C apps/multibrowser
> test` (Vitest), and neither Vitest nor `vite build` (esbuild) typechecks. A `Pick<Selection, …>`
> coupling would have broken silently when the selection shape changed. Mitigate per-builder by
> decoupling shared types early and making `check-types` a per-phase definition-of-done; the durable
> fix is adding `check-types` to the multibrowser branch of `.codev/checks/test.sh` (flagged to the
> architect — shared infra, out of #55's scope).

(Placement into `lessons-critical.md` is left to the architect because the hot tier is capped and
displacement is their call; recorded here so it is not lost.)

## Lessons learned

- **A type break can ship green here.** The porch tests-check runs only Vitest, and neither Vitest nor
  `vite build` (esbuild) typechecks. The Phase-2 selection-shape change would have silently broken
  `leaderboard.ts` via a `Pick<ResultsSelection, …>`. Fix: decouple to a standalone `Slice` type in
  Phase 1 *and* make `pnpm … check-types` a per-phase definition-of-done. **Recommended follow-up for
  the architect (out of scope here):** add `check-types` to the shared `.codev/checks/test.sh`
  multibrowser branch so the porch gate itself typechecks — it would protect #51 and all future
  multibrowser builders.
- **Reconcile by construction, then guard it.** Every numeric column reuses `computeStandings`; the
  heat strip reuses its returned `contributions`. `mean(non-null strip) == post` and `post == paper`
  are then true by construction and pinned by a committed-shard test — no second implementation of the
  aggregation convention to drift.
- **Test fixtures must be able to *fail*.** Two review catches were tests that couldn't discriminate:
  a positional-zip row-assembly bug that a `post`-only test would miss (fixed by joining columns on
  subject id + a crossing-order fixture), and a pressure-reframe test where the second subject had no
  data so rank could never change (fixed with a `false_authority` slice that flips the order).
- **Δ is the shard's matched-cell steadfastness, not post − initial** — identical on the complete
  Gemini grid, so the distinctness the UI must preserve lives on a synthetic asymmetric fixture.
- **Accessibility details matter:** `aria-label` on a role-less `<span>` is ignored (`role=generic`
  prohibits it) — the strip cells needed `role="img"`; and `aria-controls` should reference an id that
  exists (gated on `open`).

## Systematic notes

- Every phase's review feedback was incorporated with a written rebuttal (see
  `codev/projects/55-*/*-rebuttals.md`); no feedback was rejected.
- Scope discipline held: all changes are inside the `/results` leaderboard components + client
  aggregation; no contact with #51's raw-results tier, the `results/` data, or the exporter.

## PR prep

- **Rebase onto `origin/main` — DONE** (`git rebase --onto origin/main d0fa576`): dropped the
  `docs/paper/*` files inherited from the branch base (`d0fa576`, whose content already landed on
  `origin` as `9a4f735`), so the branch diff shows only the `/results` leaderboard changes. Verified
  zero conflicts (my commits touch none of those files) and 179 tests still green.
- **Interactive verification:** the 20-test `results.test.tsx` integration suite exercises every board
  interaction (columns, sort + persistent rank, pressure reframe, run switch, heat strip, dense
  drill-down, keyboard expansion, deep-link restore, judge invariance) against a byte-faithful GitHub
  fetch stand-in; `pnpm build` + `pnpm preview` confirm the bundle builds and serves the `/results`
  shell; and the real GitHub data path (git-trees + `raw` for `results/20260803/`) is reachable at the
  current `main` SHA (checked directly). A final human live click-through against the deployed site is
  the post-merge Railway step (per plan, production `railway up` is after merge) — a headless builder
  cannot drive a real browser, so that step is the architect's/user's, not automatable here.
