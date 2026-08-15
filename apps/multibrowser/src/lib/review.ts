// Reviewer-intake state for the /review workflow (expert validation of tradition content).
//
// Persistence (Spec 92, Phase 3): drafts live in the review backend (apps/api), keyed per
// (authenticated reviewer, tradition). This module keeps the SAME public store API the review pages
// use — `useReviewState()` + `updateReviewState(fn)` + the tradition-scoped pure updaters — but backs
// it with the API instead of localStorage:
//   • updates apply OPTIMISTICALLY to an in-memory snapshot, then save asynchronously (debounced);
//   • each tradition carries a `version`; a save on a stale version is reconciled (last-write-wins
//     for the active device, then server-wins if it still conflicts) so work is not silently dropped;
//   • the tolerant zod loader is retained — a corrupt/older draft degrades field-by-field to defaults.
// Reviewer identity comes from the authenticated account (`/api/auth/me`), not an in-app form.

import { useSyncExternalStore } from "react";
import { z } from "zod";
import {
  fetchCsrf,
  getDraft,
  login as apiLogin,
  logout as apiLogout,
  me as apiMe,
  putDraft,
  setReviewFetch,
  signup as apiSignup,
  type Reviewer,
} from "./reviewApi";

export { setReviewFetch };
export type { Reviewer };

/** How many scenarios a reviewer is asked to cover per tradition (the "review these 10"). */
export const REVIEW_SAMPLE_SIZE = 10;

export const CHECK_STATUSES = ["unreviewed", "approved", "flagged"] as const;
export type CheckStatus = (typeof CHECK_STATUSES)[number];

/** One reviewable unit's intake: a verdict plus free-text notes and an optional suggested fix. */
export interface CheckReview {
  status: CheckStatus;
  notes: string;
  /** The reviewer's proposed replacement/correction text (flows into the report verbatim). */
  suggestion: string;
}

/** The four per-scenario checks, in the order the review page walks them. */
export const SCENARIO_CHECKS = ["scenario", "scoring", "judgement", "pressures"] as const;
export type ScenarioCheckKey = (typeof SCENARIO_CHECKS)[number];

export const SCENARIO_CHECK_LABELS: Record<ScenarioCheckKey, string> = {
  scenario: "The scenario",
  scoring: "The scoring guide",
  judgement: "The judges' verdicts",
  pressures: "The pressure points",
};

export type ScenarioChecks = Record<ScenarioCheckKey, CheckReview>;

/** One tradition's review: the two tradition-level checks + the assigned scenario sample. */
export interface TraditionReview {
  /** Seed used to draw the sample ("" = the default even spread across the corpus). */
  sampleSeed: string;
  /** The materialized assignment — persisted so it never shifts under the reviewer. */
  sampleIds: string[];
  /** Step 1 — the tradition's canonical source (source.md). */
  source: CheckReview;
  /** Step 2 — the companionship guide (guide.md, the Guided-framing system prompt). */
  guide: CheckReview;
  /**
   * Step 3 — per-scenario checks, keyed by scenario id. May hold ANY scenario id, not only
   * `sampleIds` (Spec 92 / Waleed): out-of-sample scenarios are reviewable too. `sampleIds` is the
   * *required* set (completion is measured against it); extras beyond it are surfaced separately.
   */
  scenarios: Record<string, ScenarioChecks>;
}

export interface ReviewerInfo {
  name: string;
  /** How maintainers can reach the reviewer (email / GitHub handle) — included in the report. */
  contact: string;
  /** Standing to review (e.g. "Sunni imam, 12 years", "PhD in Patristics"). */
  background: string;
}

export interface ReviewState {
  version: 1;
  reviewer: ReviewerInfo;
  traditions: Record<string, TraditionReview>;
}

export function emptyCheck(): CheckReview {
  return { status: "unreviewed", notes: "", suggestion: "" };
}

export function emptyScenarioChecks(): ScenarioChecks {
  return { scenario: emptyCheck(), scoring: emptyCheck(), judgement: emptyCheck(), pressures: emptyCheck() };
}

export function emptyTradition(): TraditionReview {
  return { sampleSeed: "", sampleIds: [], source: emptyCheck(), guide: emptyCheck(), scenarios: {} };
}

export function emptyState(): ReviewState {
  return { version: 1, reviewer: { name: "", contact: "", background: "" }, traditions: {} };
}

// ---- tolerant persistence schema -------------------------------------------------------------
// Every field falls back independently (`.catch`), so one corrupt subfield never discards the
// rest of a reviewer's work. Mirrors the display-first posture of the data layer.

const checkSchema = z
  .object({
    status: z.enum(CHECK_STATUSES).catch("unreviewed"),
    notes: z.string().catch(""),
    suggestion: z.string().catch(""),
  })
  .catch(emptyCheck());

const scenarioChecksSchema = z
  .object({
    scenario: checkSchema,
    scoring: checkSchema,
    judgement: checkSchema,
    pressures: checkSchema,
  })
  .catch(emptyScenarioChecks());

const traditionReviewSchema = z
  .object({
    sampleSeed: z.string().catch(""),
    sampleIds: z.array(z.string()).catch([]),
    source: checkSchema,
    guide: checkSchema,
    scenarios: z.record(z.string(), scenarioChecksSchema).catch({}),
  })
  .catch(emptyTradition());

const stateSchema = z
  .object({
    version: z.literal(1).catch(1),
    reviewer: z
      .object({
        name: z.string().catch(""),
        contact: z.string().catch(""),
        background: z.string().catch(""),
      })
      .catch({ name: "", contact: "", background: "" }),
    traditions: z.record(z.string(), traditionReviewSchema).catch({}),
  })
  .catch(emptyState());

export const REVIEW_STORAGE_KEY = "multibench.review.v1";

/** Parse an untrusted whole-state payload (imported JSON backup) into a valid state. Never throws. */
export function parseReviewState(text: string | null): ReviewState {
  if (text === null) return emptyState();
  try {
    return stateSchema.parse(JSON.parse(text));
  } catch {
    return emptyState();
  }
}

/** Parse an untrusted single-tradition draft (from the API) tolerantly. Never throws. */
export function parseTraditionReview(value: unknown): TraditionReview {
  return traditionReviewSchema.parse(value ?? {});
}

// ---- async, API-backed store -----------------------------------------------------------------

/** Delay before a change is persisted, so typing doesn't fire a PUT per keystroke. */
export const SAVE_DEBOUNCE_MS = 600;

export type AuthStatus = "unknown" | "in" | "out";

export interface ReviewStatus {
  auth: AuthStatus;
  reviewer: Reviewer | null;
  /** Tradition ids with an in-flight or pending save. */
  saving: boolean;
  /** Last save error message (network / server), cleared on the next successful save. */
  error: string | null;
  /** A tradition that was reconciled from another device since the last render (id → true). */
  reconciled: string | null;
}

let current: ReviewState = emptyState();
let status: ReviewStatus = { auth: "unknown", reviewer: null, saving: false, error: null, reconciled: null };
const versions = new Map<string, number>();
const loaded = new Set<string>();
const dirty = new Set<string>();
const timers = new Map<string, ReturnType<typeof setTimeout>>();
const inflight = new Map<string, Promise<void>>();

const listeners = new Set<() => void>();
function subscribe(cb: () => void): () => void {
  listeners.add(cb);
  return () => listeners.delete(cb);
}
function emit(): void {
  for (const l of listeners) l();
}
function snapshot(): ReviewState {
  return current;
}
function statusSnapshot(): ReviewStatus {
  return status;
}
function setStatus(patch: Partial<ReviewStatus>): void {
  status = { ...status, ...patch };
  emit();
}

/** Read the shared review state (re-renders on any update). */
export function useReviewState(): ReviewState {
  return useSyncExternalStore(subscribe, snapshot);
}

/** Read auth + save status (loading, saving, errors, reviewer). */
export function useReviewStatus(): ReviewStatus {
  return useSyncExternalStore(subscribe, statusSnapshot);
}

/** Non-hook read of the current state / a tradition's version (tests, and imperative callers). */
export function peekReviewState(): ReviewState {
  return current;
}
export function peekVersion(tid: string): number {
  return versions.get(tid) ?? 0;
}

// --- saving ---

async function persistTradition(tid: string): Promise<void> {
  dirty.delete(tid);
  const t = current.traditions[tid];
  if (!t) return;
  let version = versions.get(tid) ?? 0;
  try {
    let result = await putDraft(tid, t, version);
    if (!result.ok) {
      // Conflict: another device advanced this tradition. Last-write-wins for the active device —
      // retry once with the server's version (our optimistic edits are preserved, not dropped).
      version = result.conflict.version;
      versions.set(tid, version);
      const retry = await putDraft(tid, current.traditions[tid] ?? t, version);
      if (retry.ok) {
        result = retry;
      } else {
        // Still conflicting (a third write raced): adopt the server draft (server-wins) + notice.
        versions.set(tid, retry.conflict.version);
        current = { ...current, traditions: { ...current.traditions, [tid]: parseTraditionReview(retry.conflict.state) } };
        setStatus({ reconciled: tid, error: null });
        return;
      }
    }
    versions.set(tid, result.version);
    setStatus({ error: null });
  } catch (e) {
    // Keep the optimistic state and leave the tradition dirty so a later flush retries.
    dirty.add(tid);
    setStatus({ error: e instanceof Error ? e.message : "save failed" });
  } finally {
    if (dirty.size === 0 && inflight.size <= 1) setStatus({ saving: false });
  }
}

function scheduleSave(tid: string): void {
  dirty.add(tid);
  setStatus({ saving: true });
  const existing = timers.get(tid);
  if (existing) clearTimeout(existing);
  timers.set(
    tid,
    setTimeout(() => {
      timers.delete(tid);
      const p = persistTradition(tid).finally(() => inflight.delete(tid));
      inflight.set(tid, p);
    }, SAVE_DEBOUNCE_MS),
  );
}

/** Force all pending saves now and await them (navigation, submit, tests). */
export async function flushReviewSaves(): Promise<void> {
  for (const [tid, timer] of timers) {
    clearTimeout(timer);
    timers.delete(tid);
    const p = persistTradition(tid).finally(() => inflight.delete(tid));
    inflight.set(tid, p);
  }
  await Promise.all([...inflight.values()]);
  if (dirty.size === 0) setStatus({ saving: false });
}

/**
 * Apply a pure updater to the shared state; persist any tradition whose entry actually changed. The
 * pure updaters replace only the touched tradition's reference, so a shallow reference-diff finds
 * exactly what to save — no call-site changes needed.
 */
export function updateReviewState(fn: (s: ReviewState) => ReviewState): void {
  const prev = current;
  current = fn(prev);
  const ids = new Set([...Object.keys(prev.traditions), ...Object.keys(current.traditions)]);
  for (const tid of ids) {
    if (current.traditions[tid] !== prev.traditions[tid]) scheduleSave(tid);
  }
  emit();
}

/** Ensure a tradition's draft is loaded from the API (once). Safe to call on every render. */
export async function ensureTraditionLoaded(tid: string): Promise<void> {
  if (loaded.has(tid) || current.traditions[tid]) {
    loaded.add(tid);
    return;
  }
  loaded.add(tid);
  try {
    const draft = await getDraft(tid);
    versions.set(tid, draft.version);
    if (draft.state !== null && current.traditions[tid] === undefined) {
      current = { ...current, traditions: { ...current.traditions, [tid]: parseTraditionReview(draft.state) } };
      emit();
    }
  } catch (e) {
    loaded.delete(tid); // allow a retry
    setStatus({ error: e instanceof Error ? e.message : "load failed" });
  }
}

/** Replace the whole state (JSON import). Marks every tradition dirty so it saves. */
export function replaceReviewState(next: ReviewState): void {
  const prev = current;
  current = next;
  for (const tid of new Set([...Object.keys(prev.traditions), ...Object.keys(next.traditions)])) {
    scheduleSave(tid);
  }
  emit();
}

/** Test/reset seam: drop the in-memory store (does not touch the server). */
export function resetReviewStore(): void {
  current = emptyState();
  status = { auth: "unknown", reviewer: null, saving: false, error: null, reconciled: null };
  versions.clear();
  loaded.clear();
  dirty.clear();
  for (const t of timers.values()) clearTimeout(t);
  timers.clear();
  inflight.clear();
  emit();
}

// --- auth ---

function reviewerInfoFrom(r: Reviewer): ReviewerInfo {
  return { name: r.name, contact: r.email, background: r.background ?? "" };
}

let initInFlight = false;

/** Establish the session (call on entering /review): loads the reviewer + a CSRF token. Idempotent —
 * concurrent/duplicate calls are coalesced; a reset re-arms it. */
export async function initReview(): Promise<void> {
  if (initInFlight || status.auth !== "unknown") return;
  initInFlight = true;
  try {
    await fetchCsrf();
    const reviewer = await apiMe();
    current = { ...current, reviewer: reviewer ? reviewerInfoFrom(reviewer) : current.reviewer };
    setStatus({ auth: reviewer ? "in" : "out", reviewer });
  } finally {
    initInFlight = false;
  }
}

export async function loginReview(email: string, password: string): Promise<void> {
  const reviewer = await apiLogin(email, password);
  current = { ...current, reviewer: reviewerInfoFrom(reviewer) };
  setStatus({ auth: "in", reviewer, error: null });
}

export async function signupReview(input: {
  email: string;
  password: string;
  name: string;
  background?: string;
  inviteCode: string;
}): Promise<void> {
  const reviewer = await apiSignup(input);
  current = { ...current, reviewer: reviewerInfoFrom(reviewer) };
  setStatus({ auth: "in", reviewer, error: null });
}

export async function logoutReview(): Promise<void> {
  await apiLogout();
  resetReviewStore();
  setStatus({ auth: "out", reviewer: null });
}

// ---- pure state updaters ---------------------------------------------------------------------

function traditionOf(s: ReviewState, tid: string): TraditionReview {
  return s.traditions[tid] ?? emptyTradition();
}

export function withReviewer(s: ReviewState, patch: Partial<ReviewerInfo>): ReviewState {
  return { ...s, reviewer: { ...s.reviewer, ...patch } };
}

/** Set a tradition's assigned sample (initial draw, reshuffle, add/remove). */
export function withSample(s: ReviewState, tid: string, sampleIds: string[], sampleSeed: string): ReviewState {
  const t = traditionOf(s, tid);
  return { ...s, traditions: { ...s.traditions, [tid]: { ...t, sampleIds, sampleSeed } } };
}

/** Update one of the two tradition-level checks (source / guide). */
export function withTraditionCheck(
  s: ReviewState,
  tid: string,
  which: "source" | "guide",
  patch: Partial<CheckReview>,
): ReviewState {
  const t = traditionOf(s, tid);
  return { ...s, traditions: { ...s.traditions, [tid]: { ...t, [which]: { ...t[which], ...patch } } } };
}

/** Update one scenario check. Accepts any scenario id (in-sample or out-of-sample). */
export function withScenarioCheck(
  s: ReviewState,
  tid: string,
  sid: string,
  key: ScenarioCheckKey,
  patch: Partial<CheckReview>,
): ReviewState {
  const t = traditionOf(s, tid);
  const checks = t.scenarios[sid] ?? emptyScenarioChecks();
  return {
    ...s,
    traditions: {
      ...s.traditions,
      [tid]: { ...t, scenarios: { ...t.scenarios, [sid]: { ...checks, [key]: { ...checks[key], ...patch } } } },
    },
  };
}

/** Drop one tradition's review entirely (the reviewer's explicit "start over"). */
export function withoutTradition(s: ReviewState, tid: string): ReviewState {
  const rest = { ...s.traditions };
  delete rest[tid];
  return { ...s, traditions: rest };
}

// ---- sampling --------------------------------------------------------------------------------

/**
 * The default assignment: `n` scenarios evenly spread across the ordered corpus (always includes
 * the first). Deterministic — every reviewer opening a tradition cold sees the same 10, so
 * maintainers can compare notes across reviewers.
 */
export function evenSample(ids: string[], n: number = REVIEW_SAMPLE_SIZE): string[] {
  if (ids.length <= n) return [...ids];
  const out: string[] = [];
  for (let i = 0; i < n; i++) {
    const pick = ids[Math.floor((i * ids.length) / n)];
    if (pick !== undefined) out.push(pick);
  }
  return out;
}

/** FNV-1a hash of a string → uint32 (seeds the PRNG below). */
function fnv1a(text: string): number {
  let h = 0x811c9dc5;
  for (let i = 0; i < text.length; i++) {
    h ^= text.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  return h >>> 0;
}

/** mulberry32 — tiny deterministic PRNG (good enough for drawing a review sample). */
function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/**
 * A seeded random assignment (the "reshuffle" path): deterministic for a given (ids, seed), so a
 * reviewer's sample can be reproduced from the seed recorded in their report. Picks keep corpus
 * order. An empty seed falls back to the even spread.
 */
export function seededSample(ids: string[], n: number, seed: string): string[] {
  if (seed === "") return evenSample(ids, n);
  if (ids.length <= n) return [...ids];
  const rand = mulberry32(fnv1a(seed));
  const indices = ids.map((_, i) => i);
  for (let i = indices.length - 1; i > 0; i--) {
    const j = Math.floor(rand() * (i + 1));
    const a = indices[i] as number;
    indices[i] = indices[j] as number;
    indices[j] = a;
  }
  return indices
    .slice(0, n)
    .sort((a, b) => a - b)
    .map((i) => ids[i] as string);
}

// ---- progress --------------------------------------------------------------------------------

export interface ReviewProgress {
  /** Checks answered (any non-"unreviewed" status) within the REQUIRED sample. */
  done: number;
  /** Total answerable checks in the required sample: source + guide + 4 per sampled scenario. */
  total: number;
  /** How many answered checks (required sample) are flagged "needs changes". */
  flagged: number;
  /** Scenarios reviewed BEYOND the required sample (out-of-sample) — shown separately as "+N". */
  beyondSample: number;
}

export function traditionProgress(t: TraditionReview | undefined): ReviewProgress {
  if (!t) return { done: 0, total: 0, flagged: 0, beyondSample: 0 };
  const checks: CheckReview[] = [t.source, t.guide];
  for (const sid of t.sampleIds) {
    const sc = t.scenarios[sid] ?? emptyScenarioChecks();
    for (const key of SCENARIO_CHECKS) checks.push(sc[key]);
  }
  const answered = checks.filter((c) => c.status !== "unreviewed");
  const sample = new Set(t.sampleIds);
  const beyondSample = Object.entries(t.scenarios).filter(
    ([sid, sc]) => !sample.has(sid) && SCENARIO_CHECKS.some((k) => sc[k].status !== "unreviewed"),
  ).length;
  return {
    done: answered.length,
    total: checks.length,
    flagged: answered.filter((c) => c.status === "flagged").length,
    beyondSample,
  };
}

/** The checks for one scenario (empty defaults when untouched). */
export function scenarioChecksOf(t: TraditionReview | undefined, sid: string): ScenarioChecks {
  return t?.scenarios[sid] ?? emptyScenarioChecks();
}
