import { useState } from "react";
import { Link } from "@tanstack/react-router";
import { MessageSquareText } from "lucide-react";
import { useLatestSha, useResultsRuns, useRawScenario } from "../lib/queries";
import { RawComparison } from "./RawComparison";
import { Notices } from "./Notice";
import { CenteredSpinner } from "./Loading";

/**
 * The in-context results section on the scenario page (#51 verify iter-2): a reader on
 * `/t/<tradition>/<scenario>` — where the question, pressures, and judge guidance already are —
 * can see **how each model responded on THIS question** without leaving the page (the JaleesBench
 * unification Waleed asked for).
 *
 * Perf: the ~220 KB per-scenario shard is **lazy-loaded on expand** (the query is disabled until
 * the reader engages), so plain corpus browsing never pays for it. Defaults to the most recent run.
 * The full generic explorer (grid, presets, deep links) is one cross-link away.
 */
export function ScenarioResponses({ traditionId, scenarioId }: { traditionId: string; scenarioId: string }) {
  const sha = useLatestSha().data;
  const runsQ = useResultsRuns(sha);
  // `engaged` PERSISTS across scenario navigations (same route component, changing params) — so once
  // a reader opts in, later scenarios auto-load too. That's intended: the lazy-load guarantee is
  // "plain corpus browsing never pays," not "re-collapse on every scenario." Per-scenario shards
  // still fetch only on demand (keyed by scenario), and each is cached.
  const [engaged, setEngaged] = useState(false);

  const runsSettled = !!sha && !runsQ.isLoading;
  const runId = runsQ.data?.defaultRunId ?? null;
  const scoreManifest = runsQ.data?.runs.find((r) => r.id === runId)?.manifest ?? null;
  const fingerprint = scoreManifest?.fingerprint ?? null;

  // Lazy: the raw query only fires once engaged (undefined sha/runId → useRawScenario disabled).
  const on = engaged && runsSettled && !!runId;
  const rawQ = useRawScenario(on ? sha : undefined, on ? runId! : undefined, traditionId, scenarioId, fingerprint);

  // Don't flash a "no results" claim while runs are still loading.
  if (!sha || runsQ.isLoading) return <section data-testid="scenario-responses" />;
  if (!runId) {
    return (
      <section data-testid="scenario-responses" className="flex flex-col gap-2">
        <h2 className="text-lg font-semibold">Model responses</h2>
        <p className="text-xs italic text-default-400">
          No judging results yet — model transcripts and judge verdicts will appear here once a results run is published.
        </p>
      </section>
    );
  }

  const nSubjects = scoreManifest?.subjects.length ?? 0;
  const nConditions = scoreManifest ? scoreManifest.framings.length * scoreManifest.pressures.length : 0;
  const detail = nSubjects && nConditions ? ` — ${nSubjects} models × ${nConditions} conditions` : "";

  return (
    <section data-testid="scenario-responses" className="flex flex-col gap-3 rounded-lg border border-default-200 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-lg font-semibold">Model responses &amp; judging</h2>
        <Link
          to="/results/$runId/$groupId/$itemId"
          params={{ runId, groupId: traditionId, itemId: scenarioId }}
          className="text-xs text-primary hover:underline"
        >
          Open in the full explorer (grid, presets, deep links) →
        </Link>
      </div>

      {!engaged ? (
        <button
          type="button"
          onClick={() => setEngaged(true)}
          data-testid="responses-expand"
          className="flex items-center gap-2 self-start rounded-md border border-default-200 bg-default-50 px-3 py-2 text-sm text-default-700 transition-colors hover:border-primary hover:text-primary"
        >
          <MessageSquareText size={16} aria-hidden />
          See how each model responded on this question{detail}
        </button>
      ) : (
        <ResponsesBody rawQ={rawQ} runId={runId} traditionId={traditionId} scenarioId={scenarioId} />
      )}
    </section>
  );
}

function ResponsesBody({ rawQ, runId, traditionId, scenarioId }: {
  rawQ: ReturnType<typeof useRawScenario>;
  runId: string; traditionId: string; scenarioId: string;
}) {
  const catalog = rawQ.data?.catalog ?? null;
  const shard = rawQ.data?.shard ?? null;
  const notices = rawQ.data?.notices ?? [];
  const dataNotices = notices.filter((n) => n.kind !== "source");
  const sourceNotices = notices.filter((n) => n.kind === "source");

  // Picker state; defaults derive from the catalog so no effect is needed before it loads.
  const [selA, setSelA] = useState<string | undefined>(undefined);
  const [selB, setSelB] = useState<string>(""); // "" = single-model view
  const [selCond, setSelCond] = useState<Record<string, string>>({});

  if (rawQ.isLoading && !catalog) return <CenteredSpinner label="Loading responses…" />;
  if (!catalog) {
    return (
      <Notices notices={dataNotices.length ? dataNotices : [{ severity: "error", scope: "results-raw", where: `${traditionId}/${scenarioId}`, message: "Couldn't load the responses for this scenario." }]} />
    );
  }

  const a = selA ?? catalog.subjects[0]?.id ?? "";
  const b = selB && selB !== a ? selB : null; // never compare a model against itself
  const conditions = Object.fromEntries(
    catalog.conditionAxes.map((ax) => [ax.key, selCond[ax.key] ?? ax.values[0]?.id ?? ""]),
  );

  return (
    <div className="flex flex-col gap-3" data-testid="responses-body">
      {dataNotices.length > 0 && <Notices notices={dataNotices} />}

      {/* Pickers — built entirely from the catalog (subjects + condition axes); no MB vocab. */}
      <div className="flex flex-wrap items-end gap-3" data-testid="responses-pickers">
        <Picker label="Model" value={a} onChange={setSelA}
          options={catalog.subjects.map((s) => ({ value: s.id, label: s.label }))} />
        <Picker label="Compare with" value={selB} onChange={setSelB}
          options={[{ value: "", label: "— none —" }, ...catalog.subjects.filter((s) => s.id !== a).map((s) => ({ value: s.id, label: s.label }))]} />
        {catalog.conditionAxes.map((ax) => (
          <Picker key={ax.key} label={ax.label} value={conditions[ax.key] ?? ""}
            onChange={(v) => setSelCond((c) => ({ ...c, [ax.key]: v }))}
            options={ax.values.map((v) => ({ value: v.id, label: v.label }))} />
        ))}
      </div>

      {shard
        ? <RawComparison catalog={catalog} shard={shard} a={a} b={b} conditions={conditions} />
        : <p className="text-sm text-default-500">The responses for this scenario are unavailable — see the notices above.</p>}

      {sourceNotices.length > 0 && (
        <footer className="mt-1 flex flex-col gap-0.5 border-t border-default-100 pt-2 text-xs text-default-400" data-testid="source-notes">
          {sourceNotices.map((n, i) => <span key={i}>{n.message}</span>)}
        </footer>
      )}

      <Link
        to="/results/$runId/$groupId/$itemId"
        params={{ runId, groupId: traditionId, itemId: scenarioId }}
        className="self-start text-xs text-primary hover:underline"
      >
        Deep-link / A-B / presets in the full explorer →
      </Link>
    </div>
  );
}

function Picker({ label, value, onChange, options }: {
  label: string; value: string; onChange: (v: string) => void; options: { value: string; label: string }[];
}) {
  return (
    <label className="flex flex-col text-xs font-medium text-default-500">
      {label}
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        aria-label={label}
        className="mt-1 rounded border border-default-200 px-2 py-1 text-sm text-default-800"
      >
        {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </label>
  );
}
