import { describe, it, expect } from 'vitest';
import type { Hono } from 'hono';
import { createApp } from '../app';
import { createTestDb } from '../testing/pglite';
import { CSRF_COOKIE, SESSION_COOKIE, CSRF_HEADER } from '../auth/cookies';

const auth = { inviteCode: 'test-invite', secureCookies: false };
const jsonHeaders = { 'Content-Type': 'application/json' };

async function makeApp(): Promise<Hono> {
  return createApp(await createTestDb(), { allowedOrigins: [], auth });
}

function readCookies(res: Response): Record<string, string> {
  const out: Record<string, string> = {};
  for (const raw of res.headers.getSetCookie?.() ?? []) {
    const pair = raw.split(';')[0] ?? '';
    const eq = pair.indexOf('=');
    if (eq > 0) out[pair.slice(0, eq)] = pair.slice(eq + 1);
  }
  return out;
}
const cookieHeader = (jar: Record<string, string>): string =>
  Object.entries(jar)
    .map(([k, v]) => `${k}=${v}`)
    .join('; ');

const signupBody = (over: Record<string, unknown> = {}) => ({
  email: 'reviewer@example.com',
  password: 'a-good-password',
  name: 'Rev Iewer',
  inviteCode: 'test-invite',
  ...over,
});

async function signup(app: Hono, over: Record<string, unknown> = {}): Promise<Response> {
  return app.request('/api/auth/signup', {
    method: 'POST',
    headers: jsonHeaders,
    body: JSON.stringify(signupBody(over)),
  });
}

describe('signup (invite-gated)', () => {
  it('creates a reviewer and sets session + csrf cookies', async () => {
    const app = await makeApp();
    const res = await signup(app);
    expect(res.status).toBe(201);
    const body = (await res.json()) as any;
    expect(body.reviewer.email).toBe('reviewer@example.com');
    expect(body.reviewer.id).toMatch(/[0-9a-f-]{36}/);
    const jar = readCookies(res);
    expect(jar[SESSION_COOKIE]).toBeTruthy();
    expect(jar[CSRF_COOKIE]).toBeTruthy();
  });

  it('rejects a wrong or missing invite code (fail-closed)', async () => {
    const app = await makeApp();
    expect((await signup(app, { inviteCode: 'nope' })).status).toBe(403);
    expect((await signup(app, { inviteCode: undefined })).status).toBe(403);
  });

  it('rejects a short password and a duplicate email', async () => {
    const app = await makeApp();
    expect((await signup(app, { password: 'short' })).status).toBe(400);
    expect((await signup(app)).status).toBe(201);
    expect((await signup(app)).status).toBe(409); // same email again
  });
});

describe('login / me / logout', () => {
  it('logs in with correct credentials, rejects wrong ones, and gates /me on a session', async () => {
    const app = await makeApp();
    await signup(app);

    expect(
      (
        await app.request('/api/auth/login', {
          method: 'POST',
          headers: jsonHeaders,
          body: JSON.stringify({ email: 'reviewer@example.com', password: 'wrong' }),
        })
      ).status,
    ).toBe(401);

    const login = await app.request('/api/auth/login', {
      method: 'POST',
      headers: jsonHeaders,
      body: JSON.stringify({ email: 'reviewer@example.com', password: 'a-good-password' }),
    });
    expect(login.status).toBe(200);
    const jar = readCookies(login);

    // /me without a cookie → 401; with the session cookie → 200.
    expect((await app.request('/api/auth/me')).status).toBe(401);
    const me = await app.request('/api/auth/me', { headers: { Cookie: cookieHeader(jar) } });
    expect(me.status).toBe(200);
    expect(((await me.json()) as any).reviewer.email).toBe('reviewer@example.com');

    // Logout revokes the session (delete row) → /me now 401 with the same cookie.
    const logout = await app.request('/api/auth/logout', {
      method: 'POST',
      headers: { Cookie: cookieHeader(jar) },
    });
    expect(logout.status).toBe(200);
    expect(
      (await app.request('/api/auth/me', { headers: { Cookie: cookieHeader(jar) } })).status,
    ).toBe(401);
  });
});

describe('account deletion (CSRF-protected)', () => {
  it('requires the CSRF header, then deletes the account (cascade)', async () => {
    const app = await makeApp();
    const jar = readCookies(await signup(app));

    // DELETE without the CSRF header → 403 (session valid, but double-submit fails).
    const noCsrf = await app.request('/api/account', {
      method: 'DELETE',
      headers: { Cookie: cookieHeader(jar) },
    });
    expect(noCsrf.status).toBe(403);

    // With the CSRF header echoing the csrf cookie → 200.
    const del = await app.request('/api/account', {
      method: 'DELETE',
      headers: { Cookie: cookieHeader(jar), [CSRF_HEADER]: jar[CSRF_COOKIE] ?? '' },
    });
    expect(del.status).toBe(200);

    // Account is gone: login now fails.
    const login = await app.request('/api/auth/login', {
      method: 'POST',
      headers: jsonHeaders,
      body: JSON.stringify({ email: 'reviewer@example.com', password: 'a-good-password' }),
    });
    expect(login.status).toBe(401);
  });
});
