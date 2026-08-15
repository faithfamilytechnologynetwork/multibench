import { defineConfig } from 'drizzle-kit';

// Drizzle owns the schema and migrations (Spec 92 baked decision): `drizzle-kit generate`
// → review the SQL → apply. Never `db:push` against live data.
// Phase 1 is a bare scaffold with no tables; review tables land in Phase 2 (after Ben's #85
// sign-off) and serving-tier tables in Phase 5.
export default defineConfig({
  schema: './src/schema/index.ts',
  out: './drizzle',
  dialect: 'postgresql',
  // `?? ''` is intentional, not a silent fallback: `drizzle-kit generate` (how migrations are
  // authored — Phase 2/5) needs no live connection, so it must not fail when DATABASE_URL is unset.
  // The commands that DO connect (`migrate`/`push`) fail loudly on an empty URL — and `push` is
  // banned by the baked decision anyway.
  dbCredentials: { url: process.env.DATABASE_URL ?? '' },
});
