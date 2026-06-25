import { Chip } from "@heroui/react";
import type { ScenarioMeta } from "../lib/model";

function identityColor(sig: string | null): "success" | "warning" | "danger" | "default" {
  if (sig === "clean") return "success";
  if (sig === "leaky") return "warning";
  if (sig === "intrinsic") return "danger";
  return "default";
}

export function ScenarioHeader({ id, meta }: { id: string; meta: ScenarioMeta | null }) {
  return (
    <header className="flex flex-col gap-2 border-b border-default-200 pb-4">
      <div className="flex flex-wrap items-center gap-2">
        <h1 className="font-mono text-2xl font-semibold">{id}</h1>
        {meta?.identitySignal && (
          <Chip size="sm" variant="soft" color={identityColor(meta.identitySignal)}>
            {meta.identitySignal}
          </Chip>
        )}
        {meta?.sourceLocus != null && (
          <Chip size="sm" variant="soft" color="default">
            locus #{meta.sourceLocus}
          </Chip>
        )}
      </div>
      {meta?.locusLabel && <p className="text-default-600">{meta.locusLabel}</p>}
      {meta && Object.keys(meta.tags).length > 0 && (
        <div className="flex flex-col gap-1">
          {Object.entries(meta.tags).map(([axis, values]) => (
            <div key={axis} className="flex flex-wrap items-center gap-1">
              <span className="text-xs font-medium uppercase tracking-wide text-default-500">{axis}</span>
              {values.map((v) => (
                <Chip key={v} size="sm" variant="soft" color="default">
                  {v}
                </Chip>
              ))}
            </div>
          ))}
        </div>
      )}
    </header>
  );
}
