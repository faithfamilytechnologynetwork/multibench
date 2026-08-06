import { describe, it, expect, beforeAll } from "vitest";
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { execSync, spawn } from "node:child_process";
import { createServer } from "node:net";

/**
 * Acquire a free ephemeral port (OS-assigned via bind 0) to run the smoke server on. A FIXED
 * port would deterministically collide when two builders touch multibrowser concurrently (and a
 * leaked `serve` once squatted on a hardcoded port for days, #49 review) — an ephemeral port
 * sidesteps both. There is a tiny window between close and the server's re-bind, but ephemeral
 * ports effectively never collide there.
 */
async function getFreePort(): Promise<number> {
  return new Promise<number>((resolve, reject) => {
    const probe = createServer();
    probe.once("error", reject);
    probe.listen(0, "127.0.0.1", () => {
      const addr = probe.address();
      const port = typeof addr === "object" && addr ? addr.port : 0;
      probe.close(() => (port ? resolve(port) : reject(new Error("could not acquire a free port"))));
    });
  });
}

// Build / deploy invariants (the Phase-6 acceptance items). Some run against the repo files;
// two run a REAL production build and a REAL static server. Run by vitest from apps/multibrowser.

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
  beforeAll(() => {
    execSync("pnpm build", { stdio: "ignore" });
  }, 120_000);

  it("NO source module imports tradition data — the corpus is fetched from GitHub at runtime", () => {
    for (const file of sourceFiles("src")) {
      const src = readFileSync(file, "utf8");
      expect(src, file).not.toMatch(/\bfrom\s+['"][^'"]*\/traditions\//);
      expect(src, file).not.toMatch(/scenario_id_pattern:\s*['"]/);
    }
  });

  it("the REAL production bundle bakes in NO tradition data and is the SPA entry", () => {
    const assetsDir = "dist/assets";
    const js = readdirSync(assetsDir)
      .filter((f) => f.endsWith(".js"))
      .map((f) => readFileSync(join(assetsDir, f), "utf8"))
      .join("\n");
    expect(js).not.toMatch(/JLS-\d{3}/);
    expect(js).not.toMatch(/BZ-\d{3}/);
    expect(js).not.toContain("al-jalīs"); // sunni-islam construct text
    expect(readFileSync("dist/index.html", "utf8")).toContain('id="root"');
  });

  it("vite base is '/' (absolute assets so deep links resolve on a root-served host)", () => {
    expect(readFileSync("vite.config.ts", "utf8")).toMatch(/base:\s*["']\/["']/);
  });

  it("a normal build bundles NO baked raw tier — public/data-raw/ is deploy-only (#51)", () => {
    // The ~126 MB gz raw tier is baked into `public/data-raw/` ONLY at `railway up` time (see
    // scripts/bake-and-deploy.sh) and gitignored; a normal `pnpm build` (this test's beforeAll)
    // must not carry it into `dist/`, or every CI/dev build would balloon.
    expect(existsSync("dist/data-raw")).toBe(false);
    // And the baked dir is gitignored so it never lands in git.
    expect(readFileSync(".gitignore", "utf8")).toMatch(/public\/data-raw\//);
  });

  it("the start command uses serve -s dist (SPA fallback) with serve as a RUNTIME dep", () => {
    const pkg = JSON.parse(readFileSync("package.json", "utf8")) as {
      scripts: Record<string, string>;
      dependencies: Record<string, string>;
    };
    expect(pkg.scripts.start).toMatch(/serve\s+-s\s+dist/);
    expect(pkg.dependencies.serve).toBeDefined();
  });

  it("REAL smoke: the static server returns index.html for a nested deep link (SPA fallback)", async () => {
    const port = await getFreePort(); // ephemeral — safe under concurrent builders
    // Run the actual `start` command (serve -s dist) on a test port. `detached` makes the child
    // a process-group leader so we can reap the whole tree (serve is a grandchild of pnpm).
    const server = spawn("pnpm", ["start"], {
      env: { ...process.env, PORT: String(port) },
      stdio: "ignore",
      detached: true,
    });
    try {
      let ready = false;
      for (let i = 0; i < 60 && !ready; i++) {
        try {
          const r = await fetch(`http://localhost:${port}/`);
          if (r.ok) ready = true;
        } catch {
          /* not up yet */
        }
        if (!ready) await new Promise((res) => setTimeout(res, 250));
      }
      expect(ready, "static server did not start").toBe(true);

      // A nested route that is NOT a real file must fall back to index.html (the SPA shell).
      const deep = await fetch(`http://localhost:${port}/t/sunni-islam/JLS-001`);
      expect(deep.status).toBe(200);
      expect(await deep.text()).toContain('id="root"');
    } finally {
      // Kill the whole process GROUP so the `serve` grandchild dies with the pnpm wrapper
      // (killing only the wrapper is exactly what leaked the zombie serve before).
      try {
        if (server.pid) process.kill(-server.pid, "SIGTERM");
      } catch {
        /* group may already be gone */
      }
      server.kill();
    }
  }, 60_000);
});
