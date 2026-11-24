import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../api/client";
import { useAuth } from "../lib/auth";

export function useRecoveryPlan(studentId: number | null) {
  const { ready } = useAuth();
  return useQuery({
    queryKey: ["recovery-plan", studentId],
    queryFn: ({ signal }) => apiClient.getRecoveryPlan(studentId as number, signal),
    enabled: ready && studentId !== null && studentId > 0,
  });
}
