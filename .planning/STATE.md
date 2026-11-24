# PulseGrid — Project State

## Current Status
- **Active Phase:** All 8 Phases Complete ✅ — PulseGrid Demo Ready
- **Last Action:** Finalized `start.sh`, `README.md`, `PITCH_DEMO_SCRIPT.md`, strengthened `test_health.py` (`102` backend tests), and verified live backend (`8011`), frontend (`4173`), `GET`/`HEAD /health`, and all 4 Playwright E2E scenarios
- **Date:** 2026-11-25

## Locked Decisions
- Database: SQLite WAL only (`backend/pulsegrid.db`)
- University policy: 75% attendance, 40% internal min, 14-week semester
- Deployment: Local-only (uvicorn + vite preview)
- Zero external AI/LLM APIs
- Demo mode: `DEMO_MODE=true` env + signed demo JWTs

## Hero Persona IDs (Deterministic — Must Not Change)
- `STU-001` (`id=1`): Aarav Kulkarni (`SILENT_SLIPPER`)
- `STU-002` (`id=2`): Meera Nair (`PASSIVE_COPIER_CONCEPT_GAP`)
- `STU-003` (`id=3`): Rohan Deshmukh (`DETENTION_CLIFF`)
- `STU-004` (`id=4`): Priya Sharma (`RECOVERED_AFTER_INTERVENTION`)

## Phase Completion Log
| Phase | Completed At | Key Artifact |
|---|---|---|
| Phase 1 — Foundation | 2026-11-24 | `backend/app/main.py`, `backend/ml/generate_data.py`, `frontend/` shell |
| Phase 2 — Math Core | 2026-11-24 | `backend/app/analytics/{zscore,divergence,cusum,ponr,archetype}.py` (48 tests passing) |
| Phase 3 — ML Pipeline | 2026-11-24 | `features.py`, `ml_inference.py`, `whatif.py`, `recovery_solver.py`, `snapshot_service.py`, `train_and_evaluate.py`, `ml/artifacts/*` (64 total tests passing) |
| Phase 4 — APIs | 2026-11-24 | `schemas/*`, `repositories/*`, `api/v1/*`, `frontend/src/api/{types.ts,client.ts}` (85 tests passing, `tsc` + `vite build` clean) |
| Phase 5 — UI MVP ⭐ | 2026-11-24 | `frontend/src/{lib,hooks,components,pages}/*`, `conftest.py` fix (`tsc`, `vite build`, live Playwright smoke check passed) |
| Phase 6 — Differentiators | 2026-11-25 | `csv_mapper.py`, `intervention_service.py`, `TriageMatrix`, `CsvUploader`, `InterventionTracker`, `ModelAuditTab` (90 tests passing) |
| Phase 7 — Hardening | 2026-11-25 | `MentorAlertDigest.tsx`, `RecoveryBrief.tsx`, `test_csv_edge_cases.py`, `test_slider_clamping.py`, `e2e/hero_*.spec.ts` (102 pytest + 4 E2E pass) |
| Phase 8 — Pitch Lock | 2026-11-25 | `start.sh`, `README.md`, `PITCH_DEMO_SCRIPT.md`, `test_health.py` (102 pytest, `ruff`, `tsc`, 4 E2E pass) |

## Open Questions
- None — ready for live pitch demo on `http://127.0.0.1:4173` (proxied to `http://127.0.0.1:8011`; port `8000` reserved by PID 10184 on this host).

## Next Action
Present live PulseGrid demo following `PITCH_DEMO_SCRIPT.md`.
