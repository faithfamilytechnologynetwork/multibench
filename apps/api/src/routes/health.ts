import { Hono } from 'hono';
import { ping } from '../db';
import type { AppDb } from '../db';

/**
 * Liveness/readiness: pings the database. 200 when the DB responds, 503 when it does not — so
 * Railway's health check (railway.json `healthcheckPath`) fails a deploy that can't reach Postgres.
 */
export function healthRoute(db: AppDb): Hono {
  const route = new Hono();
  route.get('/', async (c) => {
    try {
      await ping(db);
      return c.json({ status: 'ok', db: 'up' });
    } catch {
      return c.json({ status: 'error', db: 'down' }, 503);
    }
  });
  return route;
}
