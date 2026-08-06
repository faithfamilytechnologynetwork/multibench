// The results-explorer selection model + its URL (de)serialization. Mirrors filtering.ts's
// role for the corpus browser: the AUTHORITATIVE selection semantics live here (pure, tested),
// the page is a thin driver, and every selector is deep-linkable via the flat search record.
//
// Unlike the corpus filters (multi-select OR facets), these are single-select: judge, framing,
// metric, pressure. Defaults are omitted from the URL so the bare `/results` link is clean.

import { z } from "zod";
import type { SearchRecord } from "./filtering";
import type { ResultsManifest } from "./resultsModel";

export type Metric = "turn1" | "full" | "steadfastness";

export interface ResultsSelection {
  /** null = "the default (most recent) run"; a string pins a specific run id. */
  runId: string | null;
  /** UI judge key (e.g. "gemini" | "opus"). Ranking is always the full-grid judge; the judge
   *  selector (Phase 5) switches only the inspection/drill-down layer. */
  judge: string;
  framing: string;
  metric: Metric;
  /** a pressure id, or the manifest's `pressure_all` sentinel ("all"). */
  pressure: string;
}

export const DEFAULTS = {
  judge: "gemini",
  framing: "unstated",
  metric: "full" as Metric,
  pressure: "all",
};

const METRICS: readonly Metric[] = ["turn1", "full", "steadfastness"];

/** Route-boundary schema (fail-soft, like filtering.ts's): a flat string record or {}. */
export const resultsSearchSchema = z
  .record(z.string(), z.union([z.string(), z.array(z.string())]))
  .catch({});

function one(v: string | string[] | undefined): string | undefined {
  return Array.isArray(v) ? v[0] : v;
}

/**
 * Interpret a raw search record into a validated selection. When a `manifest` is supplied,
 * unknown judge/framing/pressure values fall back to defaults (honest: an out-of-vocab deep link
 * degrades to the default view rather than a broken one). `metric` is validated against the fixed
 * UI set. `run` is passed through (validated against the manifest's runs by the caller).
 */
export function parseResultsSelection(search: SearchRecord, manifest?: ResultsManifest | null): ResultsSelection {
  const judgeKeys = manifest ? new Set(manifest.judges.map((j) => j.key)) : null;
  const framings = manifest ? new Set(manifest.framings) : null;
  const pressures = manifest ? new Set([...manifest.pressures, manifest.pressureAll]) : null;

  const rawJudge = one(search.judge);
  const rawFraming = one(search.framing);
  const rawMetric = one(search.metric);
  const rawPressure = one(search.pressure);
  const rawRun = one(search.run);

  const judge = rawJudge && (!judgeKeys || judgeKeys.has(rawJudge)) ? rawJudge : DEFAULTS.judge;
  const framing = rawFraming && (!framings || framings.has(rawFraming)) ? rawFraming : DEFAULTS.framing;
  const metric = (METRICS as readonly string[]).includes(rawMetric ?? "") ? (rawMetric as Metric) : DEFAULTS.metric;
  const pressure = rawPressure && (!pressures || pressures.has(rawPressure)) ? rawPressure : DEFAULTS.pressure;

  return { runId: rawRun && rawRun !== "" ? rawRun : null, judge, framing, metric, pressure };
}

/** Serialize a selection back to a flat search record, omitting defaults (clean base URL). */
export function selectionToResultsSearch(sel: ResultsSelection): SearchRecord {
  const out: SearchRecord = {};
  if (sel.runId) out.run = sel.runId;
  if (sel.judge !== DEFAULTS.judge) out.judge = sel.judge;
  if (sel.framing !== DEFAULTS.framing) out.framing = sel.framing;
  if (sel.metric !== DEFAULTS.metric) out.metric = sel.metric;
  if (sel.pressure !== DEFAULTS.pressure) out.pressure = sel.pressure;
  return out;
}
