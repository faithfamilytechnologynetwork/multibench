import type { Context } from 'hono';
import { deleteCookie } from 'hono/cookie';
import type { CookieOptions } from 'hono/utils/cookie';

export const SESSION_COOKIE = 'mb_session';
export const CSRF_COOKIE = 'mb_csrf';
export const CSRF_HEADER = 'x-csrf-token';

// Cross-site cookies: the SPA and API are separate Railway origins, so the session cookie must be
// SameSite=None (+Secure). The session cookie is httpOnly (JS can't read it); the CSRF cookie is
// readable by JS so the SPA can echo it back in the CSRF header (double-submit).
export function sessionCookieOptions(expires: Date, secure: boolean): CookieOptions {
  return { httpOnly: true, secure, sameSite: 'None', path: '/', expires };
}

export function csrfCookieOptions(expires: Date, secure: boolean): CookieOptions {
  return { httpOnly: false, secure, sameSite: 'None', path: '/', expires };
}

/**
 * Clear the session + CSRF cookies. The clear MUST carry the same `Secure`/`SameSite=None`/`Path`
 * attributes used when setting — a cross-site browser rejects a Set-Cookie clear that lacks them,
 * leaving stale cookies behind.
 */
export function clearAuthCookies(c: Context, secure: boolean): void {
  const opts = { path: '/', secure, sameSite: 'None' as const };
  deleteCookie(c, SESSION_COOKIE, opts);
  deleteCookie(c, CSRF_COOKIE, opts);
}
