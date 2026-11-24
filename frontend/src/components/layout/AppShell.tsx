import type { ReactNode } from "react";
import { useAuth } from "../../lib/auth";
import { ErrorBanner } from "../ui/ErrorBanner";
import { Spinner } from "../ui/Spinner";
import { Sidebar, type AppRoute } from "./Sidebar";
import { TopBar } from "./TopBar";

interface AppShellProps {
  route: AppRoute;
  onNavigate: (next: AppRoute) => void;
  children: ReactNode;
}

export function AppShell({ route, onNavigate, children }: AppShellProps) {
  const { ready, switching, error, retryAuth } = useAuth();

  return (
    <div className="flex min-h-screen flex-col bg-slate-950 text-slate-100 md:flex-row">
      <Sidebar route={route} onNavigate={onNavigate} />
      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar
          onRoleChanged={(nextRole) => {
            onNavigate(
              nextRole === "faculty" ? { page: "faculty-dashboard" } : { page: "student-home" },
            );
          }}
        />
        <main className="mx-auto w-full max-w-7xl flex-1 p-4 sm:p-6">
          {error ? (
            <ErrorBanner
              title="Authentication Error"
              message={error}
              onRetry={() => void retryAuth()}
            />
          ) : !ready || switching ? (
            <div className="flex h-64 items-center justify-center">
              <Spinner label="Authenticating workspace session..." />
            </div>
          ) : (
            children
          )}
        </main>
      </div>
    </div>
  );
}
