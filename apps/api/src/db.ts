import { sql } from 'drizzle-orm';
import { drizzle as drizzleNodePg } from 'drizzle-orm/node-postgres';
import { drizzle as drizzlePglite } from 'drizzle-orm/pglite';
import { Pool } from 'pg';
import { PGlite } from '@electric-sql/pglite';

/**
 * The DB access layer, narrowed to what the scaffold needs. Routes depend on this interface, not
 * on a concrete Drizzle driver, so production (node-postgres) and tests (PGlite) are interchangeable
 * and the route layer never couples to a driver's types. Real tables + queries arrive in later
 * phases (review in Phase 2, serving tiers in Phase 5); Drizzle stays the single schema authority.
 */
export interface Database {
  /** Round-trips a trivial query; throws if the database is unreachable. */
  ping(): Promise<void>;
}

/** Production database backed by a node-postgres pool (Railway Postgres). */
export function nodePgDatabase(connectionString: string): Database {
  const pool = new Pool({ connectionString });
  const db = drizzleNodePg(pool);
  return {
    async ping() {
      await db.execute(sql`select 1`);
    },
  };
}

/** In-process Postgres for tests — no external database required. */
export function pgliteDatabase(): Database {
  const client = new PGlite();
  const db = drizzlePglite(client);
  return {
    async ping() {
      await db.execute(sql`select 1`);
    },
  };
}
