"""
Leakage-Free Feature Extraction Engine.

Builds student feature vectors strictly from weekly attendance, assignment,
and internal assessment records up to ``cutoff_week`` (default Week 8).

Anti-Leakage Guarantees:
  1. Drops all non-allowlisted columns (never reads final_exam_score,
     demographics, risk labels, or persona tags).
  2. Filters records strictly to ``week <= cutoff_week`` before computing any
     cohort Z-scores, CUSUM, divergence, or PONR statistics.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.analytics.cusum import compute_ewma, detect_cusum
from app.analytics.divergence import compute_divergence
from app.analytics.ponr import (
    DEFAULT_ATTENDANCE_THRESHOLD,
    DEFAULT_INTERNAL_THRESHOLD,
    DEFAULT_TOTAL_WEEKS,
    calculate_subject_ponr,
)
from app.analytics.zscore import compute_cohort_zscores, get_student_weekly_z_composite

ALLOWED_INPUT_COLUMNS: frozenset[str] = frozenset(
    {
        "student_id",
        "subject_id",
        "week",
        "attended_sessions",
        "total_sessions",
        "attendance_pct",
        "assignment_score",
        "internal_score",
        "sessions_per_week",
    }
)

FEATURE_NAMES: list[str] = [
    "att_mean",
    "att_min",
    "att_recent_2w",
    "assign_mean",
    "assign_recent_2w",
    "internal_mean",
    "internal_min",
    "internal_recent_2w",
    "z_att_mean",
    "z_assign_mean",
    "z_internal_mean",
    "v_composite_latest",
    "a_composite_latest",
    "divergence_index",
    "cusum_triggered",
    "cusum_shift_magnitude",
    "ewma_flagged_count",
    "min_bunk_budget",
    "sub_75_att_count",
    "sub_40_ia_count",
]

FEATURE_LABELS: dict[str, str] = {
    "att_mean": "Overall Attendance %",
    "att_min": "Lowest Subject Attendance %",
    "att_recent_2w": "Recent 2-Week Attendance %",
    "assign_mean": "Overall Assignment Score",
    "assign_recent_2w": "Recent 2-Week Assignment Score",
    "internal_mean": "Overall Internal Exam Score",
    "internal_min": "Lowest Subject Internal Score",
    "internal_recent_2w": "Recent 2-Week Internal Score",
    "z_att_mean": "Cohort Attendance Z-Score",
    "z_assign_mean": "Cohort Assignment Z-Score",
    "z_internal_mean": "Cohort Internal Z-Score",
    "v_composite_latest": "3-Week Z-Score Velocity",
    "a_composite_latest": "3-Week Z-Score Acceleration",
    "divergence_index": "Assignment-Internal Divergence",
    "cusum_triggered": "CUSUM Shift Detected",
    "cusum_shift_magnitude": "CUSUM Drop Magnitude",
    "ewma_flagged_count": "EWMA Flagged Weeks",
    "min_bunk_budget": "Minimum Subject Bunk Budget",
    "sub_75_att_count": "Subjects Below 75% Attendance",
    "sub_40_ia_count": "Subjects Below 40% Internals",
}


def sanitize_records_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Keep strictly allowlisted observational columns to prevent target leakage."""
    keep = [col for col in df.columns if col in ALLOWED_INPUT_COLUMNS]
    required = {
        "student_id",
        "subject_id",
        "week",
        "attendance_pct",
        "assignment_score",
        "internal_score",
    }
    missing = required - set(keep)
    if missing:
        raise ValueError(f"Missing required observational columns: {sorted(missing)}")
    return df[keep].copy()


def _extract_single_student_row(
    stu_df: pd.DataFrame,
    student_id: int,
    cutoff_week: int,
    total_weeks: int,
    attendance_threshold: float,
    internal_threshold: float,
) -> dict[str, float]:
    max_w = int(stu_df["week"].max())
    recent_df = stu_df[stu_df["week"] >= max(1, max_w - 1)]
    latest_df = stu_df[stu_df["week"] == max_w]

    subj_att = stu_df.groupby("subject_id")["attendance_pct"].mean()
    subj_ia = stu_df.groupby("subject_id")["internal_score"].mean()

    v_comp = float(latest_df[["v_att", "v_assign", "v_internal"]].mean().mean())
    a_comp = float(latest_df[["a_att", "a_assign", "a_internal"]].mean().mean())

    div = compute_divergence(stu_df, student_id)
    z_composites = get_student_weekly_z_composite(stu_df, student_id)
    cusum = detect_cusum(z_composites, min_std=0.25)
    ewma = compute_ewma(z_composites, min_std=0.25)

    bunk_budgets: list[int] = []
    sub_75_count = 0
    for _subj_id, sgrp in stu_df.groupby("subject_id"):
        if "attended_sessions" in sgrp.columns and "total_sessions" in sgrp.columns:
            att_sessions = int(sgrp["attended_sessions"].sum())
            tot_sessions = int(sgrp["total_sessions"].sum())
            spw = (
                int(sgrp["sessions_per_week"].iloc[0])
                if "sessions_per_week" in sgrp.columns
                else max(1, round(tot_sessions / max(1, len(sgrp))))
            )
        else:
            spw = 3
            tot_sessions = len(sgrp) * spw
            att_sessions = round(float(sgrp["attendance_pct"].mean()) / 100.0 * tot_sessions)

        subj_week = min(cutoff_week, int(sgrp["week"].max()))
        ponr = calculate_subject_ponr(
            attended_so_far=att_sessions,
            total_sessions_so_far=tot_sessions,
            sessions_per_week=spw,
            current_week=subj_week,
            total_weeks=total_weeks,
            attendance_threshold=attendance_threshold,
        )
        bunk_budgets.append(int(ponr["bunk_budget"]))
        if float(ponr["current_pct"]) < attendance_threshold * 100.0:
            sub_75_count += 1

    sub_40_count = int((subj_ia < internal_threshold * 100.0).sum())

    return {
        "student_id": int(student_id),
        "att_mean": round(float(stu_df["attendance_pct"].mean()), 4),
        "att_min": round(float(subj_att.min()), 4),
        "att_recent_2w": round(float(recent_df["attendance_pct"].mean()), 4),
        "assign_mean": round(float(stu_df["assignment_score"].mean()), 4),
        "assign_recent_2w": round(float(recent_df["assignment_score"].mean()), 4),
        "internal_mean": round(float(stu_df["internal_score"].mean()), 4),
        "internal_min": round(float(subj_ia.min()), 4),
        "internal_recent_2w": round(float(recent_df["internal_score"].mean()), 4),
        "z_att_mean": round(float(stu_df["z_att"].mean()), 4),
        "z_assign_mean": round(float(stu_df["z_assign"].mean()), 4),
        "z_internal_mean": round(float(stu_df["z_internal"].mean()), 4),
        "v_composite_latest": round(v_comp, 4),
        "a_composite_latest": round(a_comp, 4),
        "divergence_index": round(float(div["divergence_index"]), 4),
        "cusum_triggered": 1.0 if cusum["change_point_detected"] else 0.0,
        "cusum_shift_magnitude": round(float(cusum["shift_magnitude"] or 0.0), 4),
        "ewma_flagged_count": float(len(ewma["flagged_weeks"])),
        "min_bunk_budget": float(min(bunk_budgets) if bunk_budgets else 0),
        "sub_75_att_count": float(sub_75_count),
        "sub_40_ia_count": float(sub_40_count),
    }


def extract_features(
    records_df: pd.DataFrame,
    cutoff_week: int = 8,
    total_weeks: int = DEFAULT_TOTAL_WEEKS,
    attendance_threshold: float = DEFAULT_ATTENDANCE_THRESHOLD,
    internal_threshold: float = DEFAULT_INTERNAL_THRESHOLD,
) -> pd.DataFrame:
    """
    Extract leakage-free per-student features strictly from ``week <= cutoff_week``.

    Returns a DataFrame with ``student_id`` followed by ``FEATURE_NAMES``.
    """
    clean_df = sanitize_records_frame(records_df)
    window_df = clean_df[clean_df["week"] <= cutoff_week].copy()
    if window_df.empty:
        return pd.DataFrame(columns=["student_id", *FEATURE_NAMES])

    scored_df = compute_cohort_zscores(window_df)
    rows: list[dict[str, float]] = []
    for sid, stu_df in scored_df.groupby("student_id", sort=True):
        row = _extract_single_student_row(
            stu_df=stu_df,
            student_id=int(sid),
            cutoff_week=cutoff_week,
            total_weeks=total_weeks,
            attendance_threshold=attendance_threshold,
            internal_threshold=internal_threshold,
        )
        rows.append(row)

    out_df = pd.DataFrame(rows, columns=["student_id", *FEATURE_NAMES])
    return out_df.replace([np.inf, -np.inf], 0.0).fillna(0.0)
