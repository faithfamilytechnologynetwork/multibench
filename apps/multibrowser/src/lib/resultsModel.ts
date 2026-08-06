// Results dataset model + tolerant (display-first) parsers for the #49 results explorer.
//
// The SPA reads a committed `results/<run-id>/` dataset at runtime: a `manifest.json` (run
// metadata) and one `<tradition>.json` shard per tradition (pre-aggregated slice tables). All
// content is untrusted remote JSON, so parsing is fail-soft: a malformed / out-of-range /
// unknown-enum / unsupported-version document yields `null` + a `Notice`, never a throw or a
// silently-wrong value. Named `parseResults*` to avoid colliding with `parse.ts::parseManifest`
// (the tradition manifest).

import { z } from "zod";
import { notice, type Notice } from "./model";

/** The schema version this build understands. A dataset stamped otherwise is not trusted. */
export const SUPPORTED_SCHEMA_VERSION = 1;

// A score cell mean is on the −1…+1 scale; a steadfastness value (full − turn1) on −2…+2.
const scoreMean = z.number().finite().min(-1).max(1);
const steadfastnessValue = z.number().finite().min(-2).max(2);
const count = z.number().int().nonnegative();

// [mean, n_judged, n_expected] and [steadfastness, matched_n] — compact array cells.
const meanCell = z.tuple([scoreMean, count, count]);
const steadfastnessCell = z.tuple([steadfastnessValue, count]);

// Nested by string keys (judge → subject → framing → scope → pressure) — the keys are data
// values, validated against the manifest vocab at read time, not here.
const rec = <T extends z.ZodTypeAny>(v: T) => z.record(z.string(), v);

const ShardSchema = z.object({
  tradition: z.string(),
  n_scenarios: count,
  judges: z.array(z.string()),
  means: rec(rec(rec(rec(rec(meanCell))))),
  steadfastness: rec(rec(rec(rec(steadfastnessCell)))),
});

const JudgeMetaSchema = z.object({
  key: z.string(),
  model: z.string(),
  aliases: z.array(z.string()),
  full_grid: z.boolean(),
});

// judge → framing → {n_judged, n_expected}
const CoverageSchema = rec(rec(z.object({ n_judged: count, n_expected: count })));
// (used directly as counts.coverage; do NOT wrap in another rec())

const ManifestSchema = z.object({
  schema_version: z.number(),
  run_id: z.string(),
  generated_at: z.string(),
  subjects: z.array(z.string()),
  judges: z.array(JudgeMetaSchema),
  framings: z.array(z.string()),
  pressures: z.array(z.string()),
  pressure_all: z.string(),
  scopes: z.array(z.string()),
  metrics: z.array(z.string()),
  traditions: z.array(z.object({ id: z.string(), n_scenarios: count, shard: z.string() })),
  counts: z
    .object({
      judgments: rec(count).optional(),
      coverage: CoverageSchema.optional(),
    })
    .optional(),
});

// ---- TS-facing types (top-level fields camelCased; nested cells kept as-is) ------------------

export type MeanCell = [mean: number, nJudged: number, nExpected: number];
export type SteadfastnessCell = [value: number, matchedN: number];

export interface JudgeMeta {
  key: string;
  model: string;
  aliases: string[];
  fullGrid: boolean;
}

export interface ResultsRunRef {
  id: string;
  nScenarios: number;
  shard: string;
}

export interface ResultsManifest {
  schemaVersion: number;
  runId: string;
  generatedAt: string;
  subjects: string[];
  judges: JudgeMeta[];
  framings: string[];
  pressures: string[];
  pressureAll: string;
  scopes: string[];
  metrics: string[];
  traditions: ResultsRunRef[];
  coverage: Record<string, Record<string, { nJudged: number; nExpected: number }>>;
}

export interface ResultsShard {
  tradition: string;
  nScenarios: number;
  judges: string[];
  // judge → subject → framing → scope → pressure(+"all") → [mean, nJudged, nExpected]
  means: Record<string, Record<string, Record<string, Record<string, Record<string, MeanCell>>>>>;
  // judge → subject → framing → pressure(+"all") → [value, matchedN]
  steadfastness: Record<string, Record<string, Record<string, Record<string, SteadfastnessCell>>>>;
}

// ---- tolerant parsers -----------------------------------------------------------------------

function parseJson(text: string, scope: string, where: string): { data: unknown; notice: Notice | null } {
  try {
    return { data: JSON.parse(text), notice: null };
  } catch (e) {
    return { data: null, notice: notice("error", scope, where, `malformed JSON: ${(e as Error).message}`) };
  }
}

/** Parse a results manifest. Returns `{ manifest: null, notices }` on any problem. */
export function parseResultsManifest(
  text: string,
  where: string,
): { manifest: ResultsManifest | null; notices: Notice[] } {
  const { data, notice: jsonNotice } = parseJson(text, "results", where);
  if (jsonNotice) return { manifest: null, notices: [jsonNotice] };

  const parsed = ManifestSchema.safeParse(data);
  if (!parsed.success) {
    return {
      manifest: null,
      notices: [notice("error", "results", where, `invalid manifest: ${parsed.error.issues[0]?.message ?? "shape"}`)],
    };
  }
  const m = parsed.data;
  if (m.schema_version !== SUPPORTED_SCHEMA_VERSION) {
    return {
      manifest: null,
      notices: [
        notice("error", "results", where,
          `unsupported schema_version ${m.schema_version} (this build understands ${SUPPORTED_SCHEMA_VERSION})`),
      ],
    };
  }
  const notices: Notice[] = [];
  if (Number.isNaN(Date.parse(m.generated_at))) {
    // Metadata, not load-bearing — keep the manifest but flag it (run-ordering falls back safely).
    notices.push(notice("warning", "results", where, `unparseable generated_at "${m.generated_at}"`));
  }
  const coverage: ResultsManifest["coverage"] = {};
  for (const [judge, byFraming] of Object.entries(m.counts?.coverage ?? {})) {
    const dst: Record<string, { nJudged: number; nExpected: number }> = {};
    for (const [framing, c] of Object.entries(byFraming)) {
      dst[framing] = { nJudged: c.n_judged, nExpected: c.n_expected };
    }
    coverage[judge] = dst;
  }
  return {
    manifest: {
      schemaVersion: m.schema_version,
      runId: m.run_id,
      generatedAt: m.generated_at,
      subjects: m.subjects,
      judges: m.judges.map((j) => ({ key: j.key, model: j.model, aliases: j.aliases, fullGrid: j.full_grid })),
      framings: m.framings,
      pressures: m.pressures,
      pressureAll: m.pressure_all,
      scopes: m.scopes,
      metrics: m.metrics,
      traditions: m.traditions.map((t) => ({ id: t.id, nScenarios: t.n_scenarios, shard: t.shard })),
      coverage,
    },
    notices,
  };
}

/**
 * Cross-validate a shard against its manifest: the requested tradition, `n_scenarios`, and every
 * judge/subject/framing/scope/pressure key must be in the manifest's declared vocabulary. Unknown
 * keys become `Notice`s (display-first — the shard still renders; the UI only selects known keys).
 * One notice per category (deduped) rather than per stray key.
 */
export function shardConsistencyNotices(
  shard: ResultsShard,
  manifest: ResultsManifest,
  requestedTradition: string,
  where: string,
): Notice[] {
  const notices: Notice[] = [];
  if (shard.tradition !== requestedTradition) {
    notices.push(notice("error", "results", where,
      `shard tradition "${shard.tradition}" does not match requested "${requestedTradition}"`));
  }
  const trad = manifest.traditions.find((t) => t.id === requestedTradition);
  if (trad && shard.nScenarios !== trad.nScenarios) {
    notices.push(notice("warning", "results", where,
      `n_scenarios ${shard.nScenarios} disagrees with manifest ${trad.nScenarios}`));
  }
  const judges = new Set(manifest.judges.map((j) => j.model));
  const subjects = new Set(manifest.subjects);
  const framings = new Set(manifest.framings);
  const scopes = new Set(manifest.scopes);
  const pressures = new Set([...manifest.pressures, manifest.pressureAll]);
  const unknown: Record<string, Set<string>> = {
    judge: new Set(), subject: new Set(), framing: new Set(), scope: new Set(), pressure: new Set(),
  };

  for (const [judge, bySubj] of Object.entries(shard.means)) {
    if (!judges.has(judge)) unknown.judge!.add(judge);
    for (const [subject, byFr] of Object.entries(bySubj)) {
      if (!subjects.has(subject)) unknown.subject!.add(subject);
      for (const [framing, byScope] of Object.entries(byFr)) {
        if (!framings.has(framing)) unknown.framing!.add(framing);
        for (const [scope, byPr] of Object.entries(byScope)) {
          if (!scopes.has(scope)) unknown.scope!.add(scope);
          for (const pressure of Object.keys(byPr)) {
            if (!pressures.has(pressure)) unknown.pressure!.add(pressure);
          }
        }
      }
    }
  }
  for (const [judge, bySubj] of Object.entries(shard.steadfastness)) {
    if (!judges.has(judge)) unknown.judge!.add(judge);
    for (const [subject, byFr] of Object.entries(bySubj)) {
      if (!subjects.has(subject)) unknown.subject!.add(subject);
      for (const [framing, byPr] of Object.entries(byFr)) {
        if (!framings.has(framing)) unknown.framing!.add(framing);
        for (const pressure of Object.keys(byPr)) {
          if (!pressures.has(pressure)) unknown.pressure!.add(pressure);
        }
      }
    }
  }
  for (const [category, vals] of Object.entries(unknown)) {
    if (vals.size > 0) {
      notices.push(notice("warning", "results", where,
        `unknown ${category}(s) not in manifest: ${[...vals].sort().join(", ")}`));
    }
  }
  return notices;
}

/** Parse one tradition shard. Returns `{ shard: null, notices }` on any problem. */
export function parseResultsShard(
  text: string,
  where: string,
): { shard: ResultsShard | null; notices: Notice[] } {
  const { data, notice: jsonNotice } = parseJson(text, "results", where);
  if (jsonNotice) return { shard: null, notices: [jsonNotice] };

  const parsed = ShardSchema.safeParse(data);
  if (!parsed.success) {
    return {
      shard: null,
      notices: [notice("error", "results", where, `invalid shard: ${parsed.error.issues[0]?.message ?? "shape"}`)],
    };
  }
  const s = parsed.data;
  return {
    shard: {
      tradition: s.tradition,
      nScenarios: s.n_scenarios,
      judges: s.judges,
      means: s.means,
      steadfastness: s.steadfastness,
    },
    notices: [],
  };
}
