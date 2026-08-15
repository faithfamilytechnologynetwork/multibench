import { serve } from '@hono/node-server';
import { createApp } from './app';
import { parseAllowedOrigins } from './cors';
import { nodePgDatabase } from './db';

// Fail fast on missing config rather than starting a half-working service (no silent fallbacks).
const databaseUrl = process.env.DATABASE_URL;
if (!databaseUrl) {
  console.error('DATABASE_URL is required');
  process.exit(1);
}

const allowedOrigins = parseAllowedOrigins(process.env.ALLOWED_ORIGINS);
const port = Number(process.env.PORT ?? 8080);

const app = createApp(nodePgDatabase(databaseUrl), { allowedOrigins });

serve({ fetch: app.fetch, port }, (info) => {
  console.log(`api listening on :${info.port}`);
});
