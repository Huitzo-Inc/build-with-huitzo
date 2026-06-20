// The root component. It assembles the header and the snapshot panel. Everything
// data-related lives in the panel; App is just layout.

import { HubHeader } from "./components/HubHeader";
import { SnapshotPanel } from "./components/SnapshotPanel";

export function App() {
  return (
    <div style={{ maxWidth: 760, margin: "0 auto", padding: "2rem 1.25rem" }}>
      <HubHeader />
      <main>
        <SnapshotPanel />
      </main>
    </div>
  );
}
