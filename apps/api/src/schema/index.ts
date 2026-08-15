// Drizzle schema root — the single schema authority (Spec 92 baked decision).
//
// Phase 1 is a bare scaffold with NO tables. Tables arrive in later phases:
//   - Phase 2: review store (reviewers, sessions, reviews, submissions) — after Ben's #85 sign-off.
//   - Phase 5: serving tiers (runs/provenance, corpus, results, raw).
//
// Keeping this file (even empty) gives drizzle.config.ts a stable `schema` target.
export {};
