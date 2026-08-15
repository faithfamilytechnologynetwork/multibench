/**
 * Parse the comma-separated ALLOWED_ORIGINS env value into an allow-list. Trims whitespace and
 * drops empties. An empty/undefined value yields an empty list (no cross-site origin allowed) —
 * never a wildcard, which is unsafe with credentialed cookies.
 */
export function parseAllowedOrigins(raw: string | undefined): string[] {
  return (raw ?? '')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean);
}
