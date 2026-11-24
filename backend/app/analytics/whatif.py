"""
Shared What-If Feature Projection Engine.

Reused identically by both the Counterfactual Recovery Solver and /simulate.
Uses real cohort mean/std statistics and computes forward-projected CUSUM
without erasing historical trigger records.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from app.analytics.cusum import detect_cusum
from app.analytics.features import FEATURE_NAMES

DEFAULT_TOTAL_WEEKS = 14
_FALLBACK_COHORT_STD = {"att": 10.0, "assign": 10.0, "internal": 12.0}


def _projected_z(
    metric_key: str,
    projected_mean: float,
    cur_mean: float,
    cur_z: float,
    cohort_stats: dict[str, Any] | None,
) -> float:
    stat = (cohort_stats or {}).get(metric_key)
    if stat and float(stat.get("std", 0.0)) > 0:
        return (projected_mean - float(stat["mean"])) / max(float(stat["std"]), 1e-6)
    delta = projected_mean - cur_mean
    return cur_z + delta / _FALLBACK_COHORT_STD[metric_key]


def evaluate_forward_cusum(
    z_composites_history: list[float] | None,
    projected_z_future: float,
    projected_velocity: float,
    weeks_remaining: int,
    historical_triggered: bool,
) -> bool:
    """
    Evaluate forward CUSUM trajectory across Weeks current+1 .. 14 without
    mutating historical change-point records.
    """
    if not z_composites_history or weeks_remaining <= 0:
        return historical_triggered

    extended = [*z_composites_history, *([projected_z_future] * weeks_remaining)]
    fwd = detect_cusum(extended, min_std=0.25)
    # Recovery stabilization rule: sustained positive velocity across >=2 projected weeks
    baseline_mean = float(fwd.get("baseline_mean", 0.0))
    baseline_std = float(fwd.get("baseline_std", 0.25))
    stabilized = (
        weeks_remaining >= 2
        and projected_velocity > 0.0
        and projected_z_future >= baseline_mean - 0.5 * baseline_std
    )
    if stabilized:
        return False
    return bool(fwd.get("change_point_detected", False) or historical_triggered)


def project_whatif_state(
    base_features: dict[str, float],
    future_att_pct: float,
    future_assign_pct: float,
    future_internal_pct: float,
    weeks_remaining: int = 5,
    total_weeks: int = DEFAULT_TOTAL_WEEKS,
    cohort_stats: dict[str, Any] | None = None,
    z_composites_history: list[float] | None = None,
) -> tuple[dict[str, float], dict[str, bool]]:
    """
    Project features and forward CUSUM recovery flags under planned future targets.
    Historical CUSUM flags inside features remain immutable.
    """
    fut_att = float(np.clip(future_att_pct, 0.0, 100.0))
    fut_assign = float(np.clip(future_assign_pct, 0.0, 100.0))
    fut_ia = float(np.clip(future_internal_pct, 0.0, 100.0))

    rem = max(0, weeks_remaining)
    elapsed = max(1, total_weeks - rem)
    denom = float(elapsed + rem)

    cur_att = float(base_features.get("att_mean", 75.0))
    cur_assign = float(base_features.get("assign_mean", 75.0))
    cur_ia = float(base_features.get("internal_mean", 75.0))

    new_att = (elapsed * cur_att + rem * fut_att) / denom
    new_assign = (elapsed * cur_assign + rem * fut_assign) / denom
    new_ia = (elapsed * cur_ia + rem * fut_ia) / denom
    d_att, d_assign, d_ia = new_att - cur_att, new_assign - cur_assign, new_ia - cur_ia

    updated = {name: float(base_features.get(name, 0.0)) for name in FEATURE_NAMES}
    updated["att_mean"] = round(new_att, 4)
    updated["att_min"] = round(float(np.clip(updated["att_min"] + d_att * 1.15, 0.0, 100.0)), 4)
    updated["att_recent_2w"] = round(fut_att if rem >= 1 else updated["att_recent_2w"], 4)

    updated["assign_mean"] = round(new_assign, 4)
    updated["assign_recent_2w"] = round(
        fut_assign if rem >= 1 else updated["assign_recent_2w"], 4
    )

    updated["internal_mean"] = round(new_ia, 4)
    updated["internal_min"] = round(
        float(np.clip(updated["internal_min"] + d_ia * 1.1, 0.0, 100.0)), 4
    )
    updated["internal_recent_2w"] = round(fut_ia if rem >= 1 else updated["internal_recent_2w"], 4)

    z_att = _projected_z("att", new_att, cur_att, updated["z_att_mean"], cohort_stats)
    z_assign = _projected_z(
        "assign", new_assign, cur_assign, updated["z_assign_mean"], cohort_stats
    )
    z_ia = _projected_z("internal", new_ia, cur_ia, updated["z_internal_mean"], cohort_stats)
    updated["z_att_mean"] = round(z_att, 4)
    updated["z_assign_mean"] = round(z_assign, 4)
    updated["z_internal_mean"] = round(z_ia, 4)
    updated["divergence_index"] = round(z_assign - z_ia, 4)

    recent_comp = (
        base_features.get("att_recent_2w", cur_att)
        + base_features.get("assign_recent_2w", cur_assign)
        + base_features.get("internal_recent_2w", cur_ia)
    ) / 3.0
    fut_comp = (fut_att + fut_assign + fut_ia) / 3.0
    recent_gain = fut_comp - recent_comp

    if recent_gain > 0 or (d_att + d_assign + d_ia) > 0:
        effective_gain = max(recent_gain * 0.5, (d_att + d_assign + d_ia) / 3.0)
        updated["v_composite_latest"] = round(
            max(updated["v_composite_latest"], effective_gain / 6.0), 4
        )
        updated["a_composite_latest"] = round(
            max(updated["a_composite_latest"], effective_gain / 12.0), 4
        )

    extra_sessions = round((fut_att - cur_att) / 100.0 * rem * 3.0)
    updated["min_bunk_budget"] = float(updated["min_bunk_budget"] + extra_sessions)
    if updated["att_min"] >= 75.0:
        updated["sub_75_att_count"] = 0.0
    if updated["internal_min"] >= 40.0 and updated["internal_mean"] >= 45.0:
        updated["sub_40_ia_count"] = 0.0

    # Forward-projected Z-composite & CUSUM state (without mutating historical cusum_triggered)
    z_fut_att = _projected_z("att", fut_att, cur_att, updated["z_att_mean"], cohort_stats)
    z_fut_assign = _projected_z(
        "assign", fut_assign, cur_assign, updated["z_assign_mean"], cohort_stats
    )
    z_fut_ia = _projected_z("internal", fut_ia, cur_ia, updated["z_internal_mean"], cohort_stats)
    z_fut_comp = (z_fut_att + z_fut_assign + z_fut_ia) / 3.0
    hist_cusum = bool(base_features.get("cusum_triggered", 0.0) >= 0.5)
    fwd_cusum = evaluate_forward_cusum(
        z_composites_history, z_fut_comp, updated["v_composite_latest"], rem, hist_cusum
    )
    return updated, {
        "historical_cusum_triggered": hist_cusum,
        "projected_cusum_active": fwd_cusum,
    }


def project_features_for_whatif(
    base_features: dict[str, float],
    future_att_pct: float,
    future_assign_pct: float,
    future_internal_pct: float,
    weeks_remaining: int = 5,
    total_weeks: int = DEFAULT_TOTAL_WEEKS,
    cohort_stats: dict[str, Any] | None = None,
    z_composites_history: list[float] | None = None,
) -> dict[str, float]:
    """Return projected feature dict (backward-compatible wrapper around project_whatif_state)."""
    projected, _state = project_whatif_state(
        base_features=base_features,
        future_att_pct=future_att_pct,
        future_assign_pct=future_assign_pct,
        future_internal_pct=future_internal_pct,
        weeks_remaining=weeks_remaining,
        total_weeks=total_weeks,
        cohort_stats=cohort_stats,
        z_composites_history=z_composites_history,
    )
    return projected
