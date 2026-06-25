// TanStack Query data layer. Composes the GitHub fetch boundary (github.ts) with the tolerant
// parsers (parse.ts) into cached, SHA-keyed read-model hooks.
//
// Freshness: `useLatestSha` actively polls via `refetchInterval` (TanStack `staleTime` alone
// does NOT poll) + focus/reconnect. Everything else is keyed by SHA and immutable per SHA
// (`staleTime: Infinity`), so a new SHA → new keys → automatic refetch on an open page.

import { useQuery, useQueryClient, type QueryClient } from "@tanstack/react-query";
import { latestSha, raw, tree, type TreeEntry } from "./github";
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

const GC_TIME = 1000 * 60 * 60; // keep SHA-pinned (immutable) data ~1h for instant back-nav

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
  declaredAxes: string[],
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
  declaredAxes: string[],
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
    refetchOnWindowFocus: true,
    refetchOnReconnect: true,
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

export function useScenarioMeta(sha: string | undefined, tid: string, sid: string, declaredAxes: string[]) {
  const qc = useQueryClient();
  return useQuery({
    queryKey: ["scenarioMeta", REPO, sha, tid, sid],
    enabled: !!sha,
    staleTime: Infinity,
    gcTime: GC_TIME,
    queryFn: () => loadScenarioMeta(qc, sha as string, tid, sid, declaredAxes),
  });
}

export function useScenario(sha: string | undefined, tid: string, sid: string, declaredAxes: string[]) {
  const qc = useQueryClient();
  return useQuery({
    queryKey: ["scenario", REPO, sha, tid, sid],
    enabled: !!sha,
    staleTime: Infinity,
    gcTime: GC_TIME,
    queryFn: () => loadScenario(qc, sha as string, tid, sid, declaredAxes),
  });
}
