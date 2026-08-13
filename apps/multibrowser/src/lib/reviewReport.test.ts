import { describe, it, expect } from "vitest";
import {
  MAX_ISSUE_URL_LENGTH,
  blankIssueUrl,
  blobUrl,
  buildReviewReport,
  editFileUrl,
  issueTitle,
  prefilledIssueUrl,
  scenarioCheckFile,
} from "./reviewReport";
import {
  emptyState,
  withReviewer,
  withSample,
  withScenarioCheck,
  withTraditionCheck,
  type ReviewState,
} from "./review";

const REPO = "owner/repo";

function sampleState(): ReviewState {
  let s = emptyState();
  s = withReviewer(s, { name: "Rev. Example", contact: "rev@example.com", background: "pastor, 20 years" });
  s = withSample(s, "sunni-islam", ["JLS-001", "JLS-050"], "seed42");
  s = withTraditionCheck(s, "sunni-islam", "source", { status: "approved", notes: "right choice of text" });
  s = withTraditionCheck(s, "sunni-islam", "guide", { status: "flagged", suggestion: "Add the exit-ramp principle" });
  s = withScenarioCheck(s, "sunni-islam", "JLS-001", "scoring", {
    status: "flagged",
    notes: "The wronged-party exception is missing.",
    suggestion: "Cite Q4:148 explicitly.",
  });
  return s;
}

describe("buildReviewReport", () => {
  const report = buildReviewReport({
    state: sampleState(),
    traditionId: "sunni-islam",
    displayName: "Sunni Islam",
    sha: "cafebabe",
    runId: "20260803",
    repo: REPO,
    now: new Date("2026-08-13T12:00:00Z"),
  });

  it("carries the reviewer identity, date, snapshot, run, and sample (with seed)", () => {
    expect(report).toContain("# Tradition review — Sunni Islam (`sunni-islam`)");
    expect(report).toContain("- Reviewer: Rev. Example");
    expect(report).toContain("- Contact: rev@example.com");
    expect(report).toContain("- Background: pastor, 20 years");
    expect(report).toContain("- Date: 2026-08-13");
    expect(report).toContain("- Corpus snapshot: `cafebabe`");
    expect(report).toContain("- Results run: 20260803");
    expect(report).toContain("JLS-001, JLS-050");
    expect(report).toContain("(seed `seed42`)");
  });

  it("renders each check's verdict, notes as blockquote, and suggestion, with pinned file links", () => {
    expect(report).toContain("✅ looks right");
    expect(report).toContain("⚠️ needs changes");
    expect(report).toContain("> right choice of text");
    expect(report).toContain("> The wronged-party exception is missing.");
    expect(report).toContain("> Cite Q4:148 explicitly.");
    expect(report).toContain(`https://github.com/${REPO}/blob/cafebabe/traditions/sunni-islam/source.md`);
    expect(report).toContain(
      `https://github.com/${REPO}/blob/cafebabe/traditions/sunni-islam/scenarios/JLS-001/judge-guidance.md`,
    );
  });

  it("marks unanswered checks honestly and lists every sampled scenario", () => {
    expect(report).toContain("◻️ not reviewed");
    expect(report).toContain("### JLS-050");
  });

  it("degrades when nothing is known: no sha → main links, no run → '(none published)'", () => {
    const r = buildReviewReport({
      state: emptyState(),
      traditionId: "t",
      displayName: "T",
      sha: null,
      runId: null,
      repo: REPO,
      now: new Date("2026-08-13T12:00:00Z"),
    });
    expect(r).toContain("- Corpus snapshot: (unknown)");
    expect(r).toContain("- Results run: (none published)");
    expect(r).toContain("- Scenario sample: (none)");
  });
});

describe("scenarioCheckFile", () => {
  it("maps each check to the corpus file it reads against", () => {
    expect(scenarioCheckFile("t", "S-1", "scenario")).toBe("traditions/t/scenarios/S-1/turn1.md");
    expect(scenarioCheckFile("t", "S-1", "scoring")).toBe("traditions/t/scenarios/S-1/judge-guidance.md");
    expect(scenarioCheckFile("t", "S-1", "judgement")).toBe("traditions/t/scenarios/S-1/judge-guidance.md");
    expect(scenarioCheckFile("t", "S-1", "pressures")).toBe("traditions/t/scenarios/S-1/pressures.md");
  });
});

describe("submission URLs", () => {
  it("prefills title, label, and body (URL-encoded) when the report fits", () => {
    const url = prefilledIssueUrl(REPO, "Tradition review: X", "line one\nline two");
    expect(url).not.toBeNull();
    expect(url).toContain(`https://github.com/${REPO}/issues/new?title=`);
    expect(url).toContain(encodeURIComponent("Tradition review: X"));
    expect(url).toContain("labels=tradition-review");
    expect(url).toContain(encodeURIComponent("line one\nline two"));
  });

  it("returns null for a report too long to ride a URL (caller falls back to copy + blank issue)", () => {
    const url = prefilledIssueUrl(REPO, "t", "x".repeat(MAX_ISSUE_URL_LENGTH + 1));
    expect(url).toBeNull();
    expect(blankIssueUrl(REPO, "t")).toContain(`https://github.com/${REPO}/issues/new?title=t`);
  });

  it("issueTitle includes the reviewer when known", () => {
    expect(issueTitle("Sunni Islam", "A. Reviewer")).toBe("Tradition review: Sunni Islam — A. Reviewer");
    expect(issueTitle("Sunni Islam", "  ")).toBe("Tradition review: Sunni Islam");
  });

  it("edit links target a writable ref; blob links pin the reviewed snapshot", () => {
    expect(editFileUrl(REPO, "main", "traditions/t/guide.md")).toBe(
      `https://github.com/${REPO}/edit/main/traditions/t/guide.md`,
    );
    expect(blobUrl(REPO, "cafebabe", "traditions/t/guide.md")).toBe(
      `https://github.com/${REPO}/blob/cafebabe/traditions/t/guide.md`,
    );
  });
});
