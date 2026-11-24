# PulseGrid — Full Project Context & Architecture Brief for AI Review

> **How to use this file:** Paste or attach this document to any AI reviewer and ask: *"Review this architecture, ML design, security boundaries, UX flows, and implementation tradeoffs. Identify blind spots, statistical edge cases, missing features, and concrete improvements before hackathon submission or productionization."*

---

## 1. Problem Statement & Core Thesis

- **Project Name:** PulseGrid — Cohort-Calibrated Academic Early-Warning & Recovery Engine
- **Core Problem:** Universities typically detect struggling students only after mid-semester failures or final exams, when attendance rules or cumulative mark deficits make passing mathematically impossible. Conversely, naive static thresholds (e.g., `< 60%`) both miss high-baseline students who silently slip (89% → 74%) and flood advisors with false alarms whenever a single tough exam lowers the whole class average.
- **Constraints Locked:**
  - **100% Local & Zero External AI APIs:** Runs offline with local `scikit-learn`, `shap`, and `scipy` over SQLite (WAL mode). No OpenAI/Gemini runtime calls.
  - **University Policy Defaults (Configurable via `.env`):** 75% per-subject minimum attendance, 40% aggregate internal assessment minimum, 14-week semester, Theory = 3 sessions/week (`42` total), Lab = 2 sessions/week (`28` total). Current snapshot state = Week 9 of 14.
  - **Hard Guardrails:** ~250-line target per code file, Pydantic boundary validation, JWT RBAC (`faculty` vs `student` scoped access), zero N+1 SQL queries, loading/empty/error states on every UI view.

---

## 2. Verified Technology Stack

| Layer | Technologies |
|---|---|
| **Backend API** | FastAPI, Uvicorn, Pydantic v2, Pydantic-Settings, PyJWT, Python-Multipart |
| **Database & ORM** | SQLAlchemy 2.0, Alembic (`001_initial_schema.py`), SQLite WAL mode |
| **Analytics & ML** | NumPy, Pandas, SciPy (`minimize` SLSQP), scikit-learn (`LogisticRegression`, `RandomForest`, `GradientBoostingClassifier`, `GradientBoostingRegressor`), SHAP, Joblib, OpenPyXL |
| **Frontend** | React 19, TypeScript (strict), Vite 6, Tailwind CSS 3, Recharts, TanStack React Query v5, `openapi-typescript`, Lucide React |
| **QA & Tooling** | `pytest` (102 tests), `playwright` (`4` E2E specs in `playwright/test`), `ruff`, `tsc --noEmit` |

---

## 3. Database Schema (5 Tables in SQLite WAL)

Defined in `backend/app/models/` and `backend/alembic/versions/001_initial_schema.py`:

1. **`students`** — `id`, `roll_no` (unique index), `name`, `program`, `year`, `is_hero_persona` (bool), `persona_tag`
2. **`subjects`** — `id`, `code` (unique index), `name`, `subject_type` (`THEORY` | `LAB`), `sessions_per_week`, `credits`
   - Seeded subjects: `MA101` Mathematics (Theory 3/wk), `CS201` Data Structures (Theory 3/wk), `CS301` Computer Networks (Theory 3/wk), `CS301L` CN Lab (Lab 2/wk), `CS302` DBMS (Theory 3/wk), `CS303` Operating Systems (Theory 3/wk).
3. **`weekly_records`** — `id`, `student_id` (FK), `subject_id` (FK), `week`, `attended_sessions`, `total_sessions`, `attendance_pct`, `assignment_score`, `internal_score`; composite indexes `(student_id, week)`, `(student_id, subject_id)` and unique constraint `(student_id, subject_id, week)`.
4. **`interventions`** — `id`, `student_id` (FK), `faculty_id`, `week`, `intervention_type`, `notes`, `outcome`, `pre_risk_tier`, `created_at`.
5. **`prediction_snapshots`** — Precomputed analytics per student (1:1 unique `student_id`):
   - Indexed scalars: `risk_tier`, `risk_score`, `projected_final_score`, `ponr_days_left` (composite index `(risk_tier, ponr_days_left)`), `archetype`, `divergence_index`, `cusum_triggered`, `cusum_week`.
   - JSON blobs: `z_scores_json` (weekly series + baseline ML features), `cusum_json`, `ponr_json`, `shap_json`, `recovery_path_json`.

---

## 4. Analytical & ML Pipeline (All Implemented & Tested)

### A. Deterministic Math Core (`backend/app/analytics/`)
1. **`zscore.py`**:
   - Per `(subject_id, week)` cohort Z-scores: `z = (score - cohort_mean) / max(cohort_std, 1e-6)` for `attendance_pct`, `assignment_score`, `internal_score`.
   - 3-week backward velocity (`v_* = z_t - z_{t-3}`) and acceleration (`a_* = v_t - v_{t-3}`).
   - Eliminates false alarms during simulated hard exams (`CS201` Week 5 `-20` shock and `MA101` Week 8 `-18` shock).
2. **`divergence.py`**:
   - Assignment–Internal Divergence Index: `z_assign_avg - z_internal_avg` across subjects. Flagged when `> 1.5` (`PASSIVE_COPIER_CONCEPT_GAP`).
3. **`cusum.py`**:
   - One-sided downward CUSUM (`k = 0.5 * std`, `h = 4.0 * std`) + EWMA (`lambda = 0.3`, `1.5 * std` lower bound) against each student's Weeks 1–4 personal baseline.
   - Important design detail: In `features.py` and `snapshot_service.py`, CUSUM runs on **cohort-normalized weekly Z-composites** with `min_std=0.25`. Empirically across the 240-student dataset, switching from raw composites to Z-composites dropped `ON_TRACK` false triggers from `23/130` (`17.7%`) to **`0/130`** (`0%`) while capturing **`29/29`** (`100%`) of `SILENT_SLIPPER` students (firing at Week 7 for Aarav).
4. **`ponr.py`**:
   - Per-subject Point of No Return: `min_total_needed = ceil(0.75 * sessions_per_week * 14)`, `min_future_needed = max(0, min_total_needed - attended_so_far)`, `bunk_budget = remaining_sessions - min_future_needed`.
   - Status tiers: `UNRECOVERABLE_WITHOUT_WAIVER` (`min_future > remaining`), `WINDOW_CLOSING` (`bunk_budget <= 1`), `WATCH` (`2..5`), `SAFE` (`> 5`).
   - Also converts tightest `bunk_budget` into calendar days (`round(bunk_budget * 7 / sessions_per_week)`).
5. **`archetype.py`**:
   - Priority-ordered root-cause diagnoser (first match wins):
     1. `DETENTION_CLIFF`
     2. `PASSIVE_COPIER_CONCEPT_GAP`
     3. `SILENT_SLIPPER`
     4. `BROAD_DISENGAGEMENT` (`>= 3` subjects with `z_att < -1` and `z_internal < -1`)
     5. `CONCEPTUAL_STRUGGLER` (`z_internal < -1`, `z_att >= -0.5`)
     6. `ON_TRACK`

### B. Leakage-Free ML Pipeline (`features.py`, `ml/train_and_evaluate.py`, `ml_inference.py`)
- **Feature Hygiene (`features.py`):** Strict column allowlist (`ALLOWED_INPUT_COLUMNS`) strips any non-observational columns (`final_exam_score`, demographics, `persona_tag`, labels) and strictly filters `week <= cutoff_week` (`8` for training). Exports 20 ordered features:
  - `att_mean`, `att_min`, `att_recent_2w`, `assign_mean`, `assign_recent_2w`, `internal_mean`, `internal_min`, `internal_recent_2w`, `z_att_mean`, `z_assign_mean`, `z_internal_mean`, `v_composite_latest`, `a_composite_latest`, `divergence_index`, `cusum_triggered`, `cusum_shift_magnitude`, `ewma_flagged_count`, `min_bunk_budget`, `sub_75_att_count`, `sub_40_ia_count`.
- **Temporal Training & Holdout Split (`ml/train_and_evaluate.py`):**
  - Features strictly from **Weeks 1–8**; ground-truth target tiers (`0=SAFE`, `1=WATCH`, `2=AT_RISK`, `3=CRITICAL`) and composite score computed strictly from **Weeks 10–12** (`target_score = 0.25*att + 0.25*assign + 0.50*internal`).
  - Stratified 75/25 holdout (`train_size=180`, `holdout_size=60`), selecting best classifier by `at_risk_recall` (classes 2 & 3 combined), tie-broken by `macro_f1`:
    - **`LogisticRegression` (StandardScaler Pipeline — Selected):** `at_risk_recall = 0.9565`, `macro_f1 = 0.691`, `roc_auc = 0.9027`
    - `GradientBoostingClassifier`: `at_risk_recall = 0.9565`, `macro_f1 = 0.6893`, `roc_auc = 0.8942`
    - `RandomForestClassifier`: `at_risk_recall = 0.913`, `macro_f1 = 0.619`, `roc_auc = 0.8744`
    - `GradientBoostingRegressor` holdout MAE: **`0.8831`** points
  - Persists `classifier.joblib`, `regressor.joblib`, `shap_background.npy`, `feature_names.json`, `model_audit.json`.
- **SHAP Sign Convention (`ml_inference.py`):**
  - Computes per-feature SHAP contributions toward **`P(AT_RISK) + P(CRITICAL)`** using `LinearExplainer` (for linear pipelines), `TreeExplainer` (for `RandomForest`), or `shap.Explainer` fallback. Positive SHAP = pushes risk UP (red bars); negative SHAP = protective (green bars).
- **Constrained Counterfactual Solver & What-If (`whatif.py`, `recovery_solver.py`):**
  - `project_features_for_whatif` is shared between solver and `POST /simulate`.
  - Solver evaluates a 3D grid over feasible future targets (`[current, 100%]`) with vectorized batch inference + `scipy.optimize.minimize` (SLSQP) polish to reach `SAFE` or `WATCH` at minimal effort cost, plus emits subject-specific PONR recovery steps (`0.0 <= target_value <= 1.0`).

---

## 5. Seeded Cohort & 4 Hero Personas (`ml/generate_data.py`, `SEED=42`)

- **Total Dataset:** `240` students (`130 SAFE`, `17 WATCH`, `80 AT_RISK`, `13 CRITICAL` in live Week-9 snapshots).
- **Pinned Hero Personas (Verified in Live Snapshots):**
  1. `STU-001` (**Aarav Kulkarni**): `AT_RISK` (`78.26`), `proj=61.25%`, `SILENT_SLIPPER`, CUSUM Week **7**, top SHAP = `cusum_shift_magnitude` / `cusum_triggered`.
  2. `STU-002` (**Meera Nair**): `CRITICAL` (`93.84`), `proj=67.32%`, `PASSIVE_COPIER_CONCEPT_GAP`, divergence **`+3.27σ`**, top SHAP = `sub_40_ia_count` / `internal_recent_2w` / `divergence_index`.
  3. `STU-003` (**Rohan Deshmukh**): `WATCH` (`41.27`), `ponr_days_left=4`, `DETENTION_CLIFF`, `CS301L` at `12/18` (`66.7%`, bunk budget = `1` → `WINDOW_CLOSING`).
  4. `STU-004` (**Priya Sharma**): `SAFE` (`12.99`), `proj=94.35%`, `ON_TRACK`, top protective SHAP `v_composite_latest (-1.83)`, Week 7 intervention shows `AT_RISK → SAFE` **`LIFT IMPROVED`** badge.

---

## 6. Backend API Surface & Security (`backend/app/api/v1/`)

All routes prefixed under `/api/v1` with global exception handlers (`exceptions.py` preventing stack trace leaks), strict Pydantic v2 validation (`422` on invalid input), and zero-N+1 joined queries (`repositories/`):

| Method & Path | Auth / Scope | Purpose |
|---|---|---|
| `GET` & `HEAD /health` | Public | DB, model-loaded, & dataset count (`240`) |
| `POST /auth/demo-token` | Public (`DEMO_MODE=true` only) | Issues signed HS256 JWT (`faculty` or `student`) |
| `GET /dashboard/summary` | `require_faculty` | Cohort KPIs, distributions, urgent queue, 240 triage coordinates |
| `GET /students` | `require_faculty` | Filterable/searchable/sorted paginated list (`<= 3` SQL queries) |
| `GET /students/{id}/analytics` | `assert_student_scope` (`403` cross-student) | Trajectory, Z-scores, CUSUM/EWMA, PONR, SHAP, Recovery plan |
| `GET /students/{id}/recovery-plan` | `assert_student_scope` | Counterfactual solver steps `[0..1]` |
| `POST /simulate` | `assert_student_scope` | Counterfactual What-If slider projection (`0..100` clamped) |
| `GET /interventions` | Role-scoped (`403` cross-student query) | Lists mentoring logs with `risk_improved` lift flag |
| `POST /interventions` | `require_faculty` | Logs intervention & snapshots `pre_risk_tier` (`201 Created`) |
| `GET /model/audit` | `get_current_user` | Serves live `model_audit.json` holdout benchmarks |
| `POST /upload/csv` | `require_faculty` | CSV/XLSX parser (`5 MB` max), `difflib` fuzzy mapper (`services/csv_mapper.py`), health warnings |

TypeScript API contract auto-generated from FastAPI OpenAPI into `frontend/src/api/types.ts` via `openapi-typescript`, wrapped in `frontend/src/api/client.ts`.

---

## 7. Frontend Architecture (`frontend/src/`)

- **Auth & Routing:** In-memory demo JWT in `src/lib/auth.tsx` (never `localStorage`); switching roles cancels/clears TanStack Query cache cleanly. State-based navigation in `App.tsx` + `Sidebar.tsx` + `TopBar.tsx` with lazy code-split pages and `<ErrorBoundary>`.
- **Faculty Views:**
  1. `FacultyDashboard.tsx` + `StudentQueueTable.tsx` — KPI strip, search/tier/archetype/sort controls, clickable queue.
  2. `TriageMatrix.tsx` — 240-dot Recharts scatter matrix (Risk Score vs Post-Recovery Score) across 4 quadrants.
  3. `StudentDetail.tsx` — Stats cards, `TrajectoryChart.tsx` (dual-Y raw + cohort Z-score + CUSUM `<ReferenceLine>`), `WaterfallChart.tsx` (SHAP bars), per-subject PONR table, solver checklist, and `MentorAlertDigest.tsx`.
  4. `InterventionTracker.tsx` — Intervention logger form + feed with `LIFT IMPROVED` badges.
  5. `CsvUploader.tsx` — Drag-and-drop CSV/XLSX preview with fuzzy header confidence table & health warnings.
  6. `ModelAuditTab.tsx` — Classifier comparison table, 4×4 confusion matrix heatmap, top 10 feature importances.
- **Student Views:**
  1. `StudentHome.tsx` — PONR alert banners (`WINDOW CLOSING`), CUSUM shift banners, trajectory chart, subject eligibility cards.
  2. `RecoveryPage.tsx` — 150ms debounced What-If sliders (`AbortController`, `min` clamped to baseline, `max=100`) updating projected tier, score delta, and SHAP bars live.
  3. `RecoveryBrief.tsx` — Clean 1-page `@media print` brief + `MentorAlertDigest` copy-to-clipboard.

---

## 8. Verification Status

- `python -m ruff check app/ tests/ ml/` → **0 errors**
- `python -m pytest -q` → **102 passed** (unit, math, anti-leakage, RBAC, zero-N+1, CSV fuzzy/edge cases, slider clamping, health)
- `npx tsc --noEmit` & `npm run build` → **0 errors**
- `npx playwright test e2e/ --reporter=list` → **4 passed** (`hero_aarav`, `hero_meera`, `hero_rohan`, `hero_priya`)

---

## 9. Known Limitations, Tradeoffs & Areas for Reviewer Scrutiny

Please review these deliberate MVP scope boundaries and potential blind spots critically:

1. **CSV/XLSX Upload Is Preview-Only (`committed=False`):** `POST /upload/csv` parses, fuzzy-maps, and scans data health cleanly, but does **not** yet persist new rows into `weekly_records` or trigger incremental snapshot recomputation for uploaded cohorts.
2. **Demo Auth Only (No Production Login/Password Flow):** `DEMO_MODE=true` powers 1-click JWT issuance for Faculty/Student personas. Outside demo mode (`DEMO_MODE=false`), there is no username/password `/auth/login` endpoint, password hashing flow, or multi-tenant institution scoping yet.
3. **Synthetic Cohort & Single-Semester Horizon (`SEED=42`):** The `240` students and Weeks 10–12 targets come from a deterministic synthetic generator. On real multi-year university datasets, `LogisticRegression` vs gradient boosting performance, `WATCH` vs `SAFE` macro-F1 (`0.691` currently due to `WATCH` overlap with borderline `SAFE`), and `z_composite` CUSUM threshold calibration (`min_std=0.25`) should be re-validated across multiple real cohorts.
4. **Constrained Counterfactual Independence Assumption (`whatif.py`):** When sliders increase `attendance_pct` or `internal_score`, `whatif.py` updates `z_*` using fixed fallback cohort standard deviations (`DEFAULT_COHORT_STD`) and clears `cusum_triggered` above heuristic thresholds rather than recomputing against full historical cohort statistics or modeling causal correlation between attendance and exam marks.
5. **Static Policy Constants & Week Number:** Policy rules (`75%` attendance, `40%` internals, `CURRENT_WEEK=9`) are read from `.env` (`Settings`) rather than editable per-subject/department in the Admin UI or dynamically inferred from latest uploaded week.
6. **UX Action Continuity Gaps:**
   - Faculty cannot yet log an intervention *directly* inside `StudentDetail.tsx` (they switch to the Interventions tab).
   - `RecoveryBrief` currently routes cleanly via React state, not URL hash/pathname deep links (refreshing the page resets to `/faculty-dashboard`).
   - Print CSS hides dark navigation chrome cleanly, though `TrajectoryChart` SVGs are currently excluded from the printable 1-page `RecoveryBrief` (text + structured tables only).
7. **Frontend Unit Test Coverage (`vitest`):** `vitest` is listed in `package.json`, and frontend verification relies on strict `tsc`, Vite builds, and `4` full Playwright E2E specs rather than isolated component unit tests (e.g., testing `AbortController` race cancellation directly in `useSimulate` or clipboard fallbacks).
8. **PostgreSQL Row-Level Security (RLS):** Currently runs on SQLite WAL with application-layer role/row filtering (`assert_student_scope`, scoped SQL queries); `alembic` migration & Postgres RLS policies have not yet been executed against a live PostgreSQL instance.
9. **Port Conflict on Windows Host:** Port `8000` was occupied by another host process (`PID 10184`), so local testing runs backend on `8011` with `VITE_PROXY_TARGET=http://127.0.0.1:8011`.
