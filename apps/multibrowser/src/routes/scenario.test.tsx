import { describe, it, expect, afterEach, vi } from "vitest";
import { screen } from "@testing-library/react";
import { renderApp } from "../test/renderApp";
import { fakeFetch, traditionFiles } from "../test/fakeRepo";
import { REPO, PRESSURES } from "../lib/constants";

const SHA = "deadbeef";
afterEach(() => vi.unstubAllGlobals());

describe("scenario detail", () => {
  it("renders turn-1, the six pressures in canonical order, judge-guidance, framings, and an inert results region", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, traditionFiles("sunni-islam", ["JLS-001", "JLS-002"])));
    const { container } = renderApp("/t/sunni-islam/JLS-001");

    expect(await screen.findByRole("heading", { name: "JLS-001" })).toBeInTheDocument();
    expect(screen.getByText("turn1 for JLS-001")).toBeInTheDocument();

    const order = [...container.querySelectorAll("[data-pressure]")].map((el) =>
      el.getAttribute("data-pressure"),
    );
    expect(order).toEqual([...PRESSURES]); // canonical order

    expect(screen.getByText(/judge guidance for JLS-001/)).toBeInTheDocument();

    // Framings: Stated template instantiated with the tradition's adherent_noun ("Adherent").
    expect(screen.getByText(/practising Adherent/)).toBeInTheDocument();
    // Guided framing renders the tradition's actual guide.md content.
    expect(screen.getByText(/guide of sunni-islam/)).toBeInTheDocument();

    // Inert results seam: present but empty (no scores/bands/verdicts).
    const region = screen.getByTestId("results-region");
    expect(region).toHaveTextContent(/No judgement results yet/);
    expect(region).not.toHaveAttribute("data-has-results");
  });

  it("offers prev/next navigation in declared order", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, traditionFiles("sunni-islam", ["JLS-001", "JLS-002"])));
    renderApp("/t/sunni-islam/JLS-001");
    // first scenario: next = JLS-002, prev disabled
    expect(await screen.findByRole("link", { name: /JLS-002/ })).toBeInTheDocument();
  });

  it("shows inline notices (not a crash) for a malformed scenario", async () => {
    const files = traditionFiles("sunni-islam", ["JLS-001"]);
    // Drop the 'flattery' pressure and blank 'good_cause'.
    files["traditions/sunni-islam/scenarios/JLS-001/pressures.md"] = [
      "## secularize", "s", "## insistence", "i", "## false_authority", "fa",
      "## good_cause", "", "## personal_appeal", "pa", "",
    ].join("\n");
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, files));
    renderApp("/t/sunni-islam/JLS-001");

    expect(await screen.findByRole("heading", { name: "JLS-001" })).toBeInTheDocument(); // didn't crash
    const notes = await screen.findAllByText(/missing or empty/i);
    expect(notes.length).toBeGreaterThan(0); // flattery missing + good_cause empty
  });

  it("surfaces an unknown-tag-value notice on the scenario page", async () => {
    const files = traditionFiles("sunni-islam", ["JLS-001"]);
    // manifest declares pillars [a,b]; give the scenario an undeclared value.
    files["traditions/sunni-islam/scenarios/JLS-001/scenario.yaml"] =
      "id: JLS-001\ntags: {pillars: [not-a-pillar]}\nsource_locus: 1\nlocus_label: X\nidentity_signal: clean\n";
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, files));
    renderApp("/t/sunni-islam/JLS-001");
    expect(await screen.findByText(/not-a-pillar/)).toBeInTheDocument(); // the inline notice
  });

  it("renders an in-SPA 404 for an unknown scenario id", async () => {
    vi.stubGlobal("fetch", fakeFetch(REPO, SHA, traditionFiles("sunni-islam", ["JLS-001"])));
    renderApp("/t/sunni-islam/JLS-999");
    expect(await screen.findByText("404")).toBeInTheDocument();
  });
});
