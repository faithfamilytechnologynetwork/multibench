import { describe, it, expect, afterEach, vi } from "vitest";
import { screen, fireEvent, within, waitFor } from "@testing-library/react";
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
    expect(verdicts.length).toBeGreaterThanOrEqual(2); // gemini + opus on the default cell
    expect(screen.getAllByText("gemini").length).toBeGreaterThan(0); // judge label (pill + verdict)
    expect(screen.getByText("sample")).toBeInTheDocument(); // Opus (non-full-grid) badge on the default cell's verdict
    expect(screen.getByTestId("score-grid")).toBeInTheDocument(); // the cell-score grid overview
  });

  it("the grid navigates: clicking a chip opens that cell's context panel + transcript", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, filesFor(rawFixtureCatalog, "buddhism/BUD-001.json.gz", rawFixtureShard)));
    renderApp(`/results/${RUN}/buddhism/BUD-001`);
    await screen.findByRole("heading", { name: "BUD-001" });
    // default cell (claude-sonnet-5 / unstated) has no context prefix
    expect(screen.queryByText(/what the model was told/i)).not.toBeInTheDocument();
    // click the grid chip for the stated gpt-5.6-terra cell → its context panel + transcript appear
    fireEvent.click(screen.getByTitle(/gpt-5\.6-terra · stated \/ secularize/));
    expect(await screen.findByText(/what the model was told/i)).toBeInTheDocument();
    expect(screen.getByText(/practising Buddhist/)).toBeInTheDocument(); // the context text
    expect(screen.getByText(/weigh it against your values/)).toBeInTheDocument(); // the new transcript
  });

  it("A/B compare: pinning a second subject shows two cell detail columns", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, filesFor(rawFixtureCatalog, "buddhism/BUD-001.json.gz", rawFixtureShard)));
    renderApp(`/results/${RUN}/buddhism/BUD-001`);
    await screen.findByRole("heading", { name: "BUD-001" });
    expect(screen.getAllByTestId("cell-detail")).toHaveLength(1);
    fireEvent.change(screen.getByLabelText(/Compare/), { target: { value: "gpt-5.6-terra" } });
    await waitFor(() => expect(screen.getAllByTestId("cell-detail")).toHaveLength(2));
    const details = screen.getAllByTestId("cell-detail");
    expect(details.map((d) => d.getAttribute("data-subject"))).toEqual(["claude-sonnet-5", "gpt-5.6-terra"]);
  });

  it("selection is a deep link: the search carries a/scope/judge + condition axes", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, filesFor(rawFixtureCatalog, "buddhism/BUD-001.json.gz", rawFixtureShard)));
    const { router } = renderApp(`/results/${RUN}/buddhism/BUD-001`);
    await screen.findByRole("heading", { name: "BUD-001" });
    fireEvent.click(screen.getByTitle(/gpt-5\.6-terra · stated \/ secularize/));
    await screen.findByText(/weigh it against your values/);
    const s = router.state.location.search as Record<string, string>;
    expect(s.a).toBe("gpt-5.6-terra");
    expect(s.framing).toBe("stated");
    expect(s.pressure).toBe("secularize");
    expect(s.scope).toBeTruthy();
    expect(s.judge).toBe("gemini");
  });

  it("opening a deep link restores the exact cell", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, filesFor(rawFixtureCatalog, "buddhism/BUD-001.json.gz", rawFixtureShard)));
    renderApp(`/results/${RUN}/buddhism/BUD-001?a=gpt-5.6-terra&framing=stated&pressure=secularize&scope=full&judge=gemini`);
    expect(await screen.findByText(/weigh it against your values/)).toBeInTheDocument(); // gpt/stated transcript
    expect(screen.getByText(/what the model was told/i)).toBeInTheDocument(); // its context panel
  });

  it("a preset renders a deep-link into a cell", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, filesFor(rawFixtureCatalog, "buddhism/BUD-001.json.gz", rawFixtureShard)));
    renderApp(`/results/${RUN}/buddhism/BUD-001`);
    await screen.findByRole("heading", { name: "BUD-001" });
    const preset = within(screen.getByTestId("presets")).getByRole("link", { name: /gpt-5\.6-terra vs claude-sonnet-5/ });
    expect(preset.getAttribute("href")).toMatch(/\/results\/.*\/buddhism\/BUD-001\?.*a=gpt-5\.6-terra/);
  });

  it("clicking a preset navigates and restores its target cell (A vs B)", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, filesFor(rawFixtureCatalog, "buddhism/BUD-001.json.gz", rawFixtureShard)));
    const { router } = renderApp(`/results/${RUN}/buddhism/BUD-001`);
    await screen.findByRole("heading", { name: "BUD-001" });
    await userEvent.click(within(screen.getByTestId("presets")).getByRole("link", { name: /gpt-5\.6-terra vs claude-sonnet-5/ }));
    await waitFor(() => expect(screen.getAllByTestId("cell-detail")).toHaveLength(2)); // A vs B restored
    expect(screen.getAllByTestId("cell-detail").map((d) => d.getAttribute("data-subject"))).toEqual(["gpt-5.6-terra", "claude-sonnet-5"]);
    expect(screen.getByText(/three reasons it might be time/)).toBeInTheDocument(); // gpt/unstated transcript
    const s = router.state.location.search as Record<string, string>;
    expect(s).toMatchObject({ a: "gpt-5.6-terra", b: "claude-sonnet-5", framing: "unstated", scope: "turn1" });
  });

  it("an A/B deep link restores BOTH subjects at the same conditions", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, filesFor(rawFixtureCatalog, "buddhism/BUD-001.json.gz", rawFixtureShard)));
    renderApp(`/results/${RUN}/buddhism/BUD-001?a=claude-sonnet-5&b=gpt-5.6-terra&framing=unstated&pressure=secularize&scope=turn1`);
    await screen.findByRole("heading", { name: "BUD-001" });
    const details = await screen.findAllByTestId("cell-detail");
    expect(details.map((d) => d.getAttribute("data-subject"))).toEqual(["claude-sonnet-5", "gpt-5.6-terra"]);
    expect(screen.getByText(/thinking about leaving/)).toBeInTheDocument();       // A (claude)
    expect(screen.getByText(/three reasons it might be time/)).toBeInTheDocument(); // B (gpt)
  });

  it("a missing raw run degrades to a Notice + a way back (fail-soft)", async () => {
    // the catalog for `nope-run` is absent (only `fixt-run` is served)
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, filesFor(rawFixtureCatalog, "buddhism/BUD-001.json.gz", rawFixtureShard)));
    renderApp(`/results/nope-run/buddhism/BUD-001`);
    expect(await screen.findByText(/no raw dataset for run "nope-run"/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /←\s*Results/ })).toBeInTheDocument(); // the in-page way back
  });

  it("shows the catalog-declared item LABEL, not the route id", async () => {
    const labeled = { ...rawFixtureCatalog, items: [{ id: "BUD-001", label: "The firearms job", group: "buddhism", shard: "buddhism/BUD-001.json.gz" }] };
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, filesFor(labeled, "buddhism/BUD-001.json.gz", rawFixtureShard)));
    renderApp(`/results/${RUN}/buddhism/BUD-001`);
    expect(await screen.findByRole("heading", { name: "The firearms job" })).toBeInTheDocument();
  });

  it("renders a NON-MultiBench 0–4 catalog with NO #49 score tier (genericity + independence, #54)", async () => {
    // Raw tier ONLY — no results/ score manifest. The raw view must still work (fingerprint null
    // → GitHub, no coherence check), proving it's decoupled from the MultiBench score tier.
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, {
      [`results-raw/${RUN}/manifest.json`]: JSON.stringify(AFB_CATALOG),
      [`results-raw/${RUN}/afb-150/AFB-001.json.gz`]: JSON.stringify(AFB_SHARD),
    }));
    renderApp(`/results/${RUN}/afb-150/AFB-001`);
    expect(await screen.findByRole("heading", { name: "AFB-001" })).toBeInTheDocument();
    // grouping axis label + item come from the catalog, not hardcoded "Tradition"/"scenario"
    expect(screen.getByText(/Instrument: afb-150/)).toBeInTheDocument();
    expect(await screen.findByText(/vanilla omission/)).toBeInTheDocument();
    expect((await screen.findAllByTestId("verdict")).length).toBe(1);
    expect(screen.getAllByText("gpt-5.6-terra").length).toBeGreaterThan(0); // judge label (pill + verdict)
  });

  it("the scenario page embeds a lazy results section with a cross-link to the explorer", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, {
      ...traditionFiles("buddhism", ["BUD-001"]),
      ...resultsFiles(RUN, {}),
    }));
    renderApp("/t/buddhism/BUD-001");
    const section = await screen.findByTestId("scenario-responses");
    // Contentful expand button from the SCORE manifest (5 subjects × 3×6 = 18), no raw fetch yet.
    const expand = await within(section).findByTestId("responses-expand");
    expect(expand).toHaveTextContent(/5 models × 18 conditions/);
    // Cross-link into the full generic explorer for THIS scenario.
    const link = within(section).getByRole("link", { name: /full explorer/i });
    expect(link).toHaveAttribute("href", expect.stringContaining(`/results/${RUN}/buddhism/BUD-001`));
    // Lazy: the heavy body (transcript+verdicts) is not rendered until engaged.
    expect(within(section).queryByTestId("responses-body")).toBeNull();
  });

  it("expands in place to show the model's response + interleaved verdicts (jalees unification)", async () => {
    // The core of the redirect: a reader answers "how did this model respond?" ON the scenario page.
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, filesFor(rawFixtureCatalog, "buddhism/BUD-001.json.gz", rawFixtureShard)));
    renderApp("/t/buddhism/BUD-001");
    await userEvent.click(await screen.findByTestId("responses-expand"));
    // Lazy-loaded shard → interleaved comparison renders: the default cell's transcript + verdicts.
    expect(await screen.findByTestId("raw-comparison")).toBeInTheDocument();
    expect(await screen.findByText(/thinking about leaving/)).toBeInTheDocument(); // claude/unstated/secularize transcript
    expect(screen.getAllByTestId("verdict-stage").length).toBeGreaterThanOrEqual(1); // scope-interleaved verdicts
    expect((await screen.findAllByTestId("verdict")).length).toBeGreaterThanOrEqual(2); // gemini + opus (turn-1)
  });

  it("compares two models side-by-side in the embedded section (single→A/B)", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, filesFor(rawFixtureCatalog, "buddhism/BUD-001.json.gz", rawFixtureShard)));
    renderApp("/t/buddhism/BUD-001");
    await userEvent.click(await screen.findByTestId("responses-expand"));
    await screen.findByTestId("raw-comparison");
    // Pick a compare model B → the second column appears (gpt has a cell at unstated/secularize too).
    await userEvent.selectOptions(screen.getByLabelText("Compare with"), "gpt-5.6-terra");
    await waitFor(() => expect(screen.getAllByTestId("cmp-column").length).toBe(2));
    expect(screen.getByText(/three reasons it might be time/)).toBeInTheDocument(); // gpt's response
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
    expect(await screen.findByText(/Raw data for this item is unavailable/)).toBeInTheDocument();
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

  // ── iter-1 UX regressions (Waleed's live look) ──────────────────────────────────────

  it("demotes the operational source note to a footer, never a top banner", async () => {
    // Baked is absent in tests → the 'no baked bundle — serving the live GitHub copy' note fires.
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, filesFor(rawFixtureCatalog, "buddhism/BUD-001.json.gz", rawFixtureShard)));
    renderApp(`/results/${RUN}/buddhism/BUD-001`);
    await screen.findByRole("heading", { name: "BUD-001" });
    const footer = await screen.findByTestId("source-notes");
    expect(within(footer).getByText(/no baked bundle/)).toBeInTheDocument(); // lives in the footer
    const top = screen.queryByTestId("notices"); // the prominent top region (absent when no data problems)
    if (top) expect(within(top).queryByText(/no baked bundle/)).toBeNull();
  });

  it("renders presets as compact cards with a header + a show-all toggle (not a sea of links)", async () => {
    const manyPreset = {
      ...rawFixtureCatalog,
      presets: [{
        key: "models-split", label: "Models split", description: "widest turn-1 spread",
        entries: Array.from({ length: 8 }, (_, i) => ({
          key: `ms-${i}`, label: `BUD-00${i} · subject-${i} vs other`,
          params: { group: "buddhism", item: "BUD-001", scope: "turn1", a: "gpt-5.6-terra",
                    conditions: { framing: "unstated", pressure: "secularize" } },
        })),
      }],
    };
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, filesFor(manyPreset, "buddhism/BUD-001.json.gz", rawFixtureShard)));
    renderApp(`/results/${RUN}/buddhism/BUD-001`);
    const card = await screen.findByTestId("preset-card");
    expect(within(card).getByRole("heading", { name: "Models split" })).toBeInTheDocument();
    expect(within(card).getAllByRole("link")).toHaveLength(6); // collapsed → first 6
    await userEvent.click(within(card).getByTestId("preset-toggle"));
    expect(within(card).getAllByRole("link")).toHaveLength(8); // expanded → all 8
  });

  it("styles the selected Judge/Scope pill visibly — no invisible text-white regression", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, filesFor(rawFixtureCatalog, "buddhism/BUD-001.json.gz", rawFixtureShard)));
    renderApp(`/results/${RUN}/buddhism/BUD-001`);
    await screen.findByRole("heading", { name: "BUD-001" });
    const controls = screen.getByTestId("raw-controls");
    const pressed = within(controls).getAllByRole("button", { pressed: true }); // selected judge + scope
    expect(pressed.length).toBe(2);
    for (const b of pressed) {
      expect(b.className).toContain("bg-primary");
      expect(b.className).toContain("text-primary-foreground"); // readable on-primary token
      expect(b.className).not.toContain("text-white");          // the old washed-out class
    }
  });
});
