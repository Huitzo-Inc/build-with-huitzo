// A dashboard owns its own React tree, so it owns its own error boundary. If a
// render throws, Hub should see a contained error, not a blank tile. This is the
// minimal class-component boundary React requires (hooks cannot catch render errors).

import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    // In a real dashboard, forward this to Hub via context.showNotification.
    console.error("Dashboard crashed:", error, info.componentStack);
  }

  render(): ReactNode {
    if (this.state.error) {
      return (
        <div className="hz-card hz-card--warning" role="alert">
          <h2 className="hz-eyebrow hz-eyebrow--accent">Something went wrong</h2>
          <p>{this.state.error.message}</p>
        </div>
      );
    }
    return this.props.children;
  }
}
