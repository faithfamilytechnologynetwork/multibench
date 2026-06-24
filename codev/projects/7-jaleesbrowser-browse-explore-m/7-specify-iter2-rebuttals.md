# Spec 7 — Re-spec (specify iter-2): rebuttal

**Context:** this is the **re-spec** after the architecture pivot (static-site → live web app +
GitHub runtime data layer + Railway). **Reviewers:** Codex (REQUEST_CHANGES — 3) · Claude
(APPROVE — 4 minor, overlapping). Both verified the data format + GitHub facts against the live
repo and called the architecture sound. All points **accepted and folded in** — no disagreement.

## Codex (REQUEST_CHANGES)

1. **Degradation/drift behavior not restated tightly enough.** Correct — the rewrite dropped the
   prior spec's §8 degradation table. → **Restored as new §5.5**, adapted to the live/GitHub
   model: a full table over startup / GitHub-layer / tradition / scenario / section / snapshot
   classes, explicitly covering `index.json`↔folder drift (union, index-ordered, orphan/ghost
   notices), missing prose, stub-tradition on a bad manifest, missing scenario section files, and
   the incomplete-row (ghost/stub) filtering rule.

2. **C1 open but acceptance/deploy wording assumed Flask.** → **Closed C1: Flask is DECIDED**
   (§5.1; confirmed by the consult — neither reviewer advocated FastAPI; the architect's "keep it
   relatively simple" supports it). §5.4 deploy and §9 acceptance are now intentionally
   Flask-specific; FastAPI+httpx documented as the fallback. Inconsistency resolved.

3. **Removals/drift after refresh unspecified.** → Added the **Snapshot** row to §5.5 and a line
   to §5.2: a tradition/scenario removed from `main` is absent from the next tree → drops from the
   index and 404s on direct links against the new snapshot; old-SHA cache discarded.

## Claude (APPROVE — minor, all folded in)

1. **Cache eviction / bounded memory.** → §5.2: **single live snapshot** — when a new SHA is
   confirmed, the prior SHA's cached data is discarded, so memory doesn't grow across commits on
   Railway.
2. **Deleted-tradition behavior** — same fix as Codex #3.
3. **§9.7 "Flask test client" vs open C1** — resolved by deciding Flask (Codex #2).
4. **`source_locus` range inclusivity** → M5: inclusive on both ends; one-sided (only min or only
   max) allowed.

Claude also confirmed the §2.4 format and §2.5 GitHub facts are accurate against the real repo
(both traditions, the tree-API/raw/rate-limit claims), the SSRF/traversal mitigation is correct,
and the results-ready seam is well-bounded. The `GET /` "about" ambiguity it noted is already
resolved by the spec (MUST = tradition cards; intro text = COULD N2) — no change needed.

Net: every REQUEST_CHANGES item is a one-paragraph clarification now in the spec; the live/GitHub
architecture is unchanged and endorsed.
