import { ExpensePanel } from "./components/ExpensePanel";
import { HubHeader } from "./components/HubHeader";

export function App() {
  return (
    <div style={{ maxWidth: 820, margin: "0 auto", padding: "2rem 1.25rem" }}>
      <HubHeader />
      <main>
        <ExpensePanel />
      </main>
    </div>
  );
}
