import { Link, useParams } from "@tanstack/react-router";
import { useLatestSha, useRawCatalog } from "../lib/queries";
import { CenteredSpinner } from "../components/Loading";
import { Notice } from "../components/Notice";
import { RawPresets } from "../components/RawPresets";

/**
 * Landing for a standalone raw-only explorer (a `results-raw/<runId>/` catalog with no `results/`
 * score tier — e.g. the AFB before/after dataset, #54). Fully **catalog-generic**: every label,
 * subject, and item comes from the manifest, so no dataset-specific vocabulary lives here.
 *
 * Resolves the catalog with a `null` expected fingerprint (a raw-only run has no cross-tier score
 * partner). Renders the run-level `RawPresets` (curated deep links) PLUS a generic item index over
 * `catalog.items`, so EVERY item is reachable in-app — not only the preset entries. Each item link
 * carries `a`/`b` (the first two subjects) so the item opens as a two-column before/after, not a
 * single column (`parseRawSelection` defaults `b` to null → one column otherwise).
 */
export function RawRunPage() {
  const { runId } = useParams({ from: "/raw/$runId" });
  const shaQ = useLatestSha();
  const catQ = useRawCatalog(shaQ.data, runId, null); // raw-only: no cross-tier fingerprint to check
  const catalog = catQ.data?.catalog ?? null;
  const notices = catQ.data?.notices ?? [];

  if (!catalog && catQ.isLoading) return <CenteredSpinner label="Loading explorer…" />;
  if (!catalog) {
    return (
      <div className="flex flex-col gap-4">
        {notices.map((n, i) => <Notice key={i} notice={n} />)}
        {notices.length === 0 && (
          <Notice notice={{ severity: "error", scope: "results-raw", where: runId, message: `Explorer "${runId}" not found.` }} />
        )}
      </div>
    );
  }

  const judge = catalog.judges.find((j) => j.fullGrid)?.key ?? catalog.judges[0]?.key ?? "";
  const a = catalog.subjects[0]?.id ?? "";
  const b = catalog.subjects[1]?.id ?? "";
  const scope = catalog.scopes[0]?.id ?? "";

  return (
    <div className="flex flex-col gap-6">
      {notices.map((n, i) => <Notice key={i} notice={n} />)}
      <div>
        <h1 className="text-2xl font-semibold">{catalog.dataset.title}</h1>
        {catalog.dataset.description && <p className="text-default-500">{catalog.dataset.description}</p>}
      </div>

      <RawPresets presets={catalog.presets} runId={runId} judge={judge} />

      <section>
        <h2 className="text-lg font-semibold">{catalog.groupBy.label}</h2>
        <ul className="mt-2 grid gap-1 sm:grid-cols-2 lg:grid-cols-3" data-testid="raw-item-index">
          {catalog.items.map((it) => (
            <li key={`${it.group}/${it.id}`}>
              <Link
                to="/results/$runId/$groupId/$itemId"
                params={{ runId, groupId: it.group, itemId: it.id }}
                // a + b so the item opens as a two-column before/after (not vanilla-only single column).
                search={{ a, ...(b ? { b } : {}), scope, judge }}
                className="group flex items-baseline gap-2 rounded px-1.5 py-1 hover:bg-default-100"
              >
                <span className="w-24 shrink-0 font-mono text-xs text-primary group-hover:underline">{it.id}</span>
                <span className="truncate text-xs text-default-600" title={it.label}>{it.label}</span>
              </Link>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
