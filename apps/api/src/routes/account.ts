import { Hono } from 'hono';
import { eq } from 'drizzle-orm';
import type { AppDb } from '../db';
import { reviewers } from '../schema';
import { requireAuth } from '../middleware/auth';
import type { AppEnv } from '../middleware/auth';
import { clearAuthCookies } from '../auth/cookies';

export interface AccountConfig {
  /** Set Secure on cookies (must match how they were set, or the cross-site clear is rejected). */
  secureCookies: boolean;
}

/**
 * Account deletion (Spec 92: a trivial deletion path is sufficient at test-tool scale). Deletes the
 * reviewer row; FK `ON DELETE cascade` removes their sessions, drafts, and submissions. Behind
 * requireAuth (+CSRF for this DELETE).
 */
export function accountRoutes(db: AppDb, config: AccountConfig): Hono<AppEnv> {
  const route = new Hono<AppEnv>();

  route.delete('/', requireAuth(db), async (c) => {
    const reviewerId = c.get('reviewerId');
    await db.delete(reviewers).where(eq(reviewers.id, reviewerId));
    clearAuthCookies(c, config.secureCookies);
    return c.json({ ok: true });
  });

  return route;
}
