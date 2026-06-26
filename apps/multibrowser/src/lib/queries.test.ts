import { describe, it, expect, afterEach, vi } from "vitest";
import { QueryClient } from "@tanstack/react-query";
import {
  traditionIds,
  scenarioFolderIds,
  hasFile,
  loadTraditions,
  loadTradition,
  loadScenario,
  loadScenarioMeta,
} from "./queries";
import { REPO } from "./constants";
import { buildTree, fakeFetch, traditionFiles } from "../test/fakeRepo";

const SHA = "deadbeef";

function newQc() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } });
}

afterEach(() => vi.unstubAllGlobals());

describe("pure tree helpers", () => {
  const files = {
    ...traditionFiles("sunni-islam", ["JLS-001", "JLS-002"]),
    ...traditionFiles("judaism", ["MSR-001"]),
  };
  const entries = buildTree(files);

  it("traditionIds finds dirs with a tradition.yaml (sorted)", () => {
    expect(traditionIds(entries)).toEqual(["judaism", "sunni-islam"]);
  });
  it("scenarioFolderIds lists scenario dirs for a tradition", () => {
    expect(scenarioFolderIds(entries, "sunni-islam").sort()).toEqual(["JLS-001", "JLS-002"]);
    expect(scenarioFolderIds(entries, "judaism")).toEqual(["MSR-001"]);
  });
  it("hasFile detects blobs", () => {
    expect(hasFile(entries, "traditions/sunni-islam/scenarios/index.json")).toBe(true);
    expect(hasFile(entries, "traditions/sunni-islam/nope")).toBe(false);
  });
});

describe("loaders (real QueryClient + stubbed fetch)", () => {
  it("loadTraditions resolves manifests + scenario sets", async () => {
    const files = {
      ...traditionFiles("sunni-islam", ["JLS-001", "JLS-002"]),
      ...traditionFiles("judaism", ["MSR-001"]),
    };
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, files));
    const trads = await loadTraditions(newQc(), SHA);
    expect(trads.map((t) => t.id)).toEqual(["judaism", "sunni-islam"]);
    const sunni = trads.find((t) => t.id === "sunni-islam")!;
    expect(sunni.manifest?.displayName).toBe("SUNNI-ISLAM");
    expect(sunni.scenarioIds).toEqual(["JLS-001", "JLS-002"]);
    expect(sunni.notices).toHaveLength(0);
  });

  it("loadTradition includes prose; unknown id returns null", async () => {
    const files = traditionFiles("sunni-islam", ["JLS-001"]);
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, files));
    const qc = newQc();
    const t = await loadTradition(qc, SHA, "sunni-islam");
    expect(t).not.toBeNull();
    expect(t!.prose.readme).toContain("sunni-islam");
    expect(t!.prose.guide).toContain("guide of sunni-islam");
    expect(await loadTradition(qc, SHA, "does-not-exist")).toBeNull();
  });

  it("loadScenario parses all four files; results seam is inert (absent)", async () => {
    const files = traditionFiles("sunni-islam", ["JLS-001"]);
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, files));
    const s = await loadScenario(newQc(), SHA, "sunni-islam", "JLS-001", { pillars: ["a", "b"], hearts: ["c", "d"] });
    expect(s.turn1).toBe("turn1 for JLS-001");
    expect(s.judgeGuidance).toContain("judge guidance");
    expect(s.pressures.secularize).toBe("s");
    expect(s.pressures.personal_appeal).toBe("pa");
    expect(s.meta?.identitySignal).toBe("clean");
    expect(s.notices).toHaveLength(0);
    expect(s.results).toBeUndefined(); // inert seam: no results in v1
  });

  it("loadScenarioMeta flags an undeclared axis", async () => {
    const files = traditionFiles("sunni-islam", ["JLS-001"]);
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, files));
    const r = await loadScenarioMeta(newQc(), SHA, "sunni-islam", "JLS-001", { pillars: ["a", "b"] }); // 'hearts' not declared
    expect(r.notices.some((n) => n.message.includes("hearts"))).toBe(true);
  });

  it("derives the scenario set from folders when index.json is missing", async () => {
    const files = traditionFiles("sunni-islam", ["JLS-001", "JLS-002"]);
    delete files["traditions/sunni-islam/scenarios/index.json"]; // simulate missing index
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, files));
    const t = await loadTradition(newQc(), SHA, "sunni-islam");
    expect(t!.scenarioIds.sort()).toEqual(["JLS-001", "JLS-002"]);
    expect(t!.notices.some((n) => /missing|derived from folders/i.test(n.message))).toBe(true);
  });
});
