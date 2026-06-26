import { useLatestSha, useTraditions } from "../lib/queries";
import { asRateLimit, resetLabel } from "../lib/rateLimit";
import { TraditionCard } from "../components/TraditionCard";
import { RateLimitBanner } from "../components/RateLimitBanner";
import { CenteredSpinner } from "../components/Loading";
import { Notice } from "../components/Notice";

export function IndexPage() {
  const shaQ = useLatestSha();
  const traditionsQ = useTraditions(shaQ.data);
  const rl = asRateLimit(shaQ.error) ?? asRateLimit(traditionsQ.error);
  const traditions = traditionsQ.data;
  const otherError = !rl && (shaQ.error || traditionsQ.error);
  // Only spin when genuinely loading first data — NOT when an error (incl. a cold-start
  // rate-limit) means data will never arrive without a friendly fallback.
  const loadingFirst = !traditions && !rl && !otherError;

  return (
    <div className="flex flex-col gap-4">
      {rl && <RateLimitBanner error={rl} />}
      <div>
        <h1 className="text-2xl font-semibold">Traditions</h1>
        <p className="text-default-500">
          Browse MultiBench faith &amp; wisdom traditions and their scenarios — read live from GitHub.
        </p>
      </div>

      {loadingFirst && <CenteredSpinner label="Loading traditions…" />}

      {!traditions && (rl || otherError) && (
        <Notice
          notice={{
            severity: "error",
            scope: "github",
            where: "GitHub",
            message: rl
              ? `Couldn't load traditions — GitHub's rate limit was reached and nothing is cached yet. Live data resumes around ${resetLabel(rl)}.`
              : `Could not load traditions: ${(otherError as Error).message}`,
          }}
        />
      )}

      {traditions && traditions.length === 0 && (
        <p className="py-12 text-center text-default-500">No traditions found in this snapshot.</p>
      )}

      {traditions && traditions.length > 0 && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3" data-testid="tradition-grid">
          {traditions.map((t) => (
            <TraditionCard key={t.id} tradition={t} />
          ))}
        </div>
      )}
    </div>
  );
}
