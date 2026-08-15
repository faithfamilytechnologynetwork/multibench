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
