import { describe, it, expect } from 'vitest';
import { checkInviteCode } from './inviteCode';

describe('checkInviteCode (fail-closed)', () => {
  it('accepts a provided code that matches the configured one', () => {
    expect(checkInviteCode('let-me-in-2026', 'let-me-in-2026')).toBe(true);
  });

  it('rejects a mismatched code', () => {
    expect(checkInviteCode('wrong', 'let-me-in-2026')).toBe(false);
  });

  it('rejects when no code is configured (fail closed, never defaults open)', () => {
    expect(checkInviteCode('anything', undefined)).toBe(false);
    expect(checkInviteCode('anything', '')).toBe(false);
  });

  it('rejects when no code is provided', () => {
    expect(checkInviteCode(undefined, 'let-me-in-2026')).toBe(false);
    expect(checkInviteCode('', 'let-me-in-2026')).toBe(false);
  });
});
