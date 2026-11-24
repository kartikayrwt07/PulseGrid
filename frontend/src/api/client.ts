import type { components, operations } from "./types";

export type Schemas = components["schemas"];
export type TokenResponse = Schemas["TokenResponse"];
export type HealthResponse = Schemas["HealthResponse"];
export type DashboardSummary = Schemas["DashboardSummaryResponse"];
export type StudentSummary = Schemas["StudentSummary"];
export type StudentListResponse = Schemas["StudentListResponse"];
export type StudentAnalytics = Schemas["StudentAnalyticsResponse"];
export type SimulateRequest = Schemas["SimulateRequest"];
export type SimulateResponse = Schemas["SimulateResponse"];
export type RecoveryPlan = Schemas["RecoveryPlanResponse"];
export type InterventionCreate = Schemas["InterventionCreate"];
export type InterventionResponse = Schemas["InterventionResponse"];
export type InterventionListResponse = Schemas["InterventionListResponse"];
export type ModelAudit = Schemas["ModelAuditResponse"];
export type UploadResult = Schemas["UploadResult"];
export type DemoResetResponse = Schemas["DemoResetResponse"];
export type TimeMachineResponse = Schemas["TimeMachineResponse"];
export type StudentListQuery = operations["list_students_api_v1_students_get"]["parameters"]["query"];

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "") + "/api/v1";
let authToken: string | null = null;

export function setAuthToken(token: string | null): void {
  authToken = token;
}

export function getAuthToken(): string | null {
  return authToken;
}

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(status: number, message: string, code = `HTTP_${status}`) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

async function requestJson<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers);
  if (authToken) {
    headers.set("Authorization", `Bearer ${authToken}`);
  }
  if (!(init.body instanceof FormData) && init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    let code = `HTTP_${res.status}`;
    try {
      const errBody = (await res.json()) as { detail?: string; code?: string };
      if (errBody.detail) message = errBody.detail;
      if (errBody.code) code = errBody.code;
    } catch {
      // Keep generic user-safe error if response body is non-JSON
    }
    throw new ApiError(res.status, message, code);
  }
  return (await res.json()) as T;
}

export const apiClient = {
  getHealth(signal?: AbortSignal): Promise<HealthResponse> {
    return requestJson<HealthResponse>("/health", { signal });
  },

  issueDemoToken(
    role: "faculty" | "student",
    studentId?: number,
    signal?: AbortSignal,
  ): Promise<TokenResponse> {
    const qs = new URLSearchParams({ role });
    if (role === "student" && studentId !== undefined) {
      qs.set("student_id", String(studentId));
    }
    return requestJson<TokenResponse>(`/auth/demo-token?${qs.toString()}`, {
      method: "POST",
      signal,
    });
  },

  getDashboardSummary(signal?: AbortSignal): Promise<DashboardSummary> {
    return requestJson<DashboardSummary>("/dashboard/summary", { signal });
  },

  getTimeMachine(week?: number, signal?: AbortSignal): Promise<TimeMachineResponse> {
    const suffix = week !== undefined ? `?week=${week}` : "";
    return requestJson<TimeMachineResponse>(`/dashboard/time-machine${suffix}`, { signal });
  },

  listStudents(params?: StudentListQuery, signal?: AbortSignal): Promise<StudentListResponse> {
    const qs = new URLSearchParams();
    if (params?.risk_tier) qs.set("risk_tier", params.risk_tier);
    if (params?.archetype) qs.set("archetype", params.archetype);
    if (params?.search) qs.set("search", params.search);
    if (params?.sort_by) qs.set("sort_by", params.sort_by);
    if (params?.limit !== undefined) qs.set("limit", String(params.limit));
    if (params?.offset !== undefined) qs.set("offset", String(params.offset));
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    return requestJson<StudentListResponse>(`/students${suffix}`, { signal });
  },

  getStudentAnalytics(studentId: number, signal?: AbortSignal): Promise<StudentAnalytics> {
    return requestJson<StudentAnalytics>(`/students/${studentId}/analytics`, { signal });
  },

  getRecoveryPlan(studentId: number, signal?: AbortSignal): Promise<RecoveryPlan> {
    return requestJson<RecoveryPlan>(`/students/${studentId}/recovery-plan`, { signal });
  },

  simulateWhatIf(payload: SimulateRequest, signal?: AbortSignal): Promise<SimulateResponse> {
    return requestJson<SimulateResponse>("/simulate", {
      method: "POST",
      body: JSON.stringify(payload),
      signal,
    });
  },

  listInterventions(studentId?: number, signal?: AbortSignal): Promise<InterventionListResponse> {
    const suffix = studentId !== undefined ? `?student_id=${studentId}` : "";
    return requestJson<InterventionListResponse>(`/interventions${suffix}`, { signal });
  },

  createIntervention(payload: InterventionCreate): Promise<InterventionResponse> {
    return requestJson<InterventionResponse>("/interventions", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  getModelAudit(signal?: AbortSignal): Promise<ModelAudit> {
    return requestJson<ModelAudit>("/model/audit", { signal });
  },

  uploadAcademicFile(file: File, commit = false): Promise<UploadResult> {
    const form = new FormData();
    form.append("file", file);
    return requestJson<UploadResult>(`/upload/csv?commit=${commit ? "true" : "false"}`, {
      method: "POST",
      body: form,
    });
  },

  resetDemoCohort(): Promise<DemoResetResponse> {
    return requestJson<DemoResetResponse>("/admin/reset-demo", { method: "POST" });
  },
};
