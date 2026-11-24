# PulseGrid — Requirements

## FR-1: Foundation & Infrastructure

### FR-1.1 Repository Layout
- Monorepo with `backend/` and `frontend/` at root
- `.env.example` with all required keys as placeholders (no real secrets)
- `.gitignore` excluding `.env`, `*.db`, `__pycache__`, `node_modules`, `dist`, `backend/ml/artifacts/*.joblib`
- `start.sh` — single command to seed DB, start uvicorn (port 8000) + vite preview (port 4173)

### FR-1.2 Health Endpoint
- `GET /api/v1/health` → `{status, db_ok, model_loaded, dataset_count}` — 200 OK
- `HEAD /api/v1/health` → same 200 OK (no body) — prevents 405 on uptime monitors
- Returns `model_loaded: false` gracefully before ML artifacts are trained

### FR-1.3 Database (SQLite WAL)
- Single `pulsegrid.db` file (path from `DATABASE_URL` env)
- WAL mode enabled on connect for concurrent reads
- SQLAlchemy 2.0 async-compatible session factory
- Alembic migrations for schema versioning

### FR-1.4 Authentication & Demo Mode
- JWT-based auth with `pyjwt` + `passlib[bcrypt]`
- Two roles: `faculty`, `student`
- `DEMO_MODE=true` env var enables 1-click role switching via signed demo JWTs (no password DB needed for hackathon)
- `POST /api/v1/auth/demo-token?role=faculty|student` → returns signed JWT
- All protected endpoints require `Authorization: Bearer <token>` header

---

## FR-2: Data Models (SQLAlchemy ORM)

| Table | Key Columns | Indexes |
|---|---|---|
| `students` | id, name, roll_no, program, year | PK, roll_no unique |
| `subjects` | id, name, code, subject_type (THEORY/LAB), credits | PK |
| `weekly_records` | student_id, subject_id, week, attendance_pct, assignment_score, internal_score | (student_id, week), (student_id, subject_id) |
| `interventions` | id, student_id, faculty_id, week, intervention_type, notes, outcome | (student_id, week) |
| `prediction_snapshots` | student_id, computed_at, risk_tier, ponr_days_left, archetype, shap_json, recovery_path_json, z_scores_json, cusum_json | (student_id), (risk_tier, ponr_days_left) |

---

## FR-3: Deterministic Math Core

### FR-3.1 Cohort Z-Score Engine
- Formula: `z = (score - subject_mean) / max(subject_std, 1e-6)` per assessment per week
- Rolling 3-week velocity: `Δz_t = z_t - z_{t-3}` (slope)
- Rolling acceleration: `Δ²z_t = Δz_t - Δz_{t-3}`
- Computed for: attendance_pct, assignment_score, internal_score
- Input: DataFrame with columns `[student_id, subject_id, week, attendance_pct, assignment_score, internal_score]`
- Output: same DataFrame + `[z_att, z_assign, z_internal, v_att, v_assign, v_internal, a_att, a_assign, a_internal]`

### FR-3.2 Assignment–Internal Divergence Index
- Formula: `divergence = z_assign_avg - z_internal_avg` (averaged across subjects)
- Threshold: `divergence > 1.5` → flag `PASSIVE_COPIER_CONCEPT_GAP`
- Output: `{divergence_index: float, flagged: bool}`

### FR-3.3 CUSUM Change-Point Detector
- Baseline: mean of student's own weekly composite scores in Weeks 1–4
- One-sided downward CUSUM: `S_t = max(0, S_{t-1} + (baseline_mean - x_t) - k)` where `k = 0.5 * σ_baseline`
- Control limit `h = 4.0 * σ_baseline`
- Trigger: first week `S_t > h` → `change_point_detected=True`, `change_point_week=t`, `shift_magnitude=baseline_mean - x_t`
- Also compute EWMA: `E_t = λ * x_t + (1-λ) * E_{t-1}`, λ=0.3, flag if `E_t < baseline_mean - 1.5σ`
- Output: `{change_point_detected, change_point_week, shift_magnitude, cusum_series: list[float], ewma_series: list[float]}`
- **Test assertion:** Aarav Kulkarni must trigger `change_point_week == 7`

### FR-3.4 Per-Subject PONR Calculator
- Policy: 75% attendance per-subject minimum, 40% internal minimum
- Theory: 3 sessions/week × 14 weeks = 42 total; Lab: 2 sessions/week × 14 weeks = 28 total
- Inputs per subject: `attended_so_far`, `total_so_far`, `weeks_remaining`, `sessions_per_week`, `subject_type`
- Calculations:
  - `total_sessions = sessions_per_week * 14`
  - `remaining_sessions = sessions_per_week * weeks_remaining`
  - `min_total_needed = ceil(0.75 * total_sessions)`
  - `min_future_needed = max(0, min_total_needed - attended_so_far)`
  - `bunk_budget = remaining_sessions - min_future_needed`
  - `ponr_sessions_left = bunk_budget` (sessions left before bunking one more makes 75% impossible)
- Eligibility status:
  - `SAFE`: bunk_budget > 5
  - `WATCH`: bunk_budget in [2, 5]
  - `WINDOW_CLOSING`: bunk_budget in [0, 1]
  - `UNRECOVERABLE_WITHOUT_WAIVER`: min_future_needed > remaining_sessions
- **Test assertion:** Rohan Deshmukh must show CN Lab as `WINDOW_CLOSING` or `UNRECOVERABLE_WITHOUT_WAIVER`

### FR-3.5 Archetype Diagnoser
Priority order (first match wins):

| Archetype | Condition |
|---|---|
| `DETENTION_CLIFF` | Any subject PONR eligibility_status == WINDOW_CLOSING or UNRECOVERABLE |
| `PASSIVE_COPIER_CONCEPT_GAP` | divergence_index > 1.5 |
| `SILENT_SLIPPER` | change_point_detected AND z_composite_recent < -1.0 |
| `BROAD_DISENGAGEMENT` | ≥3 subjects with z_att < -1.0 AND z_internal < -1.0 |
| `CONCEPTUAL_STRUGGLER` | z_internal_avg < -1.0 AND z_att_avg ≥ -0.5 |

---

## FR-4: ML Pipeline (Phase 3)

### FR-4.1 Feature Vector (Leakage-Free — Weeks 1–8 Only)
Features (NO final exam marks, NO demographics):
- Per-subject: z_att_mean, z_assign_mean, z_internal_mean, v_att_slope, v_internal_slope
- Global: divergence_index, cusum_shift_magnitude, change_point_week (or 0), ewma_last
- PONR: min bunk_budget across subjects, count of WATCH/WINDOW_CLOSING subjects
- Interaction: z_assign_mean * z_internal_mean (divergence proxy)

### FR-4.2 Target Variables
- **Classification:** 4-tier risk label: `SAFE(0)`, `WATCH(1)`, `AT_RISK(2)`, `CRITICAL(3)` — derived from final exam outcome on holdout 20% split
- **Regression:** projected final exam score (0–100)

### FR-4.3 Model Comparison
Train + evaluate: `LogisticRegression`, `RandomForestClassifier`, `GradientBoostingClassifier`; regression: `Ridge`, `GradientBoostingRegressor`
Select best by At-Risk + Critical Recall on holdout set.

### FR-4.4 Output Artifacts
- `backend/ml/artifacts/classifier.joblib`
- `backend/ml/artifacts/regressor.joblib`
- `backend/ml/artifacts/model_audit.json` — real holdout metrics: `{at_risk_recall, macro_f1, roc_auc, mae, confusion_matrix, feature_importances, model_name, trained_at}`

### FR-4.5 SHAP Attributions
- `TreeExplainer` for tree models, `LinearExplainer` for LR
- Loaded once at FastAPI lifespan startup
- Per-student SHAP values stored as JSON in `prediction_snapshots.shap_json`
- Mapped to plain-English driver labels for waterfall chart

### FR-4.6 Counterfactual Recovery Solver
- Input: current feature vector, target tier = `SAFE`
- Variables: `future_attendance_pct` (per subject), `future_assignment_effort` (0–1), `future_internal_pct`
- Constraints: all variables within physically feasible bounds (remaining weeks)
- Objective: minimize total effort change (L1 norm) subject to: classifier predicts SAFE, all attendance ≥ 75%
- Method: bounded grid search + `scipy.optimize.minimize` with `method='SLSQP'`
- Output: `{recovery_steps: [{subject, action, target_value}], effort_score: float, feasible: bool}`

---

## FR-5: API Endpoints (Phase 4)

| Method | Path | Role | Description |
|---|---|---|---|
| GET/HEAD | `/api/v1/health` | Public | Health check |
| POST | `/api/v1/auth/demo-token` | Public | Get demo JWT by role |
| GET | `/api/v1/dashboard/summary` | Faculty | KPI strip + risk distribution |
| GET | `/api/v1/students` | Faculty | List with filters (archetype, risk_tier, subject) |
| GET | `/api/v1/students/{id}/analytics` | Faculty+Student* | Full analytics snapshot |
| POST | `/api/v1/simulate` | Faculty+Student* | What-If simulation (slider values) |
| GET | `/api/v1/students/{id}/recovery-plan` | Faculty+Student* | Counterfactual recovery path |
| GET | `/api/v1/interventions` | Faculty | List all interventions |
| POST | `/api/v1/interventions` | Faculty | Log new intervention |
| GET | `/api/v1/model/audit` | Faculty | model_audit.json contents |
| POST | `/api/v1/upload/csv` | Faculty | CSV/XLSX upload + re-score |

*Students can only access their own ID.

---

## FR-6: Faculty UI Views (Phase 5+)

### FR-6.1 KPI Strip
- Total students, At-Risk count, Critical count, Avg PONR days left
- Loaded from `/dashboard/summary`; skeleton while loading

### FR-6.2 Archetype Support Queue
- Filterable by archetype, risk tier, subject
- Each card: student name, archetype badge, risk tier, top SHAP driver, PONR status
- Empty state: "No students match current filters"

### FR-6.3 2×2 Mentor Triage Matrix (Phase 6)
- X-axis: Rescueability (% bunk budget remaining)
- Y-axis: Urgency (PONR days left, inverted)
- Quadrants: Act Now / Schedule / Monitor / Low Priority
- Each dot = one student; hover shows name + archetype

### FR-6.4 CSV/Excel Auto-Mapper (Phase 6)
- Upload messy CSV/XLSX with arbitrary column names
- Backend fuzzy-maps columns to canonical schema
- Preview table with column mapping + data health report (missing%, type errors)
- Confirm → batch re-score all students

### FR-6.5 Intervention Tracker (Phase 6)
- Log intervention: student, type (Remedial Class/Mentor Meeting/Assignment Extension), notes
- Before/After lift: compare prediction_snapshot risk tier before and after intervention week

### FR-6.6 Model Leakage & Fairness Audit Tab (Phase 6)
- Display all metrics from `model_audit.json`
- Confusion matrix heatmap (Recharts)
- Feature importance bar chart (top 10)
- Leakage declaration: "No final exam data used in features"

---

## FR-7: Student UI Views (Phase 5+)

### FR-7.1 PONR Reality Check Banner
- Per-subject status pill: SAFE / WATCH / WINDOW_CLOSING / UNRECOVERABLE
- For WINDOW_CLOSING: red banner "⚠ You can miss at most N more [subject] sessions"

### FR-7.2 Cohort-Calibrated Trajectory Chart
- Recharts LineChart: raw score vs cohort Z-score over weeks
- CUSUM change-point marker (vertical dashed line at trigger week)
- Toggle: show/hide cohort average band

### FR-7.3 Attribution Waterfall ("Why Flagged?")
- Horizontal bar chart of SHAP contributions
- Positive bars (risk ↑) in red; negative (risk ↓) in green
- Plain-English labels (e.g., "Missed 4 CN Labs", "Assignment–Internal gap: 2.3σ")

### FR-7.4 What-If Recovery Sliders
- Sliders for future attendance%, assignment effort, internal target per subject
- 150 ms debounce + AbortController on API call
- Live updated projected risk tier + score badge
- Clamped to [current, 100%] — cannot set impossible values
- Disable sliders + show spinner during in-flight request

### FR-7.5 1-Click Recovery Brief (Phase 7)
- Printable page (CSS `@media print`) with student name, risk summary, PONR table, recovery steps
- "Copy Mentor Alert" button → clipboard-ready text with student summary

---

## NFR: Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-1 | Dashboard + triage list endpoints respond in < 50 ms (read from pre-computed snapshots) |
| NFR-2 | Batch re-score of 240 students after CSV upload completes in < 500 ms |
| NFR-3 | Zero N+1 queries — all list endpoints use joins or selectinload |
| NFR-4 | Zero raw Python tracebacks or SQL errors exposed in HTTP responses |
| NFR-5 | SHAP explainer loaded once at lifespan startup — never reloaded per request |
| NFR-6 | Every file < 250 lines — propose split if approaching limit |
| NFR-7 | `ruff` linting passes clean (zero errors) |
| NFR-8 | `tsc --noEmit` passes clean (zero TypeScript errors) |
| NFR-9 | No sensitive demographic features (gender/caste/religion/income) in ML feature vector |
| NFR-10 | All UI metrics (F1, AUC, recall) read from `model_audit.json` — never hardcoded |
| NFR-11 | `HEAD /api/v1/health` returns 200 (not 405) |
| NFR-12 | Duplicate submit protection on all forms + file uploads |
