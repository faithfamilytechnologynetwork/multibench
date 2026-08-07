import { useState } from "react";
import { Link } from "@tanstack/react-router";
import { useLatestSha, useResultsRuns, useRawScenario } from "../lib/queries";
import { RawComparison } from "./RawComparison";
import { Notices } from "./Notice";
import { CenteredSpinner } from "./Loading";

/**
 * The in-context results section — the MAIN pane of the scenario page (#51 verify iter-2/3): a
 * reader on `/t/<tradition>/<scenario>` (whose question, pressures, and judge guidance sit in the
 * left sidebar) sees **how each model responded on THIS question** right here (the JaleesBench
 * unification Waleed asked for).
 *
 * Perf: the ~220 KB per-scenario shard is loaded **on demand per scenario and cached** (never baked
 * into the bundle). It is **auto-engaged** (fetches on mount) rather than gated behind a click,
 * because this IS the page's main content now — a click-to-load in the primary pane would defeat the
 * single-page goal. Defaults to the most recent run. The generic explorer is one cross-link away.
 */
export function ScenarioResponses({ traditionId, scenarioId }: { traditionId: string; scenarioId: string }) {
  const sha = useLatestSha().data;
  const runsQ = useResultsRuns(sha);

  const runsSettled = !!sha && !runsQ.isLoading;
  const runId = runsQ.data?.defaultRunId ?? null;
  const scoreManifest = runsQ.data?.runs.find((r) => r.id === runId)?.manifest ?? null;
  const fingerprint = scoreManifest?.fingerprint ?? null;

  // On-demand (per scenario, cached) — fires once runs settle and a run exists.
  const on = runsSettled && !!runId;
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

  return (
    <section data-testid="scenario-responses" className="flex flex-col gap-3">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h2 className="text-lg font-semibold">How each model answered</h2>
          <p className="text-sm text-default-500">Pick a model (and, optionally, a second to compare). Each judge&rsquo;s verdict sits with the answer it scored.</p>
        </div>
        <Link
          to="/results/$runId/$groupId/$itemId"
          params={{ runId, groupId: traditionId, itemId: scenarioId }}
          className="whitespace-nowrap text-xs text-primary hover:underline"
        >
          Open in the full explorer →
        </Link>
      </div>
      <ResponsesBody rawQ={rawQ} runId={runId} traditionId={traditionId} scenarioId={scenarioId} />
    </section>
  );
}

// Newcomer hints for MultiBench's condition axes (shown as a picker title; the id stays the value).
const AXIS_HINT: Record<string, string> = {
  framing: "How the model was set up before the question (system prompt).",
  pressure: "The follow-up push after the first answer, testing whether it holds.",
};

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

      {/* Pickers — built from the catalog (subjects + condition axes); each carries a plain-language hint. */}
      <div className="flex flex-wrap items-end gap-3" data-testid="responses-pickers">
        <Picker label="Model" value={a} onChange={setSelA} hint="The AI model being tested."
          options={catalog.subjects.map((s) => ({ value: s.id, label: s.label }))} />
        <Picker label="Compare with" value={selB} onChange={setSelB} hint="Optionally show a second model side by side."
          options={[{ value: "", label: "— none —" }, ...catalog.subjects.filter((s) => s.id !== a).map((s) => ({ value: s.id, label: s.label }))]} />
        {catalog.conditionAxes.map((ax) => (
          <Picker key={ax.key} label={ax.label} value={conditions[ax.key] ?? ""} hint={AXIS_HINT[ax.key]}
            onChange={(v) => setSelCond((c) => ({ ...c, [ax.key]: v }))}
            options={ax.values.map((v) => ({ value: v.id, label: v.label }))} />
        ))}
      </div>

      {/* Plain-language score meaning, near the verdicts (numeric + ramp, no band names). */}
      <p className="text-xs text-default-500">
        Each verdict scores the answer from <span className="font-mono">{catalog.scale.min}</span> (off the
        tradition&rsquo;s guidance) to <span className="font-mono">{catalog.scale.max}</span> (well aligned);
        the colored square follows that scale.
      </p>

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

function Picker({ label, value, onChange, options, hint }: {
  label: string; value: string; onChange: (v: string) => void; options: { value: string; label: string }[]; hint?: string;
}) {
  return (
    <label className="flex flex-col text-xs font-medium text-default-500" title={hint}>
      {label}
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        aria-label={hint ? `${label} — ${hint}` : label}
        className="mt-1 rounded border border-default-200 px-2 py-1 text-sm text-default-800"
      >
        {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </label>
  );
}
