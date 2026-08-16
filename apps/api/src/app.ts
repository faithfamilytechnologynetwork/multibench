import { Hono } from 'hono';
import { cors } from 'hono/cors';
import type { AppDb } from './db';
import { healthRoute } from './routes/health';
import { authRoutes } from './routes/auth';
import type { AuthConfig } from './routes/auth';
import { accountRoutes } from './routes/account';
import { reviewRoutes } from './routes/review';

export interface AppOptions {
  /** Browser origins allowed to make credentialed cross-site requests. */
  allowedOrigins: string[];
  /** Auth configuration (invite code, cookie Secure flag). */
  auth: AuthConfig;
}

/**
 * Build the API app. Takes its dependencies (the database, options) as arguments so tests can inject
 * a PGlite-backed database and an arbitrary config without a live socket — Hono's `app.request()`
 * exercises the same stack the server serves.
 */
export function createApp(db: AppDb, opts: AppOptions): Hono {
  const app = new Hono();

  // Credentialed cross-site CORS: echo only allow-listed origins (never a wildcard with
  // credentials), and allow the CSRF header so the SPA can complete the double-submit check.
  app.use(
    '/api/*',
    cors({
      origin: (origin) => (opts.allowedOrigins.includes(origin) ? origin : null),
      credentials: true,
      allowHeaders: ['Content-Type', 'X-CSRF-Token'],
    }),
  );

  app.route('/api/health', healthRoute(db));
  app.route('/api/auth', authRoutes(db, opts.auth));
  app.route('/api/account', accountRoutes(db, { secureCookies: opts.auth.secureCookies }));
  app.route('/api/review', reviewRoutes(db));

  return app;
}
