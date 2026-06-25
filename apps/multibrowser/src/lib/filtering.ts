// Pure filter/sort + URL-search <-> selection mapping. The AUTHORITATIVE filter semantics live
// here and are exhaustively unit-tested; the UI is a thin driver. Axis-agnostic: it operates
// over whatever axes the manifest declares (never hardcoded).

import { z } from "zod";
import { IDENTITY_SIGNALS } from "./constants";
import type { ScenarioMeta } from "./model";

/**
 * Route-boundary search schema (spec/plan: `validateSearch: searchSchema`). Validates the flat
 * shape — each key maps to a string or string[] — and is **fail-soft**: anything invalid falls
 * back to an empty record rather than throwing. Per-axis semantic interpretation (which keys are
 * taxonomy axes vs reserved) is data-dependent and handled in `parseSelection`.
 */
export const searchSchema = z
  .record(z.string(), z.union([z.string(), z.array(z.string())]))
  .catch({});

export type SortKey = "default" | "id" | "source_locus";

/** A scenario list row: id + its (possibly not-yet-loaded) metadata. */
export interface Row {
  id: string;
  meta: ScenarioMeta | null;
}

export interface Selection {
  /** axis name -> selected values (OR within an axis; AND across axes). */
  axes: Record<string, string[]>;
  /** identity_signal values (OR). */
  identity: string[];
  locusMin: number | null;
  locusMax: number | null;
  q: string;
  sort: SortKey;
}

export const RESERVED_KEYS = ["q", "sort", "locusMin", "locusMax", "identity_signal"] as const;

type SearchValue = string | string[] | undefined;
export type SearchRecord = Record<string, string | string[]>;

function toArray(v: SearchValue): string[] {
  if (v == null) return [];
  const list = Array.isArray(v) ? v : [v];
  return [...new Set(list.map(String).filter((s) => s.length > 0))];
}

function toNum(v: SearchValue): number | null {
  const s = Array.isArray(v) ? v[0] : v;
  if (s == null || s === "") return null;
  const n = Number(s);
  return Number.isFinite(n) ? n : null;
}

function toStr(v: SearchValue): string {
  const s = Array.isArray(v) ? v[0] : v;
  return s ?? "";
}

/**
 * Read a flat URL-search record into a normalized Selection, given the tradition's declared
 * axis vocabularies. **Fail-soft (spec §5.3):** values not in an axis's declared vocabulary,
 * and identity values not in the canonical set, are DROPPED (not used to filter) so a bad deep
 * link like `?pillars=bogus` degrades to "no filter" rather than zero rows.
 */
export function parseSelection(
  search: SearchRecord,
  declaredTaxonomies: Record<string, readonly string[]>,
): Selection {
  const axes: Record<string, string[]> = {};
  for (const [name, allowed] of Object.entries(declaredTaxonomies)) {
    const vals = toArray(search[name]).filter((v) => allowed.includes(v));
    if (vals.length) axes[name] = vals;
  }
  const identity = toArray(search["identity_signal"]).filter((v) =>
    (IDENTITY_SIGNALS as readonly string[]).includes(v),
  );
  const sortRaw = toStr(search["sort"]);
  return {
    axes,
    identity,
    locusMin: toNum(search["locusMin"]),
    locusMax: toNum(search["locusMax"]),
    q: toStr(search["q"]),
    sort: sortRaw === "id" || sortRaw === "source_locus" ? sortRaw : "default",
  };
}

/** Serialize a Selection back to a flat URL-search record (omitting empty/default values). */
export function selectionToSearch(sel: Selection): SearchRecord {
  const out: SearchRecord = {};
  for (const [name, vals] of Object.entries(sel.axes)) if (vals.length) out[name] = vals;
  if (sel.identity.length) out["identity_signal"] = sel.identity;
  if (sel.locusMin != null) out["locusMin"] = String(sel.locusMin);
  if (sel.locusMax != null) out["locusMax"] = String(sel.locusMax);
  if (sel.q) out["q"] = sel.q;
  if (sel.sort !== "default") out["sort"] = sel.sort;
  return out;
}

export function isActive(sel: Selection): boolean {
  return (
    Object.keys(sel.axes).length > 0 ||
    sel.identity.length > 0 ||
    sel.locusMin != null ||
    sel.locusMax != null ||
    sel.q.trim().length > 0
  );
}

function matches(row: Row, sel: Selection): boolean {
  const meta = row.meta;
  // Taxonomy axes: OR within an axis, AND across axes. A row with no metadata (ghost/stub
  // or still-loading) carries no tags, so it fails any active positive axis filter.
  for (const [axis, selected] of Object.entries(sel.axes)) {
    const rowVals = meta?.tags[axis] ?? [];
    if (!selected.some((v) => rowVals.includes(v))) return false;
  }
  if (sel.identity.length > 0) {
    if (!meta || meta.identitySignal == null || !sel.identity.includes(meta.identitySignal)) return false;
  }
  if (sel.locusMin != null) {
    if (meta?.sourceLocus == null || meta.sourceLocus < sel.locusMin) return false;
  }
  if (sel.locusMax != null) {
    if (meta?.sourceLocus == null || meta.sourceLocus > sel.locusMax) return false;
  }
  if (sel.q.trim().length > 0) {
    const hay = `${row.id} ${meta?.locusLabel ?? ""}`.toLowerCase();
    if (!hay.includes(sel.q.trim().toLowerCase())) return false;
  }
  return true;
}

export function applyFilters<T extends Row>(rows: T[], sel: Selection): T[] {
  return rows.filter((r) => matches(r, sel));
}

/** Sort rows. `default` preserves the incoming (declared) order; `source_locus`-missing sorts last. */
export function sortRows<T extends Row>(rows: T[], sort: SortKey): T[] {
  if (sort === "default") return rows;
  const copy = [...rows];
  if (sort === "id") {
    copy.sort((a, b) => a.id.localeCompare(b.id));
  } else {
    copy.sort((a, b) => {
      const an = a.meta?.sourceLocus ?? null;
      const bn = b.meta?.sourceLocus ?? null;
      if (an == null && bn == null) return a.id.localeCompare(b.id);
      if (an == null) return 1;
      if (bn == null) return -1;
      return an - bn || a.id.localeCompare(b.id);
    });
  }
  return copy;
}

/** Filter then sort. */
export function filterAndSort<T extends Row>(rows: T[], sel: Selection): T[] {
  return sortRows(applyFilters(rows, sel), sel.sort);
}

/** Toggle a value in a list (for OR-within-axis multi-select controls). */
export function toggle(list: string[], value: string): string[] {
  return list.includes(value) ? list.filter((v) => v !== value) : [...list, value];
}
