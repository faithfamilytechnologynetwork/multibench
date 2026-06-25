import { useParams } from "@tanstack/react-router";

// Filled out in the next build step (manifest header, prose, taxonomy axes, filterable
// scenario list with progressive hydration).
export function TraditionPage() {
  const params = useParams({ strict: false });
  return (
    <p className="py-12 text-center text-default-500">
      Tradition “{params.traditionId}” — scenario list &amp; filters coming next.
    </p>
  );
}
