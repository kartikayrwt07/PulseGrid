import { useQuery } from "@tanstack/react-query";
import { apiClient, type StudentListQuery } from "../api/client";
import { useAuth } from "../lib/auth";

export function useStudents(params?: StudentListQuery) {
  const { ready, role } = useAuth();
  return useQuery({
    queryKey: ["students", params ?? {}],
    queryFn: ({ signal }) => apiClient.listStudents(params, signal),
    enabled: ready && role === "faculty",
  });
}
