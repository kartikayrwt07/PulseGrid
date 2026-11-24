import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../api/client";
import { useAuth } from "../lib/auth";

export function useDashboardSummary() {
  const { ready, role } = useAuth();
  return useQuery({
    queryKey: ["dashboard-summary"],
    queryFn: ({ signal }) => apiClient.getDashboardSummary(signal),
    enabled: ready && role === "faculty",
  });
}
