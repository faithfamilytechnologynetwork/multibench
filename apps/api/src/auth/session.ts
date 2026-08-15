import { randomBytes, createHash } from 'node:crypto';
import { and, eq, gt, isNull } from 'drizzle-orm';
import type { AppDb } from '../db';
import { sessions } from '../schema';

export const SESSION_TTL_MS = 1000 * 60 * 60 * 24 * 30; // 30 days

/** Only the hash of a session token is stored, so a DB leak yields no usable tokens. */
function hashToken(token: string): string {
  return createHash('sha256').update(token).digest('hex');
}

export interface CreatedSession {
  token: string;
  expiresAt: Date;
}

/** Mint a session: return the raw token (for the cookie) and store only its hash. */
export async function createSession(
  db: AppDb,
  reviewerId: string,
  now: Date = new Date(),
): Promise<CreatedSession> {
  const token = randomBytes(32).toString('base64url');
  const expiresAt = new Date(now.getTime() + SESSION_TTL_MS);
  await db.insert(sessions).values({ tokenHash: hashToken(token), reviewerId, expiresAt });
  return { token, expiresAt };
}

/** Resolve a raw token to its reviewer, honoring expiry and revocation. Null if invalid. */
export async function reviewerIdForToken(
  db: AppDb,
  token: string,
  now: Date = new Date(),
): Promise<string | null> {
  if (!token) return null;
  const rows = await db
    .select({ reviewerId: sessions.reviewerId })
    .from(sessions)
    .where(
      and(
        eq(sessions.tokenHash, hashToken(token)),
        isNull(sessions.revokedAt),
        gt(sessions.expiresAt, now),
      ),
    )
    .limit(1);
  return rows[0]?.reviewerId ?? null;
}

/** Revoke a session by deleting its row (logout). No-op for an unknown token. */
export async function deleteSession(db: AppDb, token: string): Promise<void> {
  if (!token) return;
  await db.delete(sessions).where(eq(sessions.tokenHash, hashToken(token)));
}
