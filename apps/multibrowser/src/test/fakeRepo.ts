// Test helper: a fake GitHub backed by an in-memory file map. Builds the git-trees response
// and serves raw content / commit SHA / rate-limit responses. Used to exercise the data layer
// fully offline.

import type { TreeEntry } from "../lib/github";

export function buildTree(files: Record<string, string>): TreeEntry[] {
  const blobs = Object.keys(files);
  const dirs = new Set<string>();
  for (const p of blobs) {
    const parts = p.split("/");
    for (let i = 1; i < parts.length; i++) dirs.add(parts.slice(0, i).join("/"));
  }
  return [
    ...[...dirs].sort().map((d) => ({ path: d, type: "tree" as const })),
    ...blobs.sort().map((p) => ({ path: p, type: "blob" as const })),
  ];
}

function json(o: unknown, init?: ResponseInit): Response {
  return new Response(JSON.stringify(o), {
    status: 200,
    headers: { "content-type": "application/json" },
    ...init,
  });
}

export interface FakeOpts {
  truncated?: boolean;
  rateLimited?: boolean;
  resetEpoch?: number;
}

/** A `fetch` impl serving the given repo@sha from `files`. */
export function fakeFetch(
  repo: string,
  sha: string,
  files: Record<string, string>,
  opts: FakeOpts = {},
): typeof fetch {
  const rawPrefix = `https://raw.githubusercontent.com/${repo}/${sha}/`;
  return (async (input: RequestInfo | URL): Promise<Response> => {
    const url = typeof input === "string" ? input : input.toString();
    if (opts.rateLimited && url.startsWith("https://api.github.com")) {
      return new Response("rate limited", {
        status: 403,
        headers: { "x-ratelimit-remaining": "0", "x-ratelimit-reset": String(opts.resetEpoch ?? 0) },
      });
    }
    if (url.includes(`/repos/${repo}/commits/`)) return json({ sha });
    if (url.includes(`/repos/${repo}/git/trees/`) && url.includes("recursive=1")) {
      return json({ truncated: !!opts.truncated, tree: opts.truncated ? [] : buildTree(files) });
    }
    if (url.startsWith(rawPrefix)) {
      const path = decodeURIComponent(url.slice(rawPrefix.length));
      if (Object.prototype.hasOwnProperty.call(files, path)) {
        return new Response(files[path], { status: 200 });
      }
      return new Response("not found", { status: 404 });
    }
    return new Response("unhandled", { status: 500 });
  }) as typeof fetch;
}

/** A minimal tradition's files, parameterized by id + a couple of scenario ids. */
export function traditionFiles(id: string, scenarioIds: string[]): Record<string, string> {
  const base = `traditions/${id}`;
  const files: Record<string, string> = {
    [`${base}/tradition.yaml`]: [
      `id: ${id}`,
      `display_name: ${id.toUpperCase()}`,
      `construct: test`,
      `canonical_source: {title: T, author: A, locus_unit: bab}`,
      `adherent_noun: Adherent`,
      `maintainers: [{name: x}]`,
      `scholar_review: {status: none, reviewers: []}`,
      `taxonomies:`,
      `  pillars: {description: d, applies_to: scenario, values: [a, b]}`,
      `  hearts: {description: d, applies_to: response, values: [c, d]}`,
      `scenario_id_pattern: '^.*$'`,
      "",
    ].join("\n"),
    [`${base}/README.md`]: `# ${id}`,
    [`${base}/source.md`]: `source of ${id}`,
    [`${base}/guide.md`]: `guide of ${id}`,
    [`${base}/scenarios/index.json`]: JSON.stringify({ schema_version: 1, scenarios: scenarioIds }),
  };
  for (const sid of scenarioIds) {
    const sbase = `${base}/scenarios/${sid}`;
    files[`${sbase}/scenario.yaml`] = [
      `id: ${sid}`,
      `tags: {pillars: [a], hearts: [c]}`,
      `source_locus: 1`,
      `locus_label: Label ${sid}`,
      `identity_signal: clean`,
      "",
    ].join("\n");
    files[`${sbase}/turn1.md`] = `turn1 for ${sid}`;
    files[`${sbase}/judge-guidance.md`] = `judge guidance for ${sid}`;
    files[`${sbase}/pressures.md`] = [
      "## secularize",
      "s",
      "## insistence",
      "i",
      "## false_authority",
      "fa",
      "## good_cause",
      "gc",
      "## flattery",
      "fl",
      "## personal_appeal",
      "pa",
      "",
    ].join("\n");
  }
  return files;
}
