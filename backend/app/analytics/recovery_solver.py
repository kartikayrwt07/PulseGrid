"""
Constrained Counterfactual Recovery Solver.

Finds minimum-effort feasible adjustments over remaining semester weeks
enforcing university policy bounds:
  - >= 75% per-subject projected attendance via ponr.py floors
  - >= 40% per-subject minimum internal assessment standing
  - explicit requires_waiver=True and feasible=False when UNRECOVERABLE_WITHOUT_WAIVER
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import minimize

from app.analytics.features import FEATURE_NAMES
from app.analytics.ml_inference import RISK_TIER_LABELS, predict_batch, predict_risk
from app.analytics.ponr import DEFAULT_ATTENDANCE_THRESHOLD, DEFAULT_INTERNAL_THRESHOLD
from app.analytics.whatif import DEFAULT_TOTAL_WEEKS, project_features_for_whatif

__all__ = ["project_features_for_whatif", "solve_recovery"]


def _required_future_att_floor(ponr_results: list[dict[str, Any]] | None) -> float:
    """Minimum future attendance % needed so every recoverable subject reaches 75%."""
    req_floor = DEFAULT_ATTENDANCE_THRESHOLD * 100.0
    for item in ponr_results or []:
        rem = int(item.get("remaining_sessions", 0))
        min_fut = int(item.get("min_future_needed", 0))
        if rem > 0 and min_fut <= rem:
            req_floor = max(req_floor, (min_fut / rem) * 100.0)
    return min(100.0, round(req_floor, 2))


def _policy_bounds_satisfied(
    feat: dict[str, float],
    fut_att: float,
    req_att_floor: float,
    min_ia_pct: float = DEFAULT_INTERNAL_THRESHOLD * 100.0,
) -> bool:
    return (
        fut_att >= req_att_floor - 1e-6
        and float(feat.get("att_mean", 0.0)) >= DEFAULT_ATTENDANCE_THRESHOLD * 100.0 - 1e-6
        and float(feat.get("internal_mean", 0.0)) >= min_ia_pct - 1e-6
    )


def _build_candidate_grid(
    lb_att: float, lb_assign: float, lb_ia: float, req_att_floor: float, steps: int = 5
) -> np.ndarray:
    eff_lb_att = min(100.0, max(lb_att, req_att_floor))
    g_att = np.unique(np.append(np.linspace(eff_lb_att, 100.0, steps), [eff_lb_att, 90.0, 100.0]))
    g_assign = np.unique(np.append(np.linspace(lb_assign, 100.0, steps), [lb_assign, 85.0, 100.0]))
    g_ia = np.unique(np.append(np.linspace(lb_ia, 100.0, steps), [lb_ia, 45.0, 75.0, 90.0, 100.0]))
    g_att = g_att[g_att >= eff_lb_att - 1e-6]
    g_assign = g_assign[g_assign >= lb_assign - 1e-6]
    g_ia = g_ia[g_ia >= lb_ia - 1e-6]
    mesh = np.meshgrid(g_att, g_assign, g_ia, indexing="ij")
    return np.column_stack([m.ravel() for m in mesh])


def _effort_cost(cand: np.ndarray, lb: np.ndarray) -> float:
    diff = np.maximum(0.0, cand - lb) / 100.0
    return float(np.sum(np.array([1.0, 0.8, 1.4]) * (diff**2)))


def _make_step(
    feature: str,
    label: str,
    current_pct: float,
    target_pct: float,
    action: str,
    subject: str = "ALL",
) -> dict[str, Any]:
    cur_norm = round(float(np.clip(current_pct / 100.0, 0.0, 1.0)), 4)
    tgt_norm = round(float(np.clip(max(current_pct, target_pct) / 100.0, 0.0, 1.0)), 4)
    return {
        "feature": feature,
        "label": label,
        "action": action,
        "subject": subject,
        "current_value": cur_norm,
        "target_value": tgt_norm,
        "current_pct": round(current_pct, 1),
        "target_pct": round(max(current_pct, target_pct), 1),
        "delta_pct": round(max(0.0, target_pct - current_pct), 1),
        "unit": "ratio",
    }


def _ponr_steps(ponr_results: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    for item in ponr_results or []:
        if item.get("eligibility_status") not in ("WINDOW_CLOSING", "UNRECOVERABLE_WITHOUT_WAIVER"):
            continue
        rem = max(1, int(item.get("remaining_sessions", 1)))
        min_fut = int(item.get("min_future_needed", rem))
        req_pct = min(100.0, (min_fut / rem) * 100.0)
        cur_pct = float(item.get("current_pct", 0.0))
        code = str(item.get("subject_code", "SUBJECT"))
        steps.append(_make_step(
            "subject_attendance_pct", f"{code} Attendance Floor", cur_pct, max(cur_pct, req_pct),
            f"Attend {min(min_fut, rem)}/{rem} remaining {code} sessions (75% rule).",
            subject=code,
        ))
    return steps


def _polish_with_slsqp(
    base_features: dict[str, float],
    x0: np.ndarray,
    lb: np.ndarray,
    req_att_floor: float,
    weeks_remaining: int,
    total_weeks: int,
    cohort_stats: dict[str, Any] | None,
    artifacts_dir: Path | None,
) -> np.ndarray:
    eff_lb = np.array([max(lb[0], req_att_floor), lb[1], max(lb[2], 40.0)], dtype=float)
    bounds = [(float(min(100.0, eff_lb[i])), 100.0) for i in range(3)]

    def _safe_constraint(x: np.ndarray) -> float:
        feat = project_features_for_whatif(
            base_features, float(x[0]), float(x[1]), float(x[2]),
            weeks_remaining, total_weeks, cohort_stats=cohort_stats,
        )
        pred = predict_risk(feat, artifacts_dir=artifacts_dir)
        return float((1.0 - pred["at_risk_probability"]) - 0.55)

    res = minimize(
        lambda x: _effort_cost(x, lb),
        np.clip(x0, eff_lb, 100.0),
        method="SLSQP",
        bounds=bounds,
        constraints=[{"type": "ineq", "fun": _safe_constraint}],
        options={"maxiter": 10, "ftol": 1e-2},
    )
    return np.clip(res.x, eff_lb, 100.0) if res.success else np.clip(x0, eff_lb, 100.0)


def _build_recovery_steps(
    base_features: dict[str, float],
    lb: np.ndarray,
    target: np.ndarray,
    weeks_remaining: int,
    ponr_results: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    steps = _ponr_steps(ponr_results)
    recent_floor = [
        min(float(lb[0]), float(base_features.get("att_recent_2w", lb[0]))),
        min(float(lb[1]), float(base_features.get("assign_recent_2w", lb[1]))),
        min(float(lb[2]), float(base_features.get("internal_recent_2w", lb[2]))),
    ]
    specs = [
        (0, "attendance_pct", "Future Weekly Attendance", lambda t: (
            f"Target {round(t)}% attendance over the next {weeks_remaining} weeks."
        )),
        (1, "assignment_score", "Assignment Submission Quality", lambda t: (
            f"Score at least {round(t)}% on upcoming assignments."
        )),
        (2, "internal_score", "Closed-Book Internal Target", lambda t: (
            f"Target {round(t)}% on remaining internals via active recall prep."
        )),
    ]
    for idx, feat, label, action_fn in specs:
        cur, tgt = recent_floor[idx], float(target[idx])
        if tgt - cur >= 1.5 or tgt - float(lb[idx]) >= 1.0:
            steps.append(_make_step(feat, label, cur, tgt, action_fn(tgt)))
    if not steps:
        steps.append(_make_step(
            "attendance_pct", "Sustain Weekly Attendance", float(lb[0]), float(lb[0]),
            f"Maintain {round(lb[0])}%+ attendance consistently.",
        ))
    return steps


def solve_recovery(
    student_features: dict[str, float],
    weeks_remaining: int = 5,
    total_weeks: int = DEFAULT_TOTAL_WEEKS,
    ponr_results: list[dict[str, Any]] | None = None,
    cohort_stats: dict[str, Any] | None = None,
    artifacts_dir: Path | None = None,
) -> dict[str, Any]:
    """Compute policy-constrained counterfactual recovery plan (bounds strictly in [0, 1])."""
    baseline = predict_risk(student_features, artifacts_dir=artifacts_dir)
    score_before = baseline["projected_final_score"]
    requires_waiver = any(
        r.get("eligibility_status") == "UNRECOVERABLE_WITHOUT_WAIVER" for r in (ponr_results or [])
    )
    req_att_floor = _required_future_att_floor(ponr_results)
    cur_att = float(np.clip(student_features.get("att_mean", 75.0), 0.0, 100.0))
    cur_assign = float(np.clip(student_features.get("assign_mean", 75.0), 0.0, 100.0))
    cur_ia = float(np.clip(student_features.get("internal_mean", 75.0), 0.0, 100.0))

    if baseline["risk_tier_idx"] == 0 and not requires_waiver:
        fallback = [_make_step(
            "attendance_pct", "Maintain attendance pace", cur_att, cur_att,
            f"Maintain {round(cur_att)}% weekly attendance through Week {total_weeks}.",
        )]
        return {
            "feasible": True, "current_tier": "SAFE", "target_tier": "SAFE",
            "projected_score_before": score_before, "projected_score_after": score_before,
            "waiver_required": False, "requires_waiver": False,
            "recovery_steps": _ponr_steps(ponr_results) or fallback,
            "summary": "Student is projected SAFE. Maintain current attendance and study cadence.",
        }

    if weeks_remaining <= 0 or requires_waiver:
        return {
            "feasible": False, "current_tier": baseline["risk_tier"],
            "target_tier": baseline["risk_tier"],
            "projected_score_before": score_before, "projected_score_after": score_before,
            "waiver_required": True, "requires_waiver": True,
            "recovery_steps": _ponr_steps(ponr_results),
            "summary": (
                "Attendance waiver required: cannot satisfy 75% rule within remaining sessions."
                if requires_waiver
                else "Semester window closed; academic advisor waiver intervention required."
            ),
        }

    lb = np.array([cur_att, cur_assign, cur_ia], dtype=float)
    search_lb = np.array([
        min(cur_att, float(student_features.get("att_recent_2w", cur_att))),
        min(cur_assign, float(student_features.get("assign_recent_2w", cur_assign))),
        min(cur_ia, float(student_features.get("internal_recent_2w", cur_ia))),
    ])
    grid = _build_candidate_grid(cur_att, cur_assign, cur_ia, req_att_floor=req_att_floor)
    projected_list = [
        project_features_for_whatif(
            student_features, r[0], r[1], r[2], weeks_remaining, total_weeks,
            cohort_stats=cohort_stats,
        )
        for r in grid
    ]
    cand_arr = np.asarray([[p[n] for n in FEATURE_NAMES] for p in projected_list], dtype=float)
    probs, proj_scores = predict_batch(cand_arr, artifacts_dir=artifacts_dir)
    pred_tiers = np.argmax(probs, axis=1)

    policy_ok = np.array([
        _policy_bounds_satisfied(projected_list[i], float(grid[i, 0]), req_att_floor)
        for i in range(len(grid))
    ])
    feasible_mask = (pred_tiers <= 1) & policy_ok

    if not np.any(feasible_mask):
        best_idx = int(np.argmax((probs[:, 0] + probs[:, 1]) * 100.0 + proj_scores))
        best_x = grid[best_idx]
        feasible = False
        best_tier_idx, best_score = int(pred_tiers[best_idx]), float(proj_scores[best_idx])
    else:
        feasible_idxs = np.where(feasible_mask)[0]
        best_idx = min(
            feasible_idxs,
            key=lambda i: _effort_cost(grid[i], search_lb) + (0.015 if pred_tiers[i] == 1 else 0.0),
        )
        best_x = _polish_with_slsqp(
            student_features, grid[best_idx], lb, req_att_floor,
            weeks_remaining, total_weeks, cohort_stats, artifacts_dir,
        )
        ref_feat = project_features_for_whatif(
            student_features, best_x[0], best_x[1], best_x[2],
            weeks_remaining, total_weeks, cohort_stats=cohort_stats,
        )
        ref_pred = predict_risk(ref_feat, artifacts_dir=artifacts_dir)
        if ref_pred["risk_tier_idx"] <= 1 and _policy_bounds_satisfied(
            ref_feat, float(best_x[0]), req_att_floor
        ):
            feasible = True
            best_tier_idx, best_score = ref_pred["risk_tier_idx"], ref_pred["projected_final_score"]
        else:
            best_x = grid[best_idx]
            feasible = True
            best_tier_idx, best_score = int(pred_tiers[best_idx]), float(proj_scores[best_idx])

    target_tier = RISK_TIER_LABELS[best_tier_idx]
    steps = _build_recovery_steps(student_features, lb, best_x, weeks_remaining, ponr_results)
    summary = (
        f"Feasible recovery path reaches {target_tier} tier "
        f"(projected score {score_before:.1f}% -> {best_score:.1f}%)."
        if feasible
        else f"Advisor escalation needed; full recovery infeasible ({best_score:.1f}%)."
    )
    return {
        "feasible": feasible, "current_tier": baseline["risk_tier"], "target_tier": target_tier,
        "projected_score_before": score_before, "projected_score_after": round(best_score, 2),
        "waiver_required": False, "requires_waiver": False,
        "recovery_steps": steps, "summary": summary,
    }
