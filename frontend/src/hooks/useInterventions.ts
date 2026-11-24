import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient, type InterventionCreate } from "../api/client";
import { useAuth } from "../lib/auth";

export function useInterventions(studentId?: number) {
  const { ready } = useAuth();
  return useQuery({
    queryKey: ["interventions", studentId ?? "all"],
    queryFn: ({ signal }) => apiClient.listInterventions(studentId, signal),
    enabled: ready,
  });
}

export function useCreateIntervention() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: InterventionCreate) => apiClient.createIntervention(payload),
    onSuccess: (_res, variables) => {
      void qc.invalidateQueries({ queryKey: ["interventions"] });
      void qc.invalidateQueries({ queryKey: ["student-analytics", variables.student_id] });
      void qc.invalidateQueries({ queryKey: ["students"] });
      void qc.invalidateQueries({ queryKey: ["dashboard-summary"] });
    },
  });
}
