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
// Log the parsed allow-list at startup: an empty list is the correct default (never a wildcard),
// but it also produces opaque browser CORS failures, so surfacing it saves real debugging time.
console.log(
  allowedOrigins.length > 0
    ? `CORS allow-list: ${allowedOrigins.join(', ')}`
    : 'CORS allow-list is EMPTY — no cross-site origin is allowed (set ALLOWED_ORIGINS).',
);

const inviteCode = process.env.REVIEW_INVITE_CODE;
if (!inviteCode) {
  // Fail-closed, not fatal: the service still serves reads/login, but signup is closed until the
  // shared invite code is set. Surface it so it isn't a silent mystery.
  console.log('REVIEW_INVITE_CODE is unset — signup is CLOSED until it is configured.');
}

const port = Number(process.env.PORT ?? 8080);
if (!Number.isFinite(port)) {
  console.error(`PORT is not a valid number: ${process.env.PORT}`);
  process.exit(1);
}

const app = createApp(nodePgDatabase(databaseUrl), {
  allowedOrigins,
  auth: { inviteCode, secureCookies: true },
});

serve({ fetch: app.fetch, port }, (info) => {
  console.log(`api listening on :${info.port}`);
});
