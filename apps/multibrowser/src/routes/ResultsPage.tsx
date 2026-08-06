import { Fragment } from "react";
import { getRouteApi } from "@tanstack/react-router";
import { useLatestSha, useResultsRuns, useResultsRun } from "../lib/queries";
import { asRateLimit, resetLabel } from "../lib/rateLimit";
import { CenteredSpinner } from "../components/Loading";
import { Notice } from "../components/Notice";
import { RateLimitBanner } from "../components/RateLimitBanner";
import {
  parseResultsSelection,
  selectionToResultsSearch,
  type ResultsSelection,
  type SortDir,
  type SortSpec,
} from "../lib/resultsSelection";
import {
  computeLeaderboardRows,
  isSortableColumn,
  judgeModelForKey,
  rankingJudgeModel,
  sortRows,
  subjectDrilldownRows,
  type StripCell,
} from "../lib/leaderboard";
import { scoreColor, scoreTextColor } from "../lib/scoreColor";
import { notice, type Notice as NoticeT } from "../lib/model";
import type { ResultsManifest, ResultsShard } from "../lib/resultsModel";

const routeApi = getRouteApi("/results");

const FRAMING_LABEL: Record<string, string> = { unstated: "Unstated", stated: "Stated", guided: "Guided" };
const HEADLINE_COLS: { key: "initial" | "post" | "delta"; label: string }[] = [
  { key: "initial", label: "First response" },
  { key: "post", label: "Post-pressure" },
  { key: "delta", label: "Steadfastness (Δ)" },
];

/** Single-select segmented control (deep-linkable; mirrors FilterBar's Toggle look). */
function Segmented<T extends string>({
  label, options, value, onChange, testid,
}: {
  label: string;
  options: { value: T; label: string }[];
  value: T;
  onChange: (v: T) => void;
  testid: string;
}) {
  return (
    <div className="flex flex-wrap items-center gap-2" data-testid={testid}>
      <span className="text-xs font-medium text-default-500">{label}</span>
      {options.map((o) => (
        <button
          key={o.value}
          type="button"
          aria-pressed={value === o.value}
          onClick={() => onChange(o.value)}
          className={
            "rounded-full border px-2.5 py-0.5 text-xs transition-colors " +
            (value === o.value
              ? "border-primary bg-primary text-primary-foreground"
              : "border-default-200 bg-default-50 text-default-600 hover:border-default-300")
          }
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

function fmt(v: number | null): string {
  return v === null ? "—" : v.toFixed(3);
}

export function ResultsPage() {
  const search = routeApi.useSearch();
  const navigate = routeApi.useNavigate();
  const shaQ = useLatestSha();
  const runsQ = useResultsRuns(shaQ.data);

  const preSel = parseResultsSelection(search);
  const runs = runsQ.data?.runs ?? [];
  const knownRunIds = new Set(runs.map((r) => r.id));
  const runInvalid = preSel.runId != null && runsQ.data != null && !knownRunIds.has(preSel.runId);
  const runId =
    preSel.runId && knownRunIds.has(preSel.runId) ? preSel.runId : runsQ.data?.defaultRunId ?? undefined;
  const runQ = useResultsRun(shaQ.data, runId);
  const manifest = runQ.data?.manifest ?? null;

  const rl = asRateLimit(shaQ.error) ?? asRateLimit(runsQ.error) ?? asRateLimit(runQ.error);

  // Re-parse against the manifest so out-of-vocab deep links degrade to defaults.
  const sel = parseResultsSelection(search, manifest);

  const update = (patch: Partial<ResultsSelection>) =>
    navigate({ search: selectionToResultsSearch({ ...sel, ...patch }) });

  // Surface every data-layer notice (malformed/missing manifest or shard, unknown vocab, dropped
  // tradition) — display-first: the page never silently hides a problem or renders blank. Deduped
  // because the selected run's manifest notices arrive from BOTH the runs list and the loaded run.
  const seenNotice = new Set<string>();
  const dataNotices: NoticeT[] = [
    ...runs.flatMap((r) => r.notices),
    ...(runQ.data?.notices ?? []),
  ].filter((n) => {
    const k = `${n.severity}|${n.scope}|${n.where}|${n.message}`;
    if (seenNotice.has(k)) return false;
    seenNotice.add(k);
    return true;
  });
  if (runInvalid) {
    dataNotices.unshift(
      notice("warning", "results", "?run", `run "${preSel.runId}" not found — showing ${runId ?? "no run"}`),
    );
  }
  if (runQ.error && !rl) {
    dataNotices.unshift(notice("error", "results", "GitHub", `could not load run: ${(runQ.error as Error).message}`));
  }

  const loadingFirst = !runsQ.data && !rl && !shaQ.error && !runsQ.error;

  return (
    <div className="flex flex-col gap-5">
      {rl && <RateLimitBanner error={rl} />}
      <div>
        <h1 className="text-2xl font-semibold">Results</h1>
        <p className="text-default-500">
          Cross-tradition standings — the mean of per-tradition means, ranked on the full-grid Gemini judge.
          Every column is one pressure slice; sort any column, the rank stays canonical.
        </p>
      </div>

      {loadingFirst && <CenteredSpinner label="Loading results…" />}

      {runsQ.data && runsQ.data.runs.length === 0 && (
        <p className="py-12 text-center text-default-500">No results runs published in this snapshot yet.</p>
      )}

      {!runsQ.data && (rl || shaQ.error || runsQ.error) && (
        <Notice notice={{
          severity: "error", scope: "results", where: "GitHub",
          message: rl
            ? `Couldn't load results — GitHub's rate limit was reached. Live data resumes around ${resetLabel(rl)}.`
            : `Could not load results: ${((shaQ.error || runsQ.error) as Error).message}`,
        }} />
      )}

      {dataNotices.length > 0 && (
        <div className="flex flex-col gap-2" data-testid="results-notices">
          {dataNotices.slice(0, 20).map((n, i) => (
            <Notice key={`${n.where}-${i}`} notice={n} />
          ))}
        </div>
      )}

      {manifest && (
        <>
          <div className="flex flex-col gap-3 rounded-lg border border-default-200 bg-default-50/50 p-3">
            <div className="text-xs text-default-500" data-testid="results-run-label">
              Run <span className="font-mono text-default-700">{manifest.runId}</span> · exported{" "}
              {manifest.generatedAt.slice(0, 10)} · {manifest.traditions.length} traditions
            </div>
            {runs.length > 1 && (
              <Segmented
                label="Run"
                testid="sel-run"
                value={manifest.runId}
                onChange={(id) => update({ runId: id === runsQ.data?.defaultRunId ? null : id })}
                options={runs.map((r) => ({ value: r.id, label: r.id }))}
              />
            )}
            <Segmented
              label="Pressure"
              testid="sel-pressure"
              value={sel.pressure}
              onChange={(pressure) => update({ pressure })}
              options={[
                { value: manifest.pressureAll, label: "All" },
                ...manifest.pressures.map((p) => ({ value: p, label: p })),
              ]}
            />
            <Segmented
              label="Drill-down judge"
              testid="sel-judge"
              value={sel.judge}
              onChange={(judge) => update({ judge })}
              options={manifest.judges.map((j) => ({
                value: j.key,
                label: j.fullGrid ? `${j.key} (ranking)` : `${j.key} (validation)`,
              }))}
            />
          </div>

          {!manifest.judges.find((j) => j.key === sel.judge)?.fullGrid && (
            <p className="text-xs text-warning-700" data-testid="opus-caption">
              Showing <span className="font-medium">{sel.judge}</span> as the validation judge in the
              per-tradition drill-down — coverage is a sample (badged <span className="font-mono">n/N</span>).
              The leaderboard ranking always stays on the full-grid Gemini judge.
            </p>
          )}

          <Leaderboard
            manifest={manifest}
            shards={runQ.data!.shards}
            sel={sel}
            onSort={(key) => {
              const cur = sel.sort;
              const dir: SortDir = cur && cur.key === key && cur.dir === "desc" ? "asc" : "desc";
              update({ sort: { key, dir } });
            }}
            onToggleExpand={(subject) =>
              update({
                expanded: sel.expanded.includes(subject)
                  ? sel.expanded.filter((s) => s !== subject)
                  : [...sel.expanded, subject],
              })
            }
          />
        </>
      )}
    </div>
  );
}

/**
 * A sortable column header. Hoisted to module scope (NOT defined in the table's render body): a
 * component defined inside render gets a new identity each render, so React would remount the
 * `<th>`/button on every state change and drop keyboard focus after a sort activation.
 */
function SortHeader({
  colKey, label, sort, onSort,
}: {
  colKey: string;
  label: string;
  sort: SortSpec | null;
  onSort: (key: string) => void;
}) {
  const active = sort?.key === colKey;
  const ariaSort = active ? (sort!.dir === "desc" ? "descending" : "ascending") : "none";
  return (
    <th className="py-2 pr-2 font-medium" aria-sort={ariaSort} data-testid={`col-${colKey}`}>
      <button type="button" className="hover:text-primary" onClick={() => onSort(colKey)}>
        {label}
        {active ? (sort!.dir === "desc" ? " ↓" : " ↑") : ""}
      </button>
    </th>
  );
}

function ScoreCell({ value, testid }: { value: number | null; testid: string }) {
  return (
    <span
      className="inline-block min-w-16 rounded px-2 py-0.5 text-center font-mono tabular-nums"
      style={{ backgroundColor: scoreColor(value), color: scoreTextColor(value) }}
      data-testid={testid}
    >
      {fmt(value)}
    </span>
  );
}

/**
 * The per-tradition heat strip (the multi-faith upgrade): one `scoreColor` square per tradition, in
 * manifest order, whose non-null mean IS the Post column. Color is never the sole encoding — every
 * square carries a `title`/`aria-label` with the tradition and its exact value, and an uncovered
 * (null) tradition renders a visually distinct dashed square labelled "no data".
 */
function HeatStrip({ strip }: { strip: StripCell[] }) {
  return (
    <div className="flex items-center gap-0.5" role="group" aria-label="Per-tradition scores" data-testid="strip">
      {strip.map((c) => {
        const label = c.value === null ? `${c.tradition}: no data` : `${c.tradition}: ${fmt(c.value)}`;
        return (
          <span
            key={c.tradition}
            role="img"
            data-testid="strip-cell"
            data-tradition={c.tradition}
            data-empty={c.value === null ? "true" : undefined}
            title={label}
            aria-label={label}
            className={
              "inline-block h-4 w-4 rounded-sm border " +
              (c.value === null ? "border-dashed border-default-400" : "border-default-200/60")
            }
            style={{ backgroundColor: scoreColor(c.value) }}
          />
        );
      })}
    </div>
  );
}

function Leaderboard({
  manifest, shards, sel, onSort, onToggleExpand,
}: {
  manifest: ResultsManifest;
  shards: Record<string, ResultsShard>;
  sel: ResultsSelection;
  onSort: (key: string) => void;
  onToggleExpand: (subject: string) => void;
}) {
  const total = manifest.traditions.length;
  const firstFraming = manifest.framings[0] ?? "unstated";
  const rows = computeLeaderboardRows(shards, manifest, { pressure: sel.pressure });
  const display = sel.sort && isSortableColumn(manifest, sel.sort.key)
    ? sortRows(rows, sel.sort.key, sel.sort.dir)
    : rows;
  const drillJudge = judgeModelForKey(manifest, sel.judge) ?? rankingJudgeModel(manifest);
  const isSample = !manifest.judges.find((j) => j.key === sel.judge)?.fullGrid;
  const expanded = new Set(sel.expanded);

  const framingCols = manifest.framings.map((f) => ({ key: f, label: FRAMING_LABEL[f] ?? f }));
  // # + Subject + 3 headline + F framing + Traditions — the drill-down spans the whole row.
  const totalCols = 6 + framingCols.length;

  return (
    <div className="overflow-x-auto" data-testid="leaderboard-scroll">
      <table className="w-full border-collapse text-sm" data-testid="leaderboard">
        <thead>
          <tr className="border-b border-default-200 text-left text-xs uppercase text-default-500">
            <th className="py-2 pr-2 font-medium">#</th>
            <th className="py-2 pr-2 font-medium">Subject</th>
            {HEADLINE_COLS.map((c) => (
              <SortHeader key={c.key} colKey={c.key} label={c.label} sort={sel.sort} onSort={onSort} />
            ))}
            {framingCols.map((c) => (
              <SortHeader key={c.key} colKey={c.key} label={c.label} sort={sel.sort} onSort={onSort} />
            ))}
            <th className="py-2 pr-2 font-medium" title="Per-tradition Post scores, in manifest order; hover a square for its value">
              Traditions
            </th>
          </tr>
        </thead>
        <tbody>
          {display.map((r) => {
            const open = expanded.has(r.subject);
            const nContributing = r.strip.filter((c) => c.value !== null).length;
            const drill = open
              ? subjectDrilldownRows(shards, manifest, r.subject, { pressure: sel.pressure, judgeModel: drillJudge })
              : [];
            return (
              <Fragment key={r.subject}>
                <tr className="border-b border-default-100" data-testid="standings-row" data-subject={r.subject}>
                  <td className="py-2 pr-2 tabular-nums text-default-400" data-testid="standings-rank">{r.rank}</td>
                  <td className="py-2 pr-2">
                    <button
                      type="button"
                      aria-expanded={open}
                      onClick={() => onToggleExpand(r.subject)}
                      className="font-medium hover:text-primary"
                      data-testid="standings-expand"
                    >
                      {open ? "▾ " : "▸ "}{r.subject}
                    </button>
                  </td>
                  <td className="py-2 pr-2"><ScoreCell value={r.initial} testid="cell-initial" /></td>
                  <td className="py-2 pr-2"><ScoreCell value={r.post} testid="standings-score" /></td>
                  <td className="py-2 pr-2"><ScoreCell value={r.delta} testid="cell-delta" /></td>
                  {framingCols.map((c) => (
                    <td key={c.key} className="py-2 pr-2">
                      <ScoreCell value={r.byFraming[c.key] ?? null} testid={`cell-${c.key}`} />
                    </td>
                  ))}
                  <td className="py-2 pr-2">
                    <div className="flex items-center gap-2">
                      <HeatStrip strip={r.strip} />
                      <span className="tabular-nums text-default-400" data-testid="standings-kn">{nContributing}/{total}</span>
                    </div>
                  </td>
                </tr>
                {open && (
                  <tr data-testid="drilldown" data-subject={r.subject}>
                    <td colSpan={totalCols} className="pb-3">
                      <div className="rounded-md border border-default-200 bg-default-50/50 p-2">
                        <div className="mb-1 text-xs text-default-500">
                          Per-tradition ({isSample ? `${sel.judge} — validation sample` : `${sel.judge}`})
                          {drill.length === 0 && " — no data for this judge/selection"}
                        </div>
                        {drill.length > 0 && (
                          <div className="overflow-x-auto">
                            <table className="text-xs" data-testid="drill-table">
                              <thead>
                                <tr className="text-left text-default-500">
                                  <th className="pr-3 font-medium">Tradition</th>
                                  <th className="pr-2 font-medium">Init</th>
                                  <th className="pr-2 font-medium">Post</th>
                                  <th className="pr-2 font-medium">Δ</th>
                                  {framingCols.map((c) => <th key={c.key} className="pr-2 font-medium">{c.label}</th>)}
                                  <th className="pr-2 font-medium">Coverage</th>
                                </tr>
                              </thead>
                              <tbody>
                                {drill.map((d) => (
                                  <tr key={d.tradition} data-testid="drill-row" data-tradition={d.tradition}>
                                    <td className="pr-3 text-default-600">{d.tradition}</td>
                                    <td className="pr-2"><ScoreCell value={d.initial} testid="drill-initial" /></td>
                                    <td className="pr-2"><ScoreCell value={d.post} testid="drill-post" /></td>
                                    <td className="pr-2"><ScoreCell value={d.delta} testid="drill-delta" /></td>
                                    {framingCols.map((c) => (
                                      <td key={c.key} className="pr-2">
                                        <ScoreCell value={d.byFraming[c.key] ?? null} testid={`drill-${c.key}`} />
                                      </td>
                                    ))}
                                    <td className="pr-2 tabular-nums text-default-400" data-testid="drill-coverage">
                                      {d.nJudged ?? "—"}/{d.nExpected}
                                      {isSample && d.nJudged !== null && d.nJudged < d.nExpected && (
                                        <span className="ml-1 rounded bg-warning-100 px-1 text-warning-800" data-testid="sample-badge">
                                          sample
                                        </span>
                                      )}
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        )}
                      </div>
                    </td>
                  </tr>
                )}
              </Fragment>
            );
          })}
        </tbody>
      </table>
      <p className="mt-2 text-xs text-default-400">
        Headline columns cover the {FRAMING_LABEL[firstFraming] ?? firstFraming} framing (the paper's
        published slice); Post-pressure equals the {FRAMING_LABEL[firstFraming] ?? firstFraming} column by
        definition. The framing columns give each framing's post-pressure score. Δ is the matched-cell
        steadfastness. Rank is canonical (Post desc); sorting a column never re-numbers it.
      </p>
    </div>
  );
}
