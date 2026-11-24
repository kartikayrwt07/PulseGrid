"""Tests for leakage-free feature extraction (Weeks 1..8)."""

import numpy as np
import pandas as pd
import pytest

from app.analytics.features import FEATURE_NAMES, extract_features


def _sample_records_df(weeks: int = 12) -> pd.DataFrame:
    rows = []
    rng = np.random.default_rng(7)
    for sid in range(1, 16):
        base = 45.0 if sid <= 5 else 85.0
        for subj in (1, 2, 3):
            for wk in range(1, weeks + 1):
                rows.append(
                    {
                        "student_id": sid,
                        "subject_id": subj,
                        "week": wk,
                        "attended_sessions": 2 if base < 70 else 3,
                        "total_sessions": 3,
                        "attendance_pct": float(np.clip(base + rng.normal(0, 3), 0, 100)),
                        "assignment_score": float(np.clip(base + rng.normal(0, 3), 0, 100)),
                        "internal_score": float(np.clip(base + rng.normal(0, 3), 0, 100)),
                        "sessions_per_week": 3,
                    }
                )
    return pd.DataFrame(rows)


def test_extract_features_columns_and_no_nans():
    df = _sample_records_df()
    out = extract_features(df, cutoff_week=8)
    assert list(out.columns) == ["student_id", *FEATURE_NAMES]
    assert len(out) == 15
    assert not out.isna().any().any()


def test_extract_features_ignores_forbidden_columns():
    df = _sample_records_df()
    poisoned = df.copy()
    poisoned["final_exam_score"] = 12.0
    poisoned["persona_tag"] = "CRITICAL"
    poisoned["gender"] = "X"

    clean_out = extract_features(df, cutoff_week=8)
    poisoned_out = extract_features(poisoned, cutoff_week=8)
    pd.testing.assert_frame_equal(clean_out, poisoned_out)
    assert not any("final" in col or "gender" in col for col in poisoned_out.columns)


def test_extract_features_empty_window():
    df = _sample_records_df()
    out = extract_features(df[df["week"] > 8], cutoff_week=8)
    assert out.empty
    assert list(out.columns) == ["student_id", *FEATURE_NAMES]


def test_extract_features_missing_required_col_raises():
    df = _sample_records_df().drop(columns=["internal_score"])
    with pytest.raises(ValueError, match="Missing required observational columns"):
        extract_features(df, cutoff_week=8)
