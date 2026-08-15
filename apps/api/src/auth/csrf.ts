import { randomBytes } from 'node:crypto';
import { constantTimeEqual } from './constantTime';

/**
 * CSRF token primitives for the double-submit pattern (a random token is sent both as a cookie and
 * an echoed request header/field; the two must match). Schema-independent — no session storage, no
 * model shape assumed here; wiring into routes/cookies comes with the auth routes once the review
 * model is settled.
 */
export function generateCsrfToken(): string {
  return randomBytes(32).toString('base64url');
}

/** True only when both tokens are present and equal (constant-time). */
export function verifyCsrfToken(a: string | undefined, b: string | undefined): boolean {
  return constantTimeEqual(a ?? '', b ?? '');
}
