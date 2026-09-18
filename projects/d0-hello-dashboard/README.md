# Dashboard D0: hello-dashboard

> Read this in [Español](./README.es.md).

The smallest thing Huitzo Hub can load. No pack, no command call, no network, no Python. Hub hands your module a DOM node and a context object, and you render. If you do one thing on the dashboard track, do this.

The one idea to carry out of here: **a Huitzo Dashboard is not a website, it is a module Hub mounts inside itself.** There is no server of yours, no router, no separate URL. Hub owns the page; you own a subtree of it.

**You will learn:** the `mount`/`unmount` contract, why your dashboard brings its own React root and its own error boundary, how `useHubContext` gives you the session and theme before you fetch anything, and how to run the whole thing on your laptop with no Hub at all.

**Time:** about ten minutes.

## Prerequisites

- Node 20+ and npm

That is the whole list. No Hub account, no CLI, no Python, and no pack.

## Run it

```bash
cd dashboard
npm install
npm test            # 5 tests, no browser and no Hub
npm run build       # typechecks, then bundles dist/main.js
```

To see it in a browser:

```bash
npm run dev         # http://localhost:3000
```

There is no mock server to start, because this rung never calls a command. Everything on screen came from the context object, which is exactly the point.

## What is inside

```
dashboard/
  huitzo-dashboard.yaml    the manifest: identity and build (no pack dependencies)
  package.json             React 19 + the two Huitzo SDK packages
  vite.config.ts           library-mode build (-> dist/main.js) + the test config
  index.html               dev host; loads src/dev.tsx
  src/
    main.tsx               PRODUCTION entry: exports mount() / unmount()   <- the lesson
    dev.tsx                DEV entry: builds a mock context and calls mount()
    App.tsx                the whole UI, one component
    components/
      ErrorBoundary.tsx    a dashboard owns its own error boundary
    main.test.tsx          tests the mount contract
```

Copy `vite.config.ts` and `tsconfig.json` forward into every dashboard you write. They are identical in every rung, and this is the last time you have to think about them.

## The contract is two functions

All of `src/main.tsx` that matters:

```tsx
export function mount(container: HTMLElement, context: HuitzoContext): void {
  const root = createRoot(container);
  roots.set(container, root);
  root.render(
    <ErrorBoundary>
      <HuitzoProvider context={context}>
        <App />
      </HuitzoProvider>
    </ErrorBoundary>,
  );
}

export function unmount(container: HTMLElement): void {
  roots.get(container)?.unmount();
  roots.delete(container);
}
```

Four things to notice:

1. **You create your own React root.** Hub does not hand you one. That is what lets your dashboard bundle its own React version without fighting Hub's.
2. **You wrap the app in your own `ErrorBoundary`.** A render crash inside your dashboard must stay inside your dashboard. Hooks cannot catch render errors, so this is the one place a class component is still required.
3. **`HuitzoProvider` takes the context** and makes it available to every hook below it. Without it, `useHubContext` has nothing to read.
4. **`unmount` must actually clean up.** Hub reuses container nodes. The `WeakMap` keyed by container is how `unmount` finds the right root, and why a detached container can still be garbage collected.

## The context arrives before any fetch

`App.tsx` calls one hook and already knows who is signed in:

```tsx
const { user, theme, dashboardSlug } = useHubContext();
```

No request was made. Hub passed all of it to `mount()`, because your dashboard shares Hub's session: the same JWT, the same user, the same tenant. You never build a login screen.

`useHubContext` is also **reactive**. Flip the theme in Hub and `theme` changes and your component re-renders. It is not a snapshot taken at mount time.

## It themes itself

`main.tsx` imports the SDK's design tokens exactly once:

```tsx
import "@huitzo/dashboard-sdk-react/styles";
```

After that, `hz-card`, `hz-eyebrow`, `hz-stat__number`, `hz-btn--ghost` and `var(--color-*)` all resolve. **There is not one hex colour in this project.** That is the requirement, not a nicety: because every colour goes through a token, a white-labelled Hub restyles your dashboard with zero code change, and light mode works without you writing it.

Open `index.html` and switch `data-theme="dark"` to `"light"`. Everything should still look deliberate. If something goes washed out or invisible, you have a hard-coded colour somewhere.

## Test the contract, not the copy

`npm test` runs five tests, and none of them check what the page says. They check what Hub depends on:

```tsx
it("empties the container on unmount, so Hub can reuse the node", () => {
  const container = document.createElement("div");
  act(() => mount(container, makeContext()));
  expect(container.innerHTML).not.toBe("");

  act(() => unmount(container));
  expect(container.innerHTML).toBe("");
});
```

A dashboard that renders beautifully but leaks on unmount will break Hub on the second visit. Test the contract first; the UI is the easy part.

## Run it for real

> Re-scope it first: the example uses the `@reef` org, which you do not own. Change `namespace:` in `huitzo-dashboard.yaml` to an org you own. See [Run on your own Hub](../../README.md#run-on-your-own-hub).

Once you have a Hub account in developer mode:

```bash
huitzo dashboard validate
huitzo dashboard build      # runs npm run build
huitzo dashboard publish    # uploads dist/main.js as a new version
```

Then open it from Hub at `https://hub.huitzo.com/d/hello-dashboard`. There are no separate dashboard URLs; Hub is the single entry point.

## Next

Your dashboard mounts, but it does not do anything yet. [Tier 4: `04-first-dashboard`](../04-first-dashboard) points it at a real pack command with `useCommand`, and a mock Hub so it still runs on your laptop.
