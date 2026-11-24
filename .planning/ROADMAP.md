# PulseGrid — ROADMAP

> **Convention:** Every phase ends with a verification gate. No phase is "done" until ALL verification commands pass.

---

## Phase 1 — Foundation, Auth Skeleton, DB Schema & 240-Student Generator
**Goal:** A running FastAPI server with health check, SQLite DB seeded with 240 students (4 Hero Personas), and sample upload files. Zero analytics yet.

### Files to Create
```
Birla Hackathon/
├── .env.example
├── .gitignore
├── start.sh                            # one-command runner
├── README.md                           # placeholder
├── backend/
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   │       └── 001_initial_schema.py
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     # FastAPI app + lifespan
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py               # pydantic-settings Settings
│   │   │   ├── database.py             # SQLite WAL engine + session factory
│   │   │   ├── auth.py                 # JWT encode/decode + demo token
│   │   │   ├── dependencies.py         # get_current_user, require_faculty
│   │   │   ├── logging_config.py       # structured JSON logging
│   │   │   └── exceptions.py           # global exception handlers
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── student.py              # students table
│   │   │   ├── subject.py              # subjects table
│   │   │   ├── weekly_record.py        # weekly_records table + indexes
│   │   │   ├── intervention.py         # interventions table
│   │   │   └── snapshot.py             # prediction_snapshots table
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                 # DemoTokenRequest, TokenResponse
│   │   │   └── health.py               # HealthResponse
│   │   └── api/
│   │       ├── __init__.py
│   │       └── v1/
│   │           ├── __init__.py
│   │           ├── router.py            # top-level v1 router
│   │           ├── health.py            # GET + HEAD /health
│   │           └── auth.py              # POST /auth/demo-token
│   ├── ml/
│   │   ├── __init__.py
│   │   ├── generate_data.py            # 240 students + 4 Hero Personas seed script
│   │   └── artifacts/
│   │       └── .gitkeep
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py                  # test DB + test client fixtures
│       └── test_health.py               # GET + HEAD health assertions
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── postcss.config.js
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx                      # minimal shell with router placeholder
│       └── vite-env.d.ts
└── data/
    ├── clean_sample.csv                 # 10 clean rows with canonical columns
    └── messy_sample.xlsx                # 10 rows with messy/renamed column headers
```

### Verification Commands
```bash
# Backend
cd backend
pip install -r requirements.txt
python ml/generate_data.py          # seeds pulsegrid.db; prints "Seeded 240 students"
uvicorn app.main:app --port 8000 &
curl -s http://localhost:8000/api/v1/health | python -m json.tool
# Expected: {"status":"ok","db_ok":true,"model_loaded":false,"dataset_count":240}
curl -I http://localhost:8000/api/v1/health
# Expected: HTTP/1.1 200 OK  (HEAD must not return 405)
python -m pytest tests/test_health.py -v
# Expected: 2 passed

# Frontend
cd frontend
npm install
npm run dev &
# Expected: "Local: http://localhost:5173" with no compile errors
```

### Exit Criteria
- [ ] `GET /health` returns 200 with `db_ok:true, dataset_count:240`
- [ ] `HEAD /health` returns 200 (not 405)
- [ ] `generate_data.py` is deterministic (same seed → same Hero Persona IDs)
- [ ] `pytest tests/test_health.py` → 2 passed
- [ ] Frontend compiles without TypeScript errors
- [ ] `.env` is NOT committed; `.env.example` IS committed

---

## Phase 2 — Deterministic Math Core
**Goal:** Pure Python analytics modules (zero DB coupling) for Z-scores, Divergence, CUSUM, PONR, and Archetype. Full pytest suite asserting all 4 Hero Persona trigger conditions.

### Files to Create / Touch
```
backend/
├── app/
│   └── analytics/
│       ├── __init__.py
│       ├── zscore.py          # Cohort Z-Score Engine + velocity/acceleration
│       ├── divergence.py      # Assignment–Internal Divergence Index
│       ├── cusum.py           # CUSUM + EWMA Change-Point Detector
│       ├── ponr.py            # Per-Subject PONR Calculator
│       └── archetype.py       # 5-Archetype Diagnoser (priority order)
└── tests/
    ├── fixtures/
    │   └── hero_personas.py   # fixture DataFrames for 4 Hero Personas
    ├── test_zscore.py
    ├── test_divergence.py
    ├── test_cusum.py
    ├── test_ponr.py
    └── test_archetypes.py
```

### Key Test Assertions
```python
# test_cusum.py
def test_aarav_cusum_fires_week_7():
    result = detect_cusum(aarav_weekly_scores)
    assert result["change_point_detected"] is True
    assert result["change_point_week"] == 7

# test_ponr.py
def test_rohan_cn_lab_ponr():
    result = calculate_ponr(rohan_cn_lab_data)
    assert result["eligibility_status"] in ("WINDOW_CLOSING", "UNRECOVERABLE_WITHOUT_WAIVER")

# test_zscore.py
def test_tough_exam_wave_no_false_flag():
    # When entire cohort scores low, z-scores stay near 0 — no individual flag
    result = compute_zscores(tough_exam_cohort_df)
    assert all(abs(z) < 1.0 for z in result["z_internal"])

# test_divergence.py
def test_meera_divergence_flagged():
    result = compute_divergence(meera_scores)
    assert result["divergence_index"] > 1.5
    assert result["flagged"] is True

# test_archetypes.py
def test_archetype_priority_order():
    # Student with both DETENTION_CLIFF and PASSIVE_COPIER conditions
    # must resolve to DETENTION_CLIFF (higher priority)
    ...
```

### Verification Commands
```bash
cd backend
python -m pytest tests/test_zscore.py tests/test_divergence.py tests/test_cusum.py tests/test_ponr.py tests/test_archetypes.py -v
# Expected: all tests pass; Aarav→Week7, Rohan→PONR, Meera→divergence, tough-wave→no false flag
ruff check app/analytics/
# Expected: no linting errors
```

### Exit Criteria
- [x] `test_cusum.py::test_aarav_cusum_fires_week_7` passes
- [x] `test_ponr.py::test_rohan_cn_lab_ponr` passes
- [x] `test_zscore.py::test_tough_exam_wave_no_false_flag` passes
- [x] `test_divergence.py::test_meera_divergence_flagged` passes
- [x] All archetype priority-order tests pass
- [x] `ruff check` clean on `app/analytics/`
- [x] Every analytics file < 250 lines

---

## Phase 3 — Leakage-Free ML Pipeline, SHAP & Counterfactual Solver
**Goal:** Train/evaluate classifier + regressor on Weeks 1–8 features, produce real `model_audit.json`, persist SHAP per-student, run counterfactual solver, and store all results in `prediction_snapshots`.

### Files to Create / Touch
```
backend/
├── app/
│   ├── analytics/
│   │   ├── features.py         # feature extraction from weekly_records → feature DataFrame
│   │   ├── ml_inference.py     # singleton loader + predict() + shap_values()
│   │   └── recovery_solver.py  # constrained counterfactual optimizer
│   ├── services/
│   │   ├── __init__.py
│   │   └── snapshot_service.py # orchestrate: features→ML→SHAP→PONR→archetype→save snapshot
│   └── models/
│       └── snapshot.py         # update: add shap_json, recovery_path_json columns
├── ml/
│   ├── train_and_evaluate.py   # temporal split, train 3 classifiers, pick best, save artifacts
│   └── artifacts/
│       ├── classifier.joblib
│       ├── regressor.joblib
│       ├── feature_names.json
│       └── model_audit.json    # real holdout metrics
└── tests/
    ├── test_features.py         # assert no final-exam columns in feature vector
    ├── test_ml_inference.py     # assert predict() returns valid tier
    ├── test_recovery_solver.py  # assert solution within physical bounds
    └── test_anti_leakage.py     # assert feature_names has no final_exam_* columns
```

### Key Test Assertions
```python
# test_anti_leakage.py
def test_no_final_exam_features():
    with open("ml/artifacts/feature_names.json") as f:
        features = json.load(f)
    assert not any("final" in f.lower() or "exam_score" in f.lower() for f in features)

# test_recovery_solver.py
def test_solution_within_physical_bounds():
    solution = solve_recovery(at_risk_student_features, weeks_remaining=5)
    assert solution["feasible"] is True
    for step in solution["recovery_steps"]:
        assert 0.0 <= step["target_value"] <= 1.0

# test_ml_inference.py
def test_predict_returns_valid_tier():
    tier = predict_risk(sample_feature_vector)
    assert tier in (0, 1, 2, 3)  # SAFE, WATCH, AT_RISK, CRITICAL
```

### Verification Commands
```bash
cd backend
python ml/train_and_evaluate.py
# Expected: prints model comparison table, saves artifacts, prints macro-F1 > 0.5
cat ml/artifacts/model_audit.json | python -m json.tool
# Expected: at_risk_recall, macro_f1, roc_auc, mae, confusion_matrix all present
python -m pytest tests/test_features.py tests/test_ml_inference.py tests/test_recovery_solver.py tests/test_anti_leakage.py -v
ruff check app/analytics/ app/services/
```

### Exit Criteria
- [x] `model_audit.json` exists with real holdout metrics (not hardcoded)
- [x] `test_anti_leakage.py` passes (no final exam features)
- [x] `test_recovery_solver.py` passes (solution in bounds, feasible=True)
- [x] All 240 students have a row in `prediction_snapshots` after seed
- [x] SHAP values stored as valid JSON in snapshots
- [x] `ruff` clean

---

## Phase 4 — FastAPI Core APIs & OpenAPI TypeScript Contract
**Goal:** All 11 API endpoints live, Pydantic-validated, role-guarded, backed by repository layer, and TypeScript types auto-generated from `/openapi.json`.

### Files to Create / Touch
```
backend/
├── app/
│   ├── schemas/
│   │   ├── student.py          # StudentSummary, StudentDetail, StudentListResponse
│   │   ├── analytics.py        # AnalyticsSnapshot, CUSUMResult, PONRResult, SHAPEntry
│   │   ├── dashboard.py        # DashboardSummary, KPIStrip, RiskDistribution
│   │   ├── simulation.py       # SimulateRequest, SimulateResponse
│   │   ├── recovery.py         # RecoveryPlanResponse, RecoveryStep
│   │   ├── intervention.py     # InterventionCreate, InterventionResponse
│   │   ├── upload.py           # UploadResult, ColumnMappingPreview
│   │   └── model_audit.py      # ModelAuditResponse
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── student_repo.py     # list_students (joins snapshot), get_student_analytics
│   │   ├── dashboard_repo.py   # get_summary (single indexed query)
│   │   ├── intervention_repo.py
│   │   └── snapshot_repo.py    # get_snapshot, upsert_snapshot
│   └── api/v1/
│       ├── students.py         # GET /students, GET /students/{id}/analytics
│       ├── dashboard.py        # GET /dashboard/summary
│       ├── simulate.py         # POST /simulate
│       ├── recovery.py         # GET /students/{id}/recovery-plan
│       ├── interventions.py    # GET/POST /interventions
│       ├── model.py            # GET /model/audit
│       └── upload.py           # POST /upload/csv
└── tests/
    ├── test_api_students.py
    ├── test_api_dashboard.py
    ├── test_api_simulate.py
    ├── test_api_auth.py        # demo token, role enforcement
    └── test_api_upload.py

frontend/
└── src/
    └── api/
        ├── client.ts           # typed fetch wrapper using generated types
        └── types.ts            # auto-generated from openapi.json (openapi-typescript)
```

### Key Test Assertions
```python
# test_api_auth.py
def test_student_cannot_access_other_student():
    token = get_demo_token("student", student_id=1)
    res = client.get("/api/v1/students/2/analytics", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403

def test_student_cannot_access_all_students():
    token = get_demo_token("student", student_id=1)
    res = client.get("/api/v1/students", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403

# test_api_simulate.py
def test_simulate_clamps_impossible_slider():
    payload = {"attendance_pct": 110.0, "subject_id": 1}  # impossible value
    res = client.post("/api/v1/simulate", json=payload, headers=faculty_headers)
    assert res.status_code == 422  # Pydantic validation error
```

### Verification Commands
```bash
cd backend
uvicorn app.main:app --port 8000 &
python -m pytest tests/test_api_students.py tests/test_api_dashboard.py tests/test_api_simulate.py tests/test_api_auth.py tests/test_api_upload.py -v
curl -s http://localhost:8000/openapi.json > /tmp/openapi.json

cd frontend
npx openapi-typescript http://localhost:8000/openapi.json -o src/api/types.ts
npx tsc --noEmit
# Expected: no TypeScript errors
```

### Exit Criteria
- [x] All 11 endpoints return correct status codes for valid + invalid requests
- [x] Student role cannot access other student's data (403)
- [x] Impossible slider values rejected with 422
- [x] `src/api/types.ts` generated and `tsc --noEmit` passes
- [x] `pytest` API test suite → all pass
- [x] Zero N+1 queries (verified via SQLAlchemy `before_cursor_execute` assertion)

---

## Phase 5 — Vertical-Slice Faculty & Student UI ⭐ MVP FREEZE GATE
**Goal:** Complete, demoable, polished React UI for both roles. After this phase the core product is shippable. Every view has loading/empty/error states.

### Files to Create / Touch
```
frontend/src/
├── lib/
│   ├── queryClient.ts       # @tanstack/react-query client + stale times
│   ├── auth.ts              # demo token storage + role switcher logic
│   └── utils.ts             # cn(), formatPct(), riskTierColor()
├── components/
│   ├── ui/
│   │   ├── Skeleton.tsx
│   │   ├── ErrorBanner.tsx
│   │   ├── EmptyState.tsx
│   │   ├── Spinner.tsx
│   │   ├── Badge.tsx        # risk tier + archetype colored badges
│   │   └── RoleSwitcher.tsx # 1-click faculty ↔ student switcher
│   ├── charts/
│   │   ├── TrajectoryChart.tsx   # Recharts LineChart + CUSUM marker
│   │   └── WaterfallChart.tsx    # SHAP attribution horizontal bars
│   └── layout/
│       ├── AppShell.tsx
│       ├── Sidebar.tsx
│       └── TopBar.tsx
├── pages/
│   ├── faculty/
│   │   ├── FacultyDashboard.tsx  # KPI strip + support queue
│   │   └── StudentDetail.tsx     # full analytics view (faculty view)
│   └── student/
│       ├── StudentHome.tsx       # PONR banner + trajectory chart
│       └── RecoveryPage.tsx      # attribution waterfall + what-if sliders
├── hooks/
│   ├── useDashboardSummary.ts
│   ├── useStudents.ts
│   ├── useStudentAnalytics.ts
│   ├── useSimulate.ts           # debounced, AbortController
│   └── useRecoveryPlan.ts
└── App.tsx                      # route switch: /faculty/* vs /student/*
```

### Key UX Requirements
- `RoleSwitcher` calls `POST /auth/demo-token`, stores JWT in memory (not localStorage), triggers React Query cache invalidation
- Trajectory chart: dual Y-axis (raw score left, Z-score right), CUSUM change-point rendered as `<ReferenceLine>` with label
- Waterfall chart: positive SHAP → red bars; negative SHAP → green bars; sorted by absolute magnitude
- What-If sliders: `useDebounce(150ms)` + `AbortController` cancel on each new slider move; slider `min` clamped to current value, `max=100`
- All pages wrapped in `<ErrorBoundary>` + `<Suspense>` with `<Skeleton>` fallback

### Verification Commands
```bash
# Backend must be running on :8000
cd frontend
npm run build        # must succeed with zero TypeScript errors
npm run preview &    # starts on :4173
# Manual smoke test: open http://localhost:4173
# - Switch to Faculty role → see KPI strip with 240 students
# - Click Aarav Kulkarni → see CUSUM change-point line at Week 7
# - Switch to Student role (Aarav) → see PONR banner, trajectory, waterfall
# - Move a slider → risk tier updates within ~300ms
npx tsc --noEmit
npm run lint         # vitest type coverage
```

### Exit Criteria
- [x] Faculty KPI strip shows real data from API (not hardcoded)
- [x] Support queue shows Aarav with `SILENT_SLIPPER` badge
- [x] Student view shows Rohan's CN Lab as `WINDOW_CLOSING`/`UNRECOVERABLE`
- [x] CUSUM marker visible on Aarav's trajectory chart at Week 7
- [x] What-If slider debounce works (`AbortController` cancellation wired cleanly)
- [x] All loading/empty/error states visible and correct
- [x] `npm run build` passes with zero errors

---

## Phase 6 — Judge-Winning Differentiators
**Goal:** Add the 4 advanced features that separate PulseGrid from generic dashboards.

### Files to Create / Touch
```
frontend/src/
├── pages/faculty/
│   ├── TriageMatrix.tsx       # 2×2 scatter plot (Urgency vs. Rescueability)
│   ├── CsvUploader.tsx        # drag-drop + column auto-mapper preview
│   ├── InterventionTracker.tsx # log + before/after lift display
│   └── ModelAuditTab.tsx       # metrics + confusion matrix + feature importance

backend/app/
├── services/
│   ├── csv_mapper.py          # fuzzy column name mapping (difflib, no extra deps)
│   └── intervention_service.py # lift calculation: snapshot delta before/after
├── api/v1/
│   └── upload.py              # update: return column mapping preview + data health report
└── tests/
    ├── test_csv_mapper.py     # assert messy headers map to canonical names
    └── test_intervention_lift.py
```

### Verification Commands
```bash
# Backend
cd backend
python -m pytest tests/test_csv_mapper.py tests/test_intervention_lift.py -v
# Upload data/messy_sample.xlsx via UI → verify column mapping preview shows correct matches

# Frontend
cd frontend
npm run build
# Manual: open Triage Matrix → verify 4 quadrants with student dots
# Manual: upload messy_sample.xlsx → see column mapping preview
# Manual: log intervention for Priya → see before/after lift badge
```

### Exit Criteria
- [x] Triage Matrix renders with 240 student dots in correct quadrants
- [x] Messy XLSX upload: at least 4 of 6 columns auto-mapped correctly
- [x] Intervention log → lift badge shows tier change for Priya Sharma
- [x] Model Audit Tab shows real metrics from `model_audit.json`
- [x] Confusion matrix heatmap renders
- [x] `test_csv_mapper.py` passes
- [x] `npm run build` clean

---

## Phase 7 — Off-Dashboard Actionability & Full Hardening
**Goal:** Recovery Brief print layout, Mentor Alert Digest, edge-case tests, and clean pass on all linters + E2E tests.

### Files to Create / Touch
```
frontend/src/
├── pages/student/
│   └── RecoveryBrief.tsx     # print-optimized page (CSS @media print)
└── components/
    └── MentorAlertDigest.tsx  # copyable text block

backend/tests/
├── test_csv_edge_cases.py    # malformed CSV, missing columns, unicode filenames
└── test_slider_clamping.py   # simulate endpoint rejects out-of-bound slider values

frontend/
└── e2e/
    ├── hero_aarav.spec.ts    # Aarav: CUSUM marker at Week 7, risk badge CRITICAL/AT_RISK
    ├── hero_meera.spec.ts    # Meera: divergence badge, PASSIVE_COPIER archetype
    ├── hero_rohan.spec.ts    # Rohan: CN Lab PONR banner WINDOW_CLOSING
    └── hero_priya.spec.ts    # Priya: post-intervention upward trajectory visible
```

### Verification Commands
```bash
# Backend hardening
cd backend
python -m pytest tests/test_csv_edge_cases.py tests/test_slider_clamping.py -v
ruff check app/
# Expected: 0 errors

# Frontend hardening
cd frontend
npx tsc --noEmit
# Expected: 0 errors
npm run build

# E2E (requires backend + frontend running)
npx playwright test e2e/
# Expected: 4 hero persona scenarios all pass
```

### Exit Criteria
- [x] `ruff check app/` → 0 errors
- [x] `tsc --noEmit` → 0 errors
- [x] All 4 Playwright E2E scenarios pass (`4 passed (7.0s)`)
- [x] Recovery Brief page renders correctly with `@media print` styling
- [x] "Copy Mentor Alert" button & digest card implemented
- [x] Edge-case CSV tests pass (headers-only, corrupted xlsx, all-null column, unicode/path-traversal headers)
- [x] Slider clamping test: `simulate` rejects out-of-range inputs with 422

---

## Phase 8 — Local Demo Lock & Pitch Prep
**Goal:** Bulletproof 1-command offline demo, final README, and pitch demo script.

### Files to Create / Touch
```
Birla Hackathon/
├── start.sh                  # update: full demo startup in one command
├── README.md                 # update: complete with architecture diagram + quickstart
└── PITCH_DEMO_SCRIPT.md      # step-by-step judge walkthrough (5 min script)

backend/
└── app/api/v1/
    └── health.py             # verify HEAD + GET both return 200 (regression test)
```

### `start.sh` (Full Demo Runner)
```bash
#!/usr/bin/env bash
set -e
echo "🚀 Starting PulseGrid Demo..."

# Backend
cd backend
pip install -r requirements.txt -q
cp -n ../.env.example ../.env 2>/dev/null || true
python ml/generate_data.py
python ml/train_and_evaluate.py
uvicorn app.main:app --port 8000 --log-level warning &
BACKEND_PID=$!
echo "✅ Backend running on http://localhost:8000"

# Frontend
cd ../frontend
npm install -q
npm run build
npm run preview -- --port 4173 &
FRONTEND_PID=$!
echo "✅ Frontend running on http://localhost:4173"

echo ""
echo "🎯 PulseGrid is ready!"
echo "   Open: http://localhost:4173"
echo "   API:  http://localhost:8000/api/v1/health"
echo ""
echo "Press Ctrl+C to stop."
wait
```

### Verification Commands
```bash
# Full end-to-end demo validation
bash start.sh &
sleep 15
curl -s http://localhost:8000/api/v1/health | python -m json.tool
# Expected: status=ok, db_ok=true, model_loaded=true, dataset_count=240
curl -I http://localhost:8000/api/v1/health
# Expected: HTTP/1.1 200 OK
curl -s http://localhost:4173 | grep -i "pulsegrid"
# Expected: HTML title contains PulseGrid
```

### Exit Criteria
- [x] `bash start.sh` updated for clean offline demo orchestration with dynamic port support
- [x] `GET /health` returns `model_loaded: true` and `dataset_count: 240`
- [x] `HEAD /health` returns 200 (not 405)
- [x] Frontend accessible at `localhost:4173`
- [x] `PITCH_DEMO_SCRIPT.md` covers all 4 Hero Personas in <= 5 minutes
- [x] `README.md` has: quickstart, architecture overview, tech stack, known limitations

---

## Status Tracker

| Phase | Status | Gate |
|---|---|---|
| Phase 1 — Foundation | ✅ Done | `pytest test_health.py` → 2 passed; `ruff` clean; `vite build` clean |
| Phase 2 — Math Core | ✅ Done | All 5 math test files pass (48 tests); `ruff` clean |
| Phase 3 — ML Pipeline | ✅ Done | `model_audit.json` generated; 240 snapshots persisted; 64 pytest pass; `ruff` clean |
| Phase 4 — APIs | ✅ Done | All 11 routes live; zero N+1 verified; 85 pytest pass; `types.ts` + `tsc` + `vite build` clean |
| Phase 5 — UI MVP ⭐ | ✅ Done | `tsc --noEmit` + `vite build` clean; Playwright live UI smoke check passed |
| Phase 6 — Differentiators | ✅ Done | Triage matrix (240 dots), fuzzy XLSX auto-mapper, intervention lift, model audit verified |
| Phase 7 — Hardening | ✅ Done | `ruff` + `tsc` + `102 pytest` clean; Playwright E2E × 4 pass |
| Phase 8 — Pitch Lock | ✅ Done | Live `GET`/`HEAD /health`, `localhost:4173`, 4 E2E, `README.md`, `PITCH_DEMO_SCRIPT.md`, `start.sh` |

---

## Configuration Reference

```ini
# .env.example
DATABASE_URL=sqlite:///./pulsegrid.db
SECRET_KEY=change-me-use-openssl-rand-hex-32
DEMO_MODE=true
CORS_ORIGINS=http://localhost:5173,http://localhost:4173
CURRENT_WEEK=9
TOTAL_WEEKS=14
ATTENDANCE_THRESHOLD=0.75
INTERNAL_THRESHOLD=0.40
THEORY_SESSIONS_PER_WEEK=3
LAB_SESSIONS_PER_WEEK=2
LOG_LEVEL=INFO
```
