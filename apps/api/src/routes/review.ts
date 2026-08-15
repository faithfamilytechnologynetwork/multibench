import { Hono } from 'hono';
import { bodyLimit } from 'hono/body-limit';
import { and, desc, eq, sql } from 'drizzle-orm';
import type { AppDb } from '../db';
import { reviews, submissions } from '../schema';
import { requireAuth } from '../middleware/auth';
import type { AppEnv } from '../middleware/auth';

/** The reviewer's current draft for one tradition, or the empty (version 0) sentinel. */
async function currentDraft(
  db: AppDb,
  reviewerId: string,
  traditionId: string,
): Promise<{ state: unknown; version: number }> {
  const rows = await db
    .select({ state: reviews.state, version: reviews.version })
    .from(reviews)
    .where(and(eq(reviews.reviewerId, reviewerId), eq(reviews.traditionId, traditionId)))
    .limit(1);
  const row = rows[0];
  return row ? { state: row.state, version: row.version } : { state: null, version: 0 };
}

/**
 * Per-tradition review DRAFT persistence with optimistic concurrency. `state` is the SPA's
 * `TraditionReview` shape, stored opaquely as JSONB (the SPA's tolerant zod owns the shape — the API
 * does not re-implement it). `version` guards cross-device conflicts: a save carrying a stale version
 * is rejected 409 with the current `{state, version}` so the client can reconcile. All routes require
 * auth (and, being non-GET, the PUT also passes the CSRF check inside `requireAuth`).
 */
export function reviewRoutes(db: AppDb): Hono<AppEnv> {
  const route = new Hono<AppEnv>();
  route.use('*', requireAuth(db));

  // List all of this reviewer's drafts (so the landing page can show real cross-device progress
  // without opening each tradition). Returns [{traditionId, state, version}].
  route.get('/', async (c) => {
    const reviewerId = c.get('reviewerId');
    const rows = await db
      .select({ traditionId: reviews.traditionId, state: reviews.state, version: reviews.version })
      .from(reviews)
      .where(eq(reviews.reviewerId, reviewerId));
    return c.json({ drafts: rows });
  });

  // Load this reviewer's draft for a tradition. Absent → {state: null, version: 0}.
  route.get('/:traditionId', async (c) => {
    const draft = await currentDraft(db, c.get('reviewerId'), c.req.param('traditionId'));
    return c.json(draft);
  });

  // Save (create or update) with optimistic concurrency. Body: {state: object, version: number}.
  // version 0 = "new draft" (insert); >0 = update only if it matches the stored version. A draft is a
  // handful of KB; cap the body so an authenticated reviewer can't store arbitrarily large JSONB.
  route.put('/:traditionId', bodyLimit({ maxSize: 512 * 1024 }), async (c) => {
    const reviewerId = c.get('reviewerId');
    const traditionId = c.req.param('traditionId');
    const body = await c.req.json().catch(() => null);
    if (
      !body ||
      typeof body !== 'object' ||
      typeof body.version !== 'number' ||
      typeof body.state !== 'object' ||
      body.state === null ||
      Array.isArray(body.state)
    ) {
      return c.json({ error: 'invalid body' }, 400);
    }
    const { state, version } = body as { state: unknown; version: number };

    if (version === 0) {
      const inserted = await db
        .insert(reviews)
        .values({ reviewerId, traditionId, state, version: 1 })
        .onConflictDoNothing({ target: [reviews.reviewerId, reviews.traditionId] })
        .returning({ version: reviews.version });
      if (inserted.length === 0) {
        return c.json({ error: 'conflict', ...(await currentDraft(db, reviewerId, traditionId)) }, 409);
      }
      return c.json({ version: inserted[0]!.version });
    }

    const updated = await db
      .update(reviews)
      .set({ state, version: sql`${reviews.version} + 1`, updatedAt: new Date() })
      .where(
        and(
          eq(reviews.reviewerId, reviewerId),
          eq(reviews.traditionId, traditionId),
          eq(reviews.version, version),
        ),
      )
      .returning({ version: reviews.version });
    if (updated.length === 0) {
      return c.json({ error: 'conflict', ...(await currentDraft(db, reviewerId, traditionId)) }, 409);
    }
    return c.json({ version: updated[0]!.version });
  });

  // Submit a review: freeze a snapshot into the immutable `submissions` table. There is NO update or
  // delete path — immutability is by construction (insert-only). Private by default; `publishedIssueUrl`
  // is set only if the reviewer explicitly opted to also publish to a public GitHub issue.
  route.post('/:traditionId/submit', bodyLimit({ maxSize: 512 * 1024 }), async (c) => {
    const reviewerId = c.get('reviewerId');
    const traditionId = c.req.param('traditionId');
    const body = await c.req.json().catch(() => null);
    if (
      !body ||
      typeof body.review !== 'object' ||
      body.review === null ||
      Array.isArray(body.review)
    ) {
      return c.json({ error: 'invalid body' }, 400);
    }
    const publishedIssueUrl =
      typeof body.publishedIssueUrl === 'string' && body.publishedIssueUrl.length > 0
        ? body.publishedIssueUrl
        : null;
    // If they opted to publish, the recorded link must be a real GitHub URL (it's rendered as a link).
    if (publishedIssueUrl !== null && !/^https:\/\/github\.com\//.test(publishedIssueUrl)) {
      return c.json({ error: 'publishedIssueUrl must be a https://github.com/ URL' }, 400);
    }
    const inserted = await db
      .insert(submissions)
      .values({ reviewerId, traditionId, review: body.review, publishedIssueUrl })
      .returning({ id: submissions.id, submittedAt: submissions.submittedAt });
    return c.json({ submission: inserted[0] }, 201);
  });

  // List this reviewer's submissions for a tradition (newest first) — metadata only, so the UI can
  // show "submitted at …" and whether it was published.
  route.get('/:traditionId/submissions', async (c) => {
    const reviewerId = c.get('reviewerId');
    const traditionId = c.req.param('traditionId');
    const rows = await db
      .select({
        id: submissions.id,
        submittedAt: submissions.submittedAt,
        publishedIssueUrl: submissions.publishedIssueUrl,
      })
      .from(submissions)
      .where(and(eq(submissions.reviewerId, reviewerId), eq(submissions.traditionId, traditionId)))
      .orderBy(desc(submissions.submittedAt));
    return c.json({ submissions: rows });
  });

  // Discard this reviewer's draft for a tradition ("start over"). Idempotent — deleting a
  // non-existent draft is a no-op 200.
  route.delete('/:traditionId', async (c) => {
    const reviewerId = c.get('reviewerId');
    const traditionId = c.req.param('traditionId');
    await db
      .delete(reviews)
      .where(and(eq(reviews.reviewerId, reviewerId), eq(reviews.traditionId, traditionId)));
    return c.json({ ok: true });
  });

  return route;
}
