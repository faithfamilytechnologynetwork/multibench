# lessons-critical.md — Always-On Engineering Wisdom (HOT tier)

<!-- HOT tier: capped lessons + a bounded map of lessons-learned.md. Always injected into
every porch phase prompt and into CLAUDE.md/AGENTS.md. CAP: <=10 lessons, <=12 map topics,
<=35 lines. To add a lesson, DEMOTE a weaker one into lessons-learned.md (displacement).
MAINTAIN polices the cap and keeps the map in sync with lessons-learned.md's sections. -->

## Critical lessons (consult before deciding)
- Check for existing work (PRs, git history) before building from scratch.
- "It compiled" / "tests pass" is not "it works" — verify the real user path before calling it done.
- When stuck (2 failed hypotheses or ~30 min), get an outside perspective instead of guessing.
- Derive a data format from the **real reference data**, not its docs — load-bearing details (e.g. the embedded judge anchor) only show up there.
- **Multi-app porch tests-check:** `porch.checks` is global, so a hardcoded/guarded `&&`-chain breaks builders lacking another app's toolchain (and `&&`/`||` masks real failures). Use the **per-builder dispatcher** `.codev/checks/test.sh` — run only the touched app's suite via a registry. Keep it.
- **HeroUI v3 is provider-less** — there is no `HeroUIProvider` (only I18nProvider/ToastProvider/useTheme); wire styling via `@import "@heroui/styles"`, don't add a v2-era provider.
- **A client-side GitHub data layer** is unauthenticated (60/hr per IP, may be NAT-shared, no safe token): SHA-pin the tree (≈1 call/snapshot), fetch content via `raw` (off the API budget), poll the commit SHA gently (`refetchInterval`; `staleTime` alone does NOT poll), serve stale + a banner on 403.
- **Gemini's per-phase impl/code consult can't see the worktree here** (no verdict → blocks unanimity); per-phase consult is `["codex","claude"]` — do full 3-way only where the diff is fed inline (the PR integration CMAP).
- Porch only re-extracts plan phases at the plan→implement transition; adding a phase mid-implement needs `porch rollback <id> plan` + plan re-approval.

## Map of lessons-learned.md (consult when…)
- Toolchain & protocol environment (Python + porch) — consult when porch checks/consults misbehave in this Python repo.
- Data-format design — consult when designing or extending a data or file format.
- Verification discipline — consult when deciding whether something is actually "done."
