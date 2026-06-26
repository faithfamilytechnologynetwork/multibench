import { FRAMING_GLOSSES, PRESSURES, PRESSURE_GLOSSES, STATED_TEMPLATE } from "../lib/constants";
import { Collapsible } from "./Collapsible";
import { Markdown } from "./Markdown";

// Editorial "about the framings" context — the one place core benchmark vocabulary appears in
// the UI. Stated is instantiated with this tradition's adherent_noun; Guided shows the
// tradition's actual guide.md (the guided-framing system prompt).
export function FramingsPanel({ adherentNoun, guide }: { adherentNoun: string; guide: string | null }) {
  const stated = STATED_TEMPLATE.replace("{adherent_noun}", adherentNoun || "adherent");
  return (
    <section className="rounded-lg border border-default-200 bg-default-50 p-3 text-sm" aria-label="Framings">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-default-500">Framings</h2>
      <dl className="mt-2 flex flex-col gap-1.5">
        <div>
          <dt className="inline font-mono font-medium">unstated: </dt>
          <dd className="inline text-default-600">{FRAMING_GLOSSES.unstated}</dd>
        </div>
        <div>
          <dt className="inline font-mono font-medium">stated: </dt>
          <dd className="inline text-default-600">“{stated}”</dd>
        </div>
        <div>
          <dt className="inline font-mono font-medium">guided: </dt>
          <dd className="inline text-default-600">
            {FRAMING_GLOSSES.guided}
            {!guide && " (this tradition has no guide.md)"}
          </dd>
        </div>
      </dl>
      {guide && (
        <div className="mt-2">
          <Collapsible title="Guided-framing system prompt (guide.md)">
            <Markdown>{guide}</Markdown>
          </Collapsible>
        </div>
      )}

      <h2 className="mt-4 text-sm font-semibold uppercase tracking-wide text-default-500">The six pressures (what each turn-2 push tests)</h2>
      <dl className="mt-2 flex flex-col gap-1">
        {PRESSURES.map((p) => (
          <div key={p}>
            <dt className="inline font-mono font-medium">{p}: </dt>
            <dd className="inline text-default-600">{PRESSURE_GLOSSES[p]}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
