import { useMemo } from "react";
import { getRouteApi, Link } from "@tanstack/react-router";
import { useLatestSha, useRawScenario, useResultsRuns } from "../lib/queries";
import { asRateLimit } from "../lib/rateLimit";
import { catalogScoreColor } from "../lib/rampColor";
import { parseRawSelection, rawSelectionToSearch, type RawSelection } from "../lib/rawSelection";
import type { RawCatalog, RawCell, RawShard } from "../lib/rawModel";
import { Markdown } from "../components/Markdown";
import { Collapsible } from "../components/Collapsible";
import { Notices, Notice } from "../components/Notice";
import { RateLimitBanner } from "../components/RateLimitBanner";
import { CenteredSpinner } from "../components/Loading";

const route = getRouteApi("/results/$runId/$groupId/$itemId");

/** All condition-tuples (the cartesian product of the catalog's condition axes) — the grid columns. */
function conditionColumns(catalog: RawCatalog): Record<string, string>[] {
  let cols: Record<string, string>[] = [{}];
  for (const axis of catalog.conditionAxes) {
    cols = cols.flatMap((c) => axis.values.map((v) => ({ ...c, [axis.key]: v.id })));
  }
  return cols;
}
const condKey = (c: Record<string, string>) => Object.entries(c).map(([k, v]) => `${k}=${v}`).join("|");
const sameConditions = (a: Record<string, string>, b: Record<string, string>) =>
  Object.keys(a).length === Object.keys(b).length && Object.entries(a).every(([k, v]) => b[k] === v);

function findCell(shard: RawShard, subject: string, conditions: Record<string, string>): RawCell | undefined {
  return shard.cells.find((c) => c.subject === subject && sameConditions(c.conditions, conditions));
}
function cellScore(cell: RawCell | undefined, judge: string, scope: string): number | null {
  const v = cell?.verdicts.find((vd) => vd.judge === judge && vd.scope === scope);
  return v ? v.score : null;
}

function VerdictCard({ verdict, catalog }: { verdict: RawCell["verdicts"][number]; catalog: RawCatalog }) {
  const judge = catalog.judges.find((j) => j.key === verdict.judge);
  const scope = catalog.scopes.find((s) => s.id === verdict.scope);
  return (
    <div className="rounded-md border border-default-200 p-3 flex flex-col gap-1" data-testid="verdict">
      <div className="flex items-center gap-2 text-sm">
        <span className="inline-block h-4 w-4 rounded" style={{ backgroundColor: catalogScoreColor(catalog.scale, catalog.ramp, verdict.score) }} aria-hidden />
        <span className="font-mono tabular-nums">{verdict.score}</span>
        <span className="font-medium">{judge?.label ?? verdict.judge}</span>
        {judge && !judge.fullGrid && (
          <span className="rounded bg-warning-100 px-1.5 py-0.5 text-xs text-warning-700" title="honest-sample judge (not a full grid)">sample</span>
        )}
        <span className="text-default-400">· {scope?.label ?? verdict.scope}</span>
      </div>
      {verdict.summary && <p className="text-sm text-default-700">{verdict.summary}</p>}
      {verdict.rationale && <Collapsible title="Rationale"><Markdown>{verdict.rationale}</Markdown></Collapsible>}
    </div>
  );
}

/** One cell's detail column (context + transcript + verdicts). */
function CellDetail({ subject, catalog, shard, conditions, label }: {
  subject: string; catalog: RawCatalog; shard: RawShard; conditions: Record<string, string>; label: string;
}) {
  const cell = findCell(shard, subject, conditions);
  const subj = catalog.subjects.find((s) => s.id === subject);
  const contextText = cell?.contextKey ? shard.contexts[cell.contextKey] : undefined;
  return (
    <div className="flex flex-col gap-3" data-testid="cell-detail" data-subject={subject}>
      <h3 className="text-base font-semibold">{subj?.label ?? subject} <span className="text-xs font-normal text-default-400">({label})</span></h3>
      {!cell ? (
        <Notice notice={{ severity: "warning", scope: "results-raw", where: subject, message: "No cell for this subject / condition." }} />
      ) : (
        <>
          {contextText && <Collapsible title="Context — what the model was told"><Markdown>{contextText}</Markdown></Collapsible>}
          <div className="flex flex-col gap-2">
            {cell.transcript.map((t, i) => (
              <div key={i} className={`rounded-md p-3 ${t.role === "user" ? "bg-default-100" : "bg-primary-50"}`}>
                <div className="text-xs uppercase tracking-wide text-default-400">{t.role}</div>
                <Markdown>{t.content}</Markdown>
              </div>
            ))}
          </div>
          <div className="grid gap-2">
            {cell.verdicts.map((v, i) => <VerdictCard key={i} verdict={v} catalog={catalog} />)}
          </div>
        </>
      )}
    </div>
  );
}

export function RawResultsPage() {
  const { runId, groupId, itemId } = route.useParams();
  const search = route.useSearch();
  const navigate = route.useNavigate();

  const shaQ = useLatestSha();
  const sha = shaQ.data;
  const runsQ = useResultsRuns(sha);
  const runsSettled = !!sha && !runsQ.isLoading;
  const fingerprint = runsQ.data?.runs.find((r) => r.id === runId)?.manifest?.fingerprint ?? null;
  const rawQ = useRawScenario(runsSettled ? sha : undefined, runsSettled ? runId : undefined, groupId, itemId, fingerprint);

  const catalog = rawQ.data?.catalog ?? null;
  const shard = rawQ.data?.shard ?? null;
  const notices = rawQ.data?.notices ?? [];

  const sel: RawSelection | null = useMemo(() => (catalog ? parseRawSelection(search, catalog) : null), [catalog, search]);
  const setSel = (patch: Partial<RawSelection>) => {
    if (!sel) return;
    navigate({ search: rawSelectionToSearch({ ...sel, ...patch }) });
  };

  const rl = asRateLimit(shaQ.error) ?? asRateLimit(runsQ.error) ?? asRateLimit(rawQ.error);
  const otherError = !rl && (shaQ.error || runsQ.error || rawQ.error);

  if ((shaQ.isLoading || runsQ.isLoading || rawQ.isLoading) && !catalog) return <CenteredSpinner label="Loading raw results…" />;
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
  if (!catalog || !sel) {
    return (
      <div className="flex flex-col gap-4">
        <Notices notices={notices.length ? notices : [{ severity: "error", scope: "results-raw", where: runId, message: "No raw results for this run." }]} />
        <Link to="/results" className="text-primary hover:underline">← Results</Link>
      </div>
    );
  }

  const itemLabel = catalog.items.find((i) => i.id === itemId && i.group === groupId)?.label ?? itemId;
  const columns = conditionColumns(catalog);
  const selKey = condKey(sel.conditions);

  return (
    <div className="flex flex-col gap-6">
      {rl && <RateLimitBanner error={rl} />}
      <nav className="flex items-center gap-3 text-sm">
        <Link to="/results" className="text-primary hover:underline">← Results</Link>
        <span className="text-default-400">run {runId}</span>
      </nav>

      <header className="flex flex-col gap-1">
        <h1 className="text-xl font-semibold">{itemLabel}</h1>
        <p className="text-sm text-default-500">{catalog.groupBy.label}: {groupId} · {catalog.dataset.title}</p>
      </header>

      <Notices notices={notices} />

      {/* Judge + scope + compare controls (generic over catalog vocab). */}
      <section className="flex flex-wrap items-end gap-3" data-testid="raw-controls">
        <Pills label="Judge" value={sel.judge} options={catalog.judges.map((j) => ({ id: j.key, label: j.label }))} onSelect={(judge) => setSel({ judge })} />
        <Pills label="Scope" value={sel.scope} options={catalog.scopes.map((s) => ({ id: s.id, label: s.label }))} onSelect={(scope) => setSel({ scope })} />
        <label className="flex flex-col text-xs text-default-500">
          Compare (B)
          <select className="mt-1 rounded border border-default-200 px-2 py-1 text-sm text-default-800"
            value={sel.b ?? ""} onChange={(e) => setSel({ b: e.target.value || null })}>
            <option value="">— none —</option>
            {catalog.subjects.filter((s) => s.id !== sel.a).map((s) => <option key={s.id} value={s.id}>{s.label}</option>)}
          </select>
        </label>
      </section>

      {/* Cell-score grid: subjects × condition-tuples, colored by the catalog ramp for the selected
          judge+scope. The grid IS the navigation — click a chip to open that cell below. */}
      {shard && (
        <section className="overflow-x-auto" data-testid="score-grid">
          <table className="border-collapse text-xs">
            <thead>
              <tr>
                <th className="p-1 text-left text-default-500">subject \ condition</th>
                {columns.map((c) => (
                  <th key={condKey(c)} className="p-1 text-left font-normal text-default-400 whitespace-nowrap">
                    {Object.values(c).join(" / ")}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {catalog.subjects.map((s) => (
                <tr key={s.id}>
                  <td className="p-1 pr-2 font-medium text-default-700 whitespace-nowrap">{s.label}</td>
                  {columns.map((c) => {
                    const score = cellScore(findCell(shard, s.id, c), sel.judge, sel.scope);
                    const isA = s.id === sel.a && condKey(c) === selKey;
                    const isB = s.id === sel.b && condKey(c) === selKey;
                    return (
                      <td key={condKey(c)} className="p-0.5">
                        <button
                          type="button"
                          data-testid="grid-chip"
                          data-selected={isA ? "a" : isB ? "b" : undefined}
                          title={`${s.label} · ${Object.values(c).join(" / ")} · ${score ?? "—"}`}
                          onClick={() => setSel({ a: s.id, conditions: c })}
                          className={`h-6 w-8 rounded ${isA ? "ring-2 ring-primary" : isB ? "ring-2 ring-secondary" : ""}`}
                          style={{ backgroundColor: catalogScoreColor(catalog.scale, catalog.ramp, score) }}
                        >
                          <span className="sr-only">{score ?? "no data"}</span>
                        </button>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {/* Presets — export-computed curated deep links (may target other items). */}
      {catalog.presets.length > 0 && (
        <section className="flex flex-col gap-2" data-testid="presets">
          {catalog.presets.map((p) => (
            <div key={p.key} className="flex flex-wrap items-center gap-2 text-xs">
              <span className="font-medium text-default-600" title={p.description}>{p.label}:</span>
              {p.entries.map((e) => (
                <Link key={e.key}
                  to="/results/$runId/$groupId/$itemId"
                  params={{ runId, groupId: e.params.group, itemId: e.params.item }}
                  search={{ a: e.params.a, ...(e.params.b ? { b: e.params.b } : {}), scope: e.params.scope, judge: sel.judge, ...e.params.conditions }}
                  className="rounded bg-default-100 px-2 py-0.5 text-primary hover:underline">
                  {e.label}
                </Link>
              ))}
            </div>
          ))}
        </section>
      )}

      {/* Selected cell detail — A alone, or A vs B side by side. */}
      {!shard ? (
        <p className="text-sm text-default-500">Raw data for this item is unavailable — see the notices above.</p>
      ) : (
        <section className={`grid gap-6 ${sel.b ? "md:grid-cols-2" : ""}`} data-testid="cell-details">
          <CellDetail subject={sel.a} catalog={catalog} shard={shard} conditions={sel.conditions} label="A" />
          {sel.b && <CellDetail subject={sel.b} catalog={catalog} shard={shard} conditions={sel.conditions} label="B" />}
        </section>
      )}
    </div>
  );
}

function Pills({ label, value, options, onSelect }: {
  label: string; value: string; options: { id: string; label: string }[]; onSelect: (id: string) => void;
}) {
  return (
    <div className="flex flex-col text-xs text-default-500">
      {label}
      <div className="mt-1 flex gap-1" role="group" aria-label={label}>
        {options.map((o) => (
          <button key={o.id} type="button" onClick={() => onSelect(o.id)}
            className={`rounded px-2 py-1 text-sm ${o.id === value ? "bg-primary text-white" : "bg-default-100 text-default-700"}`}>
            {o.label}
          </button>
        ))}
      </div>
    </div>
  );
}
