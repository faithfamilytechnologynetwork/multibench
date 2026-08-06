import { describe, it, expect, beforeAll } from "vitest";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { execSync, spawn } from "node:child_process";
import { createServer } from "node:net";

/**
 * Fail fast (with a diagnostic) if `port` is already bound. A leaked `serve` grandchild from a
 * defunct worktree once squatted on this port for days — its dist was gone so it 404'd
 * everything, and new serves silently fell back to an ephemeral port, making the smoke below
 * time out with a misleading cause (#49 review). This turns that into an obvious message.
 */
async function assertPortFree(port: number): Promise<void> {
  await new Promise<void>((resolve, reject) => {
    const probe = createServer();
    probe.once("error", (err: NodeJS.ErrnoException) => {
      reject(
        err.code === "EADDRINUSE"
          ? new Error(
              `port ${port} is already in use — likely a leaked 'serve' from a defunct worktree. ` +
                `Free it: \`lsof -iTCP:${port} -sTCP:LISTEN\` then kill the PID.`,
            )
          : err,
      );
    });
    probe.once("listening", () => probe.close(() => resolve()));
    probe.listen(port, "127.0.0.1");
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

  it("the start command uses serve -s dist (SPA fallback) with serve as a RUNTIME dep", () => {
    const pkg = JSON.parse(readFileSync("package.json", "utf8")) as {
      scripts: Record<string, string>;
      dependencies: Record<string, string>;
    };
    expect(pkg.scripts.start).toMatch(/serve\s+-s\s+dist/);
    expect(pkg.dependencies.serve).toBeDefined();
  });

  it("REAL smoke: the static server returns index.html for a nested deep link (SPA fallback)", async () => {
    const port = 4199;
    // Pre-flight: a busy port means a leaked serve, not a real failure — say so up front.
    await assertPortFree(port);
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
