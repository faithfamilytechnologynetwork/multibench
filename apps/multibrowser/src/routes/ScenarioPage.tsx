import { useParams } from "@tanstack/react-router";

// Filled out in a later build step (turn-1, the six pressures, judge-guidance, framings,
// and the reserved results region).
export function ScenarioPage() {
  const params = useParams({ strict: false });
  return (
    <p className="py-12 text-center text-default-500">
      Scenario “{params.scenarioId}” of “{params.traditionId}” — detail view coming next.
    </p>
  );
}
