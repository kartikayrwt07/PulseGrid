import { useEffect, useRef, useState } from "react";
import { apiClient, type SimulateRequest, type SimulateResponse } from "../api/client";

export function useSimulate(request: SimulateRequest | null, delayMs = 150) {
  const [data, setData] = useState<SimulateResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!request) {
      setData(null);
      return;
    }

    const timer = window.setTimeout(async () => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;
      setIsLoading(true);
      setError(null);

      try {
        const res = await apiClient.simulateWhatIf(request, controller.signal);
        if (!controller.signal.aborted) {
          setData(res);
          setIsLoading(false);
        }
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") {
          return;
        }
        setError(err instanceof Error ? err.message : "Simulation failed.");
        setIsLoading(false);
      }
    }, delayMs);

    return () => {
      window.clearTimeout(timer);
    };
  }, [
    request?.student_id,
    request?.attendance_pct,
    request?.assignment_score,
    request?.internal_score,
    request?.weeks_remaining,
    delayMs,
  ]);

  useEffect(() => {
    return () => abortRef.current?.abort();
  }, []);

  return { data, isLoading, error };
}
