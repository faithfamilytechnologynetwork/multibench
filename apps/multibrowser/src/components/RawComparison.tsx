import type { ReactNode } from "react";
import { catalogScoreColor } from "../lib/rampColor";
import { findCell, type RawCatalog, type RawCell, type RawShard } from "../lib/rawModel";
import { Collapsible } from "./Collapsible";
import { Markdown } from "./Markdown";

/** One judge verdict: score chip + judge (sample-badged) + scope + summary + collapsible rationale.
 *  Light treatment (a subtle tint, no heavy border box) — verdicts sit WITH the response. The score
 *  is shown as TEXT next to the color chip (never color alone); the chip carries an aria-label. */
export function VerdictCard({ verdict, catalog }: { verdict: RawCell["verdicts"][number]; catalog: RawCatalog }) {
  const judge = catalog.judges.find((j) => j.key === verdict.judge);
  return (
    <div className="flex flex-col gap-1 rounded-md bg-default-50 p-2.5" data-testid="verdict" data-judge={verdict.judge}>
      <div className="flex items-center gap-2 text-sm">
        <span className="inline-block h-4 w-4 shrink-0 rounded" role="img"
          aria-label={`score ${verdict.score}`}
          style={{ backgroundColor: catalogScoreColor(catalog.scale, catalog.ramp, verdict.score) }} />
        <span className="font-mono tabular-nums font-medium">{verdict.score}</span>
        <span className="font-medium">{judge?.label ?? verdict.judge}</span>
        {judge && !judge.fullGrid && (
          <span className="rounded bg-warning-100 px-1.5 py-0.5 text-xs text-warning-800" title="honest-sample judge — scored only a subset, not the full grid">sample</span>
        )}
      </div>
      {verdict.summary && <p className="text-sm text-default-700">{verdict.summary}</p>}
      {verdict.rationale && <Collapsible title="Why (the judge's reasoning)"><Markdown>{verdict.rationale}</Markdown></Collapsible>}
    </div>
  );
}

// ── jalees-style interleaved comparison ──────────────────────────────────────────────────────

/**
 * Two models' responses to ONE scenario cell, laid out in conversation order (a faithful port of
 * jaleesbrowser's `Comparison`): the shared USER prompts (question, then the pressure push) render
 * ONCE full-width (both models got the identical prompt); the two ASSISTANT responses sit
 * side-by-side; and the judges' verdicts are **interleaved** — the initial-scope (turn-1) verdict
 * right after the first response, the post-pressure verdict after the last. `b === null` collapses
 * to a single-model view. A missing cell/turn/verdict fails soft ("no data"), never a crash.
 *
 * Catalog-generic: subjects/scopes/scale/ramp all come from `catalog` — no MultiBench vocab.
 */
export function RawComparison({ catalog, shard, a, b, conditions }: {
  catalog: RawCatalog; shard: RawShard; a: string; b: string | null; conditions: Record<string, string>;
}) {
  const single = !b;
  const cellA = findCell(shard, a, conditions);
  const cellB = single ? undefined : findCell(shard, b!, conditions);
  const labelA = catalog.subjects.find((s) => s.id === a)?.label ?? a;
  const labelB = b ? (catalog.subjects.find((s) => s.id === b)?.label ?? b) : "";
  const maxTurns = Math.max(cellA?.transcript.length ?? 0, cellB?.transcript.length ?? 0);

  // Scope interleave (generic over any count): the FIRST scope (turn-1) sits after the first
  // assistant response; ALL remaining scopes sit after the last. With 2 scopes that's turn-1 then
  // full (the MB case); with ≥3 scopes no middle scope is ever dropped (catalog-generic invariant,
  // AFB #54); with 1 scope only the first stage renders.
  const scopes = catalog.scopes;
  const initialScope = scopes[0];
  const restScopes = scopes.slice(1);

  const roleAt = (i: number) => cellA?.transcript[i]?.role ?? cellB?.transcript[i]?.role;
  const assistantIdx: number[] = [];
  for (let i = 0; i < maxTurns; i++) if (roleAt(i) === "assistant") assistantIdx.push(i);
  const firstAssistant = assistantIdx[0];
  const lastAssistant = assistantIdx[assistantIdx.length - 1];

  // Same conditions (incl. framing) for both columns → the "what the model was told" context is shared.
  const ctxKey = cellA?.contextKey ?? cellB?.contextKey;
  const context = ctxKey ? shard.contexts[ctxKey] : undefined;

  const colGrid = single ? "" : "sm:grid-cols-2";

  const verdictStage = (scope: { id: string; label: string } | undefined, key: string): ReactNode => {
    if (!scope) return null;
    return (
      <div className="flex flex-col gap-2" data-testid="verdict-stage" data-scope={scope.id} key={key}>
        <p className="text-xs font-medium uppercase tracking-wide text-default-500" title={`scope id: ${scope.id}`}>
          How the judges scored the {scope.label.toLowerCase()}
        </p>
        <div className={`grid gap-2 ${colGrid}`}>
          <VerdictColumn cell={cellA} scope={scope.id} catalog={catalog} />
          {!single && <VerdictColumn cell={cellB} scope={scope.id} catalog={catalog} />}
        </div>
      </div>
    );
  };

  const rows: ReactNode[] = [
    <div className={`grid gap-2 ${colGrid}`} key="headers" data-testid="cmp-headers">
      <ColumnHeader label={labelA} present={!!cellA} />
      {!single && <ColumnHeader label={labelB} present={!!cellB} />}
    </div>,
  ];
  if (context) {
    rows.push(
      <Collapsible key="ctx" title="Context — what the model was told"><Markdown>{context}</Markdown></Collapsible>,
    );
  }
  for (let i = 0; i < maxTurns; i++) {
    if (roleAt(i) === "user") {
      const turn = cellA?.transcript[i] ?? cellB?.transcript[i];
      if (turn) rows.push(<SharedTurn key={`t${i}`} content={turn.content} />);
    } else {
      rows.push(
        <div className={`grid gap-2 ${colGrid}`} key={`t${i}`}>
          <TurnCell content={cellA?.transcript[i]?.content} label={labelA} />
          {!single && <TurnCell content={cellB?.transcript[i]?.content} label={labelB} />}
        </div>,
      );
      if (i === firstAssistant) rows.push(verdictStage(initialScope, `v-init-${i}`));
      if (i === lastAssistant) restScopes.forEach((sc, k) => rows.push(verdictStage(sc, `v-rest-${i}-${k}`)));
    }
  }

  return <div className="flex flex-col gap-3" data-testid="raw-comparison">{rows}</div>;
}

function ColumnHeader({ label, present }: { label: string; present: boolean }) {
  return (
    <h3 className="text-sm font-semibold text-default-700" data-testid="cmp-column">
      {label}{!present && <span className="ml-1 font-normal text-default-400">· no data</span>}
    </h3>
  );
}

function SharedTurn({ content }: { content: string }) {
  // The person's turn (question, then the pressure push). Light: a label + the text, no filled box.
  return (
    <div data-role="user">
      <div className="mb-1 text-xs font-medium uppercase tracking-wide text-default-400">They asked</div>
      <div className="text-default-600"><Markdown>{content}</Markdown></div>
    </div>
  );
}

function TurnCell({ content, label }: { content: string | undefined; label: string }) {
  if (content === undefined) return <div className="text-sm italic text-default-400" aria-hidden>no response</div>;
  // The model's answer. A left rule marks it as the response (type hierarchy, not a heavy card).
  return (
    <div className="border-l-2 border-default-200 pl-3" data-role="assistant">
      <div className="mb-1 text-xs font-medium uppercase tracking-wide text-default-500">{label} answered</div>
      <Markdown>{content}</Markdown>
    </div>
  );
}

function VerdictColumn({ cell, scope, catalog }: { cell: RawCell | undefined; scope: string; catalog: RawCatalog }) {
  const verdicts = cell?.verdicts.filter((v) => v.scope === scope) ?? [];
  if (verdicts.length === 0) return <p className="text-sm text-default-400">No verdicts for this stage.</p>;
  return <div className="flex flex-col gap-2">{verdicts.map((v, i) => <VerdictCard key={i} verdict={v} catalog={catalog} />)}</div>;
}
