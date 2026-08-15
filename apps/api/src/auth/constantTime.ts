import { createHash, timingSafeEqual } from 'node:crypto';

/**
 * Constant-time string equality. Compares fixed-length SHA-256 digests so the check does not leak
 * input length (Node's `timingSafeEqual` throws on length mismatch) and does not short-circuit on the
 * first differing byte. Empty inputs are never equal.
 */
export function constantTimeEqual(a: string, b: string): boolean {
  if (!a || !b) return false;
  const da = createHash('sha256').update(a).digest();
  const db = createHash('sha256').update(b).digest();
  return timingSafeEqual(da, db);
}
