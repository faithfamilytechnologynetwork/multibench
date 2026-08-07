import { Link } from "@tanstack/react-router";
import type { RawSelection } from "../lib/rawSelection";
import type { RawCatalog, RawShard } from "../lib/rawModel";
import type { Notice as NoticeT, ScenarioMeta } from "../lib/model";
import { RawComparison } from "./RawComparison";
import { Collapsible } from "./Collapsible";
import { Markdown } from "./Markdown";
import { Notice, Notices } from "./Notice";
import { CenteredSpinner } from "./Loading";

export type ResponsesStatus = "loading" | "no-run" | "ready" | "error";

/**
 * The scenario page's MAIN pane (jaleesbrowser layout): the scenario at the top (id — title, tags
 * inline), a collapsible Context (the tradition's judge guidance) — BOTH always shown from scenario
 * data — then the conversation (question → each model's answer → judges' verdicts interleaved, via
 * `RawComparison`), or a loading/no-run/error state. Controls live in the sidebar (`ScenarioControls`).
 */
export function ScenarioResponses({
  status, catalog, shard, sel, scenarioId, meta, judgeGuidance, guidanceWhere, runId, traditionId, dataNotices, sourceNotices,
}: {
  status: ResponsesStatus;
  catalog: RawCatalog | null;
  shard: RawShard | null;
  sel: RawSelection | null;
  scenarioId: string;
  meta: ScenarioMeta | null;
  judgeGuidance: string | null;
  guidanceWhere: string;
  runId: string | null;
  traditionId: string;
  dataNotices: NoticeT[];
  sourceNotices: NoticeT[];
}) {
  return (
    <div className="flex flex-col gap-4" data-testid="scenario-responses">
      {/* Scenario header: id — title, with tags inline on one wrapping line (reference layout). */}
      <header className="flex flex-col gap-1">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h1 className="text-xl font-semibold">
            <span className="font-mono">{scenarioId}</span>
            {meta?.locusLabel && <span className="font-normal text-default-700"> — {meta.locusLabel}</span>}
          </h1>
          {runId && (
            <Link to="/results/$runId/$groupId/$itemId" params={{ runId, groupId: traditionId, itemId: scenarioId }}
              className="whitespace-nowrap text-xs text-primary hover:underline">
              Open in the full explorer →
            </Link>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-default-500">
          {meta?.identitySignal && <span>{meta.identitySignal}</span>}
          {meta?.sourceLocus != null && <span>locus #{meta.sourceLocus}</span>}
          {meta && Object.entries(meta.tags).map(([axis, vals]) => (
            <span key={axis}><span className="font-medium uppercase tracking-wide">{axis}</span> {vals.join(", ")}</span>
          ))}
        </div>
      </header>

      {/* Context = the tradition's guidance the judges score against (scenario data — always here). */}
      <Collapsible title="Context — what good counsel looks like (the guidance the judges use)">
        {judgeGuidance != null
          ? <Markdown>{judgeGuidance}</Markdown>
          : <Notice notice={{ severity: "error", scope: "section", where: guidanceWhere, message: "Judge-guidance is missing or empty." }} />}
      </Collapsible>

      {/* Data-layer notices (malformed scenario markdown, unknown tag values, raw-load problems) —
          always surfaced, even before/without a results run (display-first). */}
      {dataNotices.length > 0 && <Notices notices={dataNotices} />}

      {status === "loading" && <CenteredSpinner label="Loading responses…" />}

      {status === "no-run" && (
        <p className="text-sm italic text-default-400" data-testid="no-run">
          No judging results yet — model transcripts and judge verdicts will appear here once a results run is published.
        </p>
      )}

      {status === "error" && dataNotices.length === 0 && (
        <Notice notice={{ severity: "error", scope: "results-raw", where: scenarioId, message: "Couldn't load the responses for this scenario." }} />
      )}

      {status === "ready" && catalog && sel && (
        <>
          {/* Plain-language score meaning (numeric + ramp, no band names). */}
          <p className="text-xs text-default-500">
            Verdicts score each answer from <span className="font-mono">{catalog.scale.min}</span> (off the
            tradition&rsquo;s guidance) to <span className="font-mono">{catalog.scale.max}</span> (well aligned);
            the colored chip follows that scale.
          </p>
          {shard
            ? <RawComparison catalog={catalog} shard={shard} a={sel.a} b={sel.b} conditions={sel.conditions} />
            : <p className="text-sm text-default-500">The responses for this scenario are unavailable — see the notices above.</p>}
          {sourceNotices.length > 0 && (
            <footer className="mt-1 flex flex-col gap-0.5 border-t border-default-100 pt-2 text-xs text-default-400" data-testid="source-notes">
              {sourceNotices.map((n, i) => <span key={i}>{n.message}</span>)}
            </footer>
          )}
        </>
      )}
    </div>
  );
}
