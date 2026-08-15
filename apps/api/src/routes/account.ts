import { Hono } from 'hono';
import { eq } from 'drizzle-orm';
import { deleteCookie } from 'hono/cookie';
import type { AppDb } from '../db';
import { reviewers } from '../schema';
import { requireAuth } from '../middleware/auth';
import type { AppEnv } from '../middleware/auth';
import { SESSION_COOKIE, CSRF_COOKIE } from '../auth/cookies';

/**
 * Account deletion (Spec 92: a trivial deletion path is sufficient at test-tool scale). Deletes the
 * reviewer row; FK `ON DELETE cascade` removes their sessions, drafts, and submissions. Behind
 * requireAuth (+CSRF for this DELETE).
 */
export function accountRoutes(db: AppDb): Hono<AppEnv> {
  const route = new Hono<AppEnv>();

  route.delete('/', requireAuth(db), async (c) => {
    const reviewerId = c.get('reviewerId');
    await db.delete(reviewers).where(eq(reviewers.id, reviewerId));
    deleteCookie(c, SESSION_COOKIE, { path: '/' });
    deleteCookie(c, CSRF_COOKIE, { path: '/' });
    return c.json({ ok: true });
  });

  return route;
}
