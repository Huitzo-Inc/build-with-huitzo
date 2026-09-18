// The design rules, enforced.
//
// A style guide nobody runs is a style guide nobody follows. This suite reads the
// branded source and FAILS THE BUILD on the mistakes that matter, which is the
// same move the rest of this repo makes with its regression gate: turn a rule you
// would otherwise have to remember into a check that remembers for you.
//
// Point it at your own dashboard's src/ and it works unchanged.

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));

/**
 * Strip comments before scanning. This matters more than it looks: these files
 * explain the rules in prose, so an un-stripped scan counts the sentence
 * "use hz-btn--primary" as a use of the accent. A linter that reads its own
 * documentation as code is a linter that cries wolf.
 *
 * `(?<!:)` keeps `https://…` inside a string from being eaten as a line comment.
 */
function stripComments(src: string): string {
  return src.replace(/\/\*[\s\S]*?\*\//g, "").replace(/(?<!:)\/\/.*$/gm, "");
}

const read = (p: string) => stripComments(readFileSync(join(here, p), "utf8"));

const BRANDED = read("views/BrandedView.tsx");
const GENERIC = read("views/GenericView.tsx");

/** #abc, #aabbcc, #aabbccdd — but not a CSS var, a JSX id, or a hash comment. */
const HEX = /#[0-9a-fA-F]{3,8}\b/g;
const RGB_OR_HSL = /\b(rgba?|hsla?)\s*\(/g;
/** A box-shadow with a literal offset rather than a token. */
const HARDCODED_SHADOW = /box-?[Ss]hadow\s*[:=]\s*["'`][^"'`]*\d/g;
/** UI kits the design rules forbid: primitives and tokens only. */
const UI_KITS =
  /from\s+["'](@mui\/|antd|@chakra-ui\/|@radix-ui\/|shadcn|framer-motion|react-spring)/g;

describe("the branded view obeys the design system", () => {
  it("contains no hex colour literals", () => {
    // If this fails, the fix is never to delete the test. Find the colour you
    // wanted in packages/brand-tokens and use its var(--color-*) instead.
    expect(BRANDED.match(HEX) ?? []).toEqual([]);
  });

  it("contains no rgb()/hsl() literals either", () => {
    expect(BRANDED.match(RGB_OR_HSL) ?? []).toEqual([]);
  });

  it("authors no shadows of its own", () => {
    // hz-card already carries one. A second, hand-rolled shadow is how a page
    // stops looking like the rest of Hub.
    expect(BRANDED.match(HARDCODED_SHADOW) ?? []).toEqual([]);
  });

  it("imports no UI kit or animation library", () => {
    expect(BRANDED.match(UI_KITS) ?? []).toEqual([]);
  });

  it("spends the accent exactly once", () => {
    // The accent is the one thing you want clicked. Two accents is no accent.
    const accents = BRANDED.match(/hz-btn--primary|hz-eyebrow--accent|hz-card--accent/g) ?? [];
    expect(accents).toHaveLength(1);
  });

  it("uses the spacing scale rather than invented pixel values", () => {
    expect(BRANDED).toContain("var(--space-");
    // No `padding: "24px"` style literals in the branded view.
    expect(BRANDED.match(/["'`]\d+px["'`]/g) ?? []).toEqual([]);
  });

  it("builds a three-tier typographic hierarchy", () => {
    expect(BRANDED).toContain("hz-eyebrow"); // tier 1: the label
    expect(BRANDED).toMatch(/<h1[\s>]/); // tier 2: one real heading
    expect(BRANDED).toContain("var(--color-text-secondary)"); // tier 3: body
  });
});

describe("the generic view is the counter-example", () => {
  // These assertions exist so the comparison cannot silently rot: if someone
  // "tidies up" GenericView into compliance, the rung stops teaching anything.
  it("is full of exactly what the branded view avoids", () => {
    expect((GENERIC.match(HEX) ?? []).length).toBeGreaterThan(5);
    expect(GENERIC.match(HARDCODED_SHADOW)).not.toBeNull();
  });

  it("has no eyebrow, so it has no hierarchy", () => {
    expect(GENERIC).not.toContain("hz-eyebrow");
  });
});
