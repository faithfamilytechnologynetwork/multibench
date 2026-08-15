import { sql } from 'drizzle-orm';
import { drizzle as drizzlePglite } from 'drizzle-orm/pglite';
import { PGlite } from '@electric-sql/pglite';
import type { Database } from '../db';

/**
 * In-process Postgres for tests — no external database required. Lives under `src/testing/` and is
 * imported ONLY by tests, so `@electric-sql/pglite` (a devDependency) never reaches the production
 * import graph.
 */
export function pgliteDatabase(): Database {
  const client = new PGlite();
  const db = drizzlePglite(client);
  return {
    async ping() {
      await db.execute(sql`select 1`);
    },
  };
}
