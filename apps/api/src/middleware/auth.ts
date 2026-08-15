import type { MiddlewareHandler } from 'hono';
import { getCookie } from 'hono/cookie';
import type { AppDb } from '../db';
import { reviewerIdForToken } from '../auth/session';
import { verifyCsrfToken } from '../auth/csrf';
import { SESSION_COOKIE, CSRF_COOKIE, CSRF_HEADER } from '../auth/cookies';

/** Context shape set by `requireAuth`: the authenticated reviewer's id. */
export type AppEnv = { Variables: { reviewerId: string } };

/**
 * Gate a route on a valid session and enforce double-submit CSRF for state-changing methods. Reads
 * the httpOnly session cookie, resolves the reviewer, and rejects with 401 when absent/expired. For
 * non-GET/HEAD, the CSRF header must match the CSRF cookie (403 otherwise) — the session cookie is
 * SameSite=None, so CSRF protection is not automatic.
 */
export function requireAuth(db: AppDb): MiddlewareHandler<AppEnv> {
  return async (c, next) => {
    const token = getCookie(c, SESSION_COOKIE) ?? '';
    const reviewerId = await reviewerIdForToken(db, token);
    if (!reviewerId) return c.json({ error: 'unauthorized' }, 401);
    c.set('reviewerId', reviewerId);

    const method = c.req.method;
    if (method !== 'GET' && method !== 'HEAD') {
      const headerToken = c.req.header(CSRF_HEADER);
      const cookieToken = getCookie(c, CSRF_COOKIE);
      if (!verifyCsrfToken(headerToken, cookieToken)) return c.json({ error: 'csrf' }, 403);
    }
    await next();
  };
}
