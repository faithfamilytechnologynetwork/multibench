import { Fragment, useState } from "react";
import { getRouteApi, Link } from "@tanstack/react-router";
import { useLatestSha, useResultsRuns, useResultsRun } from "../lib/queries";
import { asRateLimit, resetLabel } from "../lib/rateLimit";
import { CenteredSpinner } from "../components/Loading";
import { Notice } from "../components/Notice";
import { RateLimitBanner } from "../components/RateLimitBanner";
import {
  parseResultsSelection,
  selectionToResultsSearch,
  type Metric,
  type ResultsSelection,
} from "../lib/resultsSelection";
import {
  computeStandings,
  rankingJudgeModel,
  judgeModelForKey,
  subjectTraditionValues,
} from "../lib/leaderboard";
import { scoreColor, scoreTextColor } from "../lib/scoreColor";
import { notice, type Notice as NoticeT } from "../lib/model";
import type { ResultsManifest, ResultsShard } from "../lib/resultsModel";

const routeApi = getRouteApi("/results");

const METRIC_LABEL: Record<Metric, string> = {
  turn1: "First response",
  full: "Post-pressure",
  steadfastness: "Steadfastness (Δ)",
};
const FRAMING_LABEL: Record<string, string> = { unstated: "Unstated", stated: "Stated", guided: "Guided" };

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
            <Segmented
              label="Framing"
              testid="sel-framing"
              value={sel.framing}
              onChange={(framing) => update({ framing })}
              options={manifest.framings.map((f) => ({ value: f, label: FRAMING_LABEL[f] ?? f }))}
            />
            <Segmented
              label="Metric"
              testid="sel-metric"
              value={sel.metric}
              onChange={(metric) => update({ metric })}
              options={(["turn1", "full", "steadfastness"] as Metric[]).map((m) => ({
                value: m, label: METRIC_LABEL[m],
              }))}
            />
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

          <Leaderboard manifest={manifest} shards={runQ.data!.shards} sel={sel} />
        </>
      )}
    </div>
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

function Leaderboard({
  manifest, shards, sel,
}: {
  manifest: ResultsManifest;
  shards: Record<string, ResultsShard>;
  sel: ResultsSelection;
}) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const total = manifest.traditions.length;
  const standings = computeStandings(shards, manifest, sel);
  const drillJudge = judgeModelForKey(manifest, sel.judge) ?? rankingJudgeModel(manifest);
  const isSample = !manifest.judges.find((j) => j.key === sel.judge)?.fullGrid;

  const toggle = (subject: string) =>
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(subject)) next.delete(subject);
      else next.add(subject);
      return next;
    });

  return (
    <table className="w-full border-collapse text-sm" data-testid="leaderboard">
      <thead>
        <tr className="border-b border-default-200 text-left text-xs uppercase text-default-500">
          <th className="py-2 pr-2 font-medium">#</th>
          <th className="py-2 pr-2 font-medium">Subject</th>
          <th className="py-2 pr-2 font-medium">Score</th>
          <th className="py-2 pr-2 font-medium">Traditions</th>
        </tr>
      </thead>
      <tbody>
        {standings.map((s, i) => {
          const open = expanded.has(s.subject);
          const perTradition = open
            ? subjectTraditionValues(shards, manifest, s.subject, sel, drillJudge)
            : [];
          return (
            <Fragment key={s.subject}>
              <tr className="border-b border-default-100" data-testid="standings-row"
                  data-subject={s.subject}>
                <td className="py-2 pr-2 tabular-nums text-default-400">{i + 1}</td>
                <td className="py-2 pr-2">
                  <button
                    type="button"
                    aria-expanded={open}
                    onClick={() => toggle(s.subject)}
                    className="font-medium hover:text-primary"
                    data-testid="standings-expand"
                  >
                    {open ? "▾ " : "▸ "}{s.subject}
                  </button>
                </td>
                <td className="py-2 pr-2"><ScoreCell value={s.value} testid="standings-score" /></td>
                <td className="py-2 pr-2 tabular-nums text-default-500">{s.nContributing}/{total}</td>
              </tr>
              {open && (
                <tr data-testid="drilldown" data-subject={s.subject}>
                  <td />
                  <td colSpan={3} className="pb-3">
                    <div className="rounded-md border border-default-200 bg-default-50/50 p-2">
                      <div className="mb-1 text-xs text-default-500">
                        Per-tradition ({isSample ? `${sel.judge} — validation sample` : `${sel.judge}`})
                        {perTradition.length === 0 && " — no data for this judge/selection"}
                      </div>
                      <ul className="flex flex-col gap-1">
                        {perTradition.map((tv) => (
                          <li key={tv.tradition} className="flex items-center gap-2 text-xs"
                              data-testid="drill-row" data-tradition={tv.tradition}>
                            {/* Drill-down toward the raw browser: tradition → its scenarios →
                                each scenario's raw responses & verdicts (via ResultsRegion). */}
                            <Link to="/t/$traditionId" params={{ traditionId: tv.tradition }}
                                  className="w-40 truncate text-primary hover:underline" data-testid="drill-link">
                              {tv.tradition}
                            </Link>
                            <ScoreCell value={tv.value} testid="drill-score" />
                            <span className="tabular-nums text-default-400">
                              {tv.nJudged}/{tv.nExpected}
                            </span>
                            {isSample && tv.nJudged < tv.nExpected && (
                              <span className="rounded bg-warning-100 px-1 text-warning-800" data-testid="sample-badge">
                                sample
                              </span>
                            )}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </td>
                </tr>
              )}
            </Fragment>
          );
        })}
      </tbody>
    </table>
  );
}
