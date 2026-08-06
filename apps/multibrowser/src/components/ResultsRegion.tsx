import { Link } from "@tanstack/react-router";
import { useLatestSha, useResultsRuns } from "../lib/queries";

// The per-scenario results entry (#51). Once a results run is published, this becomes a live
// drill-in to the raw-results view (transcripts + judge verdicts); until then it's a subtle
// placeholder. The generic raw browser lives at /results/$runId/$groupId/$itemId; this is the
// in-page seam that links into it, keyed to the default (most recent) results run.
export function ResultsRegion({ traditionId, scenarioId }: { traditionId: string; scenarioId: string }) {
  const sha = useLatestSha().data;
  const runId = useResultsRuns(sha).data?.defaultRunId ?? null;
  if (!runId) {
    return (
      <p data-testid="results-region" className="text-xs italic text-default-400">
        No judging results yet — model transcripts and judge verdicts will appear here once a results run is published.
      </p>
    );
  }
  return (
    <div data-testid="results-region" data-has-results="true" className="text-sm">
      <Link
        to="/results/$runId/$groupId/$itemId"
        params={{ runId, groupId: traditionId, itemId: scenarioId }}
        className="text-primary hover:underline"
      >
        Browse the models&rsquo; raw responses &amp; our judging &rarr;
      </Link>
    </div>
  );
}
