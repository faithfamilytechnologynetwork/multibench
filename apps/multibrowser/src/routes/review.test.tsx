import { describe, it, expect, afterEach, beforeEach, vi } from "vitest";
import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderApp } from "../test/renderApp";
import { fakeFetch, traditionFiles } from "../test/fakeRepo";
import { REPO } from "../lib/constants";
import { REVIEW_STORAGE_KEY, parseReviewState, resetReviewStore } from "../lib/review";

const SHA = "deadbeef";

/** The persisted intake as the tolerant loader would read it back. */
function stored() {
  return parseReviewState(localStorage.getItem(REVIEW_STORAGE_KEY));
}

// The store is module-level: isolate every test from the previous one's intake.
beforeEach(() => {
  localStorage.clear();
  resetReviewStore();
});
afterEach(() => vi.unstubAllGlobals());

describe("review landing (/review)", () => {
  it("says the three steps and lists traditions to pick", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, traditionFiles("sunni-islam", ["JLS-001", "JLS-002"])));
    renderApp("/review");
    expect(await screen.findByRole("heading", { name: /reviewer workspace/i })).toBeInTheDocument();
    const steps = screen.getByTestId("review-steps");
    expect(within(steps).getByText(/review the scenario source/i)).toBeInTheDocument();
    expect(within(steps).getByText(/review the guide/i)).toBeInTheDocument();
    expect(within(steps).getByText(/review your 10 scenarios/i)).toBeInTheDocument();
    // the four per-scenario sub-checks are spelled out
    expect(within(steps).getByText(/start with the scenario/i)).toBeInTheDocument();
    expect(within(steps).getByText(/check the scoring guide/i)).toBeInTheDocument();
    expect(within(steps).getByText(/check the judges. verdicts/i)).toBeInTheDocument();
    expect(within(steps).getByText(/check the pressure points/i)).toBeInTheDocument();
    expect(await screen.findAllByTestId("review-tradition-card")).toHaveLength(1);
  });

  it("retains the reviewer identity locally as they type", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, traditionFiles("sunni-islam", ["JLS-001"])));
    renderApp("/review");
    const name = await screen.findByLabelText("Name");
    await userEvent.type(name, "Imam Test");
    expect(stored().reviewer.name).toBe("Imam Test");
  });
});

describe("tradition review workspace (/review/$traditionId)", () => {
  it("assigns an even sample on first open and shows steps 1–3 with the corpus content", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, traditionFiles("sunni-islam", ["JLS-001", "JLS-002"])));
    renderApp("/review/sunni-islam");
    expect(await screen.findByRole("heading", { name: /reviewing: sunni-islam/i })).toBeInTheDocument();
    // step 1 + 2 render the actual prose under review
    expect(await screen.findByText("source of sunni-islam")).toBeInTheDocument();
    expect(screen.getByText("guide of sunni-islam")).toBeInTheDocument();
    // step 3: both scenarios of this small corpus are assigned (persisted, stable)
    expect(await screen.findAllByTestId("review-sample-row")).toHaveLength(2);
    await waitFor(() => expect(stored().traditions["sunni-islam"]?.sampleIds).toEqual(["JLS-001", "JLS-002"]));
  });

  it("records a tradition-level verdict (toggle + persist) and moves the progress readout", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, traditionFiles("sunni-islam", ["JLS-001", "JLS-002"])));
    renderApp("/review/sunni-islam");
    const sourceCheck = await screen.findByTestId("review-check-source");
    await userEvent.click(within(sourceCheck).getByRole("button", { name: /looks right/i }));
    expect(within(sourceCheck).getByRole("button", { name: /looks right/i })).toHaveAttribute("aria-pressed", "true");
    expect(stored().traditions["sunni-islam"]?.source.status).toBe("approved");
    // 2 tradition checks + 4×2 scenario checks = 10; one answered
    expect(screen.getByTestId("review-progress")).toHaveTextContent("1/10 checks");
    // clicking again retracts
    await userEvent.click(within(sourceCheck).getByRole("button", { name: /looks right/i }));
    expect(stored().traditions["sunni-islam"]?.source.status).toBe("unreviewed");
  });

  it("offers the submission panel: a prefilled GitHub issue and the report downloads", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, traditionFiles("sunni-islam", ["JLS-001", "JLS-002"])));
    renderApp("/review/sunni-islam");
    const submit = await screen.findByTestId("review-submit");
    const issueLink = within(submit).getByRole("link", { name: /prefilled github issue/i });
    expect(issueLink).toHaveAttribute("href", expect.stringContaining(`https://github.com/${REPO}/issues/new?title=`));
    expect(issueLink).toHaveAttribute("href", expect.stringContaining("labels=tradition-review"));
    expect(within(submit).getByRole("button", { name: /download report/i })).toBeInTheDocument();
    expect(within(submit).getByRole("button", { name: /copy report/i })).toBeInTheDocument();
    expect(within(submit).getByRole("button", { name: /back up all my reviews/i })).toBeInTheDocument();
  });

  it("reshuffle draws a seeded sample and records the seed for the report", async () => {
    const many = Array.from({ length: 30 }, (_, i) => `JLS-${String(i + 1).padStart(3, "0")}`);
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, traditionFiles("sunni-islam", many)));
    renderApp("/review/sunni-islam");
    await screen.findAllByTestId("review-sample-row");
    await userEvent.click(screen.getByRole("button", { name: /reshuffle sample/i }));
    await waitFor(() => expect(stored().traditions["sunni-islam"]?.sampleSeed).not.toBe(""));
    expect(stored().traditions["sunni-islam"]?.sampleIds).toHaveLength(10);
  });
});

describe("scenario review (/review/$traditionId/$scenarioId)", () => {
  it("walks the four checks with the content under review inline", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, traditionFiles("sunni-islam", ["JLS-001", "JLS-002"])));
    renderApp("/review/sunni-islam/JLS-001");
    expect(await screen.findByTestId("review-check-scenario")).toBeInTheDocument();
    // a — the scenario's opening message
    expect(await screen.findByText("turn1 for JLS-001")).toBeInTheDocument();
    // b — the scoring guide (judge-guidance)
    expect(screen.getByText("judge guidance for JLS-001")).toBeInTheDocument();
    // c — no results run in this fixture → honest empty state, review continues
    expect(screen.getByTestId("review-no-run")).toBeInTheDocument();
    // d — all six pushes render
    expect(screen.getByTestId("review-check-pressures").querySelectorAll("[data-pressure]")).toHaveLength(6);
  });

  it("records a per-check verdict with notes, persisted under the right scenario", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, traditionFiles("sunni-islam", ["JLS-001", "JLS-002"])));
    renderApp("/review/sunni-islam/JLS-001");
    const scoring = await screen.findByTestId("review-check-scoring");
    await userEvent.click(within(scoring).getByRole("button", { name: /needs changes/i }));
    await userEvent.type(within(scoring).getByLabelText("Notes"), "missing exception");
    const t = stored().traditions["sunni-islam"];
    expect(t?.scenarios["JLS-001"]?.scoring.status).toBe("flagged");
    expect(t?.scenarios["JLS-001"]?.scoring.notes).toBe("missing exception");
  });

  it("navigates prev/next within the reviewer's assigned sample", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, traditionFiles("sunni-islam", ["JLS-001", "JLS-002"])));
    // Visit the tradition page first so the sample exists (the assignment is drawn there).
    const { router } = renderApp("/review/sunni-islam");
    await screen.findAllByTestId("review-sample-row");
    await router.navigate({ to: "/review/$traditionId/$scenarioId", params: { traditionId: "sunni-islam", scenarioId: "JLS-001" } });
    expect(await screen.findByText(/scenario 1 of 2 in your sample/i)).toBeInTheDocument();
    await userEvent.click(screen.getByRole("link", { name: /next scenario: JLS-002/i }));
    expect(await screen.findByText(/scenario 2 of 2 in your sample/i)).toBeInTheDocument();
  });

  it("404s an unknown scenario id", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, traditionFiles("sunni-islam", ["JLS-001"])));
    renderApp("/review/sunni-islam/NOPE-999");
    expect(await screen.findByText("404")).toBeInTheDocument();
  });
});
