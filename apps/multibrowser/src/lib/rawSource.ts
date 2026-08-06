// Dual-source data layer for the #51 raw tier (Spec Decision 14).
//
// Two public sources of identical content: a same-origin BAKED bundle (`/<base>/<run>/…`,
// primary — no rate limits, no API budget) and the SHA-pinned GitHub committed tier
// (authoritative + fallback). The resolver prefers baked when present AND coherent (its
// catalog fingerprint matches the authoritative run), else falls back to GitHub with a Notice.
//
// Shards are gzip on the wire. Some hosts serve `.gz` already-decompressed (Content-Encoding),
// others hand back raw gzip bytes — so we sniff the gzip magic number and decompress only when
// still compressed (carried verbatim from jaleesbrowser datasource.ts). `manifest.json` is
// plain JSON.

import { notice, type Notice } from "./model";
import { GitHubError, RateLimitError, raw, rawBytes, type FetchImpl } from "./github";
import { isSafeRelPath, parseRawCatalog, parseRawShard, type RawCatalog, type RawShard } from "./rawModel";

/** Thrown when the browser lacks `DecompressionStream` (Safari < 16.4). Feature-detect, don't polyfill. */
export class DecompressionUnsupportedError extends Error {
  constructor() {
    super("This browser can't decompress the raw-results data (needs DecompressionStream; Safari ≥ 16.4).");
    this.name = "DecompressionUnsupportedError";
  }
}

/**
 * Decode a shard payload to text: sniff the gzip magic bytes (0x1f 0x8b) and decompress ONLY
 * when still compressed; otherwise the host already decompressed it, so decode as-is. Carried
 * verbatim from jaleesbrowser's datasource — do not "simplify" by always piping through
 * DecompressionStream (that corrupts the already-decompressed case).
 */
export async function decodeGzText(buf: ArrayBuffer): Promise<string> {
  const head = new Uint8Array(buf, 0, Math.min(2, buf.byteLength));
  const stillGzipped = head.length >= 2 && head[0] === 0x1f && head[1] === 0x8b;
  if (!stillGzipped) {
    return new TextDecoder().decode(buf);
  }
  if (typeof DecompressionStream === "undefined") {
    throw new DecompressionUnsupportedError();
  }
  const stream = new Response(buf).body!.pipeThrough(new DecompressionStream("gzip"));
  return new Response(stream).text();
}

// ---- source seam ----------------------------------------------------------------------------

/** The data-source seam: the UI/loaders depend only on this, never on fetch/host details. */
export interface RawDataSource {
  readonly kind: "baked" | "github";
  /** The catalog JSON text for a run, or null if absent (404). */
  catalogText(runId: string): Promise<string | null>;
  /** A shard's decompressed JSON text (relPath is the manifest-declared `<group>/<item>.json.gz`), or null if absent. */
  shardText(runId: string, relPath: string): Promise<string | null>;
}

const MANIFEST = "manifest.json";
const rawPath = (runId: string, rel: string) => `results-raw/${runId}/${rel}`;

/** Same-origin baked bundle (`<base>/<run>/…`, default base `data-raw`). Primary when present. */
export class BakedRawSource implements RawDataSource {
  readonly kind = "baked" as const;
  constructor(private readonly base: string = "data-raw", private readonly fetchImpl: FetchImpl = fetch) {}

  private url(runId: string, rel: string): string {
    // Root-anchored against the ORIGIN (+ Vite base) — NOT document.baseURI, which on a deep
    // route like /results/<run>/<group>/<item> would resolve to <route>/data-raw/… and miss.
    const viteBase = (import.meta.env?.BASE_URL ?? "/").replace(/\/*$/, "/");
    return new URL(`${viteBase}${this.base}/${runId}/${rel}`, location.origin).href;
  }
  async catalogText(runId: string): Promise<string | null> {
    const res = await this.fetchImpl(this.url(runId, MANIFEST));
    if (res.status === 404) return null;
    if (!res.ok) return null; // baked is best-effort; a non-OK baked read → fall back to GitHub
    return res.text();
  }
  async shardText(runId: string, relPath: string): Promise<string | null> {
    const res = await this.fetchImpl(this.url(runId, relPath));
    if (res.status === 404) return null;
    if (!res.ok) throw new Error(`baked shard ${relPath} HTTP ${res.status}`);
    return decodeGzText(await res.arrayBuffer());
  }
}

/** SHA-pinned GitHub committed tier — authoritative + fallback. */
export class GitHubRawSource implements RawDataSource {
  readonly kind = "github" as const;
  constructor(private readonly repo: string, private readonly sha: string,
              private readonly fetchImpl: FetchImpl = fetch) {}

  async catalogText(runId: string): Promise<string | null> {
    return raw(this.repo, this.sha, rawPath(runId, MANIFEST), this.fetchImpl);
  }
  async shardText(runId: string, relPath: string): Promise<string | null> {
    const buf = await rawBytes(this.repo, this.sha, rawPath(runId, relPath), this.fetchImpl);
    return buf === null ? null : decodeGzText(buf);
  }
}

// ---- resolver: baked-first, GitHub-fallback, fingerprint coherence --------------------------

export interface ResolvedRawSource {
  source: RawDataSource;
  catalog: RawCatalog | null;
  notices: Notice[];
}

/** Map a GitHub fetch error to a display-first Notice (never let it reject out of a loader). */
function errNotice(e: unknown, where: string): Notice {
  if (e instanceof RateLimitError) {
    return notice("error", "github", where, "GitHub's rate limit was reached and nothing is cached yet.");
  }
  if (e instanceof GitHubError) {
    return notice("error", "github", where, `GitHub error (${e.status}).`);
  }
  return notice("error", "results-raw", where, `couldn't load: ${(e as Error).message}`);
}

/**
 * Choose the source for a run. Uses the baked bundle ONLY when present AND provably coherent —
 * its catalog fingerprint equals `expectedFingerprint` (the authoritative score-tier fingerprint
 * for this run). Otherwise (baked absent / unreadable / unconfirmable / stale) it serves the
 * SHA-pinned GitHub tier and surfaces a `Notice` that the fallback is in use. On the GitHub path
 * it ALSO checks the fingerprint against `expectedFingerprint` so a raw↔score tier mismatch is
 * flagged. Returns the parsed catalog so the caller needn't refetch.
 */
export async function resolveRawSource(
  baked: RawDataSource,
  github: RawDataSource,
  runId: string,
  expectedFingerprint: string | null,
): Promise<ResolvedRawSource> {
  const where = rawPath(runId, MANIFEST);

  let bakedText: string | null = null;
  try {
    bakedText = await baked.catalogText(runId);
  } catch {
    bakedText = null; // baked errors → treat as absent, fall back
  }

  if (bakedText !== null) {
    const { catalog, notices: bakedNotices } = parseRawCatalog(bakedText, where);
    if (catalog && expectedFingerprint !== null && catalog.fingerprint === expectedFingerprint) {
      return { source: baked, catalog, notices: bakedNotices }; // fast path: coherent same-origin baked
    }
    const reason = !catalog
      ? "the baked data is unreadable"
      : expectedFingerprint === null
        ? "the baked data can't be confirmed (no run fingerprint)"
        : "the baked data is stale (fingerprint mismatch)";
    const gh = await loadGitHubCatalogChecked(github, runId, where, expectedFingerprint);
    return {
      source: github,
      catalog: gh.catalog,
      notices: [notice("warning", "results-raw", where, `${reason} — serving the live GitHub copy`), ...gh.notices],
    };
  }

  // baked absent → GitHub (the authoritative fallback); note that the fast path isn't in use.
  const gh = await loadGitHubCatalogChecked(github, runId, where, expectedFingerprint);
  return {
    source: github,
    catalog: gh.catalog,
    notices: [notice("warning", "results-raw", where, "no baked bundle — serving the live GitHub copy"), ...gh.notices],
  };
}

async function loadGitHubCatalogChecked(
  github: RawDataSource,
  runId: string,
  where: string,
  expectedFingerprint: string | null,
): Promise<{ catalog: RawCatalog | null; notices: Notice[] }> {
  let text: string | null;
  try {
    text = await github.catalogText(runId);
  } catch (e) {
    return { catalog: null, notices: [errNotice(e, where)] };
  }
  if (text === null) {
    return { catalog: null, notices: [notice("error", "results-raw", where, `no raw dataset for run "${runId}"`)] };
  }
  const { catalog, notices } = parseRawCatalog(text, where);
  if (catalog && expectedFingerprint !== null && catalog.fingerprint !== expectedFingerprint) {
    notices.push(notice("warning", "results-raw", where,
      "raw and score tiers disagree (fingerprint mismatch) for this run"));
  }
  return { catalog, notices };
}

/**
 * Load one scenario shard from the resolved source, fail-soft: a 404, rate-limit, decompression-
 * unsupported, malformed JSON, or version mismatch each yields `{ shard: null, notices }`, never
 * a throw.
 */
export async function loadRawShard(
  source: RawDataSource,
  runId: string,
  relPath: string,
): Promise<{ shard: RawShard | null; notices: Notice[] }> {
  const where = rawPath(runId, relPath);
  // Defensive: relPath comes from the (validated) catalog, but never splice an unsafe path into a URL.
  if (!isSafeRelPath(relPath)) {
    return { shard: null, notices: [notice("error", "results-raw", where, `unsafe shard path "${relPath}"`)] };
  }
  let text: string | null;
  try {
    text = await source.shardText(runId, relPath);
  } catch (e) {
    if (e instanceof DecompressionUnsupportedError) {
      return { shard: null, notices: [notice("error", "results-raw", where, e.message)] };
    }
    return { shard: null, notices: [errNotice(e, where)] };
  }
  if (text === null) {
    return { shard: null, notices: [notice("error", "results-raw", where, "shard not found")] };
  }
  return parseRawShard(text, where);
}
