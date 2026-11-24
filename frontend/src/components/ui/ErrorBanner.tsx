import { AlertTriangle, RefreshCw } from "lucide-react";

interface ErrorBannerProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export function ErrorBanner({
  title = "Unable to load data",
  message,
  onRetry,
}: ErrorBannerProps) {
  return (
    <div
      role="alert"
      className="flex flex-col gap-3 rounded-xl border border-rose-500/40 bg-rose-950/30 p-4 text-rose-200 sm:flex-row sm:items-center sm:justify-between"
    >
      <div className="flex items-start gap-3">
        <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-rose-400" />
        <div>
          <p className="text-sm font-semibold">{title}</p>
          <p className="mt-0.5 text-xs text-rose-200/80">{message}</p>
        </div>
      </div>
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="inline-flex items-center gap-1.5 self-start rounded-lg border border-rose-400/40 bg-rose-500/20 px-3 py-1.5 text-xs font-medium text-rose-100 hover:bg-rose-500/30 sm:self-center"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Retry
        </button>
      ) : null}
    </div>
  );
}
