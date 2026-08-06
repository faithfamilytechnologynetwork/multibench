import { getRouteApi } from "@tanstack/react-router";
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
import { computeStandings } from "../lib/leaderboard";
import { scoreColor, scoreTextColor } from "../lib/scoreColor";
import { notice, type Notice as NoticeT } from "../lib/model";

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
  // tradition) — display-first: the page never silently hides a problem or renders blank.
  const dataNotices: NoticeT[] = [
    ...runs.flatMap((r) => r.notices),
    ...(runQ.data?.notices ?? []),
  ];
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
          </div>

          <Leaderboard manifest={manifest} shards={runQ.data!.shards} sel={sel} />
        </>
      )}
    </div>
  );
}

function Leaderboard({
  manifest, shards, sel,
}: {
  manifest: NonNullable<ReturnType<typeof useResultsRun>["data"]>["manifest"];
  shards: NonNullable<ReturnType<typeof useResultsRun>["data"]>["shards"];
  sel: ResultsSelection;
}) {
  if (!manifest) return null;
  const total = manifest.traditions.length;
  const standings = computeStandings(shards, manifest, sel);
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
        {standings.map((s, i) => (
          <tr key={s.subject} className="border-b border-default-100" data-testid="standings-row"
              data-subject={s.subject}>
            <td className="py-2 pr-2 tabular-nums text-default-400">{i + 1}</td>
            <td className="py-2 pr-2 font-medium">{s.subject}</td>
            <td className="py-2 pr-2">
              <span
                className="inline-block min-w-16 rounded px-2 py-0.5 text-center font-mono tabular-nums"
                style={{ backgroundColor: scoreColor(s.value), color: scoreTextColor(s.value) }}
                data-testid="standings-score"
              >
                {fmt(s.value)}
              </span>
            </td>
            <td className="py-2 pr-2 tabular-nums text-default-500">
              {s.nContributing}/{total}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
