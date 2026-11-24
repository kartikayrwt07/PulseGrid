import { Suspense, lazy } from "react";
import { AppShell } from "./components/layout/AppShell";
import { DashboardSkeleton } from "./components/ui/Skeleton";
import { useAuth } from "./lib/auth";
import { useAppRouter } from "./lib/router";

const FacultyDashboard = lazy(() =>
  import("./pages/faculty/FacultyDashboard").then((m) => ({ default: m.FacultyDashboard })),
);
const TriageMatrix = lazy(() =>
  import("./pages/faculty/TriageMatrix").then((m) => ({ default: m.TriageMatrix })),
);
const StudentDetail = lazy(() =>
  import("./pages/faculty/StudentDetail").then((m) => ({ default: m.StudentDetail })),
);
const InterventionTracker = lazy(() =>
  import("./pages/faculty/InterventionTracker").then((m) => ({ default: m.InterventionTracker })),
);
const CsvUploader = lazy(() =>
  import("./pages/faculty/CsvUploader").then((m) => ({ default: m.CsvUploader })),
);
const ModelAuditTab = lazy(() =>
  import("./pages/faculty/ModelAuditTab").then((m) => ({ default: m.ModelAuditTab })),
);
const StudentHome = lazy(() =>
  import("./pages/student/StudentHome").then((m) => ({ default: m.StudentHome })),
);
const RecoveryPage = lazy(() =>
  import("./pages/student/RecoveryPage").then((m) => ({ default: m.RecoveryPage })),
);
const RecoveryBrief = lazy(() =>
  import("./pages/student/RecoveryBrief").then((m) => ({ default: m.RecoveryBrief })),
);

export default function App() {
  const { role, ready } = useAuth();
  const { route, navigate } = useAppRouter(role, ready);

  const openStudent = (id: number) => navigate({ page: "faculty-student", studentRef: id });

  const renderPage = () => {
    if (role === "faculty") {
      switch (route.page) {
        case "faculty-triage":
          return <TriageMatrix onSelectStudent={openStudent} />;
        case "faculty-upload":
          return (
            <CsvUploader
              onNavigateDashboard={() => navigate({ page: "faculty-dashboard" })}
            />
          );
        case "faculty-interventions":
          return <InterventionTracker onSelectStudent={openStudent} />;
        case "faculty-audit":
          return <ModelAuditTab />;
        case "faculty-brief":
          return (
            <RecoveryBrief
              studentRef={route.studentRef}
              onBack={() =>
                navigate({ page: "faculty-student", studentRef: route.studentRef })
              }
            />
          );
        case "faculty-student":
          return (
            <StudentDetail
              studentRef={route.studentRef}
              onBack={() => navigate({ page: "faculty-dashboard" })}
              onSelectStudent={openStudent}
              onOpenBrief={() =>
                navigate({ page: "faculty-brief", studentRef: route.studentRef })
              }
            />
          );
        default:
          return <FacultyDashboard onSelectStudent={openStudent} />;
      }
    }

    if (route.page === "student-brief") {
      return <RecoveryBrief onBack={() => navigate({ page: "student-home" })} />;
    }
    if (route.page === "student-recovery") {
      return <RecoveryPage />;
    }
    return <StudentHome onOpenRecovery={() => navigate({ page: "student-recovery" })} />;
  };

  return (
    <AppShell route={route} onNavigate={navigate}>
      <Suspense fallback={<DashboardSkeleton />}>{renderPage()}</Suspense>
    </AppShell>
  );
}
