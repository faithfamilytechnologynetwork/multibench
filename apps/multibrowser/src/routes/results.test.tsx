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
const VALS: Record<string, { sonnetFull: number; sonnetTurn1: number; geminiFull: number; sonnetStated: number }> = {
  buddhism: { sonnetFull: 0.6, sonnetTurn1: 0.2, geminiFull: 0.2, sonnetStated: 0.9 },
  taoism: { sonnetFull: 0.8, sonnetTurn1: 0.0, geminiFull: 0.4, sonnetStated: 0.9 },
};

function shardFor(t: string) {
  const v = VALS[t]!;
  return {
    tradition: t,
    n_scenarios: 2,
    judges: ["gemini-3.6-flash"],
    means: {
      "gemini-3.6-flash": {
        "claude-sonnet-5": {
          unstated: { full: { all: [v.sonnetFull, 2, 2] }, turn1: { all: [v.sonnetTurn1, 2, 2] } },
          stated: { full: { all: [v.sonnetStated, 2, 2] } },
        },
        "gemini-3.6-flash": { unstated: { full: { all: [v.geminiFull, 2, 2] } } },
      },
    },
    steadfastness: {},
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

  it("shows an empty-state when no results runs are published", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, {}));
    renderApp("/results");
    expect(await screen.findByText(/No results runs published/)).toBeInTheDocument();
  });
});
