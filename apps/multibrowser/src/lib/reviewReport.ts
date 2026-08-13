// The review workflow's SUBMIT seam: turn one tradition's reviewer intake into a Markdown
// report, and build the URLs that carry it to the maintainers (prefilled GitHub issue) or
// let the reviewer propose a concrete file change (GitHub's web editor, which forks for
// non-collaborators). Pure functions — everything here is unit-testable without a browser.

import type { CheckReview, ReviewState, ScenarioCheckKey, TraditionReview } from "./review";
import { SCENARIO_CHECKS, SCENARIO_CHECK_LABELS, scenarioChecksOf } from "./review";
import { FILE } from "./constants";

/** The issue label maintainers can aggregate on (`gh issue list --label tradition-review`).
 * GitHub ignores the param for reporters without triage rights — harmless either way. */
export const REVIEW_ISSUE_LABEL = "tradition-review";

/**
 * Keep prefilled-issue URLs comfortably under GitHub's ~8K handling limit; beyond this the form
 * silently truncates. Longer reports fall back to copy-the-report + a blank issue.
 */
export const MAX_ISSUE_URL_LENGTH = 6500;

const statusLine = (c: CheckReview): string =>
  c.status === "approved" ? "✅ looks right" : c.status === "flagged" ? "⚠️ needs changes" : "◻️ not reviewed";

/** Quote free text as a Markdown blockquote (safe against ``` in the reviewer's own text). */
function quoted(text: string): string {
  return text
    .trim()
    .split("\n")
    .map((l) => `> ${l}`)
    .join("\n");
}

function checkSection(heading: string, c: CheckReview, filePath: string | null, repo: string, sha: string): string {
  const lines = [`${heading}: ${statusLine(c)}`];
  if (filePath) lines.push(`  - file: https://github.com/${repo}/blob/${sha}/${filePath}`);
  if (c.notes.trim()) lines.push("", "  Notes:", "", quoted(c.notes));
  if (c.suggestion.trim()) lines.push("", "  Suggested revision:", "", quoted(c.suggestion));
  return lines.join("\n");
}

export interface ReportContext {
  state: ReviewState;
  traditionId: string;
  displayName: string;
  /** The pinned corpus snapshot the reviewer was reading (for exact file links). */
  sha: string | null;
  /** The results run whose verdicts were on screen (null when none is published). */
  runId: string | null;
  repo: string;
  /** Report timestamp — injectable for deterministic tests. */
  now?: Date;
}

/**
 * One tradition's full review as a Markdown report: reviewer identity, the two tradition-level
 * checks, then each assigned scenario's four checks with notes + suggested revisions, all linked
 * to the exact files at the reviewed snapshot.
 */
export function buildReviewReport(ctx: ReportContext): string {
  const { state, traditionId, displayName, repo, runId } = ctx;
  const sha = ctx.sha ?? "main";
  const t: TraditionReview =
    state.traditions[traditionId] ??
    ({ sampleSeed: "", sampleIds: [], source: emptyLike(), guide: emptyLike(), scenarios: {} } as TraditionReview);
  const when = (ctx.now ?? new Date()).toISOString().slice(0, 10);
  const base = `traditions/${traditionId}`;

  const out: string[] = [];
  out.push(`# Tradition review — ${displayName} (\`${traditionId}\`)`);
  out.push("");
  out.push(`- Reviewer: ${state.reviewer.name.trim() || "(not given)"}`);
  if (state.reviewer.contact.trim()) out.push(`- Contact: ${state.reviewer.contact.trim()}`);
  if (state.reviewer.background.trim()) out.push(`- Background: ${state.reviewer.background.trim()}`);
  out.push(`- Date: ${when}`);
  out.push(`- Corpus snapshot: ${ctx.sha ? `\`${ctx.sha}\`` : "(unknown)"}`);
  out.push(`- Results run: ${runId ?? "(none published)"}`);
  out.push(`- Scenario sample: ${t.sampleIds.length ? t.sampleIds.join(", ") : "(none)"}${t.sampleSeed ? ` (seed \`${t.sampleSeed}\`)` : ""}`);
  out.push("");
  out.push("## 1. Scenario source");
  out.push("");
  out.push(checkSection("Verdict", t.source, `${base}/${FILE.source}`, repo, sha));
  out.push("");
  out.push("## 2. Companionship guide");
  out.push("");
  out.push(checkSection("Verdict", t.guide, `${base}/${FILE.guide}`, repo, sha));
  out.push("");
  out.push("## 3. Scenarios");

  for (const sid of t.sampleIds) {
    const checks = scenarioChecksOf(t, sid);
    out.push("");
    out.push(`### ${sid}`);
    out.push("");
    for (const key of SCENARIO_CHECKS) {
      out.push(
        checkSection(
          `**${SCENARIO_CHECK_LABELS[key]}**`,
          checks[key],
          scenarioCheckFile(traditionId, sid, key),
          repo,
          sha,
        ),
      );
      out.push("");
    }
  }
  out.push("---");
  out.push("_Submitted from the MultiBrowser review workflow (`/review`)._ ");
  return out.join("\n");
}

function emptyLike(): CheckReview {
  return { status: "unreviewed", notes: "", suggestion: "" };
}

/** The corpus file each scenario check reads against (judgement → the judge-guidance it applies). */
export function scenarioCheckFile(tid: string, sid: string, key: ScenarioCheckKey): string {
  const base = `traditions/${tid}/${FILE.scenariosDir}/${sid}`;
  switch (key) {
    case "scenario":
      return `${base}/${FILE.turn1}`;
    case "scoring":
    case "judgement":
      return `${base}/${FILE.judgeGuidance}`;
    case "pressures":
      return `${base}/${FILE.pressures}`;
  }
}

/**
 * A prefilled new-issue URL carrying the report, or `null` when the report is too long to ride
 * a URL (the caller then offers copy-report + `blankIssueUrl`).
 */
export function prefilledIssueUrl(repo: string, title: string, body: string): string | null {
  const url =
    `https://github.com/${repo}/issues/new` +
    `?title=${encodeURIComponent(title)}` +
    `&labels=${encodeURIComponent(REVIEW_ISSUE_LABEL)}` +
    `&body=${encodeURIComponent(body)}`;
  return url.length <= MAX_ISSUE_URL_LENGTH ? url : null;
}

export function blankIssueUrl(repo: string, title: string): string {
  return (
    `https://github.com/${repo}/issues/new` +
    `?title=${encodeURIComponent(title)}` +
    `&labels=${encodeURIComponent(REVIEW_ISSUE_LABEL)}`
  );
}

export function issueTitle(displayName: string, reviewerName: string): string {
  const who = reviewerName.trim() ? ` — ${reviewerName.trim()}` : "";
  return `Tradition review: ${displayName}${who}`;
}

/**
 * GitHub's web editor for a corpus file (branch ref, NOT a SHA — editing needs a writable ref;
 * GitHub forks automatically for reviewers without push access, yielding a real PR path).
 */
export function editFileUrl(repo: string, ref: string, path: string): string {
  return `https://github.com/${repo}/edit/${ref}/${path}`;
}

/** A pinned read link to the exact reviewed snapshot of a file. */
export function blobUrl(repo: string, shaOrRef: string, path: string): string {
  return `https://github.com/${repo}/blob/${shaOrRef}/${path}`;
}
