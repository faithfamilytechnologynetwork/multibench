import { describe, it, expect } from "vitest";
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { computeStandings, rankingJudgeModel, subjectTraditionValues, traditionValue } from "./leaderboard";
import type { ResultsManifest, ResultsShard } from "./resultsModel";

const manifest: ResultsManifest = {
  schemaVersion: 1,
  runId: "r1",
  generatedAt: "2026-08-06T00:00:00+00:00",
  subjects: ["claude-sonnet-5", "gemini-3.6-flash"],
  judges: [
    { key: "gemini", model: "gemini-3.6-flash", aliases: ["gemini-3.6-flash"], fullGrid: true },
    { key: "opus", model: "claude-opus-4-8", aliases: ["claude-opus-4-8"], fullGrid: false },
  ],
  framings: ["unstated", "stated", "guided"],
  pressures: ["secularize", "insistence"],
  pressureAll: "all",
  scopes: ["turn1", "full"],
  metrics: ["turn1", "full", "steadfastness"],
  traditions: [
    { id: "a", nScenarios: 2, shard: "a.json" },
    { id: "b", nScenarios: 2, shard: "b.json" },
  ],
  coverage: {},
};

function shard(tradition: string, sonnetFullAll: number, sonnetTurn1All: number, steadAll: number): ResultsShard {
  return {
    tradition,
    nScenarios: 2,
    judges: ["gemini-3.6-flash"],
    means: {
      "gemini-3.6-flash": {
        "claude-sonnet-5": {
          unstated: { full: { all: [sonnetFullAll, 2, 2] }, turn1: { all: [sonnetTurn1All, 2, 2] } },
        },
      },
    },
    steadfastness: {
      "gemini-3.6-flash": { "claude-sonnet-5": { unstated: { all: [steadAll, 2] } } },
    },
  };
}

const shards = { a: shard("a", 0.6, 0.2, 0.4), b: shard("b", 0.8, 0.0, 0.8) };

describe("computeStandings — mean of per-tradition means", () => {
  it("post-pressure (full) = equal-weight mean across traditions, ranked desc", () => {
    const st = computeStandings(shards, manifest, { framing: "unstated", metric: "full", pressure: "all" });
    const sonnet = st.find((s) => s.subject === "claude-sonnet-5")!;
    expect(sonnet.value).toBeCloseTo(0.7, 10); // (0.6 + 0.8) / 2
    expect(sonnet.nContributing).toBe(2);
    // gemini subject has no data → value null, sorts last
    expect(st[0]!.subject).toBe("claude-sonnet-5");
    expect(st[st.length - 1]!.value).toBeNull();
  });

  it("first-response (turn1) selects the turn1 slice", () => {
    const st = computeStandings(shards, manifest, { framing: "unstated", metric: "turn1", pressure: "all" });
    expect(st.find((s) => s.subject === "claude-sonnet-5")!.value).toBeCloseTo(0.1, 10); // (0.2 + 0.0)/2
  });

  it("steadfastness reads the steadfastness slice (no client subtraction)", () => {
    const st = computeStandings(shards, manifest, { framing: "unstated", metric: "steadfastness", pressure: "all" });
    expect(st.find((s) => s.subject === "claude-sonnet-5")!.value).toBeCloseTo(0.6, 10); // (0.4 + 0.8)/2
  });

  it("a tradition without coverage for the slice is excluded (not counted as 0)", () => {
    const partial = { a: shards.a }; // only tradition a
    const st = computeStandings(partial, manifest, { framing: "unstated", metric: "full", pressure: "all" });
    const sonnet = st.find((s) => s.subject === "claude-sonnet-5")!;
    expect(sonnet.value).toBeCloseTo(0.6, 10); // just tradition a
    expect(sonnet.nContributing).toBe(1);
  });

  it("rankingJudgeModel is the full-grid judge (Gemini)", () => {
    expect(rankingJudgeModel(manifest)).toBe("gemini-3.6-flash");
  });

  it("subjectTraditionValues returns per-tradition values for a judge, omitting missing ones", () => {
    const partial = { a: shards.a }; // only tradition a has data
    const tvs = subjectTraditionValues(
      partial, manifest, "claude-sonnet-5", { framing: "unstated", metric: "full", pressure: "all" },
      "gemini-3.6-flash",
    );
    expect(tvs).toHaveLength(1);
    expect(tvs[0]).toMatchObject({ tradition: "a", value: 0.6 });
    // a judge with no data → empty (honest: nothing, not zeros)
    expect(subjectTraditionValues(partial, manifest, "claude-sonnet-5",
      { framing: "unstated", metric: "full", pressure: "all" }, "claude-opus-4-8")).toEqual([]);
  });

  it("traditionValue returns coverage for a means cell and null for a missing one", () => {
    const tv = traditionValue(shards.a, "gemini-3.6-flash", "claude-sonnet-5", "unstated", "full", "all", 12);
    expect(tv).toEqual({ tradition: "a", value: 0.6, nJudged: 2, nExpected: 2 }); // means uses cell's own nExpected
    expect(traditionValue(shards.a, "gemini-3.6-flash", "missing", "unstated", "full", "all", 12)).toBeNull();
  });

  it("steadfastness coverage uses the full-grid denominator, not matched_n (Phase-5 badging)", () => {
    const tv = traditionValue(shards.a, "gemini-3.6-flash", "claude-sonnet-5", "unstated", "steadfastness", "all", 12);
    expect(tv).toEqual({ tradition: "a", value: 0.4, nJudged: 2, nExpected: 12 }); // 2/12, not 2/2
  });
});

// Reconciliation against the REAL committed dataset (results/20260803/) — the SPA's mean-of-means
// must equal the paper's standings. Uses the committed artifact (no gitignored symlink needed);
// the paper values are the ones verified end-to-end in the Python export tests.
describe("committed dataset reconciles with the paper (Gemini standings)", () => {
  // vitest runs with cwd = apps/multibrowser; the committed dataset is at <repo>/results/.
  const root = resolve(process.cwd(), "../../results/20260803");
  const manifestPath = `${root}/manifest.json`;
  const hasCommitted = existsSync(manifestPath);
  // Paper standings (subj_overall) for ALL five subjects × three framings — committed here so the
  // reconciliation runs portably (no gitignored launch data needed).
  const PAPER: Record<string, Record<string, number>> = {
    "Qwen/Qwen3-235B-A22B-Instruct-2507": { unstated: -0.44739844429738396, stated: -0.13956766723971545, guided: 0.4360177612491137 },
    "claude-sonnet-5": { unstated: 0.5460820873085531, stated: 0.8389174367798489, guided: 0.955169687941307 },
    "gemini-3.6-flash": { unstated: 0.13878992434644954, stated: 0.5552255169248714, guided: 0.9392007764689806 },
    "gpt-5.6-terra": { unstated: 0.3665434394791269, stated: 0.6595724833623953, guided: 0.8600802417700205 },
    "thinkingmachines/Inkling": { unstated: 0.5434524040736548, stated: 0.8140794388849457, guided: 0.971569450432777 },
  };

  it.runIf(hasCommitted)("all 5 subjects × 3 framings (full/all) mean-of-means == subj_overall", () => {
    const realManifest = JSON.parse(readFileSync(manifestPath, "utf8"));
    const m: ResultsManifest = {
      ...manifest,
      subjects: realManifest.subjects,
      judges: realManifest.judges.map((j: { key: string; model: string; aliases: string[]; full_grid: boolean }) => ({
        key: j.key, model: j.model, aliases: j.aliases, fullGrid: j.full_grid,
      })),
      pressures: realManifest.pressures,
      pressureAll: realManifest.pressure_all,
      traditions: realManifest.traditions.map((t: { id: string; n_scenarios: number; shard: string }) => ({
        id: t.id, nScenarios: t.n_scenarios, shard: t.shard,
      })),
    };
    const realShards: Record<string, ResultsShard> = {};
    for (const t of m.traditions) {
      const s = JSON.parse(readFileSync(`${root}/${t.shard}`, "utf8"));
      realShards[t.id] = { tradition: s.tradition, nScenarios: s.n_scenarios, judges: s.judges, means: s.means, steadfastness: s.steadfastness };
    }
    for (const framing of ["unstated", "stated", "guided"]) {
      const st = computeStandings(realShards, m, { framing, metric: "full", pressure: "all" });
      for (const subject of Object.keys(PAPER)) {
        const row = st.find((s) => s.subject === subject)!;
        expect(row.value).toBeCloseTo(PAPER[subject]![framing]!, 9);
        expect(row.nContributing).toBe(7);
      }
    }
  });
});
