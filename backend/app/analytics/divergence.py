"""
Assignment–Internal Divergence Index.

Detects the "Assignment Comfort Trap": students who score high on take-home
assignments but fail closed-book internal assessments.

Formula:
    divergence_index = z_assign_avg - z_internal_avg
    (averaged across all subjects for the given student)

Threshold: divergence_index > 1.5 → PASSIVE_COPIER_CONCEPT_GAP flag.
"""

from __future__ import annotations

import pandas as pd


def compute_divergence(df: pd.DataFrame, student_id: int) -> dict:
    """
    Compute the Assignment–Internal Divergence Index for a single student.

    Parameters
    ----------
    df : DataFrame with pre-computed z_assign, z_internal columns
         (output of compute_cohort_zscores).
    student_id : The student to evaluate.

    Returns
    -------
    dict with keys:
        divergence_index  — z_assign_avg minus z_internal_avg
        z_assign_avg      — mean cohort z-score across all assignments
        z_internal_avg    — mean cohort z-score across all internals
        flagged           — True when divergence_index > DIVERGENCE_THRESHOLD
    """
    for col in ("z_assign", "z_internal"):
        if col not in df.columns:
            raise ValueError(f"Column '{col}' missing. Run compute_cohort_zscores() first.")

    student_df = df[df["student_id"] == student_id]
    if student_df.empty:
        return {
            "divergence_index": 0.0,
            "z_assign_avg": 0.0,
            "z_internal_avg": 0.0,
            "flagged": False,
        }

    z_assign_avg = float(student_df["z_assign"].mean())
    z_internal_avg = float(student_df["z_internal"].mean())
    divergence_index = z_assign_avg - z_internal_avg

    return {
        "divergence_index": round(divergence_index, 4),
        "z_assign_avg": round(z_assign_avg, 4),
        "z_internal_avg": round(z_internal_avg, 4),
        "flagged": divergence_index > 1.5,
    }


DIVERGENCE_THRESHOLD = 1.5
