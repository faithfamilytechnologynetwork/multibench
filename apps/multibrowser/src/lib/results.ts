// Inert results-ready seam (anticipating the judging workflow #8).
//
// v1 ALWAYS returns null — no judgement results exist yet, and none are fabricated. This is
// the SINGLE place #8's per-scenario output will be read once its schema firms up; nothing
// else in the app loads results. The render side reserves a region (ResultsRegion) that stays
// empty while this returns null. Keeping the seam present makes the future results layer an
// additive change, not a rewrite.

import type { Scenario, ScenarioResults } from "./model";

export function loadResults(_scenario: Pick<Scenario, "id">): ScenarioResults | null {
  return null;
}
