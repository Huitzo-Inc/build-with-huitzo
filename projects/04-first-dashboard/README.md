# Tier 4: first-dashboard

> Read this in [Español](./README.es.md).

You have built packs. Now build a face for one. This is a React dashboard that runs inside Huitzo Hub and calls the `macro-snapshot` pack from the browser: pick a country and an indicator, hit Run, and the pack's grounded snapshot comes back. You write no backend of your own.

The one idea to carry out of here: **the dashboard is a thin consumer of decisions the Python already made.** Every number on the screen was computed in deterministic Python inside the pack. The dashboard's whole job is to call a command and render the typed result. It never talks to a model and never does the math.

**You will learn:** the `mount`/`unmount` contract that makes a dashboard a Hub app, how `useCommand` turns a pack command into `{execute, data, loading, error}`, how the dashboard inherits Hub's theme through design tokens, and the trick that lets the whole thing run on your laptop with no Hub at all.

**Time:** about forty minutes.

## Prerequisites

- Node 20+ and npm
- You have seen [Tier 1: macro-snapshot](../01b-macro-snapshot); this dashboard consumes its `country-snapshot` command.
- No Hub account is needed to build, test, or run this locally. A Hub with the pack deployed is needed only to publish it for real.

## Run it

```bash
cd dashboard
npm install
npm test            # 8 tests, no browser and no Hub
npm run build       # typechecks, then bundles dist/main.js (exports mount/unmount)
```

To see it in a browser with a fake Hub, open two terminals:

```bash
node mock-server.mjs   # terminal 1: a tiny stand-in for the Hub API on :8787
npm run dev            # terminal 2: serves the dashboard on :3000
```

Open `http://localhost:3000`, choose a country, and hit Run. The call goes to the mock server, not a real Hub — so it returns a **fixed sample snapshot** (the same shape every time, regardless of the country you pick); its job is to let you build and see the UI offline, not to run the pack. On a real Hub the dashboard calls the actual `macro-snapshot` pack, and *then* every number is computed in deterministic Python as described above. That local loop is the centerpiece of this rung, and it is explained below.

## What is inside

```
dashboard/
  huitzo-dashboard.yaml          the manifest: identity, the pack it depends on, the build
  package.json                   React 19 + the two Huitzo SDK packages
  vite.config.ts                 library-mode build (-> dist/main.js) + the test config
  index.html                     dev host; loads src/dev.tsx
  mock-server.mjs                a tiny fake Hub API for local development
  src/
    main.tsx                     PRODUCTION entry: exports mount() / unmount()
    dev.tsx                      DEV entry: builds a mock Hub context and calls mount()
    App.tsx                      layout: header + panel
    types.ts                     the command id and result shape (the pack contract)
    components/
      SnapshotPanel.tsx          container: wires useCommand to the view
      SnapshotView.tsx           presentation: pure, takes props, easy to test
      HubHeader.tsx              useHubNavigation + useHubContext
      ErrorBoundary.tsx          a dashboard owns its own error boundary
    SnapshotView.test.tsx        renders each state from plain props
    App.test.tsx                 smoke test with the SDK hooks mocked
```

## The mount contract

A Huitzo Dashboard is not a website. It is a module that Hub loads and runs inside itself. The contract is two functions, in `src/main.tsx`:

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

Hub calls `mount()` with a DOM node and a `HuitzoContext` (the shared JWT session, the user, navigation). You create your **own** React root and wrap the app in your **own** `ErrorBoundary`, so a crash in your dashboard is contained and never takes Hub down. `HuitzoProvider` takes that context and makes it available to every hook below it.

## Calling a pack with `useCommand`

This is the whole point. One hook turns a pack command into a render-ready state machine (`src/components/SnapshotPanel.tsx`):

```tsx
const { execute, data, loading, error } = useCommand<CountrySnapshot>(
  "@reef/macro-snapshot/country-snapshot",
);
// ...
onRun={() => void execute({ country, indicator })}
```

`execute(args)` runs the command on the Hub. `loading` is true while it is in flight, `error` holds a typed `HuitzoError` on failure, and `data` is the typed `CountrySnapshot` on success. The dashboard shares no code with the pack: it agrees on the command id and the result shape (`src/types.ts` is the TypeScript mirror of the pack's Pydantic output). That loose coupling is deliberate, the same dashboard works against any pack version that still returns that shape.

## Presentation versus wiring (why testing is easy)

Notice the split: `SnapshotPanel` holds the hook, and `SnapshotView` is a pure function of its props (`loading`, `error`, `data`, `onRun`). That is what makes the rendering logic testable with no Hub, no SDK, and no network:

```tsx
it("success: shows the value, the delta, and the model summary", () => {
  render(<SnapshotView {...base} data={sample} />);
  expect(screen.getByText("3.4")).toBeTruthy();
  expect(screen.getByText(sample.summary)).toBeTruthy();
});
```

`npm test` runs eight of these. The one place we touch the SDK, `App.test.tsx`, mocks the hooks so the test still needs no Hub. The real SDK integration is verified two other ways: `npm run build` typechecks every component against the real SDK types, and `dev.tsx` runs it for real in a browser.

## It themes itself

The dashboard imports the SDK design tokens once (`import "@huitzo/dashboard-sdk-react/styles"` in `main.tsx`) and styles itself with `hz-*` classes (`hz-card`, `hz-stat__number`, `hz-btn--primary`, `hz-eyebrow`) and `var(--color-*)` tokens. There is **no hardcoded hex anywhere**. When this dashboard runs inside Hub, Hub's brand tokens win, so a white-labeled Hub restyles your dashboard with zero code change. The header reads the live theme from `useHubContext()`.

## Test it with no Hub

In production, Hub builds the `HuitzoContext` and calls `mount()`. In development, `src/dev.tsx` builds a mock context by hand and calls `mount()` itself:

```tsx
const devContext: HuitzoContext = {
  apiUrl: "http://localhost:8787",
  getToken: () => "dev-token",
  slug: "first-dashboard",
  sdkVersion: "dev",
  user: { id: "usr_dev", email: "dev@reef.example", name: "Dev", roles: ["owner"], tenantId: "ten_dev" },
  navigate: (path) => console.log("navigate ->", path),
  navigateToHub: () => alert("← Hub (mock)"),
  navigateToDashboard: (slug) => console.log("dashboard ->", slug),
  showNotification: (message, type) => console.log(`[${type}] ${message}`),
  on: () => () => {},
  emit: () => {},
};
mount(document.getElementById("root")!, devContext);
```

Point `apiUrl` at the bundled `mock-server.mjs`, which answers the command call with a canned snapshot, and the dashboard runs end to end on your machine. This is how you build and iterate on a Huitzo frontend before you have any Hub access at all.

## Other SDK hooks (not needed here)

The SDK also exports `useRealtime`, `useHubBreadcrumbs`, and `useHubActions`. These work today over the Hub mount event bus; this first dashboard simply does not need them yet. The one hook that is *not* implemented is `useConnectionStatus` — calling it raises a clear error pointing you to `useRealtime()` instead (the pack-event WebSocket layer it needs is deferred to a future backend release). The `@huitzo/dashboard-primitives` copy-in component registry and `@huitzo/dashboard-mcp` are likewise on the roadmap.

## Run it for real

Once you have a Hub account in developer mode and the `macro-snapshot` pack deployed:

```bash
huitzo dashboard validate
huitzo dashboard build      # runs npm run build
huitzo dashboard publish    # uploads dist/main.js as a new version
```

Then open it from your Hub at `https://hub.huitzo.com/d/first-dashboard`. There are no separate dashboard URLs; Hub is the single entry point, and your dashboard shares Hub's session.

## Next

You can build a frontend on a pack. [Tier 5: pack-from-outside](../05-pack-from-outside) goes the other direction: driving a deployed pack from outside the browser entirely, over REST, the CLI, and the hosted MCP server.
