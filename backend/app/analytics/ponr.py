"""
Per-Subject Point-of-No-Return (PONR) Calculator.

Computes the mathematical deadline before which a student MUST attend all
remaining sessions to satisfy university attendance minimums.

University Policy (Indian defaults, configurable):
  - Minimum attendance  : 75% per subject
  - Minimum internal    : 40% per-subject minimum internal assessment
  - Theory sessions     : 3/week × 14 weeks = 42 total
  - Lab sessions        : 2/week × 14 weeks = 28 total

Eligibility Status tiers:
  SAFE                       — bunk_budget > 5  (safe to miss a few more)
  WATCH                      — bunk_budget in [2, 5]
  WINDOW_CLOSING             — bunk_budget in [0, 1]
  UNRECOVERABLE_WITHOUT_WAIVER — cannot reach threshold even attending every session
"""

from __future__ import annotations

import math

DEFAULT_ATTENDANCE_THRESHOLD = 0.75
DEFAULT_INTERNAL_THRESHOLD = 0.40
DEFAULT_TOTAL_WEEKS = 14


def calculate_subject_ponr(
    attended_so_far: int,
    total_sessions_so_far: int,
    sessions_per_week: int,
    current_week: int,
    total_weeks: int = DEFAULT_TOTAL_WEEKS,
    attendance_threshold: float = DEFAULT_ATTENDANCE_THRESHOLD,
) -> dict:
    """
    Compute attendance PONR for a single subject.

    Parameters
    ----------
    attended_so_far        : Sessions actually attended up to current_week.
    total_sessions_so_far  : Total sessions held up to current_week.
    sessions_per_week      : Sessions scheduled per week (3 = theory, 2 = lab).
    current_week           : Week number completed (1-indexed).
    total_weeks            : Full semester length.
    attendance_threshold   : Minimum attendance fraction (default 0.75).

    Returns
    -------
    dict:
        attended_so_far        — input (echoed)
        current_pct            — attendance % to date
        bunk_budget            — sessions that can still be missed
        ponr_sessions_left     — alias for bunk_budget
        min_future_needed      — sessions MUST attend from now on
        remaining_sessions     — sessions left in semester
        min_total_needed       — absolute minimum sessions for the full semester
        eligibility_status     — SAFE | WATCH | WINDOW_CLOSING | UNRECOVERABLE_WITHOUT_WAIVER
    """
    total_sessions = sessions_per_week * total_weeks
    remaining_weeks = max(0, total_weeks - current_week)
    remaining_sessions = sessions_per_week * remaining_weeks
    min_total_needed = math.ceil(attendance_threshold * total_sessions)
    min_future_needed = max(0, min_total_needed - attended_so_far)
    bunk_budget = remaining_sessions - min_future_needed

    if min_future_needed > remaining_sessions:
        status = "UNRECOVERABLE_WITHOUT_WAIVER"
    elif bunk_budget <= 1:
        status = "WINDOW_CLOSING"
    elif bunk_budget <= 5:
        status = "WATCH"
    else:
        status = "SAFE"

    current_pct = (
        (attended_so_far / total_sessions_so_far * 100.0) if total_sessions_so_far > 0 else 0.0
    )

    return {
        "attended_so_far": attended_so_far,
        "current_pct": round(current_pct, 2),
        "bunk_budget": bunk_budget,
        "bunk_budget_sessions": bunk_budget,
        "ponr_sessions_left": bunk_budget,
        "min_future_needed": min_future_needed,
        "remaining_sessions": remaining_sessions,
        "min_total_needed": min_total_needed,
        "eligibility_status": status,
    }


def assess_internal_standing(
    internal_scores: list[float],
    threshold: float = DEFAULT_INTERNAL_THRESHOLD,
) -> dict:
    """
    Assess whether a student meets the 40% per-subject minimum internal assessment rule.

    Parameters
    ----------
    internal_scores : List of internal scores (0–100 each).
    threshold       : Minimum average required (default 0.40 → 40%).

    Returns
    -------
    dict:
        average_pct        — mean internal score / 100
        min_needed_ia_pct  — threshold (echoed)
        passing            — True if average_pct >= threshold
    """
    if not internal_scores:
        return {"average_pct": 0.0, "min_needed_ia_pct": threshold, "passing": False}
    avg = sum(internal_scores) / len(internal_scores)
    avg_pct = avg / 100.0
    return {
        "average_pct": round(avg_pct, 4),
        "min_needed_ia_pct": threshold,
        "passing": avg_pct >= threshold,
    }
