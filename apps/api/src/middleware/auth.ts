import type { MiddlewareHandler } from 'hono';
import { getCookie } from 'hono/cookie';
import type { AppDb } from '../db';
import { reviewerIdForToken } from '../auth/session';
import { verifyCsrfToken } from '../auth/csrf';
import { SESSION_COOKIE, CSRF_COOKIE, CSRF_HEADER } from '../auth/cookies';

/** Context shape set by `requireAuth`: the authenticated reviewer's id. */
export type AppEnv = { Variables: { reviewerId: string } };

/**
 * Enforce an `application/json` request body. This closes cross-site **login/signup CSRF** (session
 * fixation): a malicious origin can only send a "simple" request (which we reject here) or an
 * `application/json` one — and `application/json` is non-simple, so the browser sends a CORS preflight
 * first, which our allow-list denies for unlisted origins. So only an allow-listed origin (the real
 * SPA) can post credentials. No pre-auth token round-trip needed.
 */
export function requireJsonRequest(): MiddlewareHandler {
  return async (c, next) => {
    // Compare the MIME *essence* (the part before `;`) exactly — NOT a substring. A substring check
    // accepts `text/plain;charset=application/json`, whose essence is the CORS-safelisted `text/plain`
    // (so it triggers no preflight), reopening the cross-site login-CSRF path; `c.req.json()` would
    // then parse it regardless of content-type.
    const essence = (c.req.header('content-type') ?? '').split(';')[0]?.trim().toLowerCase() ?? '';
    if (essence !== 'application/json') {
      return c.json({ error: 'content-type must be application/json' }, 415);
    }
    await next();
  };
}

/**
 * Double-submit CSRF check for a state-changing request that is not behind `requireAuth` (e.g.
 * logout): the `X-CSRF-Token` header must match the `mb_csrf` cookie. A cross-site attacker can
 * neither read our cookie nor set our header, so a forced logout is rejected.
 */
export function requireCsrf(): MiddlewareHandler {
  return async (c, next) => {
    const headerToken = c.req.header(CSRF_HEADER);
    const cookieToken = getCookie(c, CSRF_COOKIE);
    if (!verifyCsrfToken(headerToken, cookieToken)) return c.json({ error: 'csrf' }, 403);
    await next();
  };
}

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
