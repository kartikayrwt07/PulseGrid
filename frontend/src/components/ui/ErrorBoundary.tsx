import { Component, type ErrorInfo, type ReactNode } from "react";
import { ErrorBanner } from "./ErrorBanner";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(_error: Error, _info: ErrorInfo): void {
    // Handled via friendly fallback UI; avoid leaking stack traces
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="mx-auto max-w-2xl p-8">
          <ErrorBanner
            title="Something went wrong in this view"
            message="Please refresh or retry to restore the dashboard."
            onRetry={() => this.setState({ hasError: false })}
          />
        </div>
      );
    }
    return this.props.children;
  }
}
