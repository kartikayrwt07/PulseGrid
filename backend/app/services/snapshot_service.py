"""
Prediction Snapshot Orchestration Service.

Runs the full deterministic + ML + SHAP + counterfactual pipeline for every student
using records up to ``current_week`` (never peeking into future weeks) and persists
results into ``prediction_snapshots``.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.analytics.archetype import diagnose_archetypes
from app.analytics.cusum import compute_ewma, detect_cusum
from app.analytics.divergence import compute_divergence
from app.analytics.features import FEATURE_NAMES, extract_features
from app.analytics.ml_inference import (
    DEFAULT_ARTIFACTS_DIR,
    get_grouped_and_raw_shap,
    predict_risk,
    reload_models,
)
from app.analytics.ponr import assess_internal_standing, calculate_subject_ponr
from app.analytics.recovery_solver import solve_recovery
from app.analytics.zscore import (
    compute_cohort_zscores,
    get_student_weekly_composite,
    get_student_weekly_z_composite,
)
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models import PredictionSnapshot, Subject, WeeklyRecord
from app.repositories.snapshot_repo import get_active_week
from app.services.time_machine_service import rebuild_timeline_cache

Z_CUSUM_MIN_STD = 0.25


def load_records_frame(db: Session, max_week: int | None = None) -> pd.DataFrame:
    """Load weekly_records joined with subject metadata up to max_week (all weeks if None)."""
    q = db.query(
        WeeklyRecord.student_id,
        WeeklyRecord.subject_id,
        WeeklyRecord.week,
        WeeklyRecord.attended_sessions,
        WeeklyRecord.total_sessions,
        WeeklyRecord.attendance_pct,
        WeeklyRecord.assignment_score,
        WeeklyRecord.internal_score,
        Subject.code,
        Subject.name,
        Subject.subject_type,
        Subject.sessions_per_week,
    ).join(Subject, Subject.id == WeeklyRecord.subject_id)
    if max_week is not None:
        q = q.filter(WeeklyRecord.week <= max_week)
    cols = [
        "student_id", "subject_id", "week", "attended_sessions", "total_sessions",
        "attendance_pct", "assignment_score", "internal_score",
        "subject_code", "subject_name", "subject_type", "sessions_per_week",
    ]
    return pd.DataFrame(q.all(), columns=cols)


def _compute_cohort_stats(df: pd.DataFrame) -> dict[str, Any]:
    """Compute real active cohort mean/std across attendance, assignments, and internals."""
    def _stat(series: pd.Series) -> dict[str, float]:
        return {
            "mean": round(float(series.mean()), 4),
            "std": round(max(float(series.std(ddof=0)), 1e-6), 4),
        }

    return {
        "att": _stat(df["attendance_pct"]),
        "assign": _stat(df["assignment_score"]),
        "internal": _stat(df["internal_score"]),
    }


def _compute_student_snapshot_payload(
    student_id: int,
    stu_df: pd.DataFrame,
    feat_row: dict[str, float],
    cohort_stats: dict[str, Any],
    current_week: int,
    total_weeks: int,
    attendance_threshold: float,
    internal_threshold: float,
    artifacts_dir: Path,
) -> dict[str, Any]:
    div = compute_divergence(stu_df, student_id)
    raw_composites = get_student_weekly_composite(stu_df, student_id)
    z_composites = get_student_weekly_z_composite(stu_df, student_id)
    cusum = detect_cusum(z_composites, min_std=Z_CUSUM_MIN_STD)
    ewma = compute_ewma(z_composites, min_std=Z_CUSUM_MIN_STD)

    ponr_results: list[dict[str, Any]] = []
    subject_z_summary: list[dict[str, float]] = []
    ponr_days_candidates: list[int] = []

    for subj_id, sgrp in stu_df.groupby("subject_id", sort=True):
        spw = int(sgrp["sessions_per_week"].iloc[0])
        ponr = calculate_subject_ponr(
            attended_so_far=int(sgrp["attended_sessions"].sum()),
            total_sessions_so_far=int(sgrp["total_sessions"].sum()),
            sessions_per_week=spw,
            current_week=min(current_week, int(sgrp["week"].max())),
            total_weeks=total_weeks,
            attendance_threshold=attendance_threshold,
        )
        ponr.update(
            {
                "subject_id": int(subj_id),
                "subject_code": str(sgrp["subject_code"].iloc[0]),
                "subject_name": str(sgrp["subject_name"].iloc[0]),
                "subject_type": str(sgrp["subject_type"].iloc[0]),
                "sessions_per_week": spw,
                "internal_standing": assess_internal_standing(
                    sgrp["internal_score"].tolist(), threshold=internal_threshold
                ),
            }
        )
        ponr_results.append(ponr)
        ponr_days_candidates.append(round(int(ponr["bunk_budget"]) * 7.0 / max(1, spw)))
        subject_z_summary.append(
            {
                "subject_id": int(subj_id),
                "subject_code": str(sgrp["subject_code"].iloc[0]),
                "z_att_mean": round(float(sgrp["z_att"].mean()), 4),
                "z_assign_mean": round(float(sgrp["z_assign"].mean()), 4),
                "z_internal_mean": round(float(sgrp["z_internal"].mean()), 4),
            }
        )

    z_recent = float(sum(z_composites[-2:]) / max(1, len(z_composites[-2:])))
    diag = diagnose_archetypes(
        ponr_results=ponr_results,
        divergence_result=div,
        cusum_result=cusum,
        z_composite_recent=z_recent,
        subject_z_summary=subject_z_summary,
        z_internal_avg=float(stu_df["z_internal"].mean()),
        z_att_avg=float(stu_df["z_att"].mean()),
    )
    primary_archetype = str(diag["primary_archetype"])
    secondary_flags = [str(flag) for flag in diag["secondary_flags"]]

    ml_pred = predict_risk(feat_row, artifacts_dir=artifacts_dir)
    shap_bundle = get_grouped_and_raw_shap(feat_row, artifacts_dir=artifacts_dir)
    weeks_left = max(0, total_weeks - current_week)
    recovery = solve_recovery(
        student_features=feat_row,
        weeks_remaining=weeks_left,
        total_weeks=total_weeks,
        ponr_results=ponr_results,
        cohort_stats=cohort_stats,
        artifacts_dir=artifacts_dir,
    )

    cols = [
        "attendance_pct", "assignment_score", "internal_score", "z_att", "z_assign", "z_internal"
    ]
    weekly_points = stu_df.groupby("week")[cols].mean().reset_index().sort_values("week")
    weekly_series = [
        {
            "week": int(r["week"]),
            "attendance_pct": round(float(r["attendance_pct"]), 2),
            "assignment_score": round(float(r["assignment_score"]), 2),
            "internal_score": round(float(r["internal_score"]), 2),
            "composite": round(raw_composites[i], 2) if i < len(raw_composites) else 0.0,
            "z_composite": round(z_composites[i], 4) if i < len(z_composites) else 0.0,
            "z_att": round(float(r["z_att"]), 4),
            "z_assign": round(float(r["z_assign"]), 4),
            "z_internal": round(float(r["z_internal"]), 4),
        }
        for i, (_, r) in enumerate(weekly_points.iterrows())
    ]

    z_payload = {
        "weekly": weekly_series,
        "subjects": subject_z_summary,
        "z_att_avg": round(float(stu_df["z_att"].mean()), 4),
        "z_assign_avg": div["z_assign_avg"],
        "z_internal_avg": div["z_internal_avg"],
        "features": {k: feat_row[k] for k in FEATURE_NAMES},
        "cohort_stats": cohort_stats,
    }
    cusum_payload = {**cusum, "ewma": ewma, "z_composites": [round(z, 4) for z in z_composites]}

    return {
        "student_id": student_id,
        "computed_at": datetime.now(UTC),
        "risk_tier": ml_pred["risk_tier"],
        "risk_score": ml_pred["risk_score"],
        "projected_final_score": ml_pred["projected_final_score"],
        "ponr_days_left": min(ponr_days_candidates) if ponr_days_candidates else 99,
        "archetype": primary_archetype,
        "secondary_flags_json": json.dumps(secondary_flags),
        "divergence_index": div["divergence_index"],
        "cusum_triggered": bool(cusum["change_point_detected"]),
        "cusum_week": cusum["change_point_week"],
        "z_scores_json": json.dumps(z_payload),
        "cusum_json": json.dumps(cusum_payload),
        "ponr_json": json.dumps(ponr_results),
        "shap_json": json.dumps(shap_bundle),
        "recovery_path_json": json.dumps(recovery),
    }


def recompute_all_snapshots(
    db: Session | None = None,
    current_week: int | None = None,
    artifacts_dir: Path | None = None,
    student_ids: set[int] | None = None,
    commit: bool = True,
) -> int:
    """Recompute and persist PredictionSnapshot rows (full cohort or targeted IDs)."""
    settings = get_settings()
    art_dir = Path(artifacts_dir or DEFAULT_ARTIFACTS_DIR)
    reload_models(artifacts_dir=art_dir)

    own_session = db is None
    session = db or SessionLocal()
    try:
        week = current_week if current_week is not None else get_active_week(session)
        df = load_records_frame(session, max_week=week)
        if df.empty:
            return 0
        scored_df = compute_cohort_zscores(df)
        cohort_stats = _compute_cohort_stats(df)
        feat_df = extract_features(
            df,
            cutoff_week=week,
            total_weeks=settings.TOTAL_WEEKS,
            attendance_threshold=settings.ATTENDANCE_THRESHOLD,
            internal_threshold=settings.INTERNAL_THRESHOLD,
        )
        feat_map = {
            int(row["student_id"]): {k: float(row[k]) for k in FEATURE_NAMES}
            for _, row in feat_df.iterrows()
        }

        snapshots: list[PredictionSnapshot] = []
        for sid, stu_df in scored_df.groupby("student_id", sort=True):
            student_id = int(sid)
            if student_ids is not None and student_id not in student_ids:
                continue
            payload = _compute_student_snapshot_payload(
                student_id=student_id,
                stu_df=stu_df,
                feat_row=feat_map[student_id],
                cohort_stats=cohort_stats,
                current_week=week,
                total_weeks=settings.TOTAL_WEEKS,
                attendance_threshold=settings.ATTENDANCE_THRESHOLD,
                internal_threshold=settings.INTERNAL_THRESHOLD,
                artifacts_dir=art_dir,
            )
            snapshots.append(PredictionSnapshot(**payload))

        if student_ids is None:
            session.execute(delete(PredictionSnapshot))
        elif student_ids:
            session.execute(
                delete(PredictionSnapshot).where(PredictionSnapshot.student_id.in_(student_ids))
            )
        session.bulk_save_objects(snapshots)
        rebuild_timeline_cache(
            db=session,
            raw_df=df,
            active_week=week,
            artifacts_dir=art_dir,
            commit=False,
        )
        if commit:
            session.commit()
        else:
            session.flush()
        return len(snapshots)
    finally:
        if own_session:
            session.close()
