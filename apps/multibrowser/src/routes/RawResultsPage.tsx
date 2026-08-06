import { useMemo, useState } from "react";
import { getRouteApi, Link } from "@tanstack/react-router";
import { useLatestSha, useRawScenario, useResultsRuns } from "../lib/queries";
import { asRateLimit } from "../lib/rateLimit";
import { catalogScoreColor } from "../lib/rampColor";
import type { RawCatalog, RawCell, RawShard } from "../lib/rawModel";
import { Markdown } from "../components/Markdown";
import { Collapsible } from "../components/Collapsible";
import { Notices, Notice } from "../components/Notice";
import { RateLimitBanner } from "../components/RateLimitBanner";
import { CenteredSpinner } from "../components/Loading";

const route = getRouteApi("/results/$runId/$groupId/$itemId");

/** Find the cell matching a subject + a full set of condition-axis selections. */
function findCell(shard: RawShard, subject: string, conditions: Record<string, string>): RawCell | undefined {
  return shard.cells.find(
    (c) => c.subject === subject &&
      Object.entries(conditions).every(([k, v]) => c.conditions[k] === v),
  );
}

function VerdictCard({ verdict, catalog }: { verdict: RawCell["verdicts"][number]; catalog: RawCatalog }) {
  const judge = catalog.judges.find((j) => j.key === verdict.judge);
  const scope = catalog.scopes.find((s) => s.id === verdict.scope);
  const color = catalogScoreColor(catalog.scale, catalog.ramp, verdict.score);
  return (
    <div className="rounded-md border border-default-200 p-3 flex flex-col gap-1" data-testid="verdict">
      <div className="flex items-center gap-2 text-sm">
        <span className="inline-block h-4 w-4 rounded" style={{ backgroundColor: color }} aria-hidden />
        <span className="font-mono tabular-nums">{verdict.score}</span>
        <span className="font-medium">{judge?.label ?? verdict.judge}</span>
        {judge && !judge.fullGrid && (
          <span className="rounded bg-warning-100 px-1.5 py-0.5 text-xs text-warning-700" title="honest-sample judge (not a full grid)">
            sample
          </span>
        )}
        <span className="text-default-400">· {scope?.label ?? verdict.scope}</span>
      </div>
      {verdict.summary && <p className="text-sm text-default-700">{verdict.summary}</p>}
      {verdict.rationale && (
        <Collapsible title="Rationale">
          <Markdown>{verdict.rationale}</Markdown>
        </Collapsible>
      )}
    </div>
  );
}

export function RawResultsPage() {
  const { runId, groupId, itemId } = route.useParams();
  const shaQ = useLatestSha();
  const sha = shaQ.data;
  // The score tier (#49) is consulted ONLY for an OPTIONAL coherence fingerprint — the raw view
  // does not require it. A standalone (non-MultiBench) catalog with no results/ tier still loads
  // (fingerprint null → GitHub, no coherence check). Run existence comes from the RAW catalog.
  const runsQ = useResultsRuns(sha);
  const runsSettled = !!sha && !runsQ.isLoading;
  const fingerprint = runsQ.data?.runs.find((r) => r.id === runId)?.manifest?.fingerprint ?? null;

  // Fetch the raw shard once the (optional) score manifests have settled, so `fingerprint` is
  // known (null or a value) and the baked-first coherence check isn't defeated by a first null pass.
  const rawQ = useRawScenario(runsSettled ? sha : undefined, runsSettled ? runId : undefined, groupId, itemId, fingerprint);

  const catalog = rawQ.data?.catalog ?? null;
  const shard = rawQ.data?.shard ?? null;
  const notices = rawQ.data?.notices ?? [];

  // Selection state: the first subject + the first value of each condition axis (from the catalog).
  const [subject, setSubject] = useState<string | null>(null);
  const [conditions, setConditions] = useState<Record<string, string>>({});
  const selSubject = subject ?? catalog?.subjects[0]?.id ?? "";
  const selConditions = useMemo(() => {
    if (!catalog) return {};
    const out: Record<string, string> = {};
    for (const axis of catalog.conditionAxes) out[axis.key] = conditions[axis.key] ?? axis.values[0]?.id ?? "";
    return out;
  }, [catalog, conditions]);

  const rl = asRateLimit(shaQ.error) ?? asRateLimit(runsQ.error) ?? asRateLimit(rawQ.error);
  const otherError = !rl && (shaQ.error || runsQ.error || rawQ.error);

  if ((shaQ.isLoading || runsQ.isLoading || rawQ.isLoading) && !catalog) return <CenteredSpinner label="Loading raw results…" />;
  // Rate-limit / fetch error → banner + notice (never a bare 404 for a transient failure).
  if (!catalog && (rl || otherError)) {
    return (
      <div className="flex flex-col gap-4">
        {rl && <RateLimitBanner error={rl} />}
        <Notice notice={{ severity: "error", scope: "results-raw", where: runId,
          message: rl ? "Couldn't load raw results — GitHub's rate limit was reached and nothing is cached yet."
                      : `Couldn't load raw results: ${(otherError as Error).message}` }} />
        <Link to="/results" className="text-primary hover:underline">← Results</Link>
      </div>
    );
  }
  // No raw catalog for this run — the loader added the reason to `notices`; show it + a way back.
  if (!catalog) {
    return (
      <div className="flex flex-col gap-4">
        <Notices notices={notices.length ? notices : [{ severity: "error", scope: "results-raw", where: runId, message: "No raw results for this run." }]} />
        <Link to="/results" className="text-primary hover:underline">← Results</Link>
      </div>
    );
  }
  const itemLabel = catalog.items.find((i) => i.id === itemId && i.group === groupId)?.label ?? itemId;

  const cell = shard ? findCell(shard, selSubject, selConditions) : undefined;
  const contextText = cell?.contextKey && shard ? shard.contexts[cell.contextKey] : undefined;

  return (
    <div className="flex flex-col gap-6">
      {rl && <RateLimitBanner error={rl} />}
      <nav className="flex items-center gap-3 text-sm">
        {/* Generic navigation only — no per-catalog (tradition/scenario) route is hardcoded here. */}
        <Link to="/results" className="text-primary hover:underline">← Results</Link>
        <span className="text-default-400">run {runId}</span>
      </nav>

      <header className="flex flex-col gap-1">
        <h1 className="text-xl font-semibold">{itemLabel}</h1>
        <p className="text-sm text-default-500">{catalog.groupBy.label}: {groupId} · {catalog.dataset.title}</p>
      </header>

      <Notices notices={notices} />

      {/* Selection controls — generic over the catalog's subjects + condition axes (no hardcoded axes). */}
      <section className="flex flex-wrap gap-3" data-testid="raw-controls">
        <label className="flex flex-col text-xs text-default-500">
          Subject
          <select className="mt-1 rounded border border-default-200 px-2 py-1 text-sm text-default-800"
            value={selSubject} onChange={(e) => setSubject(e.target.value)}>
            {catalog.subjects.map((s) => <option key={s.id} value={s.id}>{s.label}</option>)}
          </select>
        </label>
        {catalog.conditionAxes.map((axis) => (
          <label key={axis.key} className="flex flex-col text-xs text-default-500">
            {axis.label}
            <select className="mt-1 rounded border border-default-200 px-2 py-1 text-sm text-default-800"
              value={selConditions[axis.key]}
              onChange={(e) => setConditions((c) => ({ ...c, [axis.key]: e.target.value }))}>
              {axis.values.map((v) => <option key={v.id} value={v.id}>{v.label}</option>)}
            </select>
          </label>
        ))}
      </section>

      {!shard ? (
        <p className="text-sm text-default-500">Raw data for this scenario is unavailable — see the notices above.</p>
      ) : !cell ? (
        <Notice notice={{ severity: "warning", scope: "results-raw", where: itemId, message: "No cell for this subject / condition selection." }} />
      ) : (
        <div className="flex flex-col gap-4">
          {contextText && (
            <Collapsible title="Context — what the model was told">
              <Markdown>{contextText}</Markdown>
            </Collapsible>
          )}
          <section className="flex flex-col gap-2">
            <h2 className="text-lg font-semibold">Transcript</h2>
            {cell.transcript.map((t, i) => (
              <div key={i} className={`rounded-md p-3 ${t.role === "user" ? "bg-default-100" : "bg-primary-50"}`}>
                <div className="text-xs uppercase tracking-wide text-default-400">{t.role}</div>
                <Markdown>{t.content}</Markdown>
              </div>
            ))}
          </section>
          <section className="flex flex-col gap-2">
            <h2 className="text-lg font-semibold">Judge verdicts</h2>
            <div className="grid gap-2 sm:grid-cols-2">
              {cell.verdicts.map((v, i) => <VerdictCard key={i} verdict={v} catalog={catalog} />)}
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
