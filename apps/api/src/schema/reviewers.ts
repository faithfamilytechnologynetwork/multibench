import { pgTable, uuid, text, timestamp } from 'drizzle-orm/pg-core';

/**
 * A reviewer account. `email` is both the login identifier and the contact, and is unique.
 * Model owned by Waleed (2026-08-15, final).
 */
export const reviewers = pgTable('reviewers', {
  id: uuid('id').primaryKey().defaultRandom(),
  email: text('email').notNull().unique(),
  passwordHash: text('password_hash').notNull(),
  name: text('name').notNull(),
  background: text('background'),
  createdAt: timestamp('created_at', { withTimezone: true }).notNull().defaultNow(),
});
