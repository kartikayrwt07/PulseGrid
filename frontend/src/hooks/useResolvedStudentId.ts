import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../api/client";
import { useAuth } from "../lib/auth";

export function useResolvedStudentId(studentRef: number | string | null | undefined) {
  const { ready, role } = useAuth();
  const isNumeric = typeof studentRef === "number";
  const rollQuery = useQuery({
    queryKey: ["resolve-student-roll", String(studentRef ?? "")],
    queryFn: ({ signal }) => apiClient.listStudents({ search: String(studentRef), limit: 10 }, signal),
    enabled: ready && role === "faculty" && typeof studentRef === "string" && studentRef.length > 0,
  });

  if (isNumeric) {
    return { studentId: studentRef, isResolving: false, resolveError: null as Error | null };
  }
  const items = rollQuery.data?.items ?? [];
  const exact = items.find(
    (s) => s.roll_no.toUpperCase() === String(studentRef ?? "").trim().toUpperCase(),
  );
  const resolved = exact?.id ?? items[0]?.id ?? null;
  return {
    studentId: resolved,
    isResolving: rollQuery.isLoading,
    resolveError: rollQuery.error instanceof Error ? rollQuery.error : null,
  };
}
