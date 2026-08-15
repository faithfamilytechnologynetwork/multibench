import { hash, verify } from '@node-rs/argon2';

/**
 * Password hashing primitives (argon2id) — schema-independent, so they are safe to build before the
 * review data model is settled. `@node-rs/argon2`'s default algorithm is argon2id; the test suite
 * pins that by asserting the encoded hash starts with `$argon2id$`, so a library default change can't
 * silently downgrade the variant. The encoded PHC string carries its own parameters, so
 * `verifyPassword` needs no options.
 */
export function hashPassword(password: string): Promise<string> {
  return hash(password);
}

/** Verify a password against an encoded argon2 hash. A malformed hash is a non-match, never a throw. */
export async function verifyPassword(hashString: string, password: string): Promise<boolean> {
  try {
    return await verify(hashString, password);
  } catch {
    return false;
  }
}
