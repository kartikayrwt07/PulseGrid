import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { apiClient, setAuthToken } from "../api/client";
import { queryClient } from "./queryClient";

export type UserRole = "faculty" | "student";

interface AuthState {
  role: UserRole;
  studentId: number | null;
  ready: boolean;
  switching: boolean;
  error: string | null;
}

interface AuthContextValue extends AuthState {
  switchRole: (role: UserRole, studentId?: number) => Promise<void>;
  retryAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const STORAGE_ROLE_KEY = "pg_demo_role";
const STORAGE_SID_KEY = "pg_demo_student_id";

function readInitialAuth(): { role: UserRole; studentId?: number } {
  if (typeof window === "undefined") return { role: "faculty" };
  const savedRole = window.sessionStorage.getItem(STORAGE_ROLE_KEY);
  if (savedRole === "student") {
    const sid = Number(window.sessionStorage.getItem(STORAGE_SID_KEY) ?? "1");
    return { role: "student", studentId: Number.isFinite(sid) && sid >= 1 ? sid : 1 };
  }
  return { role: "faculty" };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    role: "faculty",
    studentId: null,
    ready: false,
    switching: false,
    error: null,
  });

  const authenticate = useCallback(async (role: UserRole, studentId?: number) => {
    setState((prev) => ({ ...prev, switching: true, error: null }));
    try {
      const targetStudentId = role === "student" ? (studentId ?? 1) : undefined;
      const res = await apiClient.issueDemoToken(role, targetStudentId);
      if (typeof window !== "undefined") {
        window.sessionStorage.setItem(STORAGE_ROLE_KEY, res.role);
        if (res.role === "student" && res.student_id) {
          window.sessionStorage.setItem(STORAGE_SID_KEY, String(res.student_id));
        } else {
          window.sessionStorage.removeItem(STORAGE_SID_KEY);
        }
      }
      await queryClient.cancelQueries();
      setAuthToken(res.access_token);
      queryClient.clear();
      setState({
        role: res.role,
        studentId: res.student_id ?? null,
        ready: true,
        switching: false,
        error: null,
      });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Could not connect to PulseGrid authentication service.";
      setState((prev) => ({
        ...prev,
        ready: false,
        switching: false,
        error: message,
      }));
    }
  }, []);

  useEffect(() => {
    const init = readInitialAuth();
    void authenticate(init.role, init.studentId);
  }, [authenticate]);

  const retryAuth = useCallback(async () => {
    await authenticate(state.role, state.studentId ?? undefined);
  }, [authenticate, state.role, state.studentId]);

  return (
    <AuthContext.Provider value={{ ...state, switchRole: authenticate, retryAuth }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
