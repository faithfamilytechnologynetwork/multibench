import { Hono } from 'hono';
import type { Context } from 'hono';
import { eq } from 'drizzle-orm';
import { setCookie, getCookie } from 'hono/cookie';
import type { AppDb } from '../db';
import { reviewers } from '../schema';
import { hashPassword, verifyPassword } from '../auth/password';
import { checkInviteCode } from '../auth/inviteCode';
import { generateCsrfToken } from '../auth/csrf';
import { createSession, deleteSession, SESSION_TTL_MS } from '../auth/session';
import {
  SESSION_COOKIE,
  CSRF_COOKIE,
  sessionCookieOptions,
  csrfCookieOptions,
  clearAuthCookies,
} from '../auth/cookies';
import { requireAuth, requireJsonRequest, requireCsrf } from '../middleware/auth';
import type { AppEnv } from '../middleware/auth';

export interface AuthConfig {
  /** The shared signup invite code (REVIEW_INVITE_CODE). Undefined ⇒ signup is closed (fail-closed). */
  inviteCode: string | undefined;
  /** Set Secure on cookies (true in production; the SPA/API are cross-site so cookies are SameSite=None). */
  secureCookies: boolean;
}

const MIN_PASSWORD_LENGTH = 8;

/** Auth routes: signup (invite-gated), login, logout, and `me`. */
export function authRoutes(db: AppDb, config: AuthConfig): Hono<AppEnv> {
  const route = new Hono<AppEnv>();

  // Returns the CSRF token so the caller can hand it to the client in the RESPONSE BODY. The SPA runs
  // on a different origin than the API and cannot read the `mb_csrf` cookie via JS (up.railway.app is
  // a public suffix, so no shared Domain), so the token is delivered in the body; the cookie remains
  // the server-side comparison half of the double-submit.
  async function startSession(c: Context, reviewerId: string): Promise<string> {
    const { token, expiresAt } = await createSession(db, reviewerId);
    setCookie(c, SESSION_COOKIE, token, sessionCookieOptions(expiresAt, config.secureCookies));
    const csrfToken = generateCsrfToken();
    setCookie(c, CSRF_COOKIE, csrfToken, csrfCookieOptions(expiresAt, config.secureCookies));
    return csrfToken;
  }

  route.post('/signup', requireJsonRequest(), async (c) => {
    const body = await c.req.json().catch(() => null);
    if (
      !body ||
      typeof body.email !== 'string' ||
      typeof body.password !== 'string' ||
      typeof body.name !== 'string'
    ) {
      return c.json({ error: 'invalid body' }, 400);
    }
    if (!checkInviteCode(body.inviteCode, config.inviteCode)) {
      return c.json({ error: 'invalid invite code' }, 403);
    }
    const email = body.email.trim().toLowerCase();
    if (!email || body.password.length < MIN_PASSWORD_LENGTH) {
      return c.json({ error: 'email required and password must be at least 8 characters' }, 400);
    }
    const passwordHash = await hashPassword(body.password);
    // Insert with onConflictDoNothing on the unique email, then treat an empty result as "taken".
    // This is race-safe (no check-then-insert window) and returns 409 instead of a raw unique-violation
    // 500 when two signups collide.
    const inserted = await db
      .insert(reviewers)
      .values({
        email,
        passwordHash,
        name: body.name,
        background: typeof body.background === 'string' ? body.background : null,
      })
      .onConflictDoNothing({ target: reviewers.email })
      .returning({ id: reviewers.id, email: reviewers.email, name: reviewers.name });
    if (inserted.length === 0) return c.json({ error: 'email already registered' }, 409);
    const reviewer = inserted[0]!;
    const csrfToken = await startSession(c, reviewer.id);
    return c.json({ reviewer, csrfToken }, 201);
  });

  route.post('/login', requireJsonRequest(), async (c) => {
    const body = await c.req.json().catch(() => null);
    if (!body || typeof body.email !== 'string' || typeof body.password !== 'string') {
      return c.json({ error: 'invalid body' }, 400);
    }
    const email = body.email.trim().toLowerCase();
    const rows = await db.select().from(reviewers).where(eq(reviewers.email, email)).limit(1);
    const reviewer = rows[0];
    if (!reviewer || !(await verifyPassword(reviewer.passwordHash, body.password))) {
      return c.json({ error: 'invalid credentials' }, 401);
    }
    const csrfToken = await startSession(c, reviewer.id);
    return c.json({
      reviewer: { id: reviewer.id, email: reviewer.email, name: reviewer.name },
      csrfToken,
    });
  });

  // Hand the SPA a CSRF token (and ensure the paired cookie exists). Lets a reloaded page — which
  // still has the httpOnly session + csrf cookies but lost the in-memory token — recover the token to
  // echo in the X-CSRF-Token header. Unauthenticated: the token is not a secret; double-submit relies
  // on the attacker being unable to read our cookie or set our header cross-site.
  route.get('/csrf', (c) => {
    let csrfToken = getCookie(c, CSRF_COOKIE);
    if (!csrfToken) {
      csrfToken = generateCsrfToken();
      const expiresAt = new Date(new Date().getTime() + SESSION_TTL_MS);
      setCookie(c, CSRF_COOKIE, csrfToken, csrfCookieOptions(expiresAt, config.secureCookies));
    }
    return c.json({ csrfToken });
  });

  // Logout: CSRF-checked (blocks cross-site forced logout) but not behind requireAuth, so it still
  // clears cookies for an already-expired session (the csrf cookie co-expires with the session, so a
  // valid double-submit is still possible while the cookies exist).
  route.post('/logout', requireCsrf(), async (c) => {
    const token = getCookie(c, SESSION_COOKIE);
    if (token) await deleteSession(db, token);
    clearAuthCookies(c, config.secureCookies);
    return c.json({ ok: true });
  });

  route.get('/me', requireAuth(db), async (c) => {
    const reviewerId = c.get('reviewerId');
    const rows = await db
      .select({
        id: reviewers.id,
        email: reviewers.email,
        name: reviewers.name,
        background: reviewers.background,
      })
      .from(reviewers)
      .where(eq(reviewers.id, reviewerId))
      .limit(1);
    const reviewer = rows[0];
    if (!reviewer) return c.json({ error: 'unauthorized' }, 401);
    return c.json({ reviewer });
  });

  return route;
}
