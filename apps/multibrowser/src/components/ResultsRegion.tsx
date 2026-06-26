import type { Scenario } from "../lib/model";

// The reserved, currently-INERT results region (the §4.1 seam for the judging workflow #8).
// In v1 `scenario.results` is always absent, so this renders only a subtle placeholder — no
// scores/bands/verdicts markup. When #8 lands, this is where its per-scenario output renders,
// beside the judge-guidance it is anchored to. The presence of this component is the whole
// point: the results layer slots in here additively, not as a rewrite.
export function ResultsRegion({ scenario }: { scenario: Scenario }) {
  if (!scenario.results) {
    return (
      <p data-testid="results-region" className="text-xs italic text-default-400">
        No judgement results yet — model scores, bands, and verdicts will appear here once available.
      </p>
    );
  }
  // #8 integration point (not reached in v1).
  return <div data-testid="results-region" data-has-results="true" />;
}
