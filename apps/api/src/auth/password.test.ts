import { describe, it, expect } from 'vitest';
import { hashPassword, verifyPassword } from './password';

describe('password hashing (argon2id)', () => {
  it('produces an argon2id PHC hash that is not the plaintext', async () => {
    const h = await hashPassword('correct horse battery staple');
    expect(h).toMatch(/^\$argon2id\$/);
    expect(h).not.toContain('correct horse battery staple');
  });

  it('verifies the correct password and rejects a wrong one', async () => {
    const h = await hashPassword('s3cret-passphrase');
    expect(await verifyPassword(h, 's3cret-passphrase')).toBe(true);
    expect(await verifyPassword(h, 's3cret-passphras')).toBe(false);
    expect(await verifyPassword(h, '')).toBe(false);
  });

  it('salts: the same password hashes differently each time', async () => {
    const a = await hashPassword('same-password');
    const b = await hashPassword('same-password');
    expect(a).not.toBe(b);
    expect(await verifyPassword(a, 'same-password')).toBe(true);
    expect(await verifyPassword(b, 'same-password')).toBe(true);
  });

  it('treats a malformed hash as a non-match instead of throwing', async () => {
    expect(await verifyPassword('not-a-valid-hash', 'whatever')).toBe(false);
  });
});
