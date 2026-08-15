import { sql } from 'drizzle-orm';
import type { PgDatabase } from 'drizzle-orm/pg-core';
import { drizzle as drizzleNodePg } from 'drizzle-orm/node-postgres';
import { Pool } from 'pg';
import * as schema from './schema';

/**
 * The Drizzle query handle, typed so production (node-postgres) and tests (PGlite) are interchangeable
 * and query code is written once against a common type. Drizzle is the single schema authority
 * (Spec 92 baked decision). The PGlite adapter lives in `src/testing/pglite.ts` (a test-only module)
 * so `@electric-sql/pglite` — a devDependency — never enters the production import graph.
 */
export type AppDb = PgDatabase<any, typeof schema>;

/** Production database backed by a node-postgres pool (Railway Postgres). */
export function nodePgDatabase(connectionString: string): AppDb {
  const pool = new Pool({ connectionString });
  // node-postgres emits 'error' on behalf of idle clients (backend restart, Railway Postgres
  // maintenance, network reset). Without a listener the EventEmitter throws and kills this
  // always-on process — and restartPolicyMaxRetries could then leave it down. Log and let the
  // pool recover the connection on the next query.
  pool.on('error', (err) => {
    console.error('pg pool idle-client error', err);
  });
  return drizzleNodePg(pool, { schema });
}

/** Round-trips a trivial query; throws if the database is unreachable. */
export async function ping(db: AppDb): Promise<void> {
  await db.execute(sql`select 1`);
}
