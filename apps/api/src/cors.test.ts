import { describe, it, expect } from 'vitest';
import { createApp } from './app';
import { parseAllowedOrigins } from './cors';
import { pgliteDatabase } from './db';

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
    const app = createApp(pgliteDatabase(), { allowedOrigins });
    const res = await app.request('/api/health', {
      headers: { Origin: 'https://multibrowser.app' },
    });
    expect(res.headers.get('access-control-allow-origin')).toBe('https://multibrowser.app');
    expect(res.headers.get('access-control-allow-credentials')).toBe('true');
  });

  it('does not echo an unlisted origin', async () => {
    const app = createApp(pgliteDatabase(), { allowedOrigins });
    const res = await app.request('/api/health', {
      headers: { Origin: 'https://evil.app' },
    });
    expect(res.headers.get('access-control-allow-origin')).not.toBe('https://evil.app');
  });
});
