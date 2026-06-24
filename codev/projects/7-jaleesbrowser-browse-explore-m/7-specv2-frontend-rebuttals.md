# Spec 7 — v2 (frontend SPA) consult: rebuttal

**Reviewers:** Codex (REQUEST_CHANGES — 3) · Claude (APPROVE — "exceptionally thorough;
verified-correct data format; sound client-side architecture; well-bounded scope"). Both
verified the format + GitHub facts against the live repo. All three Codex points **accepted and
fixed** — including a real technical error on my part.

1. **Freshness mechanism was technically inconsistent (my error).** I wrote the SHA query as a
   `staleTime ≈ 60s` "poll," but TanStack Query `staleTime` alone does **not** refetch. → **Fixed**
   (§5.2 / M7): `useLatestSha` now uses **`refetchInterval`** (default ~5 min) **plus
   `refetchOnWindowFocus`/`refetchOnReconnect`**, with the interval deliberately conservative
   because the unauthenticated **60/hr budget may be shared across users behind one NAT** (a 60 s
   poll could exhaust it). SHA-keyed tree/content queries then auto-refetch the new snapshot on an
   already-open page → freshness within ~the interval (or sooner on focus/reconnect), no redeploy.

2. **Tradition-page cold load (100–140 `scenario.yaml`) underspecified.** → **Fixed** (§5.2): the
   client fires those **`raw` (off-budget)** fetches via TanStack Query and **progressively
   hydrates** the list — rows render as metadata resolves (HeroUI skeletons for pending) with a
   **"loaded N/total" indicator**; concurrency is browser-bounded (optional explicit cap ~8);
   filters/counts operate over loaded rows and finalize when complete; each file is cached
   (immutable per SHA) so revisits/detail are instant.

3. **Railway serving ambiguous (`vite preview` vs `serve`).** → **Decided** (§5.4 / §6 I3):
   **`vite preview --host 0.0.0.0 --port $PORT`** (no extra dep, mirrors shannon, default SPA
   history fallback), with **SPA history fallback a required, verified acceptance item** (§9.1).
   `serve -s dist` documented as the drop-in alternative.

Claude (APPROVE) confirmed the §2.4 format + §2.5 GitHub facts are accurate against the real repo
(both traditions, tree/raw/rate-limit claims), the security posture is appropriate for a public
read-only SPA, and the offline testing strategy is solid; it noted the stale Python plan needs
rewriting (acknowledged — banner-marked SUPERSEDED; rewritten after spec-approval — not a spec
defect).

Net: a real freshness-mechanism bug fixed, plus two concrete behavior/deploy specifications; the
client-side SPA architecture is unchanged and endorsed.
