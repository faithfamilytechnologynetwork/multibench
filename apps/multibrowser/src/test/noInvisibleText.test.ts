import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

// Contrast sanity as a TEST, not a hope: this week shipped TWO invisible-text bugs — #55's
// `bg-default-900` (a nonexistent HeroUI shade → transparent background) and #66's `text-white`
// on a light background (white-on-white). Guard the #51 raw/scenario surface (what a reader sees)
// against both antipatterns; use semantic tokens (text-primary-foreground / text-default-*) instead.
const here = dirname(fileURLToPath(import.meta.url));
const FILES = [
  "../components/RawComparison.tsx",
  "../components/ScenarioResponses.tsx",
  "../components/PressureSection.tsx",
  "../routes/ScenarioPage.tsx",
];
const BANNED: { re: RegExp; why: string }[] = [
  { re: /\btext-white\b/, why: "#66 white-on-light pill bug — use text-primary-foreground" },
  { re: /\bbg-default-900\b/, why: "#55 nonexistent-shade tooltip bug — use a defined shade" },
];

describe("no invisible-text antipatterns in the raw/scenario UI (contrast sanity)", () => {
  for (const f of FILES) {
    it(`${f} avoids known-bad color classes`, () => {
      const src = readFileSync(resolve(here, f), "utf8");
      for (const { re, why } of BANNED) {
        expect(src, `${f} must not use ${re} (${why})`).not.toMatch(re);
      }
    });
  }
});
