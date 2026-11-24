import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../api/client";
import { useAuth } from "../lib/auth";

export function useStudentAnalytics(studentId: number | null) {
  const { ready } = useAuth();
  return useQuery({
    queryKey: ["student-analytics", studentId],
    queryFn: ({ signal }) => apiClient.getStudentAnalytics(studentId as number, signal),
    enabled: ready && studentId !== null && studentId > 0,
  });
}
