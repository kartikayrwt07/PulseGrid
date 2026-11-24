"""
CUSUM & EWMA Change-Point Detector.

Detects sustained performance drops in a student's weekly score series using:
  - One-sided downward CUSUM against the student's own early-semester baseline.
  - EWMA (Exponentially Weighted Moving Average) as a secondary indicator.

CUSUM algorithm (downward shift detection):
  S_0 = 0
  S_t = max(0, S_{t-1} + (baseline_mean - x_t) - k)

Where:
  k  = k_factor  * σ_baseline  (reference value / allowance, default 0.5σ)
  h  = h_factor  * σ_baseline  (control limit, default 4.0σ)

Trigger: first week t > baseline_weeks where S_t > h.

EWMA:
  E_0 = baseline_mean
  E_t = λ * x_t + (1 - λ) * E_{t-1}   (λ = 0.3)
  Flagged if E_t < baseline_mean - 1.5 * σ_baseline.
"""

from __future__ import annotations

import numpy as np

EWMA_LAMBDA = 0.3
EWMA_SIGMA_MULTIPLE = 1.5


def detect_cusum(
    weekly_scores: list[float],
    baseline_weeks: int = 4,
    k_factor: float = 0.5,
    h_factor: float = 4.0,
    min_std: float = 1e-6,
) -> dict:
    """
    Run one-sided downward CUSUM change-point detection on a weekly score series.

    Parameters
    ----------
    weekly_scores  : Ordered list of scores (index 0 = Week 1).
    baseline_weeks : Number of initial weeks used to compute personal baseline.
    k_factor       : CUSUM allowance = k_factor * σ_baseline.
    h_factor       : CUSUM control limit = h_factor * σ_baseline.

    Returns
    -------
    dict:
        change_point_detected  — bool
        change_point_week      — 1-indexed week of trigger (None if not detected)
        shift_magnitude        — baseline_mean - value at change point (None if not detected)
        cusum_series           — list[float] of S_t values (length = len(weekly_scores))
        baseline_mean          — float
        baseline_std           — float
    """
    if len(weekly_scores) < baseline_weeks:
        return _no_change_result(weekly_scores)

    baseline = weekly_scores[:baseline_weeks]
    baseline_arr = np.asarray(baseline, dtype=float)
    baseline_mean = float(np.mean(baseline_arr))
    baseline_std = float(np.std(baseline_arr, ddof=1)) if len(baseline_arr) > 1 else min_std
    baseline_std = max(baseline_std, min_std)

    k = k_factor * baseline_std
    h = h_factor * baseline_std

    cusum_series: list[float] = [0.0] * baseline_weeks
    s_prev = 0.0
    change_point_week: int | None = None
    shift_magnitude: float | None = None

    for i in range(baseline_weeks, len(weekly_scores)):
        x_t = weekly_scores[i]
        s_t = max(0.0, s_prev + (baseline_mean - x_t) - k)
        cusum_series.append(round(s_t, 4))
        if change_point_week is None and s_t > h:
            change_point_week = i + 1  # 1-indexed week number
            shift_magnitude = round(baseline_mean - x_t, 4)
        s_prev = s_t

    return {
        "change_point_detected": change_point_week is not None,
        "change_point_week": change_point_week,
        "shift_magnitude": shift_magnitude,
        "cusum_series": cusum_series,
        "baseline_mean": round(baseline_mean, 4),
        "baseline_std": round(baseline_std, 4),
    }


def compute_ewma(
    weekly_scores: list[float],
    baseline_weeks: int = 4,
    lam: float = EWMA_LAMBDA,
    min_std: float = 1e-6,
) -> dict:
    """
    Compute the EWMA series and flag weeks where the EWMA drops below
    baseline_mean - 1.5 * σ_baseline.

    Returns dict with ewma_series (list[float]) and flagged_weeks (list[int]).
    """
    if len(weekly_scores) < baseline_weeks:
        return {"ewma_series": list(weekly_scores), "flagged_weeks": []}

    baseline_arr = np.asarray(weekly_scores[:baseline_weeks], dtype=float)
    baseline_mean = float(np.mean(baseline_arr))
    baseline_std = max(
        float(np.std(baseline_arr, ddof=1)) if len(baseline_arr) > 1 else min_std, min_std
    )
    lower_control = baseline_mean - EWMA_SIGMA_MULTIPLE * baseline_std

    ewma = baseline_mean
    ewma_series: list[float] = []
    flagged_weeks: list[int] = []

    for i, x in enumerate(weekly_scores):
        ewma = lam * x + (1 - lam) * ewma
        ewma_series.append(round(ewma, 4))
        if i >= baseline_weeks and ewma < lower_control:
            flagged_weeks.append(i + 1)

    return {"ewma_series": ewma_series, "flagged_weeks": flagged_weeks}


def _no_change_result(scores: list[float]) -> dict:
    return {
        "change_point_detected": False,
        "change_point_week": None,
        "shift_magnitude": None,
        "cusum_series": [0.0] * len(scores),
        "baseline_mean": float(np.mean(scores)) if scores else 0.0,
        "baseline_std": 0.0,
    }
