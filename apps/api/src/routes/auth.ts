import { Hono } from 'hono';
import type { Context } from 'hono';
import { eq } from 'drizzle-orm';
import { setCookie, getCookie, deleteCookie } from 'hono/cookie';
import type { AppDb } from '../db';
import { reviewers } from '../schema';
import { hashPassword, verifyPassword } from '../auth/password';
import { checkInviteCode } from '../auth/inviteCode';
import { generateCsrfToken } from '../auth/csrf';
import { createSession, deleteSession } from '../auth/session';
import {
  SESSION_COOKIE,
  CSRF_COOKIE,
  sessionCookieOptions,
  csrfCookieOptions,
} from '../auth/cookies';
import { requireAuth } from '../middleware/auth';
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

  async function startSession(c: Context, reviewerId: string): Promise<void> {
    const { token, expiresAt } = await createSession(db, reviewerId);
    setCookie(c, SESSION_COOKIE, token, sessionCookieOptions(expiresAt, config.secureCookies));
    setCookie(
      c,
      CSRF_COOKIE,
      generateCsrfToken(),
      csrfCookieOptions(expiresAt, config.secureCookies),
    );
  }

  route.post('/signup', async (c) => {
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
    const existing = await db
      .select({ id: reviewers.id })
      .from(reviewers)
      .where(eq(reviewers.email, email))
      .limit(1);
    if (existing.length > 0) return c.json({ error: 'email already registered' }, 409);

    const passwordHash = await hashPassword(body.password);
    const inserted = await db
      .insert(reviewers)
      .values({
        email,
        passwordHash,
        name: body.name,
        background: typeof body.background === 'string' ? body.background : null,
      })
      .returning({ id: reviewers.id, email: reviewers.email, name: reviewers.name });
    const reviewer = inserted[0]!;
    await startSession(c, reviewer.id);
    return c.json({ reviewer }, 201);
  });

  route.post('/login', async (c) => {
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
    await startSession(c, reviewer.id);
    return c.json({ reviewer: { id: reviewer.id, email: reviewer.email, name: reviewer.name } });
  });

  // Logout clears the current session by its own cookie token. Not behind requireAuth so it always
  // clears cookies (even for an already-expired session); a CSRF-forced logout is benign.
  route.post('/logout', async (c) => {
    const token = getCookie(c, SESSION_COOKIE);
    if (token) await deleteSession(db, token);
    deleteCookie(c, SESSION_COOKIE, { path: '/' });
    deleteCookie(c, CSRF_COOKIE, { path: '/' });
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
