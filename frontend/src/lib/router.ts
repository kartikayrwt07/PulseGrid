import { useCallback, useEffect, useState } from "react";
import type { AppRoute } from "../components/layout/Sidebar";
import type { UserRole } from "./auth";

export function parsePathname(pathname: string): AppRoute {
  const clean = pathname.replace(/\/+$/, "") || "/";
  if (clean === "/" || clean === "/faculty/dashboard") {
    return { page: "faculty-dashboard" };
  }
  if (clean === "/faculty/triage") return { page: "faculty-triage" };
  if (clean === "/faculty/interventions") return { page: "faculty-interventions" };
  if (clean === "/faculty/upload") return { page: "faculty-upload" };
  if (clean === "/faculty/model-audit") return { page: "faculty-audit" };
  if (clean === "/student/home") return { page: "student-home" };
  if (clean === "/student/recovery") return { page: "student-recovery" };
  if (clean === "/student/brief") return { page: "student-brief" };

  const briefMatch = /^\/faculty\/students\/([^/]+)\/brief$/.exec(clean);
  if (briefMatch) {
    const raw = decodeURIComponent(briefMatch[1]);
    return { page: "faculty-brief", studentRef: /^\d+$/.test(raw) ? Number(raw) : raw };
  }
  const stuMatch = /^\/faculty\/students\/([^/]+)$/.exec(clean);
  if (stuMatch) {
    const raw = decodeURIComponent(stuMatch[1]);
    return { page: "faculty-student", studentRef: /^\d+$/.test(raw) ? Number(raw) : raw };
  }
  return { page: "faculty-dashboard" };
}

export function routeToPath(route: AppRoute): string {
  switch (route.page) {
    case "faculty-dashboard":
      return "/faculty/dashboard";
    case "faculty-triage":
      return "/faculty/triage";
    case "faculty-interventions":
      return "/faculty/interventions";
    case "faculty-upload":
      return "/faculty/upload";
    case "faculty-audit":
      return "/faculty/model-audit";
    case "faculty-student":
      return `/faculty/students/${encodeURIComponent(String(route.studentRef))}`;
    case "faculty-brief":
      return `/faculty/students/${encodeURIComponent(String(route.studentRef))}/brief`;
    case "student-home":
      return "/student/home";
    case "student-recovery":
      return "/student/recovery";
    case "student-brief":
      return "/student/brief";
  }
}

export function defaultRouteForRole(role: UserRole): AppRoute {
  return role === "faculty" ? { page: "faculty-dashboard" } : { page: "student-home" };
}

export function isRouteAllowedForRole(route: AppRoute, role: UserRole): boolean {
  const isStudentRoute = route.page.startsWith("student-");
  return role === "student" ? isStudentRoute : !isStudentRoute;
}

export function useAppRouter(role: UserRole, ready: boolean) {
  const [route, setRouteState] = useState<AppRoute>(() =>
    parsePathname(typeof window !== "undefined" ? window.location.pathname : "/"),
  );

  const navigate = useCallback((next: AppRoute, replace = false) => {
    setRouteState(next);
    const nextPath = routeToPath(next);
    if (typeof window !== "undefined" && window.location.pathname !== nextPath) {
      if (replace) {
        window.history.replaceState(null, "", nextPath);
      } else {
        window.history.pushState(null, "", nextPath);
      }
    }
  }, []);

  useEffect(() => {
    const onPopState = () => setRouteState(parsePathname(window.location.pathname));
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  useEffect(() => {
    if (!ready) return;
    if (!isRouteAllowedForRole(route, role)) {
      navigate(defaultRouteForRole(role), true);
    }
  }, [ready, role, route, navigate]);

  return { route, navigate };
}
