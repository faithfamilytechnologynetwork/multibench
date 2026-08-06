import { Link } from "@tanstack/react-router";
import { useLatestSha, useResultsRuns } from "../lib/queries";

// The per-scenario results entry (#51). Once a results run is published, this becomes a live
// drill-in to the raw-results view (transcripts + judge verdicts); until then it's a subtle
// placeholder. The generic raw browser lives at /results/$runId/$groupId/$itemId; this is the
// in-page seam that links into it, keyed to the default (most recent) results run.
export function ResultsRegion({ traditionId, scenarioId }: { traditionId: string; scenarioId: string }) {
  const sha = useLatestSha().data;
  const runs = useResultsRuns(sha).data;
  const runId = runs?.defaultRunId ?? null;
  if (!runId) {
    return (
      <p data-testid="results-region" className="text-xs italic text-default-400">
        No judging results yet — model transcripts and judge verdicts will appear here once a results run is published.
      </p>
    );
  }
  // Make the entry contentful from the run's SCORE manifest — no raw-shard fetch (the per-scenario
  // shard is ~220 KB; loading it just to summarize would tax every scenario page). The full
  // cell-score grid lives one tap away in the raw view (architect-approved perf deviation, #51).
  const manifest = runs?.runs.find((r) => r.id === runId)?.manifest;
  const nSubjects = manifest?.subjects.length ?? 0;
  const nConditions = manifest ? manifest.framings.length * manifest.pressures.length : 0;
  const detail = nSubjects && nConditions ? ` — ${nSubjects} models × ${nConditions} conditions` : "";
  return (
    <div data-testid="results-region" data-has-results="true" className="text-sm">
      <Link
        to="/results/$runId/$groupId/$itemId"
        params={{ runId, groupId: traditionId, itemId: scenarioId }}
        className="text-primary hover:underline"
      >
        Browse the models&rsquo; raw responses &amp; our judging{detail} &rarr;
      </Link>
    </div>
  );
}
