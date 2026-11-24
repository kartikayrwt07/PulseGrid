"""Tests for the Constrained Counterfactual Recovery Solver."""

from app.analytics.recovery_solver import project_features_for_whatif, solve_recovery


def _at_risk_student_features() -> dict[str, float]:
    return {
        "att_mean": 68.0,
        "att_min": 60.0,
        "att_recent_2w": 60.0,
        "assign_mean": 72.0,
        "assign_recent_2w": 66.0,
        "internal_mean": 58.0,
        "internal_min": 52.0,
        "internal_recent_2w": 55.0,
        "z_att_mean": -1.1,
        "z_assign_mean": -0.7,
        "z_internal_mean": -1.0,
        "v_composite_latest": -0.6,
        "a_composite_latest": -0.2,
        "divergence_index": 0.3,
        "cusum_triggered": 1.0,
        "cusum_shift_magnitude": 1.4,
        "ewma_flagged_count": 2.0,
        "min_bunk_budget": 1.0,
        "sub_75_att_count": 2.0,
        "sub_40_ia_count": 0.0,
    }


def test_solution_within_physical_bounds():
    solution = solve_recovery(_at_risk_student_features(), weeks_remaining=5)
    assert solution["feasible"] is True
    assert solution["target_tier"] in ("SAFE", "WATCH")
    assert solution["projected_score_after"] >= solution["projected_score_before"]
    for step in solution["recovery_steps"]:
        assert 0.0 <= step["target_value"] <= 1.0
        assert 0.0 <= step["current_value"] <= step["target_value"]


def test_zero_weeks_remaining_is_infeasible():
    solution = solve_recovery(_at_risk_student_features(), weeks_remaining=0)
    assert solution["feasible"] is False
    assert solution["waiver_required"] is True


def test_whatif_projection_clamps_out_of_bounds():
    base = _at_risk_student_features()
    projected = project_features_for_whatif(
        base, future_att_pct=150.0, future_assign_pct=-20.0, future_internal_pct=105.0
    )
    assert 0.0 <= projected["att_mean"] <= 100.0
    assert 0.0 <= projected["assign_mean"] <= 100.0
    assert 0.0 <= projected["internal_mean"] <= 100.0
