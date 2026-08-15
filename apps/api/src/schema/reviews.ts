import { pgTable, uuid, text, jsonb, integer, timestamp, unique } from 'drizzle-orm/pg-core';
import { reviewers } from './reviewers';

/**
 * A reviewer's in-progress DRAFT for one tradition. `state` is the existing SPA `TraditionReview` zod
 * shape stored verbatim as JSONB (sampleSeed, sampleIds, source/guide checks, scenarios map); the API
 * persists it opaquely and does not re-implement the shape. `version` drives optimistic concurrency:
 * a stale save is rejected (409) and the client reconciles. One draft per (reviewer, tradition).
 *
 * Out-of-sample review (Waleed, 2026-08-15): the `scenarios` map may hold ANY scenario id, not only
 * `sampleIds` — the SPA persistence work (PR 2) enforces "sampleIds required, not allowed" and the
 * progress/report semantics. Nothing here constrains it; JSONB stores whatever the SPA writes.
 */
export const reviews = pgTable(
  'reviews',
  {
    id: uuid('id').primaryKey().defaultRandom(),
    reviewerId: uuid('reviewer_id')
      .notNull()
      .references(() => reviewers.id, { onDelete: 'cascade' }),
    traditionId: text('tradition_id').notNull(),
    state: jsonb('state').notNull(),
    version: integer('version').notNull().default(1),
    updatedAt: timestamp('updated_at', { withTimezone: true }).notNull().defaultNow(),
  },
  (t) => [unique('reviews_reviewer_tradition_unique').on(t.reviewerId, t.traditionId)],
);
