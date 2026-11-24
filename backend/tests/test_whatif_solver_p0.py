"""Prompt 1 (P0) mathematical verification tests for whatif.py & recovery_solver.py."""

import json
import sqlite3
from pathlib import Path

from app.analytics.recovery_solver import solve_recovery
from app.analytics.whatif import project_features_for_whatif, project_whatif_state
from app.core.config import BACKEND_DIR


def _base_features() -> dict[str, float]:
    return {
        "att_mean": 70.0,
        "att_min": 65.0,
        "att_recent_2w": 62.0,
        "assign_mean": 74.0,
        "assign_recent_2w": 70.0,
        "internal_mean": 62.0,
        "internal_min": 55.0,
        "internal_recent_2w": 58.0,
        "z_att_mean": -0.8,
        "z_assign_mean": -0.4,
        "z_internal_mean": -0.7,
        "v_composite_latest": -0.4,
        "a_composite_latest": -0.1,
        "divergence_index": 0.3,
        "cusum_triggered": 1.0,
        "cusum_shift_magnitude": 1.6,
        "ewma_flagged_count": 2.0,
        "min_bunk_budget": 1.0,
        "sub_75_att_count": 1.0,
        "sub_40_ia_count": 0.0,
    }


def test_whatif_uses_live_cohort_stats_for_z_projection():
    base = _base_features()
    tight_stats = {
        "att": {"mean": 82.0, "std": 4.0},
        "assign": {"mean": 80.0, "std": 5.0},
        "internal": {"mean": 75.0, "std": 5.0},
    }
    wide_stats = {
        "att": {"mean": 82.0, "std": 20.0},
        "assign": {"mean": 80.0, "std": 20.0},
        "internal": {"mean": 75.0, "std": 20.0},
    }
    tight_proj, state = project_whatif_state(
        base, 95.0, 90.0, 88.0, weeks_remaining=5, cohort_stats=tight_stats,
        z_composites_history=[0.5, 0.5, 0.4, 0.5, 0.1, -0.8, -0.9],
    )
    wide_proj = project_features_for_whatif(
        base, 95.0, 90.0, 88.0, weeks_remaining=5, cohort_stats=wide_stats
    )
    assert tight_proj["z_att_mean"] != wide_proj["z_att_mean"]
    # Historical CUSUM flag MUST remain immutable
    assert tight_proj["cusum_triggered"] == 1.0
    assert state["historical_cusum_triggered"] is True
    assert state["projected_cusum_active"] is False


def test_detention_cliff_rohan_enforces_75_pct_ponr_floor():
    with sqlite3.connect(Path(BACKEND_DIR) / "pulsegrid.db") as conn:
        row = conn.execute(
            "SELECT z_scores_json, ponr_json FROM prediction_snapshots WHERE student_id=3"
        ).fetchone()
    z_data = json.loads(row[0])
    ponr_list = json.loads(row[1])
    sol = solve_recovery(
        student_features=z_data["features"],
        weeks_remaining=5,
        ponr_results=ponr_list,
        cohort_stats=z_data.get("cohort_stats"),
    )
    assert sol["requires_waiver"] is False
    # CN Lab needs 9/10 future sessions (90%); solver attendance target must meet >= 90%
    att_steps = [s for s in sol["recovery_steps"] if "attendance" in s["feature"]]
    assert any(s["target_value"] >= 0.90 for s in att_steps)


def test_unrecoverable_student_returns_requires_waiver_and_infeasible():
    base = _base_features()
    ponr = [
        {
            "subject_code": "CS301L",
            "current_pct": 40.0,
            "bunk_budget": -5,
            "min_future_needed": 15,
            "remaining_sessions": 10,
            "eligibility_status": "UNRECOVERABLE_WITHOUT_WAIVER",
        }
    ]
    sol = solve_recovery(base, weeks_remaining=5, ponr_results=ponr)
    assert sol["requires_waiver"] is True
    assert sol["waiver_required"] is True
    assert sol["feasible"] is False


def test_aarav_recovers_while_preserving_historical_cusum():
    with sqlite3.connect(Path(BACKEND_DIR) / "pulsegrid.db") as conn:
        row = conn.execute(
            "SELECT cusum_triggered, cusum_week, recovery_path_json "
            "FROM prediction_snapshots WHERE student_id=1"
        ).fetchone()
    assert row[0] == 1
    assert row[1] == 7
    rec = json.loads(row[2])
    assert rec["feasible"] is True
    assert rec["target_tier"] in ("SAFE", "WATCH")
