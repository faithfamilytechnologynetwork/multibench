import { describe, it, expect } from 'vitest';
import { createApp } from '../app';
import { pgliteDatabase } from '../db';
import type { Database } from '../db';

describe('GET /api/health', () => {
  it('returns 200 ok when the database responds (PGlite)', async () => {
    const app = createApp(pgliteDatabase(), { allowedOrigins: [] });
    const res = await app.request('/api/health');
    expect(res.status).toBe(200);
    expect(await res.json()).toEqual({ status: 'ok', db: 'up' });
  });

  it('returns 503 when the database ping fails', async () => {
    const failing: Database = {
      ping: async () => {
        throw new Error('unreachable');
      },
    };
    const app = createApp(failing, { allowedOrigins: [] });
    const res = await app.request('/api/health');
    expect(res.status).toBe(503);
    expect(await res.json()).toEqual({ status: 'error', db: 'down' });
  });
});
