# task-cqgv — corrections to JaleesBench upstream audit doc

## 2026-07-20 — task received & executed

Task: amend `docs/analysis/jaleesbench-upstream-ultracode-audit.md` with four corrections from the
taqwabench architect's independent 8-agent cross-verification (2026-07-19) against the current
upstream jaleesbench repo. Docs-only; the machine-readable record under
`docs/analysis/jaleesbench-upstream-audit/` is a frozen audit artifact (untouched), and
`traditions/sunni-islam/` is untouched.

Applied:

1. **F016** (§3 first bullet) — rewrote: the "true exclusion count is three" conclusion was wrong;
   140 = 139 cluster-derived + JLS-140 authored off-map from bab 370 (I re-verified
   `traditions/sunni-islam/scenarios/JLS-140/scenario.yaml` has `source_locus: 370` before editing).
   Real gap reframed as JLS-140's undocumented provenance + stale "139" in the design doc.
2. **F048** (§8 bullet + executive seams table) — reworded the inverted "~20:4 wife/husband asker
   skew" to "male-vs-female-marked asker skew (20 probes say 'my wife' vs 4 'my husband')" in both
   places. Finding stands.
3. **F030** (§4 bullet) — softened "silently dropped": failed cells print and stay pending, either
   judge can drop; operative defects are the `judge_all` exit-code gap (F031) and uncounted drops in
   `build_report`.
4. **F021** (§3 last bullet) — marked stale/overtaken (current upstream 10-subject run is fully
   dual-judged); kept as a historical record of the audited snapshot.

Also added a dated `## Corrections (2026-07-19 cross-verification)` section near the top crediting
the taqwabench architect and listing all four, so the correction trail is explicit.

Next: commit (doc + this thread), push, open PR
"docs(analysis): corrections to JaleesBench upstream audit from taqwabench cross-verification".
