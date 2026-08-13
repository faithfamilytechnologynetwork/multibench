// Reviewer-intake state for the /review workflow (expert validation of tradition content).
//
// Posture: the app stays a STATIC, read-only SPA — there is no backend to write to. Reviewer
// intake is therefore retained in the browser (localStorage, tolerant zod load so a corrupt or
// older payload degrades to defaults instead of wiping work) and LEAVES the browser only when
// the reviewer explicitly submits: a generated Markdown report handed to the maintainers via a
// prefilled GitHub issue, a download, or a JSON backup (see reviewReport.ts). GitHub issues are
// the durable "database" — attributable, aggregatable (`gh issue list --label tradition-review`),
// and requiring no new infrastructure. Swapping in a real API later only replaces the submit seam.

import { useSyncExternalStore } from "react";
import { z } from "zod";

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
  /** Step 3 — per-scenario checks, keyed by scenario id. */
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
  .catch({ sampleSeed: "", sampleIds: [], source: emptyCheck(), guide: emptyCheck(), scenarios: {} });

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

/** Parse an untrusted payload (localStorage / imported backup) into a valid state. Never throws. */
export function parseReviewState(text: string | null): ReviewState {
  if (text === null) return emptyState();
  try {
    return stateSchema.parse(JSON.parse(text));
  } catch {
    return emptyState();
  }
}

function loadFromStorage(): ReviewState {
  try {
    return parseReviewState(localStorage.getItem(REVIEW_STORAGE_KEY));
  } catch {
    return emptyState(); // storage unavailable (private mode) → in-memory only
  }
}

function saveToStorage(state: ReviewState): void {
  try {
    localStorage.setItem(REVIEW_STORAGE_KEY, JSON.stringify(state));
  } catch {
    // quota / private mode: keep working in memory; the export buttons still work.
  }
}

// ---- store (module-level, useSyncExternalStore) ----------------------------------------------
// One shared snapshot across all review pages; every update persists immediately. A cross-tab
// `storage` event re-reads so two open tabs converge.

let current: ReviewState | null = null;
const listeners = new Set<() => void>();

function snapshot(): ReviewState {
  if (current === null) current = loadFromStorage();
  return current;
}

function emit(): void {
  for (const l of listeners) l();
}

function subscribe(cb: () => void): () => void {
  listeners.add(cb);
  return () => listeners.delete(cb);
}

if (typeof window !== "undefined") {
  window.addEventListener("storage", (e) => {
    if (e.key === REVIEW_STORAGE_KEY) {
      current = null;
      emit();
    }
  });
}

/** Read the shared review state (re-renders on any update, including from another tab). */
export function useReviewState(): ReviewState {
  return useSyncExternalStore(subscribe, snapshot);
}

/** Apply a pure updater to the shared state; persists and notifies subscribers. */
export function updateReviewState(fn: (s: ReviewState) => ReviewState): void {
  current = fn(snapshot());
  saveToStorage(current);
  emit();
}

/** Replace the whole state (JSON import). The payload goes through the tolerant parser. */
export function replaceReviewState(next: ReviewState): void {
  updateReviewState(() => next);
}

/** Test/reset seam: drop the in-memory snapshot so the next read hits storage again. */
export function resetReviewStore(): void {
  current = null;
  emit();
}

// ---- pure state updaters ---------------------------------------------------------------------

function traditionOf(s: ReviewState, tid: string): TraditionReview {
  return (
    s.traditions[tid] ?? { sampleSeed: "", sampleIds: [], source: emptyCheck(), guide: emptyCheck(), scenarios: {} }
  );
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

/** Update one scenario check. */
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
  /** Checks answered (any non-"unreviewed" status). */
  done: number;
  /** Total answerable checks: source + guide + 4 per sampled scenario. */
  total: number;
  /** How many answered checks are flagged "needs changes". */
  flagged: number;
}

export function traditionProgress(t: TraditionReview | undefined): ReviewProgress {
  if (!t) return { done: 0, total: 0, flagged: 0 };
  const checks: CheckReview[] = [t.source, t.guide];
  for (const sid of t.sampleIds) {
    const sc = t.scenarios[sid] ?? emptyScenarioChecks();
    for (const key of SCENARIO_CHECKS) checks.push(sc[key]);
  }
  const answered = checks.filter((c) => c.status !== "unreviewed");
  return {
    done: answered.length,
    total: checks.length,
    flagged: answered.filter((c) => c.status === "flagged").length,
  };
}

/** The checks for one scenario (empty defaults when untouched). */
export function scenarioChecksOf(t: TraditionReview | undefined, sid: string): ScenarioChecks {
  return t?.scenarios[sid] ?? emptyScenarioChecks();
}
