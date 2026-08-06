import { describe, it, expect, afterEach, vi } from "vitest";
import { QueryClient } from "@tanstack/react-query";
import {
  resultsRunIds,
  loadResultsRuns,
  loadResultsShard,
  loadResultsManifest,
} from "./queries";
import { parseResultsManifest, parseResultsShard } from "./resultsModel";
import { tree } from "./github";
import { REPO } from "./constants";
import { buildTree, fakeFetch, resultsFiles } from "../test/fakeRepo";

const SHA = "deadbeef";

function newQc() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } });
}

afterEach(() => vi.unstubAllGlobals());

describe("resultsRunIds discovery", () => {
  it("finds results/<id>/manifest.json dirs (sorted)", () => {
    const files = { ...resultsFiles("20260803"), ...resultsFiles("20260701") };
    expect(resultsRunIds(buildTree(files))).toEqual(["20260701", "20260803"]);
  });
  it("ignores non-results and non-manifest paths", () => {
    const entries = buildTree({
      "results/r1/manifest.json": "{}",
      "results/r1/buddhism.json": "{}",
      "traditions/x/tradition.yaml": "{}",
    });
    expect(resultsRunIds(entries)).toEqual(["r1"]);
  });
});

describe("loadResultsRuns (real QueryClient + stubbed fetch)", () => {
  it("defaults to the most recent run by generated_at", async () => {
    const files = {
      ...resultsFiles("older", { generatedAt: "2026-07-01T00:00:00+00:00" }),
      ...resultsFiles("newer", { generatedAt: "2026-08-03T00:00:00+00:00" }),
    };
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, files));
    const { runs, defaultRunId } = await loadResultsRuns(newQc(), SHA);
    expect(runs.map((r) => r.id).sort()).toEqual(["newer", "older"]);
    expect(defaultRunId).toBe("newer"); // latest by manifest date
  });

  it("an invalid manifest yields a notice and does not become the default", async () => {
    const files = {
      ...resultsFiles("good", { generatedAt: "2026-07-01T00:00:00+00:00" }),
      "results/bad/manifest.json": "{ not json",
    };
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, files));
    const { runs, defaultRunId } = await loadResultsRuns(newQc(), SHA);
    expect(defaultRunId).toBe("good");
    const bad = runs.find((r) => r.id === "bad")!;
    expect(bad.manifest).toBeNull();
    expect(bad.notices.length).toBeGreaterThan(0);
  });

  it("orders by parsed instant; an unparseable date warns and sorts last", async () => {
    const files = {
      ...resultsFiles("good", { generatedAt: "2026-08-03T00:00:00+00:00" }),
      ...resultsFiles("nodate", { generatedAt: "not-a-date" }),
    };
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, files));
    const { runs, defaultRunId } = await loadResultsRuns(newQc(), SHA);
    expect(defaultRunId).toBe("good"); // valid date wins; unparseable sorts last
    const nodate = runs.find((r) => r.id === "nodate")!;
    expect(nodate.manifest).not.toBeNull(); // still accepted (date is metadata)
    expect(nodate.notices.some((n) => /unparseable generated_at/.test(n.message))).toBe(true);
  });

  it("compares non-UTC offsets by instant, not lexically", async () => {
    // "2026-08-03T00:00:00+05:00" is EARLIER than "2026-08-02T21:00:00+00:00"? No — equal instant.
    // Use a case where lexical order would be wrong: +05:00 midnight vs +00:00 01:00 same day.
    const files = {
      ...resultsFiles("offset", { generatedAt: "2026-08-03T00:00:00+05:00" }), // = 2026-08-02T19:00Z
      ...resultsFiles("utc", { generatedAt: "2026-08-02T20:00:00+00:00" }), // later instant
    };
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, files));
    const { defaultRunId } = await loadResultsRuns(newQc(), SHA);
    expect(defaultRunId).toBe("utc"); // later instant wins (lexical would pick "offset")
  });
});

describe("loadResultsShard / loadResultsManifest", () => {
  it("loads and parses a shard", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, resultsFiles("r1", { traditions: ["buddhism"] })));
    const { shard, notices } = await loadResultsShard(newQc(), SHA, "r1", "buddhism");
    expect(notices).toEqual([]);
    expect(shard?.tradition).toBe("buddhism");
    expect(shard?.means?.["gemini-3.6-flash"]?.["claude-sonnet-5"]?.unstated?.full?.all).toEqual([0.5, 2, 2]);
  });

  it("a tradition absent from the manifest yields a notice", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, resultsFiles("r1", { traditions: ["buddhism"] })));
    const { shard, notices } = await loadResultsShard(newQc(), SHA, "r1", "atlantis");
    expect(shard).toBeNull();
    expect(notices[0]?.message).toMatch(/not in manifest/);
  });

  it("a manifest-listed shard whose file is missing yields a notice", async () => {
    const files = resultsFiles("r1", { traditions: ["buddhism"] });
    delete files["results/r1/buddhism.json"]; // manifest lists it; file absent
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, files));
    const { shard, notices } = await loadResultsShard(newQc(), SHA, "r1", "buddhism");
    expect(shard).toBeNull();
    expect(notices[0]?.message).toMatch(/no results shard/);
  });

  it("uses the shard filename declared in the manifest (single source of truth)", async () => {
    const files = resultsFiles("r1", {
      traditions: ["buddhism"],
      shard: (t) => ({ tradition: t, n_scenarios: 2, judges: ["gemini-3.6-flash"], means: {}, steadfastness: {} }),
    });
    // Rename the shard file + point the manifest at the new name.
    const manifest = JSON.parse(files["results/r1/manifest.json"]!);
    manifest.traditions[0].shard = "buddhism.v2.json";
    files["results/r1/manifest.json"] = JSON.stringify(manifest);
    files["results/r1/buddhism.v2.json"] = files["results/r1/buddhism.json"]!;
    delete files["results/r1/buddhism.json"];
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, files));
    const { shard, notices } = await loadResultsShard(newQc(), SHA, "r1", "buddhism");
    expect(shard?.tradition).toBe("buddhism");
    expect(notices).toEqual([]);
  });

  it("unknown selector keys + tradition/n_scenarios mismatch surface as notices (shard still returned)", async () => {
    const files = resultsFiles("r1", {
      traditions: ["buddhism"],
      shard: () => ({
        tradition: "WRONG", // mismatch
        n_scenarios: 99, // mismatch (manifest says 2)
        judges: ["gemini-3.6-flash"],
        means: {
          "mystery-judge": { "claude-sonnet-5": { unstated: { full: { bogus_pressure: [0.5, 1, 1] } } } },
        },
        steadfastness: {},
      }),
    });
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, files));
    const { shard, notices } = await loadResultsShard(newQc(), SHA, "r1", "buddhism");
    expect(shard).not.toBeNull(); // display-first: still returned
    const msgs = notices.map((n) => n.message).join(" | ");
    expect(msgs).toMatch(/does not match requested/);
    expect(msgs).toMatch(/n_scenarios 99/);
    expect(msgs).toMatch(/unknown judge\(s\).*mystery-judge/);
    expect(msgs).toMatch(/unknown pressure\(s\).*bogus_pressure/);
  });

  it("a missing manifest yields a notice", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, {}));
    const { manifest, notices } = await loadResultsManifest(newQc(), SHA, "ghost");
    expect(manifest).toBeNull();
    expect(notices[0]?.message).toMatch(/not found/);
  });
});

describe("parseResultsManifest / parseResultsShard validation (fail-soft)", () => {
  it("rejects an unsupported schema_version", () => {
    const text = resultsFiles("r1", { schemaVersion: 99 })["results/r1/manifest.json"]!;
    const { manifest, notices } = parseResultsManifest(text, "m");
    expect(manifest).toBeNull();
    expect(notices[0]?.message).toMatch(/unsupported schema_version 99/);
  });

  it("maps snake_case manifest fields to camelCase + coverage", () => {
    const text = resultsFiles("r1")["results/r1/manifest.json"]!;
    const { manifest } = parseResultsManifest(text, "m");
    expect(manifest?.runId).toBe("r1");
    expect(manifest?.judges.find((j) => j.key === "opus")?.fullGrid).toBe(false);
    expect(manifest?.coverage?.["gemini-3.6-flash"]?.unstated).toEqual({ nJudged: 10, nExpected: 10 });
  });

  it("rejects an out-of-range score in a shard cell", () => {
    const bad = JSON.stringify({
      tradition: "b", n_scenarios: 2, judges: ["gemini-3.6-flash"],
      means: { "gemini-3.6-flash": { s: { unstated: { full: { all: [1.5, 2, 2] } } } } },
      steadfastness: {},
    });
    const { shard, notices } = parseResultsShard(bad, "s");
    expect(shard).toBeNull();
    expect(notices[0]?.message).toMatch(/invalid shard/);
  });

  it("rejects a non-finite / malformed cell", () => {
    const bad = JSON.stringify({
      tradition: "b", n_scenarios: 2, judges: ["g"],
      means: { g: { s: { unstated: { full: { all: [0.5, 2] } } } } }, // wrong tuple arity
      steadfastness: {},
    });
    expect(parseResultsShard(bad, "s").shard).toBeNull();
  });

  it("malformed JSON yields a notice, not a throw", () => {
    expect(parseResultsShard("{oops", "s").shard).toBeNull();
    expect(parseResultsManifest("{oops", "m").manifest).toBeNull();
  });
});

describe("truncation fallback discovers results/", () => {
  it("a truncated recursive tree still yields results/ + traditions/ entries", async () => {
    const files = {
      ...resultsFiles("20260803", { traditions: ["buddhism", "taoism"] }),
      "traditions/sunni-islam/tradition.yaml": "id: sunni-islam",
    };
    const entries = await tree(REPO, SHA, fakeFetch(REPO, SHA, files, { truncated: true }));
    const paths = entries.map((e) => e.path);
    expect(paths).toContain("results/20260803/manifest.json");
    expect(paths).toContain("results/20260803/buddhism.json");
    expect(paths).toContain("traditions/sunni-islam/tradition.yaml");
    // and resultsRunIds still works off the fallback-built tree
    expect(resultsRunIds(entries)).toEqual(["20260803"]);
  });
});
