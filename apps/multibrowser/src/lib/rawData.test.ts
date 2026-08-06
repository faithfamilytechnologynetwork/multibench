import { afterEach, describe, expect, it, vi } from "vitest";
import { gzipSync } from "node:zlib";
import { RateLimitError } from "./github";
import {
  isSafeRelPath,
  parseRawCatalog,
  parseRawShard,
  rawShardConsistencyNotices,
  RAW_SUPPORTED_SCHEMA_VERSION,
  type RawCatalog,
  type RawShard,
} from "./rawModel";
import {
  BakedRawSource,
  GitHubRawSource,
  decodeGzText,
  loadRawShard,
  resolveRawSource,
  type RawDataSource,
} from "./rawSource";
import { fakeRawSource } from "../test/rawFixture";

// ── fixtures ──────────────────────────────────────────────────────────────────────

const MB_CATALOG = {
  schema_version: 1,
  dataset: { title: "MultiBench raw results", language: "en", license: "CC-BY-4.0" },
  scale: { min: -1, center: 0, max: 1 },
  ramp: ["#9E1B32", "#D9D2C5", "#1B7837"],
  subjects: [{ id: "claude-sonnet-5", label: "claude-sonnet-5" }],
  judges: [{ key: "gemini", label: "gemini", fullGrid: true }],
  conditionAxes: [
    { key: "framing", label: "Framing", values: [{ id: "unstated", label: "Unstated" }, { id: "stated", label: "Stated" }] },
    { key: "pressure", label: "Pressure", values: [{ id: "secularize", label: "Secularize" }] },
  ],
  groupBy: { key: "tradition", label: "Tradition" },
  scopes: [{ id: "turn1", label: "turn1" }],
  items: [{ id: "BUD-001", label: "BUD-001", group: "buddhism", shard: "buddhism/BUD-001.json.gz" }],
  presets: [],
  fingerprint: "sha256:abc",
};

// A NON-MultiBench catalog (issue #54): 0–4 scale, non-tradition items, non-leaderboard subjects.
const AFB_CATALOG = {
  schema_version: 1,
  dataset: { title: "AFB before/after", license: "MIT" },
  scale: { min: 0, center: 2, max: 4 },
  ramp: ["#000", "#888", "#fff"],
  subjects: [{ id: "gemma-4-31b-it", label: "gemma-4-31b-it" }, { id: "mb-sft-dpo", label: "mb-sft-dpo" }],
  judges: [{ key: "terra", label: "gpt-5.6-terra", fullGrid: true }],
  conditionAxes: [{ key: "condition", label: "Condition", values: [{ id: "cold", label: "Cold" }] }],
  groupBy: { key: "instrument", label: "Instrument" },
  scopes: [{ id: "single", label: "single" }],
  items: [{ id: "AFB-001", label: "AFB-001", group: "afb-150", shard: "afb-150/AFB-001.json.gz" }],
  presets: [],
  fingerprint: "sha256:xyz",
};

const SHARD = {
  schema_version: 1,
  contexts: { stated: "[Context …]" },
  cells: [{
    subject: "claude-sonnet-5",
    conditions: { framing: "unstated", pressure: "secularize" },
    transcript: [{ role: "user", content: "hi" }, { role: "assistant", content: "hello" }],
    verdicts: [{ judge: "gemini", scope: "turn1", score: 1.0, summary: "held" }],
  }],
};

// ── isSafeRelPath ───────────────────────────────────────────────────────────────────

describe("isSafeRelPath", () => {
  it("accepts <group>/<item>.json.gz and rejects traversal / wrong extension", () => {
    expect(isSafeRelPath("buddhism/BUD-001.json.gz")).toBe(true);
    expect(isSafeRelPath("buddhism/BUD-001.json")).toBe(false);
    expect(isSafeRelPath("../evil.json.gz")).toBe(false);
    expect(isSafeRelPath("good/../../evil.json.gz")).toBe(false);
    expect(isSafeRelPath("solo.json.gz")).toBe(false); // needs ≥2 segments
  });
});

// ── parsers ───────────────────────────────────────────────────────────────────────

describe("parseRawCatalog", () => {
  it("parses a MultiBench catalog", () => {
    const { catalog, notices } = parseRawCatalog(JSON.stringify(MB_CATALOG), "m");
    expect(catalog?.schemaVersion).toBe(RAW_SUPPORTED_SCHEMA_VERSION);
    expect(catalog?.dataset.license).toBe("CC-BY-4.0");
    expect(catalog?.items[0]?.shard).toBe("buddhism/BUD-001.json.gz");
    expect(notices).toHaveLength(0);
  });

  it("parses a NON-MultiBench 0–4 catalog with no code change (genericity, #54)", () => {
    const { catalog, notices } = parseRawCatalog(JSON.stringify(AFB_CATALOG), "m");
    expect(catalog).not.toBeNull();
    expect(catalog?.scale).toEqual({ min: 0, center: 2, max: 4 });
    expect(catalog?.groupBy.key).toBe("instrument"); // not "tradition"
    expect(catalog?.conditionAxes[0]?.key).toBe("condition"); // not framing/pressure
    expect(notices).toHaveLength(0);
  });

  it("rejects an unsupported schema_version", () => {
    const { catalog, notices } = parseRawCatalog(JSON.stringify({ ...MB_CATALOG, schema_version: 99 }), "m");
    expect(catalog).toBeNull();
    expect(notices[0]?.message).toMatch(/unsupported schema_version/);
  });

  it("drops an item with an unsafe shard path (with a notice)", () => {
    const bad = { ...MB_CATALOG, items: [{ id: "X", label: "X", group: "g", shard: "../evil.json.gz" }] };
    const { catalog, notices } = parseRawCatalog(JSON.stringify(bad), "m");
    expect(catalog?.items).toHaveLength(0);
    expect(notices[0]?.message).toMatch(/unsafe shard path/);
  });

  it("flags malformed JSON", () => {
    const { catalog, notices } = parseRawCatalog("{not json", "m");
    expect(catalog).toBeNull();
    expect(notices[0]?.severity).toBe("error");
  });
});

describe("parseRawShard", () => {
  it("parses a shard and keeps contexts + generic conditions", () => {
    const { shard } = parseRawShard(JSON.stringify(SHARD), "s");
    expect(shard?.contexts.stated).toMatch(/Context/);
    expect(shard?.cells[0]?.conditions).toEqual({ framing: "unstated", pressure: "secularize" });
    expect(shard?.cells[0]?.verdicts[0]?.summary).toBe("held");
  });
  it("rejects an unsupported version", () => {
    const { shard, notices } = parseRawShard(JSON.stringify({ ...SHARD, schema_version: 2 }), "s");
    expect(shard).toBeNull();
    expect(notices[0]?.message).toMatch(/unsupported schema_version/);
  });
});

// ── catalog-aware shard consistency ──────────────────────────────────────────────────

describe("rawShardConsistencyNotices", () => {
  const catalog = parseRawCatalog(JSON.stringify(MB_CATALOG), "m").catalog as RawCatalog;
  const okShard = parseRawShard(JSON.stringify(SHARD), "s").shard as RawShard;

  it("passes a shard whose values are all catalog-declared", () => {
    expect(rawShardConsistencyNotices(okShard, catalog, "s")).toHaveLength(0);
  });

  it("flags an out-of-scale verdict score", () => {
    const bad: RawShard = { ...okShard, cells: [{ ...okShard.cells[0]!, verdicts: [{ judge: "gemini", scope: "turn1", score: 4, summary: "x" }] }] };
    const n = rawShardConsistencyNotices(bad, catalog, "s");
    expect(n.some((x) => /outside the catalog scale/.test(x.message))).toBe(true);
  });

  it("flags unknown subject / judge / scope / condition value / contextKey", () => {
    const bad: RawShard = {
      schemaVersion: 1,
      contexts: {},
      cells: [{
        subject: "who?",
        conditions: { framing: "nope", galaxy: "x" },
        transcript: [],
        contextKey: "missing",
        verdicts: [{ judge: "wat", scope: "midturn", score: 0, summary: "s" }],
      }],
    };
    const msgs = rawShardConsistencyNotices(bad, catalog, "s").map((n) => n.message).join(" | ");
    expect(msgs).toMatch(/subject/);
    expect(msgs).toMatch(/judge/);
    expect(msgs).toMatch(/scope/);
    expect(msgs).toMatch(/condition axis|condition value/);
    expect(msgs).toMatch(/contextKey/);
  });
});

// ── gunzip sniff ────────────────────────────────────────────────────────────────────

describe("decodeGzText", () => {
  it("decompresses raw gzip bytes (0x1f 0x8b)", async () => {
    const gz = gzipSync(Buffer.from(JSON.stringify(SHARD)));
    const text = await decodeGzText(gz.buffer.slice(gz.byteOffset, gz.byteOffset + gz.byteLength));
    expect(JSON.parse(text).cells).toHaveLength(1);
  });
  it("passes through already-decompressed bytes (host set Content-Encoding)", async () => {
    const plain = new TextEncoder().encode(JSON.stringify(SHARD));
    const text = await decodeGzText(plain.buffer);
    expect(JSON.parse(text).schema_version).toBe(1);
  });
});

// ── resolver (baked-first / GitHub-fallback / stale) ─────────────────────────────────

function bakedFrom(catalog: unknown | null): RawDataSource {
  return {
    kind: "baked",
    catalogText: async () => (catalog === null ? null : JSON.stringify(catalog)),
    shardText: async () => null,
  };
}
function githubFrom(catalog: unknown | null): RawDataSource {
  return {
    kind: "github",
    catalogText: async () => (catalog === null ? null : JSON.stringify(catalog)),
    shardText: async () => null,
  };
}

describe("resolveRawSource", () => {
  it("uses baked when present and fingerprint-coherent (no notice)", async () => {
    const r = await resolveRawSource(bakedFrom(MB_CATALOG), githubFrom(MB_CATALOG), "run1", "sha256:abc");
    expect(r.source.kind).toBe("baked");
    expect(r.notices).toHaveLength(0);
  });

  it("falls back to GitHub with a notice when baked is stale (fingerprint mismatch)", async () => {
    const staleBaked = { ...MB_CATALOG, fingerprint: "sha256:OLD" };
    const r = await resolveRawSource(bakedFrom(staleBaked), githubFrom(MB_CATALOG), "run1", "sha256:abc");
    expect(r.source.kind).toBe("github");
    expect(r.notices[0]?.message).toMatch(/stale.*live GitHub/);
    expect(r.catalog?.fingerprint).toBe("sha256:abc");
  });

  it("falls back to GitHub WITH a notice when baked is absent (serving fallback)", async () => {
    const r = await resolveRawSource(bakedFrom(null), githubFrom(MB_CATALOG), "run1", "sha256:abc");
    expect(r.source.kind).toBe("github");
    expect(r.notices.some((n) => /no baked bundle/.test(n.message))).toBe(true);
    expect(r.catalog).not.toBeNull();
  });

  it("flags a raw↔score fingerprint mismatch on the GitHub path", async () => {
    const wrongGh = { ...MB_CATALOG, fingerprint: "sha256:WRONG" };
    const r = await resolveRawSource(bakedFrom(null), githubFrom(wrongGh), "run1", "sha256:abc");
    expect(r.source.kind).toBe("github");
    expect(r.notices.some((n) => /raw and score tiers disagree/.test(n.message))).toBe(true);
  });

  it("does NOT use baked when the run fingerprint is unavailable (can't confirm coherence)", async () => {
    const r = await resolveRawSource(bakedFrom(MB_CATALOG), githubFrom(MB_CATALOG), "run1", null);
    expect(r.source.kind).toBe("github");
    expect(r.notices.some((n) => /can't be confirmed/.test(n.message))).toBe(true);
  });

  it("errors when neither source has the run", async () => {
    const r = await resolveRawSource(bakedFrom(null), githubFrom(null), "run1", null);
    expect(r.catalog).toBeNull();
    expect(r.notices.some((n) => /no raw dataset/.test(n.message))).toBe(true);
  });
});

// ── source impls (URL shape) ─────────────────────────────────────────────────────────

describe("loadRawShard (fail-soft)", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("loads + parses a shard from the fixture source", async () => {
    const { shard, notices } = await loadRawShard(fakeRawSource("baked"), "run1", "buddhism/BUD-001.json.gz");
    expect(shard?.cells).toHaveLength(2);
    expect(notices).toHaveLength(0);
  });

  it("returns a notice (no throw) when the shard is absent (404)", async () => {
    const { shard, notices } = await loadRawShard(fakeRawSource("baked"), "run1", "buddhism/MISSING.json.gz");
    expect(shard).toBeNull();
    expect(notices[0]?.message).toMatch(/not found/);
  });

  it("converts a GitHub rate-limit into an error notice (no throw)", async () => {
    const src: RawDataSource = {
      kind: "github",
      catalogText: async () => null,
      shardText: async () => { throw new RateLimitError(null); },
    };
    const { shard, notices } = await loadRawShard(src, "run1", "buddhism/BUD-001.json.gz");
    expect(shard).toBeNull();
    expect(notices[0]?.message).toMatch(/rate limit/);
  });

  it("converts a missing DecompressionStream into a fail-soft notice (feature-detect, no polyfill)", async () => {
    vi.stubGlobal("DecompressionStream", undefined);
    const gz = gzipSync(Buffer.from(JSON.stringify(SHARD)));
    const fetchImpl = (async () => new Response(gz, { status: 200 })) as unknown as typeof fetch;
    const src = new GitHubRawSource("owner/repo", "deadbeef", fetchImpl);
    const { shard, notices } = await loadRawShard(src, "run1", "buddhism/BUD-001.json.gz");
    expect(shard).toBeNull();
    expect(notices[0]?.message).toMatch(/DecompressionStream|can't decompress/i);
  });
});

describe("GitHubRawSource / BakedRawSource fetch shapes", () => {
  it("GitHubRawSource gunzips a shard fetched via raw bytes", async () => {
    const gz = gzipSync(Buffer.from(JSON.stringify(SHARD)));
    const fetchImpl = (async (url: string) => {
      if (url.endsWith(".json.gz")) return new Response(gz, { status: 200 });
      return new Response(null, { status: 404 });
    }) as unknown as typeof fetch;
    const src = new GitHubRawSource("owner/repo", "deadbeef", fetchImpl);
    const text = await src.shardText("run1", "buddhism/BUD-001.json.gz");
    expect(JSON.parse(text!).cells).toHaveLength(1);
  });

  it("BakedRawSource returns null on a 404 catalog", async () => {
    const fetchImpl = (async () => new Response(null, { status: 404 })) as unknown as typeof fetch;
    const src = new BakedRawSource("data-raw", fetchImpl);
    expect(await src.catalogText("run1")).toBeNull();
  });

  it("BakedRawSource resolves root-anchored URLs (not relative to a deep route)", async () => {
    let seen = "";
    const fetchImpl = (async (url: string) => { seen = url; return new Response("{}", { status: 200 }); }) as unknown as typeof fetch;
    // Simulate the viewer sitting on a deep route — the baked URL must still be /data-raw/…
    window.history.pushState({}, "", "/results/run1/buddhism/BUD-001");
    await new BakedRawSource("data-raw", fetchImpl).catalogText("run1");
    expect(new URL(seen).pathname).toBe("/data-raw/run1/manifest.json");
    expect(new URL(seen).origin).toBe(location.origin);
  });
});

describe("committed real catalog", () => {
  it("the shipped results-raw/20260803 manifest parses through parseRawCatalog", async () => {
    const fs = await import("node:fs");
    const url = await import("node:url");
    const path = await import("node:path");
    const here = path.dirname(url.fileURLToPath(import.meta.url));
    const manifest = path.resolve(here, "../../../../results-raw/20260803/manifest.json");
    if (!fs.existsSync(manifest)) return; // committed dataset absent in this checkout — skip
    const { catalog, notices } = parseRawCatalog(fs.readFileSync(manifest, "utf8"), "real");
    expect(catalog).not.toBeNull();
    expect(catalog!.items.length).toBe(519);
    expect(catalog!.dataset.license).toBe("CC-BY-4.0");
    expect(catalog!.fingerprint).toMatch(/^sha256:/);
    expect(notices).toHaveLength(0);
  });

  it("a real committed .gz shard gunzips, parses, and is catalog-consistent (drift guard)", async () => {
    const fs = await import("node:fs");
    const zlib = await import("node:zlib");
    const url = await import("node:url");
    const path = await import("node:path");
    const here = path.dirname(url.fileURLToPath(import.meta.url));
    const root = path.resolve(here, "../../../../results-raw/20260803");
    const manifestPath = path.join(root, "manifest.json");
    if (!fs.existsSync(manifestPath)) return; // committed dataset absent — skip
    const { catalog } = parseRawCatalog(fs.readFileSync(manifestPath, "utf8"), "real");
    const item = catalog!.items[0]!;
    const shardPath = path.join(root, item.shard);
    const text = zlib.gunzipSync(fs.readFileSync(shardPath)).toString("utf8");
    const { shard, notices } = parseRawShard(text, "real-shard");
    expect(shard).not.toBeNull();
    expect(notices).toHaveLength(0);
    expect(rawShardConsistencyNotices(shard!, catalog!, "real-shard")).toHaveLength(0);
  });
});
