# spir-92 — Multibrowser data platform (Postgres serving layer)

Builder thread. Project 92 / issue #92. Protocol: SPIR (strict). Spec + plan gates warranted.

## Status
- **2026-08-13** — Started. Phase: **specify**. No pre-existing spec; authoring from the issue.
- **2026-08-13** — Spec drafted & committed (`[Spec 92] Initial specification draft`). Signaled
  SPEC_DRAFTED; porch runs the 3-way (codex+claude) consult next. Checks (exists + required
  sections) pass.

## Spec recommendations (my calls, open to consult/architect)
- Overall arch: Postgres+thin API behind existing `lib/queries.ts` hook seam (issue's direction).
- Raw storage: **Postgres bytea** now, object-storage as escape hatch.
- Ingest: **Python `analysis ingest`** → Drizzle-owned schema via SQL + schema-drift contract test.
- Auth: **magic-link primary**, optional GitHub OAuth.
- Cutover order: results → raw → corpus → review (lowest-risk-first).
- 4 Critical open Qs flagged for architect: raw storage, ingest/schema authority, auth scope,
  corpus-in-DB-vs-git.

## Architect resolutions (2026-08-14) — all 4 Critical + 3 Important settled
- Raw storage: **bytea in Postgres** (A); object storage = escape hatch only.
- Ingest: **Python `analysis ingest`** → Drizzle schema via SQL + CI schema-drift contract test (A).
- Auth: **magic-link primary + optional GitHub OAuth**; OAuth-in-first-slice = plan-time cost call.
- Corpus: **moves to DB**. End state = **ZERO runtime GitHub reads** (github.ts + SHA poll retired).
- Cutover: order results→raw→corpus→review approved; **PR PER TIER** (not one mega-PR).
- Fail-soft: **fail visibly with a notice, NO GitHub fallback** (don't rebuild dual-source — the scar).
- Spec finalized with these; running porch check/done → consult → spec-approval gate.

## Consult iter1 (2026-08-14): codex REQUEST_CHANGES, claude COMMENT — both HIGH, converged
Accepted ~all. Spec revised + rebuttal written. Key fixes:
- "UI unchanged" ⚔ "zero GitHub reads" contradiction (8 routes use useLatestSha, RateLimitBanner
  imports github.ts) → reworded to "no redesign, bounded mechanical swaps"; fixed false Current-State claim.
- Ingest: independent per-tier + raw-only runs (AFB) + corpus content-hash provenance + transactional publish.
- Two data classes: serving-cache (rebuildable) vs operational review store (authoritative, backup/restore).
- Review security posture: authz isolation, single-use tokens, CSRF, PII deletion, email-provider (Resend collision).
- Read-endpoint posture + caching; retention N → Important; cost ceiling (actuals, not estimates); per-tier rollback.
Committed `[Spec 92] Specification with multi-agent review`. Running porch done → re-verify.

## Still-open (plan-time)
Freshness/version endpoint · API framework (Hono/Fastify/Express) · review data model (w/ Ben) ·
OAuth-in-first-slice y/n · raw retention N.

## Spec gate: APPROVED by Waleed (2026-08-14). Advanced to PLAN.

## Plan (2026-08-14) — DRAFTED
9 phases across **4 tier-PRs** (results→raw→corpus→review), architect's PR-per-tier call.
Plan-level decisions settled:
- API framework: **Hono** (+Drizzle +node-postgres); Fastify fallback.
- Freshness: single **`GET /api/version`** per-tier provenance envelope; replaces SHA poll.
- **Table-level Drizzle schema for all serving tiers = Phase 1** (architect note). Review tables =
  Phase 8 migration, gated on Ben's sign-off.
- Raw retention **N=2**; review auth first slice = **magic-link only** (OAuth deferred).
- Magic-link email transport chosen w/ Ben, **must not collide with `resend` CLI rule** (no direct
  api.resend.com; default Postmark/SES).
- Read cache: fingerprint-keyed ETag + immutable.
- Pre-always-on **cost gate** vs actuals (not a phase).
Phase→PR: P3→PR1(results), P5→PR2(raw), P7→PR3(corpus, deletes github.ts → ZERO GitHub reads), P9→PR4(review).
Flagged risk: porch multi-PR-per-project gate friction — raise w/ architect before P3 opens PR1.
Checks pass (plan_exists, has_phases_json, 9 phases). Signaling PLAN_DRAFTED → porch 2-way consult.

## Plan consult iter1 (2026-08-14): codex + claude BOTH REQUEST_CHANGES, HIGH — accepted ~all
Claude verified vs worktree; both surfaced real implementability gaps. Revised 9→11 phases. Key fixes:
- **Drift-guard had no CI** — cross-registered contract test in .codev/checks/test.sh (Phase 1).
- **No test-Postgres** — PGlite (TS) + pytest-postgresql (Python), DATABASE_URL-gated (Phase 1).
- **Immutable-cache unsafe on stable URLs** — fingerprint-qualified content URLs; /api/version no-store.
- **Ingest committed-tree-bound** (refuse dirty paths) → provenance-rebuild + full drop-and-rebuild tests.
- **Retention N=2** actually implemented: transactional prune, per-dataset-lineage (AFB never evicted).
- **Phase 7 github.ts blast radius** corrected: rateLimit.ts, queryClient.ts, fakeRepo.ts, 9 sites
  (incl. RootLayout); zero-GitHub guard scoped to RUNTIME hosts only (reviewReport opt-in links kept).
- **fakeApi.ts harness** built Phase 3; git-modeling tests named as rewrites (not "unchanged").
- **Phase 9 split → 9/10/11** (sync→async persistence / submission+assignment / aggregation); dropped
  misapplied "only seam" quote.
- Topology (CORS + cross-site cookies), PII-deletion endpoint, optimistic-concurrency conflict, verified
  backup/restore (Phase 8). Cost gate = Phase 1 precondition. RAW_SCENARIO_QK exclusion KEPT (scar).
Committed `[Spec 92] Plan with multi-agent review`. Rebuttal written. → porch done, expect plan-approval gate.
Flagged to raise w/ architect: porch pr-gate × multi-PR before Phase 3 opens PR1.

## PLAN RE-CUT (architect/Waleed, 2026-08-15) — still AT gate, revised in place (no rollback)
Direction: **REVIEW-FIRST bare-minimum**; serving tiers DEFERRED (kept in plan, later PRs). Re-cut 11→**13 phases, 6 PRs**:
- PR1 = infra scaffold + review schema + auth; PR2 = persistence swap + submission.
- PR3 results, PR4 raw, PR5 corpus (deferred serving, all iter-1 fixes retained); PR6 review assignment+dashboards (deferred).
- **Phase 1 slimmed** to bare service scaffold: Hono+Drizzle+node-postgres, PGlite rig, Railway+PG, CORS/cross-site-cookie, engines.node>=20. CUT serving tables/ingest/drift-guard/version/fingerprint-URLs → moved intact to Phase 5.
- **AUTH SIMPLIFIED** (test tool, ~5 users): email+password (argon2id), NO magic-link, NO mail/ at all,
  httpOnly Secure SameSite=None revocable cookies, CSRF, per-reviewer isolation, invite-code gate (REVIEW_INVITE_CODE, flagged for Waleed veto).
- **Addendum**: dropped verified backup/restore + restore-check (Railway managed backups + 1 README line);
  account-deletion trivial/SQL one-liner; skipped enumeration/rate-limit hardening. Kept only cheap hygiene.
- Ben #85 gate STANDS (schema migration only after his sign-off). Cost gate = review-only tiny envelope, brought to architect before provisioning.
- Addressed architect inline Q: Hono≠Drizzle (framework vs ORM); recommend Hono, Express as boring fallback — flagged for their confirm.
Committed & resubmitting at plan gate. Architect reviews, Waleed approves.

## PLAN APPROVED by Waleed (2026-08-15). Hono confirmed, REVIEW_INVITE_CODE kept. → IMPLEMENT.

## Phase 1 (implement) — API service scaffold — CODE DONE, provisioning gated
Built apps/api: Hono + Drizzle + node-postgres (prod) / PGlite (tests), tsx runtime, `build`=tsc typecheck.
Files: package.json (engines.node>=20), tsconfig, vitest.config, drizzle.config (schema/index.ts empty —
tables come Phase 2/5), .env.example (DATABASE_URL/ALLOWED_ORIGINS/PORT), railway.json (NIXPACKS,
healthcheck /api/health), README. src: db.ts (Database iface, ping via drizzle select 1), cors.ts
(allow-list parser), app.ts (createApp(db,opts), hono/cors credentialed allow-list), routes/health.ts
(200/503), server.ts (fail-fast on missing DATABASE_URL). Tests: health (PGlite 200 + 503) + cors (6 total).
Registered apps/api in .codev/checks/test.sh. Dispatcher runs it → 6/6 green. Build/typecheck green.
Committed `[Spec 92][Phase: implement] feat: apps/api service scaffold`.
**HOLDING PHASE_COMPLETE**: last deliverable = Railway provisioning, gated on architect cost-OK
(Waleed bound: bring review-only envelope BEFORE provisioning). Sent envelope, awaiting go-ahead.

## COST GATE APPROVED (architect, $40/mo ceiling, smallest footprint). PROVISIONED & VERIFIED:
- Railway workspace Haadi, DEDICATED project **multibench-api** (id 5154c67b) — isolated for clean cost reconcile.
- API service **multibench-api** (id 5d25f594): no replicas, default region (US West/lax1), no reserved sizing.
  Public URL: https://multibench-api-production.up.railway.app
- **Postgres** managed template (postgres-ssl:18), US West, usage-based volume. DATABASE_URL via ${{Postgres.DATABASE_URL}}.
- **/api/health VERIFIED on public URL → 200 {"status":"ok","db":"up"}** (live Postgres round-trip). CORS creds present.
- Deploy = `railway up` (Nixpacks). Follow-up (non-blocker): wire GitHub auto-deploy source at/after PR1 merge.
- ALLOWED_ORIGINS not set on service yet (no cross-origin caller until Phase 2/3 SPA integration).
Reported all to architect. All Phase-1 deliverables met. Signaling PHASE_COMPLETE → per-phase consult (codex+claude).

## Phase 1 consult iter1 (2026-08-15): codex + claude BOTH REQUEST_CHANGES (HIGH) — accepted all
3 blocking, all fixed:
- **pglite in PROD import graph** (codex): db.ts imported @electric-sql/pglite (devDep) → prod-only
  install would crash. Moved adapter to test-only `src/testing/pglite.ts`; db.ts = node-postgres only.
- **pg.Pool no 'error' listener** (claude): idle-client error crashes always-on process. Added pool.on('error').
- **CORS negative test passed for `*`** (claude): changed to assert toBeNull(). Added OPTIONS preflight test.
Minors fixed: startup allow-list log, PORT NaN guard, removed unused @/* tsconfig path, documented
drizzle.config `?? ''` (generate needs no URL). Deferred: Database.close() → Phase 2.
Build green, **7/7 tests** (was 6). **REDEPLOYED** — new deploy d767a5e0 Online, boot log shows new
CORS line, /api/health 200 {ok,db:up}: fixed prod code live & clean without pglite.
Committed fix. Rebuttal written. → porch done to re-verify.

## Phase 1 consult iter2 (2026-08-15): codex APPROVE + claude APPROVE. **PHASE 1 COMPLETE** (porch ✓).
Live: https://multibench-api-production.up.railway.app/api/health → 200 {ok,db:up}. PR not opened yet
(PR 1 = Phases 1–2 together per plan).

## Phase 2 — BLOCKED on Ben's #85 sign-off (baked precondition)
Porch advanced to phase_2 (Review schema + email/password auth — opens PR 1). Plan + architect bind:
**review-schema migration is written ONLY AFTER Ben (@benolio) signs off on the #85 data model.**
Checked #85: no data-model sign-off from Ben (only Waleed's 2026-08-14 scope-update comment). → HOLDING.
Notified architect to coordinate Ben's sign-off. NOT writing the migration until then.
(Note: /compact advisable before phase_2 per porch's phase-boundary reminder.)

## Phase 2 partial — architect approved option (c): schema-INDEPENDENT primitives only. DONE + PARKED.
Built (no tables/migration/sessions/routes): `src/auth/password.ts` (argon2id via @node-rs/argon2,
default variant pinned by a `$argon2id$` test), `src/auth/constantTime.ts` (sha256-digest timingSafeEqual),
`src/auth/inviteCode.ts` (fail-closed REVIEW_INVITE_CODE gate), `src/auth/csrf.ts` (double-submit token
gen/verify). +7 tests. Build green, dispatcher 18/18 green. Committed.
Note: @node-rs/argon2 `Algorithm` is an ambient const enum → can't import under verbatimModuleSyntax;
dropped the explicit option, rely on argon2id default, guarded by the `$argon2id$` assertion.
**PARKED**: that exhausts the schema-independent scope. Rest of Phase 2 (reviewers/sessions/reviews/
submissions tables + migration + session persistence + auth routes) stays blocked on Ben's #85 sign-off.
Did NOT signal PHASE_COMPLETE (phase_2 not complete). Awaiting architect relay of Ben's sign-off / model.

## Phase 2 UNBLOCKED (Waleed owns model, final, 2026-08-15) — BUILT + LIVE-VERIFIED.
Drizzle schema (4 tables: reviewers/sessions/reviews(drafts,version)/submissions(immutable)) matching
Waleed's model exactly. Migration generated → reviewed → applied (drizzle 0000_review_store.sql).
Auth on the parked primitives: signup (invite-gated, fail-closed), login, logout, /me, DELETE /account.
Sessions = server-side rows (token hash stored; revoke=delete). Cookies httpOnly Secure SameSite=None.
CSRF double-submit on authed mutations. FK ON DELETE CASCADE. AppDb type unifies node-pg/pglite.
**Migration apply**: internal Railway host unreachable locally (no public proxy) → runtime migrator
`src/migrate.ts` + railway.json `preDeployCommand: pnpm migrate` (drizzle-orm programmatic migrator,
runtime dep; applies committed reviewed SQL inside Railway; idempotent; NOT db:push).
Tests 23/23 (PGlite runs the REAL migrations). Build green.
**LIVE smoke** (redeploy 59d5706a): /me 404→401 (new deploy+migration ok), signup 201, /me 200,
DELETE /account 200 (cascade) — DB left clean. Set REVIEW_INVITE_CODE on the service (value in Railway env only — not recorded here)
(reported to Waleed to keep/rotate).
Committed schema+auth+migrate-infra. Plan updated with Waleed's out-of-sample requirement (PR 2 phases).
→ signal phase_2 PHASE_COMPLETE. PR 1 (Phases 1+2) opens after phase_2 verification approves.

## Phase 2 consult iter1 (2026-08-15): codex + claude BOTH REQUEST_CHANGES (HIGH) — accepted all.
- **CSRF unusable cross-site** (both, load-bearing): SPA on diff origin can't read mb_csrf cookie
  (up.railway.app = public suffix). FIX: return csrfToken in signup/login body + GET /api/auth/csrf;
  cookie stays the compare half. Tests assert body==cookie.
- **deleteCookie dropped Secure/SameSite=None** (claude) → cross-site clear rejected. FIX: clearAuthCookies helper.
- **No two-reviewer isolation test** (both, plan criterion). ADDED.
- Minors: stale README blockquote → Phase 2; signup race → onConflictDoNothing (409, race-safe);
  expired-session pruning documented (deferred).
- Claude ask: PR 1 description must carry the Ben-override (Waleed owns model, final). WILL DO in PR1 desc.
Build green, **25/25** tests. Redeployed (eff3ac07) for the CSRF body contract; verifying /csrf live.
Committed fixes. Rebuttal written. Architect approved preDeployCommand migrator as standard (documented in README).

## Phase 2 consult iter2: claude APPROVE, codex REQUEST_CHANGES (login/logout CSRF). Split — fixed codex's.
Codex (HIGH): login/signup CSRF (simple cross-site request → session fixation) + logout CSRF (forced logout).
Legit CSRF-class gap (addendum KEPT CSRF). Took codex's offered "preflight-only contract" (cheapest, no
SPA round-trip): requireJsonRequest() → signup/login reject non-application/json (415, forces CORS
preflight → allow-list gates cross-site); requireCsrf() on logout (403 without token). +2 tests
(login text/plain→415, logout no-csrf→403). Build green, **27/27**. Redeployed (b94e13cb), verifying live.
Committed. Iter2 rebuttal written. → re-signal PHASE_COMPLETE for iter3 review.

## What this is
Move multibrowser off runtime GitHub-reading onto a **Postgres serving layer + thin API**
(new `apps/` member). Git stays source of truth; DB is a rebuildable serving cache. Four tiers:
corpus, results (score), raw, review. Review slice = the #85 read-write backend (auth + intake),
folded into this spec.

## Key context gathered
- No existing backend under `apps/` (only `multibrowser` SPA + `tradition_validator`). API is greenfield.
- Issue names `drizzle-kit generate` → Drizzle (TS ORM) owns migrations. Ingest is Python (`analysis ingest`).
- Tier contracts: `traditions/README.md`, `results/README.md` (Spec 49), `results-raw/README.md` (Spec 51).
- Review slice design = issue #85 + spec #83 (reviewer workspace, localStorage/GitHub-issue seam;
  "submit panel is the only seam to replace").
- Per-phase consult is `[codex, claude]` (Gemini blind to worktree). Full 3-way at PR gate.

## Open decisions the spec must settle (from issue Protocol)
schema · API surface · ingest contract · raw-tier storage (DB bytea vs object store) · auth · cutover order.

## Coordination
- Review-slice design is **Ben's (@benolio) seam** — coordinate. #85 stays the tracking issue.

## Phase 2 consult iter3: codex + claude BOTH REQUEST_CHANGES (HIGH) — my iter2 fix had a real bug.
requireJsonRequest used includes() substring → `text/plain;charset=application/json` (CORS-safelisted,
no preflight) bypassed it; c.req.json() parses regardless → session-fixation reopened (claude repro'd 200).
FIX: compare MIME essence exactly (split ';'[0]==='application/json'). +regression test. Minors: password
length cap 1024 (unbounded argon2 DoS), email format check. Build green, **29/29**. Redeployed (2f4fd80f),
verifying essence fix live. Committed. Iter3 rebuttal written. → re-signal for iter4.

## Phase 2 APPROVED (codex+claude both APPROVE, iter5). PR 1 OPENED.
5 review iterations (all codex findings legit): iter1 (pglite-in-prod, pool error, cors test), iter2
(login/logout CSRF), iter3 (MIME-essence bypass — my regression), iter4 (committed invite code → rotated+redacted).
iter5 both APPROVE.
**PR #97** opened (base main, head builder/spir-92) = Phases 1+2 (apps/api infra + review schema + auth).
Recorded via porch done --pr 97. Live: https://multibench-api-production.up.railway.app. 29/29 tests.
PR body carries the Ben-override note (Waleed owns model, final) per claude's ask.

## OPEN SEQUENCING Q (raised to architect): porch auto-advanced to phase_3 (= PR 2 work) but PR 1 not merged.
Per plan PR-per-tier: PR2 = Phases 3+4. Need architect direction: (a) pause phase_3 until PR 1 merges then
branch PR 2 from main, or (b) stack PR 2 branch on PR 1. PAUSING phase_3 pending their call + PR 1 review.

## Sequencing DECIDED (architect): (a) — pause phase_3 until PR 1 merges, then branch PR 2 from origin/main.
Non-stacked = house style. Architect doing PR #97 integration review now. PAUSED.
Next actions when unblocked: if PR review requests changes → fix on builder/spir-92; when PR 1 MERGES →
`git fetch origin main && git checkout -b <pr2-branch> origin/main`, resume phase_3 (persistence swap +
out-of-sample requirement), phase_4 (submission) → PR 2.

## PR #97 integration review: APPROVE PENDING 4 FIXES (architect 3-way CMAP). All 4 done:
1. **Spec amended** (2026-08-15 banner + inline markers at auth Success Criteria / Constraints auth / delivery-order):
   magic-link→email+password, results-first→review-first. Spec no longer self-contradictory.
2. **engines.node pinned 20.x** (was >=20; Nixpacks major-drift + @node-rs/argon2 native-binding scar).
3. **status.yaml reconciled**: appended phase_2 iter4 (RC/APPROVE) + iter5 (APPROVE/APPROVE) to history,
   annotated force_advanced as superseded. Done per architect's EXPLICIT instruction (I flagged the
   standing "never hand-edit status.yaml" rule; architect directed this truthful record-correction).
4. **Backups VERIFIED + ENABLED**: queried Railway API — NO schedule existed (README was assuming).
   Enabled DAILY schedule on postgres-volume (cron `7 14 * * *` UTC, ~6d retention). README now states
   the actual config. 29/29 tests still green.
Invite-code rotation CONFIRMED by architect (old code 403s); no history rewrite; thread closed.

## PR-2 PRECONDITION (architect, flagged now): real-browser Safari+Chrome verification of cross-site
cookie topology (up.railway.app = public suffix → 3rd-party cookie blocking may bite) BEFORE the PR-2
SPA swap is called done. If blocked → decide custom-domains (same-site) vs same-origin proxy. Do this in phase_3.

## POST-MERGE follow-ups (tracked, not blocking): add apps/api job to validate.yml CI; MAINTAIN refresh
of arch-critical/arch.md (neither knows apps/api exists); keep test-tool deviations visible.

## PR #97 MERGED (Waleed's word, merge commit 276865f). apps/api confirmed on origin/main.
Recorded porch done --merged 97. Daily Postgres backups active.

## GitHub auto-deploy wiring follow-up — BLOCKED (surfaced to architect, not forced):
Railway API returns "Not Authorized" for service/repoTrigger ops with my personal accessToken (volume/backup
ops worked, service-source ops don't). Connecting the Railway GitHub App to the repo is a dashboard OAuth
action regardless. Rewiring a live prod service source blind = risk to the shipped review backend. NOT forcing it.
Mechanism identified for whoever has access: serviceInstanceUpdate source.repo=faithfamilytechnologynetwork/multibench,
rootDirectory=apps/api, branch=main. Recommend: dashboard connect (handles App auth + rootDir + branch safely),
OR keep current `railway up` + preDeployCommand (works). Meanwhile deploys are manual `railway up` from apps/api.
Proceeding to phase_3 (SPA work; wiring is not a prerequisite).
