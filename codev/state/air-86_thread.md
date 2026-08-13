# air-86 thread — Issue #86: numbered HeroUI shades are app-wide no-ops → @theme shim

## 2026-08-13 — implement (AIR strict)

**Root cause (confirmed):** `@heroui/styles@3.2.1` defines its color tokens via `@theme inline`
in `dist/themes/shared/theme.css` — **only semantic tokens** (`--color-default`,
`--color-default-{foreground,hover,soft}`, `--color-warning`, `--color-border{,-secondary,
-tertiary}`, …). There is **no numbered scale**. Tailwind v4 only generates a `text-default-500`
utility if a `--color-default-500` theme var exists, so every numbered shade the app uses
(`text-default-500` ×42, `border-default-200` ×28, `bg-warning-50`, …) compiled to **nothing**.
Same bug class as the #55 tooltip scar, now root-caused. Verified by inspecting the installed
package CSS, not the docs.

**Fix (one file):** appended a `@theme inline` block to `apps/multibrowser/src/styles.css`
mapping a 50→900 ramp for the families actually used with numbers — **default** (neutral) plus
the **warning / danger / success** status hues — onto HeroUI's own theme-aware poles via
`color-mix(in oklab, …)`:
- neutral: `var(--foreground)` ↔ `var(--background)` (4%→96%)
- status hues: light steps tint `--background`, `-500` = the base hue, dark steps tint
  `--foreground`.

`@theme inline` is **required** (not plain `@theme`): it inlines the `color-mix` value into each
utility instead of emitting a fixed `:root` var, so the inner `var(--foreground)` etc. resolve in
the element's context and the whole ramp **flips correctly light↔dark by construction** (HeroUI
redefines those poles per theme). No new deps, no v2-era provider (HeroUI v3 is provider-less —
standing lesson).

**Verification against the REAL built CSS** (`pnpm build` → `dist/assets/*.css`):
- Numbered utilities now emit rules. Lightning CSS wraps them as progressive enhancement: a plain
  fallback (`.text-default-500{color:var(--foreground)}`) for ancient no-color-mix browsers, then
  an `@supports (color:color-mix(...))` block with the real ramp — the `@supports` override sits
  **after** the fallback (higher byte offset) so the color-mix value wins in every modern browser.
  Confirmed ordering programmatically for 5 representative classes.
- Test: added an `it(...)` to `src/deploy.test.ts`'s existing build-once `describe` (reuses the
  single `pnpm build`) asserting 10 representative numbered utilities each emit a rule whose value
  is a color-mix / var over the expected theme-aware pole — catches both the no-op regression and
  a static-color (dark-mode-breaking) regression.

**Status:** full multibrowser suite 309/309 green, `tsc --noEmit` clean, `porch check 86` passed.
Dark-mode contrast is theme-aware by construction; a human eyeball of leaderboard / raw explorer
(and `/review` once #83 merges) is the recommended final visual check — noted in the PR.
