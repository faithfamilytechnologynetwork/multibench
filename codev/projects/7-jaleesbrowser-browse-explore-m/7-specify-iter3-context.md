### Iteration 1 Reviews
- codex: REQUEST_CHANGES — Strong, well-bounded spec, but it still needs two behavior clarifications around degraded-content handling and index/folder drift before it is builder-ready.
- claude: COMMENT — High-quality spec with sharp scope boundaries; six minor clarifications would tighten it further but nothing blocks proceeding.

### Builder Response to Iteration 1
# Spec 7 — Specify iteration 1: rebuttal

**Reviewers:** Codex (REQUEST_CHANGES), Claude (COMMENT). Both rated the spec strong and
well-bounded with no blockers; their points converged on the same set of one-sentence
sharpenings. **I accepted and incorporated all of them** — there are no disagreements to
defend. Below, each point maps to the concrete spec edit.

## Codex (REQUEST_CHANGES)

1. **Fail-soft vs fail-loud internally inconsistent for broken scenario files.** — *Agreed;
   this was the one substantive issue.* §3 and §8 both listed "unreadable file" under
   fail-loud, contradicting the display-first posture. **Fixed** by adding the **§8
   degradation-scope table** that classifies every failure as **invocation** (abort,
   non-zero exit), **tradition**, **scenario**, or **section** (the last three degrade to
   inline notices), and by re-classifying an unreadable / non-UTF-8 / oversized / malformed
   *content* file as data-to-display (notice), not a process abort. Missing `turn1.md`,
   invalid UTF-8 in `judge-guidance.md`, permission-denied `pressures.md` are now each given
   an explicit row and behavior.

2. **`index.json` ↔ folder drift not specified tightly.** — *Agreed.* **Fixed** in **M6**
   and the §8 table: render the **union**, ordered by `index.json` with orphan folders
   appended (id-sorted); **folder authoritative for content, index for declared order**;
   orphan (folder ∉ index) and ghost (index entry, no folder) each render with an inline
   notice. No more ambiguity over union/intersection/order.

3. **Prev/next navigation order ambiguous.** — *Agreed.* **Fixed** in **M9**: prev/next
   follows the tradition's **default declared order** (the M6 order) so each static page has
   deterministic neighbors; filtered/sorted-view nav is a client-side layer that does not
   change the canonical page links (keeps deep links stable and testable).

4. **Read-only acceptance should be testable.** — *Agreed.* **Fixed** in **§10.5/§10.7**:
   a **fixture-tree snapshot invariant** — hash every path under the tradition root before
   and after both `build` and `serve`, assert identical.

5. **Security: require escaping/safe serialization, not just markdown sanitization.** —
   *Agreed.* **Fixed** in the new **§8 Security** block: Jinja **autoescape on**; sanitized
   markdown pipeline; embedded filter-index JSON **safely serialized** (`</` escaped);
   query-string filter state **validated + escaped** on restore (fail-soft to defaults); plus
   path-containment and the 5 MiB size cap (point shared with Claude).

## Claude (COMMENT)

1. **Filter semantics within an axis undefined (OR vs AND).** — *Agreed.* **Fixed** in
   **M7**: **OR within a single axis, AND across axes**; free-text search ANDs with the rest.

2. **Index↔folder divergence in display-first mode.** — *Agreed.* Same fix as Codex #2 (M6 +
   §8 table: union with orphan/ghost notices).

3. **Static-site link integrity not a test target.** — *Agreed.* **Fixed** in **§10.6/§10.7**:
   all generated inter-page links (tradition→scenario, prev/next, back-to-index) must
   resolve; link integrity is an explicit integration-test assertion.

4. **Path-containment + size-cap should be explicit, not inherited-by-hope.** — *Agreed.*
   **Fixed** in §8 Security: jaleesbrowser **replicates** the validator's symlink/`..`
   containment guard and `MAX_FILE_BYTES` cap; an escaping/oversized file is a located
   notice.

5. **Self-contained static output (no external CDN).** — *Agreed.* **Fixed** as an explicit
   **non-functional requirement in §10**: no external CDN/network references; works offline.

6. **"Inline notice" undefined.** — *Agreed.* **Fixed** in §2.4: defined once as "a visually
   distinct warning block rendered into the HTML page, never a console log."

7. **Confirm #6 actually renames `scenario.md` → `turn1.md`.** — *Agreed; good catch.* This
   is #6's least-obvious rename. **Noted** in §8 (format-names-isolated bullet) and §9 R1:
   the constants module must account for it and it must be **confirmed against #6's actual
   implementation at rebase**.

## Items both reviewers explicitly deferred to Plan (no spec change needed)

- `watchfiles` vs polling for `serve --watch` (stdlib has no watcher) — Plan picks the mechanism.
- Import-dependency on `tradition_validator` vs. a vendored lenient read-model (I1) — the spec
  fixes only the *posture* (display-first); the dependency topology is a Plan decision.
- Concrete markdown renderer + sanitizer pick (I3, e.g. `markdown-it-py` + `nh3`/`bleach`).

Both reviewers endorsed **Approach A** (Python static-site generator) over B, and the
**post-rename-with-synthetic-fixtures** sequencing for the #6 dependency.


### Iteration 2 Reviews
- codex: REQUEST_CHANGES — Strong re-spec overall, but it dropped a few builder-critical behavior decisions during the architecture pivot and still has one internal inconsistency around framework choice.
- claude: APPROVE — High-quality re-spec with sound architecture; four minor clarifications would tighten it but nothing blocks proceeding to human review and plan rewrite.

### Builder Response to Iteration 2
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


### IMPORTANT: Stateful Review Context
This is NOT the first review iteration. Previous reviewers raised concerns and the builder has responded.
Before re-raising a previous concern:
1. Check if the builder has already addressed it in code
2. If the builder disputes a concern with evidence, verify the claim against actual project files before insisting
3. Do not re-raise concerns that have been explained as false positives with valid justification
4. Check package.json and config files for version numbers before flagging missing configuration
