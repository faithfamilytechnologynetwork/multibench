// TanStack Query data layer. Composes the GitHub fetch boundary (github.ts) with the tolerant
// parsers (parse.ts) into cached, SHA-keyed read-model hooks.
//
// Freshness: `useLatestSha` actively polls via `refetchInterval` (TanStack `staleTime` alone
// does NOT poll) + focus/reconnect. Everything else is keyed by SHA and immutable per SHA
// (`staleTime: Infinity`), so a new SHA → new keys → automatic refetch on an open page.

import { useQueries, useQuery, useQueryClient, type QueryClient } from "@tanstack/react-query";
import { latestSha, raw, tree, type TreeEntry } from "./github";
import { BakedRawSource, GitHubRawSource, loadRawShard, resolveRawSource } from "./rawSource";
import type { RawCatalog, RawShard } from "./rawModel";
import {
  parseIndex,
  parseManifest,
  parsePressures,
  parseScenarioMeta,
  proseSection,
  resolveScenarioSet,
} from "./parse";
import { FILE, REF, REPO, SHA_POLL_MS, PRESSURES } from "./constants";
import {
  emptyPressureMap,
  notice,
  type Notice,
  type Scenario,
  type ScenarioMeta,
  type Tradition,
} from "./model";
import { loadResults } from "./results";
import {
  isSafePathSegment,
  parseResultsManifest,
  parseResultsShard,
  shardConsistencyNotices,
  type ResultsManifest,
  type ResultsShard,
} from "./resultsModel";

const GC_TIME = 1000 * 60 * 60; // keep SHA-pinned (immutable) data ~1h for instant back-nav

// Cap concurrent scenario-metadata fetches during a tradition's progressive cold load, so a
// 140-scenario tradition doesn't dispatch 140 requests at once. (raw is off-budget, but this
// keeps it tidy and polite; the browser would otherwise queue them.)
function makeLimiter(max: number) {
  let active = 0;
  const queue: Array<() => void> = [];
  return async function run<T>(fn: () => Promise<T>): Promise<T> {
    if (active >= max) await new Promise<void>((resolve) => queue.push(resolve));
    active++;
    try {
      return await fn();
    } finally {
      active--;
      queue.shift()?.();
    }
  };
}
const metaLimiter = makeLimiter(8);

// ---- pure tree helpers (testable without network) -------------------------------------------

/** Tradition ids = directories that contain a `tradition.yaml`. */
export function traditionIds(entries: TreeEntry[]): string[] {
  const ids: string[] = [];
  for (const e of entries) {
    const m = /^traditions\/([^/]+)\/tradition\.yaml$/.exec(e.path);
    if (m && m[1]) ids.push(m[1]);
  }
  return ids.sort();
}

/** Scenario folder ids for a tradition = `traditions/<id>/scenarios/<sid>` tree entries. */
export function scenarioFolderIds(entries: TreeEntry[], traditionId: string): string[] {
  const ids: string[] = [];
  const prefix = `traditions/${traditionId}/${FILE.scenariosDir}/`;
  for (const e of entries) {
    if (e.type !== "tree" || !e.path.startsWith(prefix)) continue;
    const rest = e.path.slice(prefix.length);
    if (rest.length > 0 && !rest.includes("/")) ids.push(rest);
  }
  return ids;
}

export function hasFile(entries: TreeEntry[], path: string): boolean {
  return entries.some((e) => e.type === "blob" && e.path === path);
}

/** Results run ids = `results/<id>/manifest.json` blobs (the #49 results datasets). */
export function resultsRunIds(entries: TreeEntry[]): string[] {
  const ids: string[] = [];
  for (const e of entries) {
    const m = /^results\/([^/]+)\/manifest\.json$/.exec(e.path);
    if (m && m[1]) ids.push(m[1]);
  }
  return ids.sort();
}

// ---- shared cached fetchers (dedupe across derived queries) ----------------------------------

function ensureTree(qc: QueryClient, sha: string): Promise<TreeEntry[]> {
  return qc.ensureQueryData({
    queryKey: ["gh", "tree", REPO, sha],
    queryFn: () => tree(REPO, sha),
    staleTime: Infinity,
    gcTime: GC_TIME,
  });
}

function ensureRaw(qc: QueryClient, sha: string, path: string): Promise<string | null> {
  return qc.ensureQueryData({
    queryKey: ["gh", "raw", REPO, sha, path],
    queryFn: () => raw(REPO, sha, path),
    staleTime: Infinity,
    gcTime: GC_TIME,
  });
}

const tPath = (id: string, ...rest: string[]) => ["traditions", id, ...rest].join("/");
const sPath = (tid: string, sid: string, file: string) =>
  tPath(tid, FILE.scenariosDir, sid, file);

// ---- derived loaders -------------------------------------------------------------------------

async function resolveScenarioIds(
  qc: QueryClient,
  sha: string,
  entries: TreeEntry[],
  id: string,
): Promise<{ scenarioIds: string[]; notices: Notice[] }> {
  const indexPath = tPath(id, FILE.scenariosDir, FILE.index);
  const folderIds = scenarioFolderIds(entries, id);
  let indexIds: string[] | null = null;
  const notices: Notice[] = [];
  if (hasFile(entries, indexPath)) {
    const text = await ensureRaw(qc, sha, indexPath);
    if (text !== null) {
      const parsed = parseIndex(text, indexPath);
      indexIds = parsed.ids;
      notices.push(...parsed.notices);
    }
  } else {
    notices.push(notice("warning", "tradition", indexPath, "scenarios/index.json is missing."));
  }
  const resolved = resolveScenarioSet(indexIds, folderIds, tPath(id, FILE.scenariosDir));
  notices.push(...resolved.notices);
  // Keep ghosts in the ordered list — they render as stub rows (with their notices).
  return { scenarioIds: resolved.ordered, notices };
}

/** Manifest + scenario set (no prose) — enough for the index card and the tradition header. */
async function loadTraditionCore(qc: QueryClient, sha: string, entries: TreeEntry[], id: string): Promise<Tradition> {
  const notices: Notice[] = [];
  const manifestPath = tPath(id, FILE.manifest);
  const manifestText = await ensureRaw(qc, sha, manifestPath);
  let manifest = null;
  if (manifestText === null) {
    notices.push(notice("error", "tradition", manifestPath, "tradition.yaml is missing."));
  } else {
    const parsed = parseManifest(manifestText, manifestPath);
    manifest = parsed.manifest;
    notices.push(...parsed.notices);
  }
  const { scenarioIds, notices: setNotices } = await resolveScenarioIds(qc, sha, entries, id);
  notices.push(...setNotices);
  return { id, manifest, prose: { readme: null, source: null, guide: null }, scenarioIds, notices };
}

export async function loadTraditions(qc: QueryClient, sha: string): Promise<Tradition[]> {
  const entries = await ensureTree(qc, sha);
  const ids = traditionIds(entries);
  return Promise.all(ids.map((id) => loadTraditionCore(qc, sha, entries, id)));
}

// ---- results datasets (#49): discovery + manifest/shard loaders --------------------

export interface ResultsRun {
  id: string;
  manifest: ResultsManifest | null;
  notices: Notice[];
}

export interface ResultsRunsResult {
  runs: ResultsRun[];
  /** The run to show by default: the most recent by manifest `generatedAt`, or null if none. */
  defaultRunId: string | null;
}

const rPath = (runId: string, file: string) => ["results", runId, file].join("/");

export async function loadResultsManifest(
  qc: QueryClient,
  sha: string,
  runId: string,
): Promise<{ manifest: ResultsManifest | null; notices: Notice[] }> {
  const where = rPath(runId, "manifest.json");
  const text = await ensureRaw(qc, sha, where);
  if (text === null) {
    return { manifest: null, notices: [notice("error", "results", where, "manifest not found")] };
  }
  return parseResultsManifest(text, where);
}

/** Discover every `results/<id>/` run and load its manifest; newest (by date) is the default. */
export async function loadResultsRuns(qc: QueryClient, sha: string): Promise<ResultsRunsResult> {
  const entries = await ensureTree(qc, sha);
  const ids = resultsRunIds(entries);
  const runs: ResultsRun[] = await Promise.all(
    ids.map(async (id) => ({ id, ...(await loadResultsManifest(qc, sha, id)) })),
  );
  // Order by parsed instant (not lexical): a non-UTC offset or unparseable date must not
  // misorder the runs. Invalid/absent dates parse to NaN and sort last.
  const ts = (r: ResultsRun) => (r.manifest ? Date.parse(r.manifest.generatedAt) : NaN);
  const valid = runs.filter((r) => r.manifest !== null);
  valid.sort((a, b) => {
    const [ta, tb] = [ts(a), ts(b)];
    if (Number.isNaN(ta) && Number.isNaN(tb)) return a.id.localeCompare(b.id);
    if (Number.isNaN(ta)) return 1;
    if (Number.isNaN(tb)) return -1;
    return tb - ta; // most recent first
  });
  return { runs, defaultRunId: valid[0]?.id ?? null };
}

export interface LoadedResultsRun {
  manifest: ResultsManifest | null;
  shards: Record<string, ResultsShard>;
  notices: Notice[];
}

/** Load a run's manifest + all its tradition shards (for the leaderboard's mean-of-means). */
export async function loadResultsRun(qc: QueryClient, sha: string, runId: string): Promise<LoadedResultsRun> {
  const { manifest, notices } = await loadResultsManifest(qc, sha, runId);
  if (manifest === null) return { manifest: null, shards: {}, notices };
  const all: Notice[] = [...notices];
  const shards: Record<string, ResultsShard> = {};
  await Promise.all(
    manifest.traditions.map(async (t) => {
      const { shard, notices: sn } = await loadResultsShard(qc, sha, runId, t.id);
      if (shard) shards[t.id] = shard;
      all.push(...sn);
    }),
  );
  return { manifest, shards, notices: all };
}

export async function loadResultsShard(
  qc: QueryClient,
  sha: string,
  runId: string,
  tradition: string,
): Promise<{ shard: ResultsShard | null; notices: Notice[] }> {
  // Load the manifest first: it is the single source of truth for the shard filename and the
  // vocabulary the shard is cross-validated against (unknown keys → Notice).
  const { manifest, notices: mNotices } = await loadResultsManifest(qc, sha, runId);
  if (manifest === null) return { shard: null, notices: mNotices };
  const entry = manifest.traditions.find((t) => t.id === tradition);
  if (!entry) {
    return {
      shard: null,
      notices: [notice("error", "results", rPath(runId, "manifest.json"), `tradition ${tradition} not in manifest`)],
    };
  }
  // The shard filename is untrusted manifest data spliced into a raw URL — reject a hostile
  // (`../`, absolute) value before fetching (mirrors the exporter's path-segment guard).
  if (!isSafePathSegment(entry.shard)) {
    return {
      shard: null,
      notices: [notice("error", "results", rPath(runId, "manifest.json"), `unsafe shard filename "${entry.shard}"`)],
    };
  }
  const where = rPath(runId, entry.shard);
  const text = await ensureRaw(qc, sha, where);
  if (text === null) {
    return { shard: null, notices: [notice("error", "results", where, `no results shard for ${tradition}`)] };
  }
  const { shard, notices } = parseResultsShard(text, where);
  if (shard === null) return { shard: null, notices };
  const consistency = shardConsistencyNotices(shard, manifest, tradition, where);
  const all = [...notices, ...consistency];
  // A contract-breaking shard (error-severity notice — e.g. a tradition mismatch) is EXCLUDED
  // from the data so it can't be counted under the wrong tradition; unknown-vocab/coverage
  // warnings are display-only and keep the shard.
  if (consistency.some((n) => n.severity === "error")) {
    return { shard: null, notices: all };
  }
  return { shard, notices: all };
}

export async function loadTradition(qc: QueryClient, sha: string, id: string): Promise<Tradition | null> {
  const entries = await ensureTree(qc, sha);
  if (!traditionIds(entries).includes(id)) return null; // unknown tradition → caller 404s
  const core = await loadTraditionCore(qc, sha, entries, id);
  const [readmeRaw, sourceRaw, guideRaw] = await Promise.all([
    ensureRaw(qc, sha, tPath(id, FILE.readme)),
    ensureRaw(qc, sha, tPath(id, FILE.source)),
    ensureRaw(qc, sha, tPath(id, FILE.guide)),
  ]);
  const readme = proseSection(readmeRaw, FILE.readme, "tradition", tPath(id, FILE.readme));
  const source = proseSection(sourceRaw, FILE.source, "tradition", tPath(id, FILE.source));
  const guide = proseSection(guideRaw, FILE.guide, "tradition", tPath(id, FILE.guide));
  const proseNotices = [readme.notice, source.notice, guide.notice].filter((n): n is Notice => n !== null);
  return {
    ...core,
    prose: { readme: readme.text, source: source.text, guide: guide.text },
    notices: [...core.notices, ...proseNotices],
  };
}

export async function loadScenarioMeta(
  qc: QueryClient,
  sha: string,
  tid: string,
  sid: string,
  declaredAxes: Record<string, readonly string[]>,
): Promise<{ meta: ScenarioMeta | null; notices: Notice[] }> {
  const path = sPath(tid, sid, FILE.scenarioMeta);
  const text = await ensureRaw(qc, sha, path);
  if (text === null) {
    return { meta: null, notices: [notice("error", "scenario", path, "scenario.yaml is missing.")] };
  }
  return parseScenarioMeta(text, sid, path, declaredAxes);
}

export async function loadScenario(
  qc: QueryClient,
  sha: string,
  tid: string,
  sid: string,
  declaredAxes: Record<string, readonly string[]>,
): Promise<Scenario> {
  const notices: Notice[] = [];
  const [metaR, turn1R, judgeR, pressuresR] = await Promise.all([
    loadScenarioMeta(qc, sha, tid, sid, declaredAxes),
    ensureRaw(qc, sha, sPath(tid, sid, FILE.turn1)),
    ensureRaw(qc, sha, sPath(tid, sid, FILE.judgeGuidance)),
    ensureRaw(qc, sha, sPath(tid, sid, FILE.pressures)),
  ]);
  notices.push(...metaR.notices);

  const turn1 = proseSection(turn1R, FILE.turn1, "section", sPath(tid, sid, FILE.turn1));
  const judge = proseSection(judgeR, FILE.judgeGuidance, "section", sPath(tid, sid, FILE.judgeGuidance));
  for (const n of [turn1.notice, judge.notice]) if (n) notices.push(n);

  let pressures = emptyPressureMap(PRESSURES);
  if (pressuresR === null) {
    notices.push(notice("error", "section", sPath(tid, sid, FILE.pressures), "pressures.md is missing."));
  } else {
    const parsed = parsePressures(pressuresR, sPath(tid, sid, FILE.pressures));
    pressures = parsed.pressures;
    notices.push(...parsed.notices);
  }

  const scenario: Scenario = {
    id: sid,
    meta: metaR.meta,
    turn1: turn1.text,
    judgeGuidance: judge.text,
    pressures,
    notices,
  };
  const results = loadResults(scenario);
  if (results !== null) scenario.results = results; // inert: always null in v1
  return scenario;
}

// ---- hooks -----------------------------------------------------------------------------------

/** The freshness trigger: actively polls the latest commit SHA. */
export function useLatestSha() {
  return useQuery({
    queryKey: ["gh", "sha", REPO, REF],
    queryFn: () => latestSha(REPO, REF),
    staleTime: SHA_POLL_MS,
    refetchInterval: SHA_POLL_MS,
    refetchIntervalInBackground: false,
    // "always" (not true): true only refetches when stale, but staleTime == the poll interval,
    // so a tab refocused within the window would otherwise not refresh. "always" gives the
    // planned "sooner on focus/reconnect" freshness. It's just the cheap SHA call (raw is off-budget).
    refetchOnWindowFocus: "always",
    refetchOnReconnect: "always",
  });
}

/** Primitive hook: the repo tree at a SHA (immutable; shares cache with the derived loaders). */
export function useTree(sha: string | undefined) {
  return useQuery({
    queryKey: ["gh", "tree", REPO, sha],
    enabled: !!sha,
    staleTime: Infinity,
    gcTime: GC_TIME,
    queryFn: () => tree(REPO, sha as string),
  });
}

/** Primitive hook: a raw file's text at a SHA (immutable; off the API rate budget). */
export function useRawFile(sha: string | undefined, path: string) {
  return useQuery({
    queryKey: ["gh", "raw", REPO, sha, path],
    enabled: !!sha,
    staleTime: Infinity,
    gcTime: GC_TIME,
    queryFn: () => raw(REPO, sha as string, path),
  });
}

export function useTraditions(sha: string | undefined) {
  const qc = useQueryClient();
  return useQuery({
    queryKey: ["traditions", REPO, sha],
    enabled: !!sha,
    staleTime: Infinity,
    gcTime: GC_TIME,
    queryFn: () => loadTraditions(qc, sha as string),
  });
}

export function useTradition(sha: string | undefined, id: string) {
  const qc = useQueryClient();
  return useQuery({
    queryKey: ["tradition", REPO, sha, id],
    enabled: !!sha,
    staleTime: Infinity,
    gcTime: GC_TIME,
    queryFn: () => loadTradition(qc, sha as string, id),
  });
}

/** All results runs + the default (most recent). SHA-keyed, immutable per snapshot. */
export function useResultsRuns(sha: string | undefined) {
  const qc = useQueryClient();
  return useQuery({
    queryKey: ["results", "runs", REPO, sha],
    enabled: !!sha,
    staleTime: Infinity,
    gcTime: GC_TIME,
    queryFn: () => loadResultsRuns(qc, sha as string),
  });
}

/** One tradition's results shard for a run (off the API budget; parsed fail-soft). */
export function useResultsShard(sha: string | undefined, runId: string | undefined, tradition: string) {
  const qc = useQueryClient();
  return useQuery({
    queryKey: ["results", "shard", REPO, sha, runId, tradition],
    enabled: !!sha && !!runId,
    staleTime: Infinity,
    gcTime: GC_TIME,
    queryFn: () => loadResultsShard(qc, sha as string, runId as string, tradition),
  });
}

/** A whole run: manifest + all shards (drives the leaderboard). */
export function useResultsRun(sha: string | undefined, runId: string | undefined) {
  const qc = useQueryClient();
  return useQuery({
    queryKey: ["results", "run", REPO, sha, runId],
    enabled: !!sha && !!runId,
    staleTime: Infinity,
    gcTime: GC_TIME,
    queryFn: () => loadResultsRun(qc, sha as string, runId as string),
  });
}

export function useScenarioMeta(sha: string | undefined, tid: string, sid: string, declaredAxes: Record<string, readonly string[]>) {
  const qc = useQueryClient();
  return useQuery({
    queryKey: ["scenarioMeta", REPO, sha, tid, sid],
    enabled: !!sha,
    staleTime: Infinity,
    gcTime: GC_TIME,
    queryFn: () => loadScenarioMeta(qc, sha as string, tid, sid, declaredAxes),
  });
}

/** Progressive hydration: one query per scenario's metadata. Results align with `scenarioIds`. */
export function useScenarioMetas(
  sha: string | undefined,
  tid: string,
  scenarioIds: string[],
  declaredAxes: Record<string, readonly string[]>,
) {
  const qc = useQueryClient();
  return useQueries({
    queries: scenarioIds.map((sid) => ({
      queryKey: ["scenarioMeta", REPO, sha, tid, sid],
      enabled: !!sha,
      staleTime: Infinity,
      gcTime: GC_TIME,
      queryFn: () => metaLimiter(() => loadScenarioMeta(qc, sha as string, tid, sid, declaredAxes)),
    })),
  });
}

export function useScenario(sha: string | undefined, tid: string, sid: string, declaredAxes: Record<string, readonly string[]>) {
  const qc = useQueryClient();
  return useQuery({
    queryKey: ["scenario", REPO, sha, tid, sid],
    enabled: !!sha,
    staleTime: Infinity,
    gcTime: GC_TIME,
    queryFn: () => loadScenario(qc, sha as string, tid, sid, declaredAxes),
  });
}

// ── Raw-results tier (#51): resolve baked-vs-GitHub source + load one scenario shard ─────────

export interface LoadedRawScenario {
  catalog: RawCatalog | null;
  shard: RawShard | null;
  notices: Notice[];
}

/**
 * Load one scenario's raw shard: resolve the source (baked-first / GitHub-fallback, keyed to the
 * authoritative score-tier `expectedFingerprint`), find the item in the catalog, and load its
 * shard — all fail-soft (every failure becomes a `Notice`, never a throw).
 */
export async function loadRawScenario(
  sha: string,
  runId: string,
  group: string,
  item: string,
  expectedFingerprint: string | null,
): Promise<LoadedRawScenario> {
  const github = new GitHubRawSource(REPO, sha);
  const baked = new BakedRawSource();
  const { source, catalog, notices } = await resolveRawSource(baked, github, runId, expectedFingerprint);
  if (!catalog) return { catalog: null, shard: null, notices };
  const where = `results-raw/${runId}/manifest.json`;
  const it = catalog.items.find((i) => i.id === item && i.group === group);
  if (!it) {
    return { catalog, shard: null, notices: [...notices, notice("error", "results-raw", where, `no item "${group}/${item}" in this run`)] };
  }
  const { shard, notices: sn } = await loadRawShard(source, runId, it.shard);
  return { catalog, shard, notices: [...notices, ...sn] };
}

export function useRawScenario(
  sha: string | undefined,
  runId: string | undefined,
  group: string,
  item: string,
  expectedFingerprint: string | null,
) {
  return useQuery({
    queryKey: ["rawScenario", REPO, sha, runId, group, item],
    enabled: !!sha && !!runId,
    staleTime: Infinity,
    gcTime: GC_TIME,
    queryFn: () => loadRawScenario(sha as string, runId as string, group, item, expectedFingerprint),
  });
}
