import { drizzle as drizzlePglite } from 'drizzle-orm/pglite';
import { migrate } from 'drizzle-orm/pglite/migrator';
import { PGlite } from '@electric-sql/pglite';
import type { AppDb } from '../db';
import * as schema from '../schema';

/**
 * In-process Postgres for tests — no external database required. Applies the real generated migrations
 * (from `drizzle/`) so tests run against the same schema production does, and a broken migration fails
 * a test. Lives under `src/testing/` and is imported ONLY by tests, so `@electric-sql/pglite` (a
 * devDependency) never reaches the production import graph.
 */
export async function createTestDb(): Promise<AppDb> {
  const client = new PGlite();
  const db = drizzlePglite(client, { schema });
  await migrate(db, { migrationsFolder: 'drizzle' });
  return db as unknown as AppDb;
}
