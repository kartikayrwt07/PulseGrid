# PulseGrid — Project Context

## Identity
- **Project:** PulseGrid — Cohort-Calibrated Academic Early-Warning & Recovery Engine
- **Hackathon:** Birla Hackathon
- **Status:** Initialization — Phase 1 not yet started
- **Current Week in Dataset:** Week 9 of 14-week semester

## Problem Statement
Students fail to recognize declining academic performance until final exams, when recovery is mathematically impossible. Generic pass/fail dashboards generate false alarms on hard papers and miss "silent slippers" drifting below their personal baseline. No existing tool calculates *exactly how many lectures/marks remain* before a student crosses the Point of No Return, nor prescribes the *minimum realistic recovery path*.

## Winning Differentiators
1. **CUSUM/EWMA Change-Point Detection** — catches silent performance drops weeks before static thresholds fire
2. **Cohort-Normalized Z-Scores** — eliminates tough-exam false alarms by calibrating against the class
3. **Assignment–Internal Divergence Index** — exposes the "assignment comfort trap" (high take-home, fail closed-book)
4. **Per-Subject PONR Calculator** — exact mathematical deadline, Theory vs. Lab weighted separately
5. **Constrained Counterfactual Recovery Solver** — minimum-effort recovery path via scipy optimization
6. **Off-Dashboard Actionability** — 1-click printable Recovery Brief + copyable Mentor Alert Digest

## Confirmed Decisions (Locked)

| Decision | Value |
|---|---|
| Database | SQLite only (WAL mode, single file `pulsegrid.db`) |
| University Policy | 75% per-subject attendance, 40% internal minimum |
| Semester Length | 14 weeks; dataset at Week 9 |
| Theory load | 3 h/week per subject |
| Lab load | 2 h/week per lab subject |
| Deployment | Local-only: `uvicorn` (port 8000) + `vite preview` (port 4173) |
| External AI/LLM | ZERO — fully local, deterministic Python |
| Auth demo mode | `DEMO_MODE=true` env + signed demo JWTs (faculty/student roles) |
| Python | 3.11+ |
| Node | 20 LTS |
| Subjects (5) | Mathematics, Data Structures, Computer Networks (has Lab), DBMS, Operating Systems |
| Total students | 240 (seeded deterministically) |

## Hero Personas (Pinned — Must Never Change Across Seeds)

| ID | Name | Archetype | Key Trigger |
|---|---|---|---|
| STU-001 | Aarav Kulkarni | SILENT_SLIPPER | Weeks 1–5 avg 89%; CUSUM fires Week 7 (cumulative 76%) |
| STU-002 | Meera Nair | PASSIVE_COPIER_CONCEPT_GAP | 94% assignments, 86% attendance, 39% internals |
| STU-003 | Rohan Deshmukh | DETENTION_CLIFF | CN Lab at 67%, 3 labs left before PONR |
| STU-004 | Priya Sharma | RECOVERED_AFTER_INTERVENTION | Flagged Week 6, mentoring Week 7, upward lift by Week 9 |

## Five Academic Archetypes
- `SILENT_SLIPPER` — high baseline, gradual masked drop
- `DETENTION_CLIFF` — single-subject attendance cliff (lab/theory)
- `PASSIVE_COPIER_CONCEPT_GAP` — high take-home, low closed-book
- `CONCEPTUAL_STRUGGLER` — low marks across the board, decent attendance
- `BROAD_DISENGAGEMENT` — attendance AND marks declining in multiple subjects

## Binding Rules (Enforced Every Phase)
1. **Plan before code** — no code without explicit user approval of implementation plan
2. **Debugging protocol** — root-cause first, targeted fix, stop after 2 failures
3. **Secrets hygiene** — `.env` only, `.env.example` with placeholders, `.gitignore` enforced
4. **Resilient UX** — loading/empty/error states on every view; no raw tracebacks to browser
5. **Approved packages only** — no unapproved deps without explicit ask + justification

## Repository Root
`c:\Users\karti\OneDrive\Desktop\Birla Hackathon\`

## Architecture Overview
```
pulsegrid/
├── backend/
│   ├── app/
│   │   ├── core/          # settings, auth, logging, exception handlers
│   │   ├── models/        # SQLAlchemy 2.0 ORM
│   │   ├── schemas/       # Pydantic v2 DTOs
│   │   ├── repositories/  # scoped DB query layer (zero N+1)
│   │   ├── analytics/     # pure math/ML functions (<250 lines each)
│   │   ├── services/      # business orchestration
│   │   └── api/v1/        # thin FastAPI routers
│   ├── ml/
│   │   ├── generate_data.py
│   │   ├── train_and_evaluate.py
│   │   └── artifacts/     # serialized .joblib models + model_audit.json
│   ├── tests/
│   └── alembic/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── api/           # auto-generated OpenAPI types
│   │   └── lib/
│   └── ...
├── data/
│   ├── clean_sample.csv
│   └── messy_sample.xlsx
├── .env.example
├── .gitignore
├── README.md
└── start.sh
```
