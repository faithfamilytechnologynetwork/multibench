import { pgTable, uuid, text, timestamp } from 'drizzle-orm/pg-core';
import { reviewers } from './reviewers';

/**
 * A server-side session row. The client cookie carries the raw token; only its hash is stored, so a
 * DB leak does not yield usable session tokens. Revocation is a row delete (logout); `revoked_at`
 * supports soft-revocation/audit — a session is valid only while the row exists, is unexpired, and
 * has a null `revoked_at`. FK cascades so deleting a reviewer removes their sessions.
 */
export const sessions = pgTable('sessions', {
  id: uuid('id').primaryKey().defaultRandom(),
  tokenHash: text('token_hash').notNull().unique(),
  reviewerId: uuid('reviewer_id')
    .notNull()
    .references(() => reviewers.id, { onDelete: 'cascade' }),
  createdAt: timestamp('created_at', { withTimezone: true }).notNull().defaultNow(),
  expiresAt: timestamp('expires_at', { withTimezone: true }).notNull(),
  revokedAt: timestamp('revoked_at', { withTimezone: true }),
});
