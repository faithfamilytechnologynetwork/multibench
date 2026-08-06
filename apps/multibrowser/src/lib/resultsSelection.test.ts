import { describe, it, expect } from "vitest";
import {
  DEFAULTS,
  parseResultsSelection,
  selectionToResultsSearch,
  type ResultsSelection,
} from "./resultsSelection";
import type { ResultsManifest } from "./resultsModel";

const manifest = {
  framings: ["unstated", "stated", "guided"],
  pressures: ["secularize", "insistence"],
  pressureAll: "all",
  judges: [{ key: "gemini" }, { key: "opus" }],
} as unknown as ResultsManifest;

describe("parseResultsSelection", () => {
  it("returns defaults on an empty search", () => {
    expect(parseResultsSelection({})).toEqual({
      runId: null, judge: DEFAULTS.judge, framing: DEFAULTS.framing, metric: DEFAULTS.metric, pressure: DEFAULTS.pressure,
    });
  });

  it("reads valid values", () => {
    const sel = parseResultsSelection(
      { run: "20260803", judge: "opus", framing: "stated", metric: "turn1", pressure: "secularize" }, manifest);
    expect(sel).toEqual({
      runId: "20260803", judge: "opus", framing: "stated", metric: "turn1", pressure: "secularize",
    });
  });

  it("clamps out-of-vocab values to defaults when a manifest is supplied", () => {
    const sel = parseResultsSelection(
      { judge: "bogus", framing: "sideways", metric: "vibes", pressure: "bribery" }, manifest);
    expect(sel).toMatchObject({
      judge: DEFAULTS.judge, framing: DEFAULTS.framing, metric: DEFAULTS.metric, pressure: DEFAULTS.pressure,
    });
  });

  it("validates metric against the fixed UI set even without a manifest", () => {
    expect(parseResultsSelection({ metric: "steadfastness" }).metric).toBe("steadfastness");
    expect(parseResultsSelection({ metric: "nonsense" }).metric).toBe(DEFAULTS.metric);
  });
});

describe("selectionToResultsSearch", () => {
  it("omits defaults (clean base URL)", () => {
    const sel: ResultsSelection = { runId: null, ...DEFAULTS };
    expect(selectionToResultsSearch(sel)).toEqual({});
  });

  it("emits only non-default values", () => {
    const sel: ResultsSelection = {
      runId: "r9", judge: "opus", framing: "guided", metric: "steadfastness", pressure: "flattery",
    };
    expect(selectionToResultsSearch(sel)).toEqual({
      run: "r9", judge: "opus", framing: "guided", metric: "steadfastness", pressure: "flattery",
    });
  });

  it("round-trips a non-default selection through parse", () => {
    const sel: ResultsSelection = {
      runId: null, judge: "gemini", framing: "stated", metric: "turn1", pressure: "insistence",
    };
    expect(parseResultsSelection(selectionToResultsSearch(sel), manifest)).toEqual(sel);
  });
});
