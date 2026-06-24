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
