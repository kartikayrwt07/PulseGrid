import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../api/client";
import { useAuth } from "../lib/auth";

export function useTimeMachine(week?: number) {
  const { ready, role } = useAuth();
  return useQuery({
    queryKey: ["dashboard-time-machine", week ?? "active"],
    queryFn: ({ signal }) => apiClient.getTimeMachine(week, signal),
    enabled: ready && role === "faculty",
    placeholderData: (prev) => prev,
  });
}
