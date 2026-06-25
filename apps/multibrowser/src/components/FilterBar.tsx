import { Search, X } from "lucide-react";
import { IDENTITY_SIGNALS } from "../lib/constants";
import { isActive, toggle, type Selection, type SortKey } from "../lib/filtering";
import type { TaxonomyAxis } from "../lib/model";

// Manifest-DRIVEN filter controls: the axis groups are generated from `taxonomies`, so this
// adapts to 2-axis or 5-axis traditions with no hardcoded vocabulary. Interactive controls use
// accessible native elements + toggle buttons (HeroUI Chips are used for read-only display).
function Toggle({
  selected,
  onClick,
  children,
}: {
  selected: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      aria-pressed={selected}
      onClick={onClick}
      className={
        "rounded-full border px-2.5 py-0.5 text-xs transition-colors " +
        (selected
          ? "border-primary bg-primary text-primary-foreground"
          : "border-default-200 bg-default-50 text-default-600 hover:border-default-300")
      }
    >
      {children}
    </button>
  );
}

export interface FilterBarProps {
  taxonomies: Record<string, TaxonomyAxis>;
  selection: Selection;
  onChange: (next: Selection) => void;
  total: number;
  shown: number;
  loadedAll: boolean;
}

export function FilterBar({ taxonomies, selection, onChange, total, shown, loadedAll }: FilterBarProps) {
  const set = (patch: Partial<Selection>) => onChange({ ...selection, ...patch });

  const toggleAxis = (axis: string, v: string) => {
    const next = toggle(selection.axes[axis] ?? [], v);
    const axes = { ...selection.axes };
    if (next.length) axes[axis] = next;
    else delete axes[axis];
    set({ axes });
  };

  const clear = () =>
    onChange({ axes: {}, identity: [], locusMin: null, locusMax: null, q: "", sort: "default" });

  return (
    <section aria-label="Filters" className="flex flex-col gap-3 rounded-lg border border-default-200 p-3">
      <div className="flex flex-wrap items-center gap-3">
        <label className="flex items-center gap-1.5 rounded-md border border-default-200 px-2">
          <Search size={14} className="text-default-400" aria-hidden />
          <input
            type="search"
            aria-label="Search scenarios"
            placeholder="Search id or label…"
            value={selection.q}
            onChange={(e) => set({ q: e.target.value })}
            className="w-44 bg-transparent py-1 text-sm outline-none"
          />
        </label>

        <label className="flex items-center gap-1 text-sm text-default-600">
          locus
          <input
            type="number"
            aria-label="Minimum source locus"
            value={selection.locusMin ?? ""}
            onChange={(e) => set({ locusMin: e.target.value === "" ? null : Number(e.target.value) })}
            className="w-16 rounded-md border border-default-200 px-1.5 py-1 text-sm"
          />
          –
          <input
            type="number"
            aria-label="Maximum source locus"
            value={selection.locusMax ?? ""}
            onChange={(e) => set({ locusMax: e.target.value === "" ? null : Number(e.target.value) })}
            className="w-16 rounded-md border border-default-200 px-1.5 py-1 text-sm"
          />
        </label>

        <label className="flex items-center gap-1 text-sm text-default-600">
          sort
          <select
            aria-label="Sort scenarios"
            value={selection.sort}
            onChange={(e) => set({ sort: e.target.value as SortKey })}
            className="rounded-md border border-default-200 px-1.5 py-1 text-sm"
          >
            <option value="default">declared order</option>
            <option value="id">id</option>
            <option value="source_locus">source locus</option>
          </select>
        </label>

        <span className="ml-auto text-sm text-default-500" data-testid="result-count">
          {shown} of {total}
          {!loadedAll && <span className="ml-1 text-default-400">(loading…)</span>}
        </span>
        {isActive(selection) && (
          <button
            type="button"
            onClick={clear}
            className="flex items-center gap-1 rounded-md px-2 py-1 text-sm text-default-500 hover:text-default-700"
          >
            <X size={14} aria-hidden /> clear
          </button>
        )}
      </div>

      <div className="flex flex-col gap-2">
        {Object.entries(taxonomies).map(([axis, def]) => (
          <div key={axis} className="flex flex-wrap items-center gap-1.5">
            <span className="mr-1 text-xs font-medium uppercase tracking-wide text-default-500">{axis}</span>
            {def.values.map((v) => (
              <Toggle key={v} selected={(selection.axes[axis] ?? []).includes(v)} onClick={() => toggleAxis(axis, v)}>
                {v}
              </Toggle>
            ))}
          </div>
        ))}
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="mr-1 text-xs font-medium uppercase tracking-wide text-default-500">identity</span>
          {IDENTITY_SIGNALS.map((v) => (
            <Toggle
              key={v}
              selected={selection.identity.includes(v)}
              onClick={() => set({ identity: toggle(selection.identity, v) })}
            >
              {v}
            </Toggle>
          ))}
        </div>
      </div>
    </section>
  );
}
