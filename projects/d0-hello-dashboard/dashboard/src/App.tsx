// The whole dashboard. One component, no command call, no network.
//
// Everything on screen comes from the HuitzoContext that Hub handed to mount().
// That is the point of this rung: before a dashboard fetches anything, it is
// already connected to Hub — it knows who is signed in, which theme is active and
// where it sits. `useHubContext` reads that, and it is reactive: when the user
// flips Hub's theme, this component re-renders with the new value.
//
// Every class here (hz-card, hz-eyebrow, hz-stat__number) comes from the SDK's
// stylesheet, imported once in main.tsx. There is no hex colour anywhere in this
// project, which is why it follows Hub's theme for free.

import { useHubContext, useHubNavigation } from "@huitzo/dashboard-sdk-react";

export function App() {
  const { user, theme, dashboardSlug } = useHubContext();
  const { navigateToHub } = useHubNavigation();

  return (
    <div className="huitzo-dashboard" style={{ maxWidth: 680, margin: "0 auto", padding: "2rem 1.25rem" }}>
      <header style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "2rem" }}>
        <button className="hz-btn hz-btn--ghost" onClick={navigateToHub}>
          &larr; Hub
        </button>
        <span className="hz-eyebrow" style={{ marginLeft: "auto" }}>
          {dashboardSlug}
        </span>
      </header>

      <main>
        <p className="hz-eyebrow hz-eyebrow--accent">Dashboard rung D0</p>
        <h1 style={{ marginTop: 0 }}>It mounted.</h1>
        <p style={{ color: "var(--color-text-secondary)" }}>
          Hub imported this module, called <code className="hz-code">mount()</code> with a
          container and a context, and React took it from there. No backend of your own, and
          not one line of Python.
        </p>

        <div className="hz-card hz-card--lg" style={{ marginTop: "var(--space-8)" }}>
          <p className="hz-eyebrow">Who Hub says you are</p>
          <p className="hz-stat__number">{user?.name ?? "Not signed in"}</p>
          <p style={{ color: "var(--color-text-secondary)", margin: 0 }}>
            {user?.email ?? "No session on the mount context."}
            {user?.roles?.length ? ` · ${user.roles.join(", ")}` : null}
          </p>
        </div>

        <div className="hz-card hz-card--md" style={{ marginTop: "var(--space-6)" }}>
          <p className="hz-eyebrow">Active theme</p>
          <p style={{ margin: 0, color: "var(--color-text-secondary)" }}>
            Hub is in <strong>{theme}</strong> mode, and this page followed it without being
            told. Flip the theme in Hub and the value above changes with it — that is
            <code className="hz-code">useHubContext</code> being reactive, not a page reload.
          </p>
        </div>
      </main>
    </div>
  );
}
