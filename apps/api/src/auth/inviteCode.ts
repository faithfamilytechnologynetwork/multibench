import { constantTimeEqual } from './constantTime';

/**
 * Fail-closed invite-code gate for signup (Spec 92: signup is gated by one shared `REVIEW_INVITE_CODE`
 * env var). Returns true only when a code is configured (non-empty `expected`) AND the provided code
 * matches it (constant-time). If no code is configured, no signup is allowed — the gate must be set
 * explicitly rather than defaulting open.
 *
 * Schema-independent: this decides nothing about reviewer records, only whether a signup attempt
 * carries the shared code.
 */
export function checkInviteCode(
  provided: string | undefined,
  expected: string | undefined,
): boolean {
  if (!expected) return false;
  return constantTimeEqual(provided ?? '', expected);
}
