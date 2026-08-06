import { describe, expect, it } from "vitest";
import { QueryClient } from "@tanstack/react-query";
import { loadRawScenario, type RawSources } from "./queries";
import { GitHubRawSource } from "./rawSource";
import {
  RAW_FIXTURE_FINGERPRINT,
  fakeRawSource,
  rawFixtureCatalog,
  rawFixtureShardGz,
} from "../test/rawFixture";

function qc() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } });
}

/** Injected sources: baked serves the fixture (fingerprint overridable); GitHub serves fixture gz over a fake fetch. */
function sources(bakedFingerprint?: string): RawSources {
  const gz = rawFixtureShardGz();
  const fetchImpl = (async (url: string) => {
    if (url.endsWith("manifest.json")) return new Response(JSON.stringify(rawFixtureCatalog), { status: 200 });
    if (url.endsWith(".json.gz")) return new Response(gz, { status: 200 });
    return new Response(null, { status: 404 });
  }) as unknown as typeof fetch;
  return {
    baked: fakeRawSource("baked", bakedFingerprint ? { fingerprint: bakedFingerprint } : {}),
    github: new GitHubRawSource("owner/repo", "sha", fetchImpl),
  };
}

describe("loadRawScenario (integration)", () => {
  it("loads catalog + shard via the coherent baked source", async () => {
    const r = await loadRawScenario(qc(), "sha", "fixt-run", "buddhism", "BUD-001",
      RAW_FIXTURE_FINGERPRINT, sources());
    expect(r.catalog?.items).toHaveLength(1);
    expect(r.shard?.cells).toHaveLength(2);
    expect(r.notices).toHaveLength(0); // coherent baked → no fallback notice
  });

  it("notices a missing item", async () => {
    const r = await loadRawScenario(qc(), "sha", "fixt-run", "buddhism", "NOPE",
      RAW_FIXTURE_FINGERPRINT, sources());
    expect(r.shard).toBeNull();
    expect(r.notices.some((n) => /no item/.test(n.message))).toBe(true);
  });

  it("rejects an unsafe run id before any fetch", async () => {
    const r = await loadRawScenario(qc(), "sha", "../evil", "buddhism", "BUD-001", null, sources());
    expect(r.catalog).toBeNull();
    expect(r.notices[0]?.message).toMatch(/unsafe run id/);
  });

  it("re-resolves when the fingerprint transitions null → known (different query keys)", async () => {
    const client = qc();
    const src = sources();
    // null fingerprint → can't confirm baked → GitHub fallback (with a notice)
    const first = await loadRawScenario(client, "sha", "fixt-run", "buddhism", "BUD-001", null, src);
    expect(first.notices.some((n) => /can't be confirmed/.test(n.message))).toBe(true);
    // known matching fingerprint → coherent baked (no fallback notice); a DIFFERENT cache key
    const second = await loadRawScenario(client, "sha", "fixt-run", "buddhism", "BUD-001",
      RAW_FIXTURE_FINGERPRINT, src);
    expect(second.notices).toHaveLength(0);
    expect(second.shard?.cells).toHaveLength(2);
  });

  it("serves the GitHub gz shard when baked is stale", async () => {
    const r = await loadRawScenario(qc(), "sha", "fixt-run", "buddhism", "BUD-001",
      RAW_FIXTURE_FINGERPRINT, sources("sha256:STALE"));
    expect(r.notices.some((n) => /stale/.test(n.message))).toBe(true);
    expect(r.shard?.cells).toHaveLength(2); // still renders — from the GitHub gz fallback
  });

  it("survives cache persistence/hydration (no class instance is cached)", async () => {
    const client = qc();
    const src = sources();
    await loadRawScenario(client, "sha", "fixt-run", "buddhism", "BUD-001", RAW_FIXTURE_FINGERPRINT, src);
    // simulate a localStorage round-trip: every cached value becomes a plain object
    for (const q of client.getQueryCache().getAll()) {
      if (q.state.data !== undefined) {
        client.setQueryData(q.queryKey, JSON.parse(JSON.stringify(q.state.data)));
      }
    }
    // a later load in the same run must still work — the source is reconstructed from `kind`,
    // not read back as a (now method-less) hydrated instance
    const r = await loadRawScenario(client, "sha", "fixt-run", "buddhism", "BUD-001", RAW_FIXTURE_FINGERPRINT, src);
    expect(r.shard?.cells).toHaveLength(2);
    expect(r.notices).toHaveLength(0);
  });

  it("falls back to the GitHub shard when a coherent baked bundle is missing that shard", async () => {
    const gz = rawFixtureShardGz();
    // GitHub serves a COHERENT catalog (matching fingerprint) + the gz shard.
    const ghFetch = (async (url: string) => {
      if (url.endsWith("manifest.json")) return new Response(JSON.stringify(rawFixtureCatalog), { status: 200 });
      if (url.endsWith(".json.gz")) return new Response(gz, { status: 200 });
      return new Response(null, { status: 404 });
    }) as unknown as typeof fetch;
    const src: RawSources = {
      // baked catalog is coherent, but this shard isn't uploaded (partial bake) → shardText null
      baked: { kind: "baked", catalogText: fakeRawSource("baked").catalogText, shardText: async () => null },
      github: new GitHubRawSource("owner/repo", "sha", ghFetch),
    };
    const r = await loadRawScenario(qc(), "sha", "fixt-run", "buddhism", "BUD-001", RAW_FIXTURE_FINGERPRINT, src);
    expect(r.shard?.cells).toHaveLength(2); // served from GitHub
    expect(r.notices.some((n) => /baked shard unavailable — served from GitHub/.test(n.message))).toBe(true);
  });

  it("declines the per-shard GitHub fallback when the GitHub catalog is incoherent", async () => {
    const gz = rawFixtureShardGz();
    const ghFetch = (async (url: string) => {
      // GitHub catalog has a DIFFERENT fingerprint than the run (drifted tier)
      if (url.endsWith("manifest.json")) return new Response(JSON.stringify({ ...rawFixtureCatalog, fingerprint: "sha256:GH-DRIFT" }), { status: 200 });
      if (url.endsWith(".json.gz")) return new Response(gz, { status: 200 });
      return new Response(null, { status: 404 });
    }) as unknown as typeof fetch;
    const src: RawSources = {
      baked: { kind: "baked", catalogText: fakeRawSource("baked").catalogText, shardText: async () => null },
      github: new GitHubRawSource("owner/repo", "sha", ghFetch),
    };
    const r = await loadRawScenario(qc(), "sha", "fixt-run", "buddhism", "BUD-001", RAW_FIXTURE_FINGERPRINT, src);
    expect(r.shard).toBeNull(); // did NOT mix an incoherent GitHub shard with the baked catalog
    expect(r.notices.some((n) => /GitHub raw tier disagrees/.test(n.message))).toBe(true);
  });

  it("does NOT touch the GitHub source when baked is coherent", async () => {
    let githubCalls = 0;
    const src: RawSources = {
      baked: fakeRawSource("baked"),
      github: {
        kind: "github",
        catalogText: async () => { githubCalls++; return null; },
        shardText: async () => { githubCalls++; return null; },
      },
    };
    const r = await loadRawScenario(qc(), "sha", "fixt-run", "buddhism", "BUD-001", RAW_FIXTURE_FINGERPRINT, src);
    expect(r.shard?.cells).toHaveLength(2);
    expect(githubCalls).toBe(0); // coherent baked → no GitHub fetch (rate-limit immunity)
  });
});
