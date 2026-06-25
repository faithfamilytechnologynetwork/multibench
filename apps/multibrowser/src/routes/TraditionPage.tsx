import { useMemo } from "react";
import { getRouteApi } from "@tanstack/react-router";
import { useLatestSha, useScenarioMetas, useTradition } from "../lib/queries";
import { filterAndSort, parseSelection, selectionToSearch, type Selection } from "../lib/filtering";
import { asRateLimit } from "../lib/rateLimit";
import { TraditionHeader } from "../components/TraditionHeader";
import { TaxonomyAxes } from "../components/TaxonomyAxes";
import { FilterBar } from "../components/FilterBar";
import { ScenarioList, type ListRow } from "../components/ScenarioList";
import { Collapsible } from "../components/Collapsible";
import { Markdown } from "../components/Markdown";
import { Notices, Notice } from "../components/Notice";
import { RateLimitBanner } from "../components/RateLimitBanner";
import { CenteredSpinner } from "../components/Loading";
import { NotFound } from "./NotFound";

const route = getRouteApi("/t/$traditionId");

export function TraditionPage() {
  const { traditionId } = route.useParams();
  const search = route.useSearch();
  const navigate = route.useNavigate();

  const shaQ = useLatestSha();
  const sha = shaQ.data;
  const tradQ = useTradition(sha, traditionId);
  const tradition = tradQ.data;

  const taxonomies = tradition?.manifest?.taxonomies ?? {};
  const axisNames = useMemo(() => Object.keys(taxonomies), [taxonomies]);
  const scenarioIds = tradition?.scenarioIds ?? [];

  const metas = useScenarioMetas(sha, traditionId, scenarioIds, axisNames);
  const selection = useMemo(() => parseSelection(search, axisNames), [search, axisNames]);

  const entries: ListRow[] = scenarioIds.map((sid, i) => ({
    id: sid,
    meta: metas[i]?.data?.meta ?? null,
    loading: metas[i]?.isPending ?? !sha,
  }));
  const visible = filterAndSort(entries, selection);
  const loadedAll = entries.length > 0 && entries.every((e) => !e.loading);

  const rl = asRateLimit(shaQ.error) ?? asRateLimit(tradQ.error);
  const onChange = (next: Selection) => navigate({ search: selectionToSearch(next) });

  if (tradQ.isLoading && !tradition) {
    return <CenteredSpinner label="Loading tradition…" />;
  }
  if (tradition === null) {
    return <NotFound what={`Tradition “${traditionId}”`} />;
  }
  if (!tradition) return null;

  return (
    <div className="flex flex-col gap-6">
      {rl && <RateLimitBanner error={rl} />}

      {tradition.manifest ? (
        <TraditionHeader manifest={tradition.manifest} />
      ) : (
        <div className="border-b border-default-200 pb-4">
          <h1 className="text-2xl font-semibold">{traditionId}</h1>
          <Notice
            notice={{
              severity: "error",
              scope: "tradition",
              where: `${traditionId}/tradition.yaml`,
              message: "Manifest unavailable — showing scenarios with limited metadata.",
            }}
          />
        </div>
      )}

      <Notices notices={tradition.notices} />

      <div className="flex flex-col gap-2">
        {tradition.prose.readme && (
          <Collapsible title="Overview">
            <Markdown>{tradition.prose.readme}</Markdown>
          </Collapsible>
        )}
        {tradition.prose.source && (
          <Collapsible title="Source">
            <Markdown>{tradition.prose.source}</Markdown>
          </Collapsible>
        )}
        {tradition.prose.guide && (
          <Collapsible title="Guide (the Guided-framing system prompt)">
            <Markdown>{tradition.prose.guide}</Markdown>
          </Collapsible>
        )}
      </div>

      {tradition.manifest && <TaxonomyAxes taxonomies={tradition.manifest.taxonomies} />}

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-semibold">Scenarios</h2>
        <FilterBar
          taxonomies={taxonomies}
          selection={selection}
          onChange={onChange}
          total={scenarioIds.length}
          shown={visible.length}
          loadedAll={loadedAll}
        />
        <ScenarioList traditionId={traditionId} rows={visible} />
      </section>
    </div>
  );
}
