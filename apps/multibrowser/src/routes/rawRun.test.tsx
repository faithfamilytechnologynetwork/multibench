import { describe, it, expect, afterEach, vi } from "vitest";
import { screen, within } from "@testing-library/react";
import { renderApp } from "../test/renderApp";
import { fakeFetch, resultsFiles, buildTree } from "../test/fakeRepo";
import { REPO } from "../lib/constants";
import { rawRunIds, resultsRunIds } from "../lib/queries";

const SHA = "deadbeef";
const RUN = "afb-20260803";
afterEach(() => vi.unstubAllGlobals());

// A raw-only AFB catalog (no results/ score tier), 2 items, generic shape.
const AFB = {
  schema_version: 1,
  dataset: { title: "AFB before/after", description: "vanilla vs tuned", language: "en", license: "MIT" },
  scale: { min: 0, center: 2, max: 4 },
  ramp: ["#4C72B0", "#8B95A1", "#DD8452"],
  subjects: [{ id: "gemma-4-31b-it", label: "Vanilla Gemma-4-31B" },
             { id: "mb-sft-dpo", label: "MultiWeights (SFT+DPO)" }],
  judges: [{ key: "terra", label: "gpt-5.6-terra", fullGrid: true }],
  conditionAxes: [{ key: "condition", label: "Condition", values: [{ id: "cold", label: "Cold" }] }],
  groupBy: { key: "instrument", label: "Instrument" },
  scopes: [{ id: "single", label: "single" }],
  items: [
    { id: "AFB-001", label: "First question?", group: "afb-150", shard: "afb-150/AFB-001.json.gz" },
    { id: "AFB-002", label: "Second question?", group: "afb-150", shard: "afb-150/AFB-002.json.gz" },
  ],
  presets: [{
    key: "dpo-base", label: "Omission → repair", description: "biggest moves",
    entries: [{
      key: "dpo-base:afb-150:AFB-001", label: "AFB-001 · First question?",
      params: { group: "afb-150", item: "AFB-001", scope: "single",
                a: "gemma-4-31b-it", b: "mb-sft-dpo", conditions: { condition: "cold" } },
    }],
  }],
  fingerprint: "sha256:afb-fp",
  content_fingerprint: "sha256:afb-cfp",
};

const shard = (tag: string) => ({
  schema_version: 1,
  cells: [
    { subject: "gemma-4-31b-it", conditions: { condition: "cold" },
      transcript: [{ role: "user", content: "Q?" }, { role: "assistant", content: `VANILLA-${tag}` }],
      verdicts: [{ judge: "terra", scope: "single", score: 0, summary: "no religious representation", rationale: "r" }] },
    { subject: "mb-sft-dpo", conditions: { condition: "cold" },
      transcript: [{ role: "user", content: "Q?" }, { role: "assistant", content: `TUNED-${tag}` }],
      verdicts: [{ judge: "terra", scope: "single", score: 2, summary: "meaningful religious reference", rationale: "r" }] },
  ],
});

const afbFiles = () => ({
  [`results-raw/${RUN}/manifest.json`]: JSON.stringify(AFB),
  [`results-raw/${RUN}/afb-150/AFB-001.json.gz`]: JSON.stringify(shard("one")),
  [`results-raw/${RUN}/afb-150/AFB-002.json.gz`]: JSON.stringify(shard("two")),
});

describe("raw-only explorer discovery + landing (#54)", () => {
  it("rawRunIds finds results-raw runs; raw-ONLY filter drops runs that also have a score tier", () => {
    const entries = buildTree({
      "results/mbrun/manifest.json": "{}", "results-raw/mbrun/manifest.json": "{}",
      "results-raw/afb/manifest.json": "{}",
    });
    expect(rawRunIds(entries)).toEqual(["afb", "mbrun"]);
    const scored = new Set(resultsRunIds(entries));
    expect(rawRunIds(entries).filter((id) => !scored.has(id))).toEqual(["afb"]); // AFB is raw-only
  });

  it("the run landing lists EVERY item, with a+b/scope/judge on each link", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, afbFiles()));
    renderApp(`/raw/${RUN}`);
    expect(await screen.findByRole("heading", { name: "AFB before/after" })).toBeInTheDocument();
    const index = await screen.findByTestId("raw-item-index");
    expect(within(index).getByText("AFB-001")).toBeInTheDocument();
    expect(within(index).getByText("AFB-002")).toBeInTheDocument(); // ALL items, not just the ≤12 presets
    const href = within(index).getByText("AFB-001").closest("a")!.getAttribute("href")!;
    expect(href).toContain("/results/" + RUN + "/afb-150/AFB-001");
    for (const q of ["a=gemma-4-31b-it", "b=mb-sft-dpo", "scope=single", "judge=terra"]) {
      expect(href).toContain(q); // b MUST be present or the item opens single-column
    }
    expect(screen.getByTestId("presets")).toBeInTheDocument(); // the shipped RawPresets is reused
    expect(screen.queryByText(/manifest not found/i)).toBeNull(); // no false score-tier error
  });

  it("landing on an item link renders BOTH response columns (before/after, not single-column)", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, afbFiles()));
    renderApp(`/results/${RUN}/afb-150/AFB-001?a=gemma-4-31b-it&b=mb-sft-dpo&scope=single&judge=terra`);
    expect(await screen.findByText(/VANILLA-one/)).toBeInTheDocument(); // base column
    expect(await screen.findByText(/TUNED-one/)).toBeInTheDocument();   // dpo column
  });

  it("a raw-only item page back-links to its /raw explorer, not the MB leaderboard", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, afbFiles())); // raw-only run (no results/ tier)
    renderApp(`/results/${RUN}/afb-150/AFB-001?a=gemma-4-31b-it&b=mb-sft-dpo&scope=single&judge=terra`);
    const back = await screen.findByRole("link", { name: /← Explorer/ });
    expect(back).toHaveAttribute("href", `/raw/${RUN}`);           // not dead-ended on /results
    expect(screen.queryByRole("link", { name: /← Results/ })).toBeNull();
  });

  it("the index surfaces raw-only runs as Explorers and never a score-tier run", async () => {
    const mixed = {
      ...resultsFiles("mbrun", {}),                                 // an MB run WITH a score tier
      "results-raw/mbrun/manifest.json": JSON.stringify({ ...AFB, items: [] }),
      ...afbFiles(),                                                // the AFB raw-only run
    };
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, mixed));
    renderApp("/");
    const explorers = await screen.findByTestId("explorers");
    expect(within(explorers).getByText(RUN)).toBeInTheDocument();   // AFB (raw-only) listed
    expect(within(explorers).queryByText("mbrun")).toBeNull();      // MB (has score tier) NOT listed
    expect(screen.queryByText(/manifest not found/i)).toBeNull();   // no false error on the index
  });

  it("a SHA load failure shows an error, not a premature 'not found'", async () => {
    // The catalog query is disabled until the SHA arrives; if the SHA fetch FAILS the page must show
    // an error (surfacing shaQ.error), NOT the misleading "Explorer not found" (the fixed bug).
    const base = fakeFetch(REPO, SHA, afbFiles());
    vi.stubGlobal("fetch", ((input: RequestInfo | URL, init?: RequestInit) => {
      const url = typeof input === "string" ? input : input.toString();
      if (url.includes("/commits/")) return Promise.resolve(new Response("boom", { status: 500 }));
      return base(input, init);
    }) as typeof fetch);
    renderApp(`/raw/${RUN}`);
    expect(await screen.findByText(/Couldn't load this explorer/i)).toBeInTheDocument();
    expect(screen.queryByText(/not found/i)).toBeNull();
  });

  it("the GitHub-served run puts the 'no baked bundle' note in the FOOTER, not a top banner", async () => {
    // No baked bundle in the fixture → resolveRawSource emits a `kind:"source"` note. It must be a
    // quiet footer, never a top banner (the AFB run is GitHub-served by design in Phase 5).
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, afbFiles()));
    renderApp(`/raw/${RUN}`);
    await screen.findByRole("heading", { name: "AFB before/after" });
    const foot = await screen.findByTestId("source-notes");
    expect(within(foot).getByText(/baked/i)).toBeInTheDocument();
    expect(screen.getAllByText(/baked/i)).toHaveLength(1); // ONLY in the footer, not also a top banner
  });

  it("useRawExplorerRunIds adds no git-trees API call beyond the shared tree walk", async () => {
    let treeCalls = 0;
    const base = fakeFetch(REPO, SHA, { ...resultsFiles("mbrun", {}), ...afbFiles() });
    vi.stubGlobal("fetch", ((input: RequestInfo | URL, init?: RequestInit) => {
      const url = typeof input === "string" ? input : input.toString();
      if (url.includes("/git/trees/")) treeCalls++;
      return base(input, init);
    }) as typeof fetch);
    renderApp("/");
    await screen.findByTestId("explorers");
    expect(treeCalls).toBe(1); // one recursive tree walk serves traditions + results + explorers
  });
});
