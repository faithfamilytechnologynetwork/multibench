import { sql } from 'drizzle-orm';
import { drizzle as drizzleNodePg } from 'drizzle-orm/node-postgres';
import { Pool } from 'pg';

/**
 * The DB access layer, narrowed to what the scaffold needs. Routes depend on this interface, not
 * on a concrete Drizzle driver, so production (node-postgres) and tests (PGlite) are interchangeable
 * and the route layer never couples to a driver's types. Real tables + queries arrive in later
 * phases (review in Phase 2, serving tiers in Phase 5); Drizzle stays the single schema authority.
 *
 * The PGlite adapter lives in `src/testing/pglite.ts` (a test-only module) so `@electric-sql/pglite`
 * — a devDependency — never enters the production import graph via `server.ts` → `db.ts`.
 */
export interface Database {
  /** Round-trips a trivial query; throws if the database is unreachable. */
  ping(): Promise<void>;
}

/** Production database backed by a node-postgres pool (Railway Postgres). */
export function nodePgDatabase(connectionString: string): Database {
  const pool = new Pool({ connectionString });
  // node-postgres emits 'error' on behalf of idle clients (backend restart, Railway Postgres
  // maintenance, network reset). Without a listener the EventEmitter throws and kills this
  // always-on process — and restartPolicyMaxRetries could then leave it down. Log and let the
  // pool recover the connection on the next query.
  pool.on('error', (err) => {
    console.error('pg pool idle-client error', err);
  });
  const db = drizzleNodePg(pool);
  return {
    async ping() {
      await db.execute(sql`select 1`);
    },
  };
}
