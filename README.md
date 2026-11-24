# PulseGrid — Cohort-Calibrated Academic Early-Warning & Recovery Engine

PulseGrid is a local-first, zero-external-LLM academic early-warning and counterfactual recovery engine built for universities. It detects high-baseline decline early, prevents tough-exam false alarms via cohort normalization, diagnoses root causes, calculates per-subject Point-of-No-Return (PONR) attendance cliffs, and prescribes minimum-effort recovery paths.

---

## Core Architecture & Analytical Engines

1. **Cohort-Normalized Z-Score Engine (`app/analytics/zscore.py`)**
   - Normalizes student attendance, assignments, and closed-book internals per `(subject_id, week)` (`z`, 3-week velocity, and acceleration) so difficult cohort-wide exams do not trigger false alerts.
2. **CUSUM & EWMA Change-Point Detector (`app/analytics/cusum.py`)**
   - Tracks one-sided downward cumulative sum shifts (`k=0.5σ`, `h=4.0σ`) on cohort-normalized weekly Z-composites against each student's personal Weeks 1–4 baseline to catch **Silent Slippers** weeks before static averages drop.
3. **Assignment–Internal Divergence Index (`app/analytics/divergence.py`)**
   - Flags `z_assign_avg - z_internal_avg > 1.5` to surface **Passive Copier Concept Gaps** (high take-home assignment scores paired with failing closed-book internals).
4. **Per-Subject PONR Calculator (`app/analytics/ponr.py`)**
   - Applies university policy defaults (75% attendance minimum per subject, 40% aggregate internal minimum, 14-week semester, 3 sessions/week Theory vs. 2 sessions/week Lab) and classifies `SAFE | WATCH | WINDOW_CLOSING | UNRECOVERABLE_WITHOUT_WAIVER`.
5. **Leakage-Free ML Pipeline + SHAP + Counterfactual Solver (`ml/train_and_evaluate.py`, `app/analytics/`)**
   - Trains purely on Weeks 1–8 observational features to forecast Weeks 10–12 standing (zero final-exam or demographic columns; verified via `tests/test_anti_leakage.py`).
   - Current holdout benchmark (`train=180`, `holdout=60`): selected `LogisticRegression` (`at_risk_recall=0.957`, `macro_f1=0.691`, `roc_auc=0.903`) alongside `GradientBoostingRegressor` (`MAE=0.883`).
   - Computes signed SHAP risk attributions and constrained `scipy` SLSQP counterfactual targets clamped strictly to `[current, 100%]`.

---

## Tech Stack

- **Backend:** FastAPI, SQLAlchemy 2.0, SQLite (WAL mode), Pydantic v2, PyJWT, NumPy, SciPy, Pandas, scikit-learn, SHAP, OpenPyXL
- **Frontend:** React 19, TypeScript, Vite, Tailwind CSS, Recharts, TanStack React Query, `openapi-typescript`, Lucide Icons
- **Testing & Quality:** `pytest` (102 backend tests), `playwright` (4 Hero Persona E2E specs), `ruff`, `tsc --noEmit`

---

## Quickstart (Local Offline Demo)

### Linux / macOS / Git Bash
```bash
bash start.sh
```

### Windows PowerShell
```powershell
# 1. Backend
cd backend
python ml/generate_data.py
python ml/train_and_evaluate.py
python -m uvicorn app.main:app --host 127.0.0.1 --port 8011

# 2. Frontend (new terminal)
cd frontend
npm run build
$env:VITE_PROXY_TARGET = "http://127.0.0.1:8011"
npm run preview -- --host 127.0.0.1 --port 4173
```
*(Port `8000` is used by default if free; use `--port 8011` + `VITE_PROXY_TARGET` if port `8000` is occupied on Windows.)*

Open **http://127.0.0.1:4173** in your browser. `DEMO_MODE=true` enables 1-click signed demo JWT switching between **Faculty** and **Student** roles without bypassing RBAC (`401`/`403` row-level checks remain enforced).

---

## Seeded Hero Personas (`STU-001` – `STU-004`)

| ID | Roll No | Student | Archetype / Scenario | Key Signal |
|---|---|---|---|---|
| 1 | `STU-001` | **Aarav Kulkarni** | `SILENT_SLIPPER` | Drops from ~89% baseline; CUSUM triggers at **Week 7** |
| 2 | `STU-002` | **Meera Nair** | `PASSIVE_COPIER_CONCEPT_GAP` | ~94% assignments vs ~39% closed-book internals (`+3.27σ` divergence) |
| 3 | `STU-003` | **Rohan Deshmukh** | `DETENTION_CLIFF` | `CS301L` CN Lab at 12/18 (`66.7%`, bunk budget = 1 → `WINDOW_CLOSING`) |
| 4 | `STU-004` | **Priya Sharma** | `ON_TRACK` (Post-Intervention) | Logged Week 7 intervention shows `AT_RISK → SAFE` lift badge |

---

## Verification Commands

```powershell
# Backend lint + tests (102 tests)
cd backend
python -m ruff check app/ tests/ ml/
python -m pytest -v

# Frontend typecheck + build + Playwright E2E (with preview server running on 4173)
cd ..\frontend
npx tsc --noEmit
npm run build
npx playwright test e2e/ --reporter=list
```

---

## Known Limitations

- The seeded dataset (`240` students across `6` subjects and `12` weeks) is deterministically synthesized (`SEED = 42`) rather than connected to a live university ERP/SIS.
- Institutional policy thresholds (`75%` attendance, `40%` internal minimum, `14`-week semester) are read globally from `.env` settings rather than per-department rule overrides.
- CSV/XLSX ingestion previews fuzzy column alignments (`difflib` + health warnings) safely without mutating the baseline 240-student cohort unless integrated into a live batch import job.
