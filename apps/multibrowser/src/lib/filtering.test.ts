import { describe, it, expect } from "vitest";
import {
  applyFilters,
  filterAndSort,
  isActive,
  parseSelection,
  selectionToSearch,
  sortRows,
  type Row,
  type Selection,
} from "./filtering";
import type { ScenarioMeta } from "./model";

function row(
  id: string,
  tags: Record<string, string[]>,
  sourceLocus: number | null = 1,
  identitySignal = "clean",
  locusLabel = "",
): Row {
  const meta: ScenarioMeta = { id, tags, sourceLocus, locusLabel, identitySignal };
  return { id, meta };
}

const sel = (over: Partial<Selection> = {}): Selection => ({
  axes: {},
  identity: [],
  locusMin: null,
  locusMax: null,
  q: "",
  sort: "default",
  ...over,
});

// A mixed set spanning a 2-axis (sunni) and a 5-axis (judaism) shape — axis-agnostic.
const rows: Row[] = [
  row("JLS-001", { pillars: ["restraint", "justice"], hearts: ["patience"] }, 10, "clean", "Backbiting"),
  row("JLS-002", { pillars: ["justice"], hearts: ["vigilance"] }, 20, "leaky", "Justice"),
  row("MSR-001", { middot: ["anavah"], virtues: ["emet"], domain: ["speech"], register: ["plain"], middle_path: ["balance"] }, 5, "clean", "Humility"),
];

describe("axis filters (OR within axis, AND across axes; arbitrary axis names)", () => {
  it("OR within an axis", () => {
    const out = applyFilters(rows, sel({ axes: { pillars: ["restraint", "courage"] } }));
    expect(out.map((r) => r.id)).toEqual(["JLS-001"]); // has restraint
  });
  it("AND across axes", () => {
    const both = applyFilters(rows, sel({ axes: { pillars: ["justice"], hearts: ["vigilance"] } }));
    expect(both.map((r) => r.id)).toEqual(["JLS-002"]);
    const none = applyFilters(rows, sel({ axes: { pillars: ["justice"], hearts: ["patience"] } }));
    expect(none.map((r) => r.id)).toEqual(["JLS-001"]);
  });
  it("works over a 5-axis tradition's axes", () => {
    const out = applyFilters(rows, sel({ axes: { domain: ["speech"], register: ["plain"] } }));
    expect(out.map((r) => r.id)).toEqual(["MSR-001"]);
  });
});

describe("identity / locus / search", () => {
  it("identity_signal OR", () => {
    expect(applyFilters(rows, sel({ identity: ["leaky"] })).map((r) => r.id)).toEqual(["JLS-002"]);
    expect(applyFilters(rows, sel({ identity: ["clean", "leaky"] })).length).toBe(3);
  });
  it("source_locus range inclusive both ends; one-sided allowed", () => {
    expect(applyFilters(rows, sel({ locusMin: 10, locusMax: 20 })).map((r) => r.id)).toEqual(["JLS-001", "JLS-002"]);
    expect(applyFilters(rows, sel({ locusMin: 10 })).map((r) => r.id)).toEqual(["JLS-001", "JLS-002"]);
    expect(applyFilters(rows, sel({ locusMax: 5 })).map((r) => r.id)).toEqual(["MSR-001"]);
  });
  it("free-text over id and locus_label", () => {
    expect(applyFilters(rows, sel({ q: "msr" })).map((r) => r.id)).toEqual(["MSR-001"]);
    expect(applyFilters(rows, sel({ q: "backbiting" })).map((r) => r.id)).toEqual(["JLS-001"]);
  });
});

describe("incomplete rows (ghost/stub/loading: meta null)", () => {
  const withGhost: Row[] = [...rows, { id: "JLS-999", meta: null }];
  it("appears when unfiltered", () => {
    expect(applyFilters(withGhost, sel()).map((r) => r.id)).toContain("JLS-999");
  });
  it("is excluded by any active positive filter", () => {
    expect(applyFilters(withGhost, sel({ axes: { pillars: ["justice"] } })).map((r) => r.id)).not.toContain("JLS-999");
    expect(applyFilters(withGhost, sel({ identity: ["clean"] })).map((r) => r.id)).not.toContain("JLS-999");
    expect(applyFilters(withGhost, sel({ locusMin: 0 })).map((r) => r.id)).not.toContain("JLS-999");
  });
  it("is still findable by id search", () => {
    expect(applyFilters(withGhost, sel({ q: "999" })).map((r) => r.id)).toEqual(["JLS-999"]);
  });
});

describe("sort", () => {
  it("default preserves declared order", () => {
    expect(sortRows(rows, "default").map((r) => r.id)).toEqual(["JLS-001", "JLS-002", "MSR-001"]);
  });
  it("by id", () => {
    expect(sortRows(rows, "id").map((r) => r.id)).toEqual(["JLS-001", "JLS-002", "MSR-001"]);
  });
  it("by source_locus, with null last", () => {
    const withNull: Row[] = [...rows, { id: "ZZZ", meta: null }];
    const ids = sortRows(withNull, "source_locus").map((r) => r.id);
    expect(ids).toEqual(["MSR-001", "JLS-001", "JLS-002", "ZZZ"]); // 5,10,20,null
  });
});

describe("URL search <-> selection round-trip", () => {
  it("parseSelection separates axes from reserved keys", () => {
    const s = parseSelection(
      { pillars: ["restraint", "justice"], identity_signal: "clean", locusMin: "10", q: "x", sort: "id", unknownAxis: "z" },
      ["pillars", "hearts"],
    );
    expect(s.axes).toEqual({ pillars: ["restraint", "justice"] }); // unknownAxis ignored (not declared)
    expect(s.identity).toEqual(["clean"]);
    expect(s.locusMin).toBe(10);
    expect(s.q).toBe("x");
    expect(s.sort).toBe("id");
  });
  it("selectionToSearch omits empty/default and round-trips", () => {
    const original = sel({ axes: { pillars: ["a", "b"] }, identity: ["leaky"], locusMax: 50, q: "hi", sort: "source_locus" });
    const search = selectionToSearch(original);
    expect(search).toEqual({ pillars: ["a", "b"], identity_signal: ["leaky"], locusMax: "50", q: "hi", sort: "source_locus" });
    expect(parseSelection(search, ["pillars"])).toEqual(original);
  });
  it("isActive reflects whether any filter is set", () => {
    expect(isActive(sel())).toBe(false);
    expect(isActive(sel({ q: "x" }))).toBe(true);
    expect(isActive(sel({ axes: { pillars: ["a"] } }))).toBe(true);
  });
});

describe("filterAndSort composes", () => {
  it("filters then sorts", () => {
    const out = filterAndSort(rows, sel({ identity: ["clean"], sort: "source_locus" }));
    expect(out.map((r) => r.id)).toEqual(["MSR-001", "JLS-001"]); // clean rows, by locus
  });
});
