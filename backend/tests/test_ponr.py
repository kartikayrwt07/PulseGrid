"""Tests for the Per-Subject PONR Calculator."""

import math

from app.analytics.ponr import assess_internal_standing, calculate_subject_ponr

# ---------------------------------------------------------------------------
# Rohan Deshmukh — DETENTION_CLIFF (CN Lab)
# After Week 9: attended=12, total_so_far=18, remaining=10, min_needed=21
# bunk_budget = 10 - (21-12) = 10 - 9 = 1  →  WINDOW_CLOSING
# ---------------------------------------------------------------------------

def test_rohan_cn_lab_ponr(rohan_cn_lab_ponr_input):
    """Rohan's CN Lab PONR must be WINDOW_CLOSING or UNRECOVERABLE after Week 9."""
    result = calculate_subject_ponr(**rohan_cn_lab_ponr_input)
    assert result["eligibility_status"] in (
        "WINDOW_CLOSING", "UNRECOVERABLE_WITHOUT_WAIVER"
    ), f"Expected cliff status, got {result['eligibility_status']}"


def test_rohan_cn_lab_bunk_budget_critical(rohan_cn_lab_ponr_input):
    """Rohan's bunk budget for CN Lab must be <= 1."""
    result = calculate_subject_ponr(**rohan_cn_lab_ponr_input)
    assert result["bunk_budget"] <= 1


def test_rohan_cn_lab_min_future_sessions(rohan_cn_lab_ponr_input):
    """Rohan must attend at least 9 of the 10 remaining CN Lab sessions."""
    result = calculate_subject_ponr(**rohan_cn_lab_ponr_input)
    assert result["min_future_needed"] == 9


# ---------------------------------------------------------------------------
# Safe student — always attending, plenty of bunk budget
# ---------------------------------------------------------------------------

def test_safe_student_is_safe(safe_student_ponr_input):
    result = calculate_subject_ponr(**safe_student_ponr_input)
    assert result["eligibility_status"] == "SAFE"


def test_safe_student_bunk_budget_positive(safe_student_ponr_input):
    result = calculate_subject_ponr(**safe_student_ponr_input)
    assert result["bunk_budget"] > 5


# ---------------------------------------------------------------------------
# Boundary / mathematical correctness tests
# ---------------------------------------------------------------------------

def test_unrecoverable_status():
    """Student who missed so many sessions they cannot recover."""
    result = calculate_subject_ponr(
        attended_so_far=5,
        total_sessions_so_far=28,
        sessions_per_week=2,
        current_week=14,  # semester over!
        total_weeks=14,
    )
    assert result["eligibility_status"] == "UNRECOVERABLE_WITHOUT_WAIVER"
    assert result["bunk_budget"] < 0


def test_watch_status():
    """Student with bunk_budget=3 should be WATCH."""
    # 75% of 42 = 31.5 → 32 needed
    # attended=25, total_so_far=36 (12 weeks × 3), remaining=6
    # min_future = 32-25 = 7, but remaining=6 → WINDOW_CLOSING? Let me calc:
    # attended=27, remaining=3*2=6 (2 weeks left × 3/wk), min_total=32
    # min_future = 32-27=5, bunk_budget=6-5=1 → WINDOW_CLOSING
    # Try: attended=29, 2 weeks left × 3 = 6 remaining, min_future=32-29=3, budget=6-3=3 → WATCH
    result = calculate_subject_ponr(
        attended_so_far=29,
        total_sessions_so_far=36,
        sessions_per_week=3,
        current_week=12,
        total_weeks=14,
    )
    assert result["eligibility_status"] == "WATCH"
    assert 2 <= result["bunk_budget"] <= 5


def test_window_closing_status():
    result = calculate_subject_ponr(
        attended_so_far=27,
        total_sessions_so_far=36,
        sessions_per_week=3,
        current_week=12,
        total_weeks=14,
    )
    # min_future = 32-27=5, remaining=6, bunk_budget=1 → WINDOW_CLOSING
    assert result["eligibility_status"] == "WINDOW_CLOSING"


def test_min_total_needed_uses_ceiling():
    """75% of 42 = 31.5 → must be rounded UP to 32."""
    result = calculate_subject_ponr(
        attended_so_far=35,
        total_sessions_so_far=42,
        sessions_per_week=3,
        current_week=14,
        total_weeks=14,
    )
    assert result["min_total_needed"] == math.ceil(0.75 * 42)


def test_no_negative_min_future_needed():
    """Student who already has 100% attendance should need 0 future sessions."""
    result = calculate_subject_ponr(
        attended_so_far=42,
        total_sessions_so_far=42,
        sessions_per_week=3,
        current_week=14,
        total_weeks=14,
    )
    assert result["min_future_needed"] == 0


# ---------------------------------------------------------------------------
# Internal standing tests
# ---------------------------------------------------------------------------

def test_internal_standing_pass():
    result = assess_internal_standing([45.0, 50.0, 42.0])  # avg=45.67 → 45.67% > 40%
    assert result["passing"] is True


def test_internal_standing_fail():
    result = assess_internal_standing([30.0, 35.0, 38.0])  # avg=34.33 → 34.33% < 40%
    assert result["passing"] is False


def test_internal_standing_empty():
    result = assess_internal_standing([])
    assert result["passing"] is False
    assert result["average_pct"] == 0.0
