import { describe, it, expect } from 'vitest';
import { createApp } from './app';
import { parseAllowedOrigins } from './cors';
import { createTestDb } from './testing/pglite';

const auth = { inviteCode: 'test-invite', secureCookies: false };

describe('parseAllowedOrigins', () => {
  it('splits, trims, and drops empty entries', () => {
    expect(parseAllowedOrigins('https://a.app, https://b.app ,')).toEqual([
      'https://a.app',
      'https://b.app',
    ]);
  });

  it('yields an empty list for undefined/empty (never a wildcard)', () => {
    expect(parseAllowedOrigins(undefined)).toEqual([]);
    expect(parseAllowedOrigins('')).toEqual([]);
  });
});

describe('CORS (credentialed cross-site)', () => {
  const allowedOrigins = ['https://multibrowser.app'];

  it('echoes an allow-listed origin with credentials enabled', async () => {
    const app = createApp(await createTestDb(), { allowedOrigins, auth });
    const res = await app.request('/api/health', {
      headers: { Origin: 'https://multibrowser.app' },
    });
    expect(res.headers.get('access-control-allow-origin')).toBe('https://multibrowser.app');
    expect(res.headers.get('access-control-allow-credentials')).toBe('true');
  });

  it('sends no allow-origin for an unlisted origin (never a wildcard with credentials)', async () => {
    const app = createApp(await createTestDb(), { allowedOrigins, auth });
    const res = await app.request('/api/health', {
      headers: { Origin: 'https://evil.app' },
    });
    // Assert null, not `!== evil`: a `*` header would pass the weaker check yet is exactly the
    // wildcard-with-credentials hazard the allow-list guards against.
    expect(res.headers.get('access-control-allow-origin')).toBeNull();
  });

  it('handles a credentialed preflight (OPTIONS) from an allow-listed origin', async () => {
    const app = createApp(await createTestDb(), { allowedOrigins, auth });
    const res = await app.request('/api/health', {
      method: 'OPTIONS',
      headers: {
        Origin: 'https://multibrowser.app',
        'Access-Control-Request-Method': 'POST',
      },
    });
    expect(res.headers.get('access-control-allow-origin')).toBe('https://multibrowser.app');
    expect(res.headers.get('access-control-allow-credentials')).toBe('true');
  });
});
