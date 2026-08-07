import { PRESSURES, PRESSURE_GLOSSES } from "../lib/constants";
import type { PressureMap } from "../lib/model";
import { Markdown } from "./Markdown";
import { Notice } from "./Notice";

// The six turn-2 pressure pushes, ALWAYS in canonical order. A missing/empty pressure shows an
// inline notice rather than a blank (display-first). `compact` renders a tight accordion (each
// pressure a collapsible row) for the scenario page's sidebar, so all six fit without a mega-scroll.
export function PressureSection({ pressures, where, compact = false }: { pressures: PressureMap; where: string; compact?: boolean }) {
  if (compact) {
    return (
      <section className="flex flex-col gap-1" aria-label="Pressures" data-testid="pressures">
        <h2 className="text-sm font-semibold text-default-700">The six pushes</h2>
        <p className="text-xs text-default-400">follow-up messages that pressure the assistant to compromise — open one to read it</p>
        {PRESSURES.map((p) => (
          <details key={p} className="rounded border border-default-200" data-pressure={p}>
            <summary className="cursor-pointer px-2 py-1 text-xs">
              <span className="font-mono">{p}</span>
              <span className="ml-1 font-normal text-default-400">— {PRESSURE_GLOSSES[p]}</span>
            </summary>
            <div className="px-2 pb-2 text-xs text-default-600">
              {pressures[p] != null ? (
                <Markdown>{pressures[p] as string}</Markdown>
              ) : (
                <Notice notice={{ severity: "error", scope: "section", where: `${where} → ## ${p}`, message: `Pressure “${p}” is missing or empty.` }} />
              )}
            </div>
          </details>
        ))}
      </section>
    );
  }
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
