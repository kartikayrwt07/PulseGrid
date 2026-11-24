"""Tests for the Cohort Z-Score Engine."""

import pandas as pd
import pytest

from app.analytics.zscore import (
    compute_cohort_zscores,
    get_student_weekly_composite,
    get_student_weekly_z_composite,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_simple_df() -> pd.DataFrame:
    """20-student cohort, 2 subjects, 3 weeks — deterministic values."""
    rows = []
    for sid in range(1, 21):
        for subj_id in (1, 2):
            for week in (1, 2, 3):
                rows.append(
                    {
                        "student_id": sid,
                        "subject_id": subj_id,
                        "week": week,
                        "attendance_pct": 70.0 + sid,
                        "assignment_score": 60.0 + sid,
                        "internal_score": 50.0 + sid,
                    }
                )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Structural / output-shape tests
# ---------------------------------------------------------------------------

def test_zscores_adds_required_columns():
    df = _make_simple_df()
    out = compute_cohort_zscores(df)
    expected_new = {
        "z_att", "z_assign", "z_internal",
        "v_att", "v_assign", "v_internal",
        "a_att", "a_assign", "a_internal",
    }
    assert expected_new.issubset(set(out.columns))


def test_zscores_preserves_row_count():
    df = _make_simple_df()
    out = compute_cohort_zscores(df)
    assert len(out) == len(df)


def test_cohort_z_mean_is_near_zero():
    """The mean Z-score across all students for a given (subject, week) should be ~0."""
    df = _make_simple_df()
    out = compute_cohort_zscores(df)
    for (_subj, _week), grp in out.groupby(["subject_id", "week"]):
        assert abs(grp["z_att"].mean()) < 1e-6, f"Mean z_att != 0 for subj={_subj} week={_week}"
        assert abs(grp["z_assign"].mean()) < 1e-6
        assert abs(grp["z_internal"].mean()) < 1e-6


def test_cohort_z_std_is_near_one():
    """Z-scores should have std ≈ 1 (sample) across the cohort per (subject, week)."""
    df = _make_simple_df()
    out = compute_cohort_zscores(df)
    for (_subj, _week), grp in out.groupby(["subject_id", "week"]):
        # With ddof=0 internally, population std ≈ 1 is expected
        assert abs(grp["z_att"].std(ddof=0) - 1.0) < 0.05


def test_missing_column_raises():
    df = _make_simple_df().drop(columns=["internal_score"])
    with pytest.raises(ValueError, match="Missing required columns"):
        compute_cohort_zscores(df)


# ---------------------------------------------------------------------------
# Tough-exam wave: entire cohort drops equally → z-scores stay near 0
# ---------------------------------------------------------------------------

def test_tough_exam_wave_no_false_flag(tough_exam_cohort_df):
    """
    When a whole cohort gets a low score on a tough exam, cohort-normalized
    Z-scores must remain near 0 — no individual false alarms.
    """
    out = compute_cohort_zscores(tough_exam_cohort_df)
    week5 = out[(out["subject_id"] == 2) & (out["week"] == 5)]
    # Every z_internal at Week 5 should be < 1.0 in absolute value
    assert all(abs(z) < 1.0 for z in week5["z_internal"]), (
        f"Tough exam wave produced false flags: {week5['z_internal'].tolist()}"
    )


# ---------------------------------------------------------------------------
# Weekly composite utility
# ---------------------------------------------------------------------------

def test_get_student_weekly_composite_length():
    df = _make_simple_df()
    composites = get_student_weekly_composite(df, student_id=1)
    assert len(composites) == 3  # 3 weeks in fixture


def test_get_student_weekly_z_composite_requires_zscores():
    df = _make_simple_df()  # no z_* cols
    with pytest.raises(ValueError, match="z_att"):
        get_student_weekly_z_composite(df, student_id=1)
