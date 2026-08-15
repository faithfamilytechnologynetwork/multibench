import { describe, it, expect } from 'vitest';
import type { Hono } from 'hono';
import { createApp } from '../app';
import { createTestDb } from '../testing/pglite';
import { CSRF_COOKIE, CSRF_HEADER } from '../auth/cookies';

const auth = { inviteCode: 'test-invite', secureCookies: false };
const json = { 'Content-Type': 'application/json' };

function readCookies(res: Response): Record<string, string> {
  const out: Record<string, string> = {};
  for (const raw of res.headers.getSetCookie?.() ?? []) {
    const pair = raw.split(';')[0] ?? '';
    const eq = pair.indexOf('=');
    if (eq > 0) out[pair.slice(0, eq)] = pair.slice(eq + 1);
  }
  return out;
}
const cookieHeader = (jar: Record<string, string>) =>
  Object.entries(jar)
    .map(([k, v]) => `${k}=${v}`)
    .join('; ');

async function signedIn(app: Hono, email = 'rev@example.com') {
  const res = await app.request('/api/auth/signup', {
    method: 'POST',
    headers: json,
    body: JSON.stringify({ email, password: 'a-good-password', name: 'Rev', inviteCode: 'test-invite' }),
  });
  return readCookies(res);
}
function authed(jar: Record<string, string>, extra: Record<string, string> = {}) {
  return { Cookie: cookieHeader(jar), [CSRF_HEADER]: jar[CSRF_COOKIE] ?? '', ...extra };
}
const put = (app: Hono, jar: Record<string, string>, tid: string, payload: unknown) =>
  app.request(`/api/review/${tid}`, {
    method: 'PUT',
    headers: authed(jar, json),
    body: JSON.stringify(payload),
  });

const sampleState = (note = '') => ({
  sampleSeed: '',
  sampleIds: ['s1', 's2'],
  source: { status: 'approved', notes: note, suggestion: '' },
  guide: { status: 'unreviewed', notes: '', suggestion: '' },
  scenarios: {},
});

describe('review drafts', () => {
  it('requires auth', async () => {
    const app = createApp(await createTestDb(), { allowedOrigins: [], auth });
    expect((await app.request('/api/review/sunni-islam')).status).toBe(401);
  });

  it('creates a draft (version 0 → 1), then reads it back', async () => {
    const app = createApp(await createTestDb(), { allowedOrigins: [], auth });
    const jar = await signedIn(app);
    const created = await put(app, jar, 'sunni-islam', { state: sampleState('hi'), version: 0 });
    expect(created.status).toBe(200);
    expect(((await created.json()) as any).version).toBe(1);

    const got = await app.request('/api/review/sunni-islam', { headers: { Cookie: cookieHeader(jar) } });
    const body = (await got.json()) as any;
    expect(body.version).toBe(1);
    expect(body.state.source.notes).toBe('hi');
  });

  it('updates on a matching version and rejects a stale one with 409 + current', async () => {
    const app = createApp(await createTestDb(), { allowedOrigins: [], auth });
    const jar = await signedIn(app);
    await put(app, jar, 'sunni-islam', { state: sampleState('v1'), version: 0 }); // → v1

    const ok = await put(app, jar, 'sunni-islam', { state: sampleState('v2'), version: 1 }); // → v2
    expect(ok.status).toBe(200);
    expect(((await ok.json()) as any).version).toBe(2);

    // A save that still thinks it's on v1 is stale → 409 with the current state/version to reconcile.
    const stale = await put(app, jar, 'sunni-islam', { state: sampleState('v1-again'), version: 1 });
    expect(stale.status).toBe(409);
    const conflict = (await stale.json()) as any;
    expect(conflict.version).toBe(2);
    expect(conflict.state.source.notes).toBe('v2');
  });

  it('rejects a mutating save without the CSRF header', async () => {
    const app = createApp(await createTestDb(), { allowedOrigins: [], auth });
    const jar = await signedIn(app);
    const res = await app.request('/api/review/sunni-islam', {
      method: 'PUT',
      headers: { Cookie: cookieHeader(jar), ...json }, // no X-CSRF-Token
      body: JSON.stringify({ state: sampleState(), version: 0 }),
    });
    expect(res.status).toBe(403);
  });

  it('isolates drafts per reviewer', async () => {
    const app = createApp(await createTestDb(), { allowedOrigins: [], auth });
    const jarA = await signedIn(app, 'a@example.com');
    const jarB = await signedIn(app, 'b@example.com');
    await put(app, jarA, 'sunni-islam', { state: sampleState('A-only'), version: 0 });
    // B has no draft for the same tradition.
    const bGet = await app.request('/api/review/sunni-islam', { headers: { Cookie: cookieHeader(jarB) } });
    expect(((await bGet.json()) as any).version).toBe(0);
  });

  it('lists all of the reviewer\'s drafts', async () => {
    const app = createApp(await createTestDb(), { allowedOrigins: [], auth });
    const jar = await signedIn(app);
    await put(app, jar, 'sunni-islam', { state: sampleState('a'), version: 0 });
    await put(app, jar, 'roman-catholic', { state: sampleState('b'), version: 0 });
    const res = await app.request('/api/review', { headers: { Cookie: cookieHeader(jar) } });
    const body = (await res.json()) as any;
    expect(body.drafts.map((d: any) => d.traditionId).sort()).toEqual(['roman-catholic', 'sunni-islam']);
  });

  it('deletes a draft (start over), idempotently', async () => {
    const app = createApp(await createTestDb(), { allowedOrigins: [], auth });
    const jar = await signedIn(app);
    await put(app, jar, 'sunni-islam', { state: sampleState('x'), version: 0 });
    const del = await app.request('/api/review/sunni-islam', { method: 'DELETE', headers: authed(jar) });
    expect(del.status).toBe(200);
    const gone = await app.request('/api/review/sunni-islam', { headers: { Cookie: cookieHeader(jar) } });
    expect(((await gone.json()) as any).version).toBe(0); // discarded
    // Deleting again is still a no-op 200.
    expect((await app.request('/api/review/sunni-islam', { method: 'DELETE', headers: authed(jar) })).status).toBe(200);
  });

  it('rejects an array state (only objects are valid drafts)', async () => {
    const app = createApp(await createTestDb(), { allowedOrigins: [], auth });
    const jar = await signedIn(app);
    const res = await app.request('/api/review/sunni-islam', {
      method: 'PUT',
      headers: authed(jar, json),
      body: JSON.stringify({ state: [1, 2, 3], version: 0 }),
    });
    expect(res.status).toBe(400);
  });

  it('rejects an over-large draft body (bodyLimit)', async () => {
    const app = createApp(await createTestDb(), { allowedOrigins: [], auth });
    const jar = await signedIn(app);
    const big = { state: { blob: 'x'.repeat(600 * 1024) }, version: 0 };
    const res = await app.request('/api/review/sunni-islam', {
      method: 'PUT',
      headers: authed(jar, json),
      body: JSON.stringify(big),
    });
    expect(res.status).toBe(413);
  });
});

describe('review submissions (immutable)', () => {
  const submit = (app: Hono, jar: Record<string, string>, tid: string, body: unknown) =>
    app.request(`/api/review/${tid}/submit`, { method: 'POST', headers: authed(jar, json), body: JSON.stringify(body) });

  it('requires auth + CSRF to submit', async () => {
    const app = createApp(await createTestDb(), { allowedOrigins: [], auth });
    // unauthenticated
    expect(
      (await app.request('/api/review/sunni-islam/submit', { method: 'POST', headers: json, body: '{}' })).status,
    ).toBe(401);
    // authed but no CSRF header
    const jar = await signedIn(app);
    const noCsrf = await app.request('/api/review/sunni-islam/submit', {
      method: 'POST',
      headers: { Cookie: cookieHeader(jar), ...json },
      body: JSON.stringify({ review: sampleState() }),
    });
    expect(noCsrf.status).toBe(403);
  });

  it('creates a private immutable snapshot; a second submit adds a new one', async () => {
    const app = createApp(await createTestDb(), { allowedOrigins: [], auth });
    const jar = await signedIn(app);
    const first = await submit(app, jar, 'sunni-islam', { review: sampleState('v1') });
    expect(first.status).toBe(201);
    const meta = ((await first.json()) as any).submission;
    expect(meta.id).toBeTruthy();
    expect(meta.submittedAt).toBeTruthy();

    // Submit again (the draft evolved) → a SEPARATE immutable row (no update path).
    await submit(app, jar, 'sunni-islam', { review: sampleState('v2') });
    const list = await app.request('/api/review/sunni-islam/submissions', { headers: { Cookie: cookieHeader(jar) } });
    const rows = ((await list.json()) as any).submissions;
    expect(rows).toHaveLength(2);
    expect(rows.every((r: any) => r.publishedIssueUrl === null)).toBe(true); // private by default
  });

  it('records publishedIssueUrl only when the reviewer opted to publish', async () => {
    const app = createApp(await createTestDb(), { allowedOrigins: [], auth });
    const jar = await signedIn(app);
    await submit(app, jar, 'sunni-islam', { review: sampleState(), publishedIssueUrl: 'https://github.com/x/y/issues/1' });
    const rows = ((await (await app.request('/api/review/sunni-islam/submissions', { headers: { Cookie: cookieHeader(jar) } })).json()) as any).submissions;
    expect(rows[0].publishedIssueUrl).toBe('https://github.com/x/y/issues/1');
  });

  it('rejects a non-GitHub publishedIssueUrl', async () => {
    const app = createApp(await createTestDb(), { allowedOrigins: [], auth });
    const jar = await signedIn(app);
    const res = await submit(app, jar, 'sunni-islam', { review: sampleState(), publishedIssueUrl: 'https://evil.example/x' });
    expect(res.status).toBe(400);
  });

  it('isolates submissions per reviewer', async () => {
    const app = createApp(await createTestDb(), { allowedOrigins: [], auth });
    const jarA = await signedIn(app, 'a@example.com');
    const jarB = await signedIn(app, 'b@example.com');
    await submit(app, jarA, 'sunni-islam', { review: sampleState('A') });
    const bList = await app.request('/api/review/sunni-islam/submissions', { headers: { Cookie: cookieHeader(jarB) } });
    expect(((await bList.json()) as any).submissions).toHaveLength(0);
  });
});
