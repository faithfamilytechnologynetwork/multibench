import { describe, it, expect, afterEach, vi } from "vitest";
import { screen, fireEvent, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderApp } from "../test/renderApp";
import { fakeFetch, resultsFiles, traditionFiles } from "../test/fakeRepo";
import { REPO } from "../lib/constants";
import { rawFixtureCatalog, rawFixtureShard } from "../test/rawFixture";

const SHA = "deadbeef";
const RUN = "fixt-run";
afterEach(() => vi.unstubAllGlobals());

/** Score-tier manifest (for the run + its fingerprint) + the raw catalog + one raw shard. */
function filesFor(catalog: { fingerprint: string }, shardRel: string, shard: unknown) {
  const score = resultsFiles(RUN, {});
  const sm = JSON.parse(score[`results/${RUN}/manifest.json`]!);
  sm.fingerprint = catalog.fingerprint; // make the score tier agree with the raw tier
  score[`results/${RUN}/manifest.json`] = JSON.stringify(sm);
  return {
    ...traditionFiles("buddhism", ["BUD-001"]),
    ...score,
    [`results-raw/${RUN}/manifest.json`]: JSON.stringify(catalog),
    [`results-raw/${RUN}/${shardRel}`]: JSON.stringify(shard),
  };
}

// A NON-MultiBench catalog (issue #54): 0–4 scale, `instrument` grouping, `condition` axis.
const AFB_CATALOG = {
  schema_version: 1,
  dataset: { title: "AFB before/after", license: "MIT" },
  scale: { min: 0, center: 2, max: 4 },
  ramp: ["#000000", "#888888", "#ffffff"],
  subjects: [{ id: "gemma-4-31b-it", label: "gemma-4-31b-it" }, { id: "mb-sft-dpo", label: "mb-sft-dpo" }],
  judges: [{ key: "terra", label: "gpt-5.6-terra", fullGrid: true }],
  conditionAxes: [{ key: "condition", label: "Condition", values: [{ id: "cold", label: "Cold" }] }],
  groupBy: { key: "instrument", label: "Instrument" },
  scopes: [{ id: "single", label: "single" }],
  items: [{ id: "AFB-001", label: "AFB-001", group: "afb-150", shard: "afb-150/AFB-001.json.gz" }],
  presets: [],
  fingerprint: "sha256:afb-fixture",
};
const AFB_SHARD = {
  schema_version: 1,
  cells: [{
    subject: "gemma-4-31b-it",
    conditions: { condition: "cold" },
    transcript: [{ role: "user", content: "AFB prompt text" }, { role: "assistant", content: "vanilla omission" }],
    verdicts: [{ judge: "terra", scope: "single", score: 1, summary: "omitted the concern" }],
  }],
};

describe("raw-results view", () => {
  it("renders a scenario's transcript + judge verdicts (MultiBench catalog)", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, filesFor(rawFixtureCatalog, "buddhism/BUD-001.json.gz", rawFixtureShard)));
    renderApp(`/results/${RUN}/buddhism/BUD-001`);
    expect(await screen.findByRole("heading", { name: "BUD-001" })).toBeInTheDocument();
    expect(await screen.findByText(/thinking about leaving/)).toBeInTheDocument(); // transcript (default cell)
    const verdicts = await screen.findAllByTestId("verdict");
    expect(verdicts.length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("gemini")).toBeInTheDocument(); // judge label
    expect(screen.getByText("opus")).toBeInTheDocument();
    expect(screen.getByText("sample")).toBeInTheDocument(); // Opus (non-full-grid) badge on the default cell
  });

  it("shows the context-prefix panel + switches cells via the condition-axis selectors", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, filesFor(rawFixtureCatalog, "buddhism/BUD-001.json.gz", rawFixtureShard)));
    renderApp(`/results/${RUN}/buddhism/BUD-001`);
    await screen.findByRole("heading", { name: "BUD-001" });
    // default cell (claude-sonnet-5 / unstated) has no context prefix
    expect(screen.queryByText(/what the model was told/i)).not.toBeInTheDocument();
    // switch to the stated gpt-5.6-terra cell → its context panel + transcript appear
    fireEvent.change(screen.getByLabelText(/Subject/), { target: { value: "gpt-5.6-terra" } });
    fireEvent.change(screen.getByLabelText(/Framing/), { target: { value: "stated" } });
    expect(await screen.findByText(/what the model was told/i)).toBeInTheDocument();
    expect(screen.getByText(/practising Buddhist/)).toBeInTheDocument(); // the context text
    expect(screen.getByText(/weigh it against your values/)).toBeInTheDocument(); // the new transcript
  });

  it("shows the catalog-declared item LABEL, not the route id", async () => {
    const labeled = { ...rawFixtureCatalog, items: [{ id: "BUD-001", label: "The firearms job", group: "buddhism", shard: "buddhism/BUD-001.json.gz" }] };
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, filesFor(labeled, "buddhism/BUD-001.json.gz", rawFixtureShard)));
    renderApp(`/results/${RUN}/buddhism/BUD-001`);
    expect(await screen.findByRole("heading", { name: "The firearms job" })).toBeInTheDocument();
  });

  it("renders a NON-MultiBench 0–4 catalog with no component change (genericity, #54)", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, filesFor(AFB_CATALOG, "afb-150/AFB-001.json.gz", AFB_SHARD)));
    renderApp(`/results/${RUN}/afb-150/AFB-001`);
    expect(await screen.findByRole("heading", { name: "AFB-001" })).toBeInTheDocument();
    // grouping axis label + item come from the catalog, not hardcoded "Tradition"/"scenario"
    expect(screen.getByText(/Instrument: afb-150/)).toBeInTheDocument();
    expect(await screen.findByText(/vanilla omission/)).toBeInTheDocument();
    expect((await screen.findAllByTestId("verdict")).length).toBe(1);
    expect(screen.getByText("gpt-5.6-terra")).toBeInTheDocument();
  });

  it("ResultsRegion becomes a live drill-in link when a results run exists", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, {
      ...traditionFiles("buddhism", ["BUD-001"]),
      ...resultsFiles(RUN, {}),
    }));
    renderApp("/t/buddhism/BUD-001");
    // wait for the async run resolution → the placeholder becomes a live drill-in link
    const link = await screen.findByRole("link", { name: /raw responses/i });
    expect(link).toHaveAttribute("href", expect.stringContaining(`/results/${RUN}/buddhism/BUD-001`));
    expect(screen.getByTestId("results-region")).toHaveAttribute("data-has-results", "true");
    // contentful from the score manifest (5 subjects × 3 framings × 6 pressures = 18), no raw fetch
    expect(link).toHaveTextContent(/5 models × 18 conditions/);
  });

  it("shows an 'unavailable' message (not 'no cell') when the shard fails to load", async () => {
    // catalog present, but the shard is 404 (not in the served files)
    const score = resultsFiles(RUN, {});
    const sm = JSON.parse(score[`results/${RUN}/manifest.json`]!);
    sm.fingerprint = rawFixtureCatalog.fingerprint;
    score[`results/${RUN}/manifest.json`] = JSON.stringify(sm);
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, {
      ...traditionFiles("buddhism", ["BUD-001"]),
      ...score,
      [`results-raw/${RUN}/manifest.json`]: JSON.stringify(rawFixtureCatalog),
    }));
    renderApp(`/results/${RUN}/buddhism/BUD-001`);
    expect(await screen.findByText(/Raw data for this scenario is unavailable/)).toBeInTheDocument();
    expect(screen.queryByText(/No cell for this/)).not.toBeInTheDocument();
  });

  it("/results drills down into a tradition (toward the raw browser)", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, { ...traditionFiles("buddhism", ["BUD-001"]), ...resultsFiles(RUN, {}) }));
    renderApp("/results");
    const rows = await screen.findAllByTestId("standings-row");
    for (const row of rows) await userEvent.click(within(row).getByRole("button")); // expand all subjects
    const link = await screen.findByTestId("drill-link");
    expect(link).toHaveAttribute("href", expect.stringContaining("/t/buddhism"));
  });
});
