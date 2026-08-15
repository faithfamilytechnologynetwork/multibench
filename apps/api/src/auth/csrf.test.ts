import { describe, it, expect } from 'vitest';
import { generateCsrfToken, verifyCsrfToken } from './csrf';

describe('CSRF tokens (double-submit)', () => {
  it('generates distinct, non-trivial tokens', () => {
    const a = generateCsrfToken();
    const b = generateCsrfToken();
    expect(a).not.toBe(b);
    expect(a.length).toBeGreaterThanOrEqual(32);
    expect(a).toMatch(/^[A-Za-z0-9_-]+$/); // base64url
  });

  it('verifies matching tokens and rejects mismatches', () => {
    const token = generateCsrfToken();
    expect(verifyCsrfToken(token, token)).toBe(true);
    expect(verifyCsrfToken(token, generateCsrfToken())).toBe(false);
  });

  it('rejects when either side is missing', () => {
    const token = generateCsrfToken();
    expect(verifyCsrfToken(token, undefined)).toBe(false);
    expect(verifyCsrfToken(undefined, token)).toBe(false);
    expect(verifyCsrfToken('', '')).toBe(false);
  });
});
