import { describe, it, expect, beforeEach } from "vitest";
import { setReviewFetch } from "./reviewApi";
import {
  ensureTraditionLoaded,
  flushReviewSaves,
  peekReviewState,
  peekVersion,
  resetReviewStore,
  updateReviewState,
  withScenarioCheck,
  withTraditionCheck,
} from "./review";

/** A tiny in-memory fake of the review API that models optimistic-concurrency versions. */
function fakeApi(seed: Record<string, { state: unknown; version: number }> = {}) {
  const store = new Map(Object.entries(seed));
  const puts: Array<{ tid: string; version: number }> = [];
  const json = (obj: unknown, status = 200) =>
    new Response(JSON.stringify(obj), { status, headers: { "content-type": "application/json" } });
  const impl = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    const path = new URL(String(input), "http://x").pathname;
    const method = init?.method ?? "GET";
    if (path === "/api/auth/csrf") return json({ csrfToken: "t" });
    if (path.startsWith("/api/review/")) {
      const tid = decodeURIComponent(path.slice("/api/review/".length));
      if (method === "GET") {
        const d = store.get(tid);
        return json(d ? { state: d.state, version: d.version } : { state: null, version: 0 });
      }
      if (method === "PUT") {
        const body = JSON.parse(String(init?.body ?? "{}"));
        puts.push({ tid, version: body.version });
        const cur = store.get(tid);
        const curV = cur?.version ?? 0;
        if (body.version === curV) {
          const version = curV + 1;
          store.set(tid, { state: body.state, version });
          return json({ version });
        }
        return json({ error: "conflict", state: cur?.state ?? null, version: curV }, 409);
      }
    }
    return json({ error: "not found" }, 404);
  };
  return { impl: impl as unknown as typeof fetch, puts, store };
}

beforeEach(() => resetReviewStore());

describe("review store — async persistence", () => {
  it("saves a changed tradition optimistically and advances the version", async () => {
    const api = fakeApi();
    setReviewFetch(api.impl);

    updateReviewState((s) => withTraditionCheck(s, "t", "source", { status: "approved" }));
    // Optimistic: in memory immediately.
    expect(peekReviewState().traditions.t?.source.status).toBe("approved");

    await flushReviewSaves();
    expect(api.puts).toEqual([{ tid: "t", version: 0 }]); // new draft
    expect(peekVersion("t")).toBe(1);

    updateReviewState((s) => withTraditionCheck(s, "t", "guide", { status: "flagged" }));
    await flushReviewSaves();
    expect(api.puts).toEqual([
      { tid: "t", version: 0 },
      { tid: "t", version: 1 }, // update on the advanced version
    ]);
    expect(peekVersion("t")).toBe(2);
  });

  it("only saves the tradition that actually changed (reference diff)", async () => {
    setReviewFetch(fakeApi().impl);
    updateReviewState((s) => withTraditionCheck(s, "a", "source", { status: "approved" }));
    await flushReviewSaves();
    const api2 = fakeApi();
    setReviewFetch(api2.impl);
    updateReviewState((s) => withTraditionCheck(s, "b", "source", { status: "approved" }));
    await flushReviewSaves();
    expect(api2.puts.map((p) => p.tid)).toEqual(["b"]); // "a" not re-saved
  });

  it("reconciles a version conflict (last-write-wins) without dropping the active edit", async () => {
    // Server already at version 3 (another device advanced it); our store thinks it's new (0).
    const api = fakeApi({ t: { state: { source: { status: "unreviewed" } }, version: 3 } });
    setReviewFetch(api.impl);

    updateReviewState((s) => withScenarioCheck(s, "t", "S-1", "scenario", { status: "flagged" }));
    await flushReviewSaves();

    // First PUT (version 0) → 409; retry with the server's version 3 → succeeds at 4.
    expect(api.puts).toEqual([
      { tid: "t", version: 0 },
      { tid: "t", version: 3 },
    ]);
    expect(peekVersion("t")).toBe(4);
    // The active device's edit survived the reconcile.
    expect(api.store.get("t")?.version).toBe(4);
    expect((api.store.get("t")?.state as any).scenarios["S-1"].scenario.status).toBe("flagged");
  });

  it("loads an existing draft from the API tolerantly", async () => {
    const api = fakeApi({
      t: { state: { sampleIds: ["S-1"], source: { status: "approved", notes: "ok", bogus: 1 } }, version: 5 },
    });
    setReviewFetch(api.impl);
    await ensureTraditionLoaded("t");
    const t = peekReviewState().traditions.t;
    expect(t?.source.status).toBe("approved");
    expect(t?.sampleIds).toEqual(["S-1"]);
    expect(peekVersion("t")).toBe(5);
  });
});
