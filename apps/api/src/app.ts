import { Hono } from 'hono';
import { cors } from 'hono/cors';
import type { Database } from './db';
import { healthRoute } from './routes/health';

export interface AppOptions {
  /** Browser origins allowed to make credentialed cross-site requests. */
  allowedOrigins: string[];
}

/**
 * Build the API app. Takes its dependencies (the database, options) as arguments so tests can
 * inject a PGlite-backed database and an arbitrary origin list without a live socket — Hono's
 * `app.request()` exercises the same stack the server serves.
 */
export function createApp(db: Database, opts: AppOptions): Hono {
  const app = new Hono();

  // Credentialed cross-site CORS: echo only allow-listed origins (never a wildcard with
  // credentials). The SPA and API are separate Railway origins, so the SPA origin must be listed
  // for the Phase-2 session cookie to be sent.
  app.use(
    '/api/*',
    cors({
      origin: (origin) => (opts.allowedOrigins.includes(origin) ? origin : null),
      credentials: true,
    }),
  );

  app.route('/api/health', healthRoute(db));

  return app;
}
