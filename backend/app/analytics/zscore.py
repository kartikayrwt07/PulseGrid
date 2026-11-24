"""
Cohort-Normalized Z-Score Engine.

Computes per-week, per-subject cohort Z-scores and rolling velocity /
acceleration for attendance, assignment, and internal scores.

Formula: z = (student_score - cohort_mean) / max(cohort_std, 1e-6)
Velocity: delta_z_t = z_t - z_{t-3}   (3-week backward difference)
Acceleration: delta2_z_t = delta_z_t - delta_z_{t-3}
"""

from __future__ import annotations

import numpy as np  # noqa: F401 — kept for type compatibility
import pandas as pd

METRICS: list[tuple[str, str, str, str]] = [
    ("attendance_pct", "z_att", "v_att", "a_att"),
    ("assignment_score", "z_assign", "v_assign", "a_assign"),
    ("internal_score", "z_internal", "v_internal", "a_internal"),
]

REQUIRED_COLS = {
    "student_id", "subject_id", "week",
    "attendance_pct", "assignment_score", "internal_score",
}


def compute_cohort_zscores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute cohort Z-scores, velocity, and acceleration for every row.

    Parameters
    ----------
    df : DataFrame with columns: student_id, subject_id, week,
         attendance_pct, assignment_score, internal_score

    Returns
    -------
    DataFrame with additional columns:
        z_att, z_assign, z_internal  -- cohort-normalized scores
        v_att, v_assign, v_internal  -- 3-week velocity (delta z)
        a_att, a_assign, a_internal  -- 3-week acceleration (delta^2 z)
    """
    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    out = df.copy().sort_values(["student_id", "subject_id", "week"]).reset_index(drop=True)

    # --- Step 1: Cohort Z-scores per (subject_id, week) ---
    for metric, z_col, _v, _a in METRICS:
        cohort_stats = (
            out.groupby(["subject_id", "week"])[metric]
            .agg(["mean", "std"])
            .rename(columns={"mean": "_mean", "std": "_std"})
            .reset_index()
        )
        cohort_stats["_std"] = cohort_stats["_std"].fillna(0.0).clip(lower=1e-6)
        out = out.merge(cohort_stats, on=["subject_id", "week"], how="left")
        out[z_col] = (out[metric] - out["_mean"]) / out["_std"]
        out = out.drop(columns=["_mean", "_std"])

    # --- Step 2: Velocity (3-week backward diff on z-scores) ---
    out = out.sort_values(["student_id", "subject_id", "week"]).reset_index(drop=True)
    for _metric, z_col, v_col, _a in METRICS:
        out[v_col] = (
            out.groupby(["student_id", "subject_id"])[z_col]
            .transform(lambda s: s.diff(periods=3).fillna(0.0))
        )

    # --- Step 3: Acceleration (3-week backward diff on velocity) ---
    for _metric, _z, v_col, a_col in METRICS:
        out[a_col] = (
            out.groupby(["student_id", "subject_id"])[v_col]
            .transform(lambda s: s.diff(periods=3).fillna(0.0))
        )

    return out


def get_student_weekly_composite(df: pd.DataFrame, student_id: int) -> list[float]:
    """
    Return a student's per-week raw composite score averaged across all subjects.

    Composite = mean(attendance_pct, assignment_score, internal_score) across subjects.
    Returned list is ordered by week (ascending).
    """
    student_df = df[df["student_id"] == student_id]
    weekly = (
        student_df.groupby("week")[["attendance_pct", "assignment_score", "internal_score"]]
        .mean()
        .mean(axis=1)
        .sort_index()
    )
    return weekly.tolist()


def get_student_weekly_z_composite(df: pd.DataFrame, student_id: int) -> list[float]:
    """
    Return a student's per-week Z-composite (mean of z_att, z_assign, z_internal)
    averaged across all subjects. Requires z_* columns from compute_cohort_zscores().
    """
    for col in ("z_att", "z_assign", "z_internal"):
        if col not in df.columns:
            raise ValueError(
                f"Z-score column '{col}' not found. Run compute_cohort_zscores() first."
            )
    student_df = df[df["student_id"] == student_id]
    weekly = (
        student_df.groupby("week")[["z_att", "z_assign", "z_internal"]]
        .mean()
        .mean(axis=1)
        .sort_index()
    )
    return weekly.tolist()
