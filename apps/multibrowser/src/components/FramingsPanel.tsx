import { FRAMINGS, FRAMING_GLOSSES, STATED_TEMPLATE } from "../lib/constants";

// Editorial "about the framings" context — the one place core benchmark vocabulary appears in
// the UI. The Stated template is instantiated with this tradition's adherent_noun.
export function FramingsPanel({ adherentNoun, hasGuide }: { adherentNoun: string; hasGuide: boolean }) {
  const stated = STATED_TEMPLATE.replace("{adherent_noun}", adherentNoun || "adherent");
  return (
    <section className="rounded-lg border border-default-200 bg-default-50 p-3 text-sm" aria-label="Framings">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-default-500">Framings</h2>
      <dl className="mt-2 flex flex-col gap-1.5">
        {FRAMINGS.map((f) => (
          <div key={f}>
            <dt className="inline font-mono font-medium">{f}: </dt>
            <dd className="inline text-default-600">
              {f === "stated" ? (
                <>“{stated}”</>
              ) : f === "guided" ? (
                <>{FRAMING_GLOSSES.guided}{hasGuide ? "" : " (this tradition has no guide.md)"}</>
              ) : (
                FRAMING_GLOSSES[f]
              )}
            </dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
