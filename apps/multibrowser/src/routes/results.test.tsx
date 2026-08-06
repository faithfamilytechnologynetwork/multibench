import { describe, it, expect, afterEach, vi } from "vitest";
import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderApp } from "../test/renderApp";
import { fakeFetch, resultsFiles } from "../test/fakeRepo";
import { REPO } from "../lib/constants";

const SHA = "deadbeef";

// Per-tradition means so the leaderboard's mean-of-means is a clean number:
//   claude-sonnet-5 unstated/full/all: buddhism 0.6, taoism 0.8 → 0.700 (rank 1)
//   gemini-3.6-flash unstated/full/all: buddhism 0.2, taoism 0.4 → 0.300 (rank 2)
//   claude-sonnet-5 unstated/turn1/all: buddhism 0.2, taoism 0.0 → 0.100
//   claude-sonnet-5 stated/full/all:    buddhism 0.9, taoism 0.9 → 0.900
// sonnetSecularize: unstated/full/secularize (a specific pressure); sonnetStead: unstated steadfastness/all
const VALS: Record<string, {
  sonnetFull: number; sonnetTurn1: number; geminiFull: number; sonnetStated: number;
  sonnetSecularize: number; sonnetStead: number;
}> = {
  buddhism: { sonnetFull: 0.6, sonnetTurn1: 0.2, geminiFull: 0.2, sonnetStated: 0.9, sonnetSecularize: 0.5, sonnetStead: 0.4 },
  taoism: { sonnetFull: 0.8, sonnetTurn1: 0.0, geminiFull: 0.4, sonnetStated: 0.9, sonnetSecularize: 0.3, sonnetStead: 0.8 },
};

function shardFor(t: string) {
  const v = VALS[t]!;
  const gemini = {
    "claude-sonnet-5": {
      unstated: {
        full: { all: [v.sonnetFull, 2, 12], secularize: [v.sonnetSecularize, 2, 2] },
        turn1: { all: [v.sonnetTurn1, 2, 12] },
      },
      stated: { full: { all: [v.sonnetStated, 2, 12] } },
    },
    "gemini-3.6-flash": { unstated: { full: { all: [v.geminiFull, 2, 12] } } },
  };
  const means: Record<string, unknown> = { "gemini-3.6-flash": gemini };
  // Opus (validation) data ONLY for buddhism → taoism is omitted in the Opus drill-down, and the
  // buddhism cell is a sample (5/12) so it earns a badge.
  if (t === "buddhism") {
    means["claude-opus-4-8"] = {
      "claude-sonnet-5": { unstated: { full: { all: [0.7, 5, 12] } } },
    };
  }
  return {
    tradition: t,
    n_scenarios: 2,
    judges: t === "buddhism" ? ["gemini-3.6-flash", "claude-opus-4-8"] : ["gemini-3.6-flash"],
    means,
    steadfastness: {
      "gemini-3.6-flash": { "claude-sonnet-5": { unstated: { all: [v.sonnetStead, 2] } } },
    },
  };
}

function files() {
  return resultsFiles("20260803", { traditions: ["buddhism", "taoism"], shard: shardFor });
}

afterEach(() => vi.unstubAllGlobals());

describe("/results leaderboard", () => {
  it("renders Gemini-ranked standings = mean of per-tradition means", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, files()));
    renderApp("/results");
    const rows = await screen.findAllByTestId("standings-row");
    // ranked desc: claude-sonnet-5 (0.700) first, gemini-3.6-flash (0.300) second
    expect(rows[0]).toHaveAttribute("data-subject", "claude-sonnet-5");
    expect(within(rows[0]!).getByTestId("standings-score")).toHaveTextContent("0.700");
    const gem = rows.find((r) => r.getAttribute("data-subject") === "gemini-3.6-flash")!;
    expect(within(gem).getByTestId("standings-score")).toHaveTextContent("0.300");
  });

  it("the run label names the run + tradition count", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, files()));
    renderApp("/results");
    expect(await screen.findByTestId("results-run-label")).toHaveTextContent("20260803");
    expect(screen.getByTestId("results-run-label")).toHaveTextContent("2 traditions");
  });

  it("changing the metric to first-response updates the table AND the URL (deep-link)", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, files()));
    const { router } = renderApp("/results");
    await screen.findAllByTestId("standings-row");
    await userEvent.click(within(screen.getByTestId("sel-metric")).getByText("First response"));
    await waitFor(() =>
      expect(within(screen.getByTestId("leaderboard")).getAllByTestId("standings-score")[0]).toHaveTextContent("0.100"),
    );
    expect(router.state.location.searchStr).toContain("metric=turn1");
  });

  it("honors a deep-linked framing+metric on first load", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, files()));
    renderApp("/results?framing=stated&metric=full");
    const rows = await screen.findAllByTestId("standings-row");
    // claude-sonnet-5 stated/full/all = 0.900
    expect(within(rows[0]!).getByTestId("standings-score")).toHaveTextContent("0.900");
  });

  it("the framing selector updates the table AND the URL", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, files()));
    const { router } = renderApp("/results");
    await screen.findAllByTestId("standings-row");
    await userEvent.click(within(screen.getByTestId("sel-framing")).getByText("Stated"));
    await waitFor(() =>
      expect(within(screen.getByTestId("leaderboard")).getAllByTestId("standings-score")[0]).toHaveTextContent("0.900"),
    );
    expect(router.state.location.searchStr).toContain("framing=stated");
  });

  it("the pressure selector filters + updates the URL", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, files()));
    const { router } = renderApp("/results");
    await screen.findAllByTestId("standings-row");
    await userEvent.click(within(screen.getByTestId("sel-pressure")).getByText("secularize"));
    // claude-sonnet-5 unstated/full/secularize: (0.5 + 0.3)/2 = 0.400
    await waitFor(() =>
      expect(within(screen.getByTestId("leaderboard")).getAllByTestId("standings-score")[0]).toHaveTextContent("0.400"),
    );
    expect(router.state.location.searchStr).toContain("pressure=secularize");
  });

  it("the steadfastness metric reads the steadfastness slice", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, files()));
    const { router } = renderApp("/results");
    await screen.findAllByTestId("standings-row");
    await userEvent.click(within(screen.getByTestId("sel-metric")).getByText("Steadfastness (Δ)"));
    // claude-sonnet-5 unstated steadfastness/all: (0.4 + 0.8)/2 = 0.600
    await waitFor(() =>
      expect(within(screen.getByTestId("leaderboard")).getAllByTestId("standings-score")[0]).toHaveTextContent("0.600"),
    );
    expect(router.state.location.searchStr).toContain("metric=steadfastness");
  });

  it("renders a notice (not a blank page) on a malformed manifest", async () => {
    const bad = files();
    bad["results/20260803/manifest.json"] = "{ not valid json";
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, bad));
    renderApp("/results");
    expect(await screen.findByTestId("results-notices")).toBeInTheDocument();
    expect(screen.queryByTestId("leaderboard")).not.toBeInTheDocument();
  });

  it("expanding a subject shows the per-tradition drill-down (Gemini)", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, files()));
    renderApp("/results");
    const rows = await screen.findAllByTestId("standings-row");
    await userEvent.click(within(rows[0]!).getByTestId("standings-expand")); // claude-sonnet-5
    const drill = await screen.findByTestId("drilldown");
    const drillRows = within(drill).getAllByTestId("drill-row");
    // both traditions have Gemini data (0.6 buddhism, 0.8 taoism)
    expect(drillRows).toHaveLength(2);
    const bud = drillRows.find((r) => r.getAttribute("data-tradition") === "buddhism")!;
    expect(within(bud).getByTestId("drill-score")).toHaveTextContent("0.600");
  });

  it("the judge selector switches the drill-down to Opus WITHOUT re-ranking the leaderboard", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, files()));
    const { router } = renderApp("/results");
    let rows = await screen.findAllByTestId("standings-row");
    // top score before: Gemini claude-sonnet-5 = 0.700
    expect(within(rows[0]!).getByTestId("standings-score")).toHaveTextContent("0.700");
    await userEvent.click(within(screen.getByTestId("sel-judge")).getByText(/opus/));
    await screen.findByTestId("opus-caption");
    // ranking UNCHANGED (still Gemini 0.700) — judge selector only affects the drill-down
    rows = screen.getAllByTestId("standings-row");
    expect(rows[0]).toHaveAttribute("data-subject", "claude-sonnet-5");
    expect(within(rows[0]!).getByTestId("standings-score")).toHaveTextContent("0.700");
    expect(router.state.location.searchStr).toContain("judge=opus");
    // drill-down now shows ONLY buddhism (taoism has no Opus data), badged as a sample
    await userEvent.click(within(rows[0]!).getByTestId("standings-expand"));
    const drill = await screen.findByTestId("drilldown");
    const drillRows = within(drill).getAllByTestId("drill-row");
    expect(drillRows).toHaveLength(1);
    expect(drillRows[0]).toHaveAttribute("data-tradition", "buddhism");
    expect(within(drillRows[0]!).getByTestId("sample-badge")).toBeInTheDocument();
  });

  it("shows an empty-state when no results runs are published", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, {}));
    renderApp("/results");
    expect(await screen.findByText(/No results runs published/)).toBeInTheDocument();
  });
});
