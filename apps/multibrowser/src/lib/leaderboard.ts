// Pure leaderboard computation (authoritative, tested). The SPA's ONLY cross-tradition statistic
// is the equal-weight mean of the per-tradition means — which reconciles with the paper's
// tab_standings by construction (the per-tradition means come from the canonical Python export).

import type { ResultsManifest, ResultsShard } from "./resultsModel";
import type { Metric, ResultsSelection } from "./resultsSelection";

export interface TraditionValue {
  tradition: string;
  value: number;
  /** coverage numerator/denominator for this slice (honest-degradation badging). */
  nJudged: number;
  nExpected: number;
}

export interface Standing {
  subject: string;
  /** mean of per-tradition means, or null if no tradition had coverage for the selection. */
  value: number | null;
  /** the per-tradition contributions (for the drill-down + `k/N` annotation). */
  contributions: TraditionValue[];
  /** how many of the run's traditions contributed a value. */
  nContributing: number;
}

/** The judge model that ranks the leaderboard: the manifest's full-grid judge (Gemini). */
export function rankingJudgeModel(manifest: ResultsManifest): string {
  return manifest.judges.find((j) => j.fullGrid)?.model ?? "gemini-3.6-flash";
}

/** Resolve a UI judge key (e.g. "opus") to its model id via the manifest. */
export function judgeModelForKey(manifest: ResultsManifest, key: string): string | null {
  return manifest.judges.find((j) => j.key === key)?.model ?? null;
}

/**
 * One tradition's value for a (judge, subject, framing, metric, pressure) slice, or null.
 * `expectedCells` is the full-grid denominator for this slice (n_scenarios × pressures, or ×1 for
 * a single pressure) — used as the steadfastness coverage denominator, since a steadfastness cell
 * only carries its matched-cell count, not the expected total.
 */
export function traditionValue(
  shard: ResultsShard, judgeModel: string, subject: string, framing: string,
  metric: Metric, pressure: string, expectedCells: number,
): TraditionValue | null {
  if (metric === "steadfastness") {
    const cell = shard.steadfastness?.[judgeModel]?.[subject]?.[framing]?.[pressure];
    if (!cell) return null;
    return { tradition: shard.tradition, value: cell[0], nJudged: cell[1], nExpected: expectedCells };
  }
  const cell = shard.means?.[judgeModel]?.[subject]?.[framing]?.[metric]?.[pressure];
  if (!cell) return null;
  return { tradition: shard.tradition, value: cell[0], nJudged: cell[1], nExpected: cell[2] };
}

/**
 * One subject's per-tradition values for the selection under a SPECIFIC judge — the drill-down /
 * inspection data. Iterates traditions in manifest order (stable display). A tradition with no
 * value for this judge/slice is omitted (honest: zero coverage shows nothing, never a 0). This is
 * what the judge selector re-points to Opus without ever changing the Gemini-ranked leaderboard.
 */
export function subjectTraditionValues(
  shards: Record<string, ResultsShard>,
  manifest: ResultsManifest,
  subject: string,
  sel: Pick<ResultsSelection, "framing" | "metric" | "pressure">,
  judgeModel: string,
): TraditionValue[] {
  const perScenario = sel.pressure === manifest.pressureAll ? manifest.pressures.length : 1;
  const out: TraditionValue[] = [];
  for (const t of manifest.traditions) {
    const shard = shards[t.id];
    if (!shard) continue;
    const tv = traditionValue(shard, judgeModel, subject, sel.framing, sel.metric, sel.pressure, t.nScenarios * perScenario);
    if (tv !== null) out.push(tv);
  }
  return out;
}

/**
 * Standings for the given selection, ranked by the equal-weight mean of per-tradition means,
 * descending. `judgeModel` defaults to the ranking (full-grid) judge — the leaderboard always
 * ranks on Gemini; the judge selector (Phase 5) only re-points the drill-down/inspection layer.
 */
export function computeStandings(
  shards: Record<string, ResultsShard>,
  manifest: ResultsManifest,
  sel: Pick<ResultsSelection, "framing" | "metric" | "pressure">,
  judgeModel: string = rankingJudgeModel(manifest),
): Standing[] {
  const perScenario = sel.pressure === manifest.pressureAll ? manifest.pressures.length : 1;
  const standings = manifest.subjects.map((subject) => {
    const contributions: TraditionValue[] = [];
    for (const shard of Object.values(shards)) {
      const expectedCells = shard.nScenarios * perScenario;
      const tv = traditionValue(shard, judgeModel, subject, sel.framing, sel.metric, sel.pressure, expectedCells);
      if (tv !== null) contributions.push(tv);
    }
    const value = contributions.length
      ? contributions.reduce((a, c) => a + c.value, 0) / contributions.length
      : null;
    return { subject, value, contributions, nContributing: contributions.length };
  });
  // Rank by value desc; nulls (no coverage) sort last, deterministically (no NaN from null−null).
  standings.sort((a, b) => {
    if (a.value === null && b.value === null) return a.subject.localeCompare(b.subject);
    if (a.value === null) return 1;
    if (b.value === null) return -1;
    return b.value - a.value;
  });
  return standings;
}
