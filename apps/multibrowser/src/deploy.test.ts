import { describe, it, expect } from "vitest";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { execSync } from "node:child_process";

// Build / deploy invariants (the Phase-6 acceptance items), verified from the repo files —
// no real build/server needed. Run by vitest from apps/multibrowser (the package cwd).

// Production source only — test files and test/ helpers are NOT bundled by vite build.
function sourceFiles(dir: string): string[] {
  const out: string[] = [];
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) {
      if (name === "test") continue;
      out.push(...sourceFiles(p));
    } else if (/\.(ts|tsx)$/.test(name) && !/\.test\.(ts|tsx)$/.test(name)) {
      out.push(p);
    }
  }
  return out;
}

describe("build / deploy invariants", () => {
  it("NO source module imports tradition data — the corpus is fetched from GitHub at runtime", () => {
    for (const file of sourceFiles("src")) {
      const src = readFileSync(file, "utf8");
      // no static import that pulls in tradition content (e.g. `../../traditions/...`)
      expect(src, file).not.toMatch(/\bfrom\s+['"][^'"]*\/traditions\//);
      // and no inlined manifest/scenario yaml literals masquerading as bundled data
      expect(src, file).not.toMatch(/scenario_id_pattern:\s*['"]/);
    }
  });

  it("vite base is '/' (absolute assets so deep links resolve on a root-served host)", () => {
    const vite = readFileSync("vite.config.ts", "utf8");
    expect(vite).toMatch(/base:\s*["']\/["']/);
  });

  it("a REAL production build bakes in NO tradition data and is the SPA entry", () => {
    execSync("pnpm build", { stdio: "ignore" });
    const assetsDir = "dist/assets";
    const js = readdirSync(assetsDir)
      .filter((f) => f.endsWith(".js"))
      .map((f) => readFileSync(join(assetsDir, f), "utf8"))
      .join("\n");
    // No scenario ids or tradition prose compiled into the bundle — data is fetched at runtime.
    expect(js).not.toMatch(/JLS-\d{3}/);
    expect(js).not.toMatch(/BZ-\d{3}/);
    expect(js).not.toContain("al-jalīs"); // sunni-islam construct text
    // index.html is the SPA mount point; `serve -s dist` falls back to it for deep links.
    expect(readFileSync("dist/index.html", "utf8")).toContain('id="root"');
  }, 120_000);

  it("the start command serves the built dist with SPA history fallback", () => {
    const pkg = JSON.parse(readFileSync("package.json", "utf8")) as {
      scripts: Record<string, string>;
      dependencies: Record<string, string>;
    };
    // `serve -s dist` => `-s` is single-page mode (history fallback to index.html)
    expect(pkg.scripts.start).toMatch(/serve\s+-s\s+dist/);
    expect(pkg.dependencies.serve).toBeDefined(); // a RUNTIME dep (vite is dev-only)
  });
});
