# Dashboard D3: design-system

> Read this in [Español](./README.es.md).

The same macro snapshot, rendered twice. One version is what an AI assistant writes when nobody tells it about the design system. The other is the same information on Huitzo's brand tokens, with not one colour decision of your own. Flip between them in the browser and the difference is immediate.

The one idea to carry out of here: **a Huitzo dashboard should look like Huitzo on first render, not after someone redesigns it by hand.** That is not a matter of taste: it is a property you get for free by never inventing a colour, and lose the moment you invent one.

**You will learn:** the brand token system and why it survives white-labelling, the `hz-*` primitives, the three-tier typographic hierarchy, the accent budget, and how to make the design rules a test that fails the build rather than a document nobody reads.

**Time:** about thirty minutes.

## Prerequisites

- Node 20+ and npm
- [D0: `d0-hello-dashboard`](../d0-hello-dashboard) for the `mount`/`unmount` contract

No Hub, no pack, no network. This rung renders a fixed sample so the lesson stays on design.

## Run it

```bash
cd dashboard
npm install
npm test            # 14 tests, 9 of which are the design rules themselves
npm run build
npm run dev         # http://localhost:3000, then use the Branded / Generic toggle
```

## What is inside

```
dashboard/
  src/
    sample.ts                the CountrySnapshot both views render (from D1's pack)
    App.tsx                  the toggle
    views/
      GenericView.tsx        ❌ the before: hand-picked hex, gradient CTA, no hierarchy
      BrandedView.tsx        ✅ the after: same data, tokens and hz-* only
    design-rules.test.ts     the gate: fails the build on a hex literal   <- the lesson
    App.test.tsx             render tests for the toggle
```

## The before

`GenericView.tsx` is the page the design rules exist to prevent: a centred `<h1>` "Welcome to…", one subtitle paragraph, a blue-to-purple gradient button, and about a dozen hex values somebody had to choose.

It is not broken and it is not ugly. **It is generic:** it could belong to any product. And it only works in dark mode: flip the dev host to `data-theme="light"` and it stays stubbornly dark, because none of its colours go through a token.

## The four rules

`BrandedView.tsx` renders the identical data under four constraints.

**1. Three typographic tiers, always.** An eyebrow label, then a real `<h1>`, then body copy in `var(--color-text-secondary)`. Never lead with a paragraph; never set everything at one weight.

```tsx
<p className="hz-eyebrow">USA · 2025</p>
<h1>Macro snapshot</h1>
<p style={{ color: "var(--color-text-secondary)" }}>{SAMPLE.summary}</p>
```

**2. The accent appears once per viewport.** `--color-accent` marks the one thing you want clicked: here, a single `hz-btn--primary`. Two accents is no accent. Status colours (`--color-success`, `--color-warning`, `--color-error`) are for *state*, not decoration, and do not count against the budget.

**3. Backgrounds are layered, and the card owns its own surface.** `--color-bg-primary` (page) sits under `--color-bg-elevated` (cards). `hz-card` already carries the surface, the radius and the shadow, so you author none of them. A second, hand-rolled `box-shadow` is how a page stops looking like the rest of Hub.

**4. Spacing comes off the scale.** `var(--space-*)` is a 4px scale. Major sections get `--space-12` or more. Generous whitespace beats a dense layout; empty space is part of the design.

Notice too that the status modifier is chosen **from the data**, not by taste:

```tsx
const direction = trend(SAMPLE.delta_pct);   // deterministic, in sample.ts
className={direction === "improving" ? "hz-stat__number--success" : "hz-stat__number--warning"}
```

That is the same discipline as a pack: the deterministic thing decides, and the presentation follows.

## Why tokens survive white-labelling

This is the part worth understanding rather than memorising. The SDK ships its tokens inside a **CSS cascade layer**:

```css
@layer huitzo-tokens {
  :root { --color-accent: …; --space-4: …; }
}
```

Anything a host defines *unlayered* beats a layered rule **regardless of stylesheet order**. So when your dashboard runs at `/d/{slug}` inside a white-labelled Hub, that Hub's unlayered brand tokens win automatically, and your dashboard restyles itself with zero code change. Run the same bundle standalone and it falls back to the SDK defaults.

The `hz-*` primitives are deliberately *not* in the layer; they just consume `var(--color-*)`, so they pick up whichever token set won.

That mechanism is the whole reason "never write a hex" is a real engineering rule rather than a style preference. **A hex literal is the one thing a host cannot override.**

> One detail worth getting right: tokens resolve at `:root`, so they are available everywhere. The `huitzo-dashboard` class you will see on the root element (and which `TemplateFrame` adds for you) is a scoping hook for host-side and white-label CSS. It is *not* what makes the tokens resolve.

## The rules as a test, not a document

A style guide nobody runs is a style guide nobody follows. `design-rules.test.ts` reads the branded source and fails on the mistakes that matter:

```ts
it("contains no hex colour literals", () => {
  expect(BRANDED.match(HEX) ?? []).toEqual([]);
});

it("spends the accent exactly once", () => {
  const accents = BRANDED.match(/hz-btn--primary|hz-eyebrow--accent|hz-card--accent/g) ?? [];
  expect(accents).toHaveLength(1);
});
```

Nine checks in total: no hex, no `rgb()`/`hsl()`, no hand-authored shadow, no UI kit or animation library, one accent, spacing on the scale, and a three-tier hierarchy. Two more assert that `GenericView` stays a *bad* example, so the comparison cannot silently rot when someone tidies it up.

One subtlety the implementation had to handle: **it strips comments before scanning.** These files explain the rules in prose, so an un-stripped scan counts the sentence "use `hz-btn--primary`" as a use of the accent. A linter that reads its own documentation as code is a linter that cries wolf.

Point it at your own dashboard's `src/` and it works unchanged. If it fails, the fix is never to delete the check. Find the colour you wanted in the token set and use its `var(--color-*)`.

## Verify both themes before you call it done

1. `npm run dev` and look at it in dark.
2. Open `index.html`, change `data-theme="dark"` to `"light"`, reload.
3. Both must look intentional.

If light looks washed out or something disappears, you have a hard-coded colour leaking somewhere, and the test above will tell you which file.

## Going further: copy-in primitives

When a primitive is missing, do not re-invent it locally. [`@huitzo/dashboard-primitives`](https://www.npmjs.com/package/@huitzo/dashboard-primitives) is a copy-in registry, shadcn-style: per-primitive typed React source, brand-token styled, SHA-256 hash-pinned, so you own the code but it still matches Hub.

## Next

You can make a dashboard look right. The remaining rungs cover declarative forms, streaming and queued commands, and the governed interface that renders a withheld decision and its evidence record. See [the learning path](../../docs/en/index.md#the-dashboard-path). The capstone both paths share is [`06-fullstack-triage`](../06-fullstack-triage).
