import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../api/client";
import { useAuth } from "../lib/auth";

export function useModelAudit() {
  const { ready } = useAuth();
  return useQuery({
    queryKey: ["model-audit"],
    queryFn: ({ signal }) => apiClient.getModelAudit(signal),
    enabled: ready,
  });
}
