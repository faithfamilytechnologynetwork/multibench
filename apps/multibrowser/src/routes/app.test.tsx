import { describe, it, expect, afterEach, vi } from "vitest";
import { screen, render } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderApp } from "../test/renderApp";
import { fakeFetch, traditionFiles } from "../test/fakeRepo";
import { REPO } from "../lib/constants";
import { ErrorBoundary } from "../components/ErrorBoundary";

const SHA = "deadbeef";
const files = {
  ...traditionFiles("sunni-islam", ["JLS-001", "JLS-002"]),
  ...traditionFiles("judaism", ["MSR-001"]),
};

afterEach(() => vi.unstubAllGlobals());

describe("index page", () => {
  it("lists the traditions fetched from GitHub", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, files));
    renderApp("/");
    expect(await screen.findByText("SUNNI-ISLAM")).toBeInTheDocument();
    expect(await screen.findByText("JUDAISM")).toBeInTheDocument();
    const cards = await screen.findAllByTestId("tradition-card");
    expect(cards).toHaveLength(2);
  });

  it("shows a rate-limit banner (keeping the page usable) on 403", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, files, { rateLimited: true }));
    renderApp("/");
    expect(await screen.findByRole("alert")).toHaveTextContent(/rate limit/i);
  });
});

describe("routing", () => {
  it("navigates to a tradition deep link", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, files));
    renderApp("/t/sunni-islam");
    expect(await screen.findByText(/sunni-islam/)).toBeInTheDocument();
  });

  it("renders an in-SPA 404 for an unknown route", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, files));
    renderApp("/totally/unknown/path");
    expect(await screen.findByText("404")).toBeInTheDocument();
  });

  it("clicking a card navigates to its tradition", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, files));
    renderApp("/");
    const card = await screen.findByText("SUNNI-ISLAM");
    await userEvent.click(card);
    expect(await screen.findByText(/sunni-islam/)).toBeInTheDocument();
  });
});

describe("ErrorBoundary", () => {
  it("catches a thrown render error and shows a message, not a blank page", () => {
    const Boom = () => {
      throw new Error("kaboom");
    };
    // Silence the expected console.error from the boundary.
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});
    render(
      <ErrorBoundary>
        <Boom />
      </ErrorBoundary>,
    );
    expect(screen.getByRole("alert")).toHaveTextContent(/Something went wrong/);
    expect(screen.getByText("kaboom")).toBeInTheDocument();
    spy.mockRestore();
  });
});
