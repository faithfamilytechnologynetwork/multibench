# Spec 7 — Re-spec (specify iter-3): rebuttal

**Reviewers:** Codex (REQUEST_CHANGES — 3 runtime-contract clarifications) · Claude (APPROVE —
"all prior concerns addressed; degradation behavior comprehensive; ready for human review").
All three Codex points **accepted and fixed** — no disagreement; each is a tight runtime contract
a builder needs.

1. **Snapshot swap / stale-cache atomicity (was self-conflicting).** §5.2 discarded the old SHA
   on new-SHA confirmation, while §5.2/§5.5 also require stale-cache fallback on GitHub failure —
   leaving a window where a partial new fetch + GitHub error could make a warm app cold. →
   **Fixed**: §5.2 now specifies an **atomic last-known-good swap** — the new snapshot is
   *promoted* only once successfully discoverable/usable, the old data is discarded **only after**
   promotion, and a mid-refresh failure **defers the swap** (keeps serving the warm snapshot + the
   stale banner). No cold window.

2. **Canonical multi-select filter encoding was missing.** → **Fixed**: §5.3 now mandates
   **repeated params** for multi-value axes (`?pillars=restraint&pillars=justice`), OR-within /
   AND-across; `identity_signal` repeatable; `locus_min`/`locus_max` inclusive/one-sided; `q`;
   `sort`. Unknown axis/values and duplicates are **ignored/de-duped, fail-soft**. Deterministic
   for deep links, forms, and tests.

3. **Startup-fail vs `/healthz` inconsistency.** §5.5 said both "fail fast" and "`/healthz`
   reports unhealthy" — two different Railway modes. → **Fixed** with one contract: invalid
   **required** config → the process **exits non-zero** at startup (don't start a broken server);
   `/healthz` is therefore **pure liveness** (200 whenever up, independent of GitHub). A running
   process is by definition correctly configured.

Net: three one-paragraph runtime contracts added; the architecture is unchanged and Claude
APPROVE'd. The spec is internally consistent on snapshot swapping, filter encoding, and
startup/health semantics.
