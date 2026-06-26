import { PRESSURES, PRESSURE_GLOSSES } from "../lib/constants";
import type { PressureMap } from "../lib/model";
import { Markdown } from "./Markdown";
import { Notice } from "./Notice";

// The six turn-2 pressure pushes, ALWAYS in canonical order. A missing/empty pressure shows an
// inline notice rather than a blank (display-first).
export function PressureSection({ pressures, where }: { pressures: PressureMap; where: string }) {
  return (
    <section className="flex flex-col gap-3" aria-label="Pressures" data-testid="pressures">
      <h2 className="text-lg font-semibold">The six pressures</h2>
      {PRESSURES.map((p) => (
        <article key={p} className="rounded-lg border border-default-200 p-3" data-pressure={p}>
          <h3 className="font-medium">
            <span className="font-mono text-sm">{p}</span>{" "}
            <span className="text-xs font-normal text-default-400">— {PRESSURE_GLOSSES[p]}</span>
          </h3>
          <div className="mt-2">
            {pressures[p] != null ? (
              <Markdown>{pressures[p] as string}</Markdown>
            ) : (
              <Notice
                notice={{
                  severity: "error",
                  scope: "section",
                  where: `${where} → ## ${p}`,
                  message: `Pressure “${p}” is missing or empty.`,
                }}
              />
            )}
          </div>
        </article>
      ))}
    </section>
  );
}
