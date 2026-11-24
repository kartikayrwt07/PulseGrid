"""Precomputed Week 4..active_week Time Machine engine comparing PulseGrid vs Naive Static."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.analytics.archetype import diagnose_archetypes
from app.analytics.cusum import detect_cusum
from app.analytics.divergence import compute_divergence
from app.analytics.features import FEATURE_NAMES, extract_features
from app.analytics.ml_inference import DEFAULT_ARTIFACTS_DIR, RISK_TIER_LABELS, predict_batch
from app.analytics.ponr import calculate_subject_ponr
from app.analytics.zscore import compute_cohort_zscores, get_student_weekly_z_composite
from app.core.config import Settings, get_settings
from app.models import Student, WeeklyTimelineCache
from app.repositories.snapshot_repo import get_active_week, safe_json_loads
from app.schemas.time_machine import (
    EngineWeekMetrics,
    ShockBanner,
    TimeMachinePoint,
    TimeMachineResponse,
)

MIN_TIME_MACHINE_WEEK = 4
SHOCK_DROP_THRESHOLD = 12.0


def _detect_week_shock(raw_df: pd.DataFrame, week: int) -> ShockBanner | None:
    prior = raw_df[raw_df["week"] < week]
    curr = raw_df[raw_df["week"] == week]
    if prior.empty or curr.empty:
        return None
    prior_means = prior.groupby("subject_code")["internal_score"].mean()
    curr_means = curr.groupby(["subject_code", "subject_name"])["internal_score"].mean()
    worst: tuple[float, str, str] | None = None
    for (code, name), c_mean in curr_means.items():
        if code not in prior_means:
            continue
        drop = float(prior_means[code] - c_mean)
        if drop >= SHOCK_DROP_THRESHOLD and (worst is None or drop > worst[0]):
            worst = (drop, str(code), str(name))
    if worst is None:
        return None
    drop_pts, code, name = worst
    rounded_drop = round(drop_pts, 1)
    return ShockBanner(
        subject_code=code,
        subject_name=name,
        week=week,
        drop_pts=rounded_drop,
        message=f"{code} ({name}) Week {week} Hard Exam Shock (-{rounded_drop:.0f} pts avg)",
    )


def _naive_assessment(
    cum_att_min: float, cum_marks_mean: float, wk_min_ia: float, wk_min_att: float
) -> tuple[str, float, bool]:
    """Static uncalibrated ERP rule (<60% marks or <75% attendance)."""
    marks_breach = cum_marks_mean < 60.0 or wk_min_ia < 60.0
    att_breach = cum_att_min < 75.0
    if marks_breach and att_breach:
        tier = "CRITICAL"
    elif marks_breach or att_breach:
        tier = "AT_RISK"
    elif wk_min_ia < 70.0 or wk_min_att < 75.0:
        tier = "WATCH"
    else:
        tier = "SAFE"

    marks_gap = max(0.0, 82.0 - min(cum_marks_mean, wk_min_ia))
    att_gap = max(0.0, 82.0 - cum_att_min)
    score = round(min(100.0, max(5.0, marks_gap * 2.1 + att_gap * 1.4)), 2)
    return tier, score, marks_breach or att_breach


def _compute_week_payload(
    raw_df: pd.DataFrame,
    meta_map: dict[int, tuple[str, str, str | None]],
    week: int,
    active_week: int,
    available_weeks: list[int],
    settings: Settings,
    artifacts_dir: Path,
) -> dict[str, Any]:
    sub_df = raw_df[raw_df["week"] <= week]
    scored_w = compute_cohort_zscores(sub_df)
    feat_df = extract_features(
        sub_df,
        cutoff_week=week,
        total_weeks=settings.TOTAL_WEEKS,
        attendance_threshold=settings.ATTENDANCE_THRESHOLD,
        internal_threshold=settings.INTERNAL_THRESHOLD,
    )
    probs_arr, proj_arr = predict_batch(feat_df[FEATURE_NAMES], artifacts_dir=artifacts_dir)
    ml_map = {
        int(row["student_id"]): (probs_arr[i], float(proj_arr[i]))
        for i, (_, row) in enumerate(feat_df.iterrows())
    }

    wk_only = sub_df[sub_df["week"] == week]
    wk_ia_min = wk_only.groupby("student_id")["internal_score"].min().to_dict()
    wk_att_min = wk_only.groupby("student_id")["attendance_pct"].min().to_dict()

    pg_counts: Counter[str] = Counter()
    nv_counts: Counter[str] = Counter()
    pg_fa = 0
    nv_fa = 0
    pg_slip_det = 0
    nv_slip_det = 0
    slip_total = 0
    aarav_pg = False
    aarav_nv = False
    points: list[dict[str, Any]] = []

    for sid, stu_df in scored_w.groupby("student_id", sort=True):
        student_id = int(sid)
        roll_no, name, tag = meta_map.get(student_id, (f"STU-{student_id:03d}", "Student", None))
        is_on_track = (tag or "ON_TRACK") == "ON_TRACK"
        is_silent_slipper = tag == "SILENT_SLIPPER"
        is_aarav = roll_no == "STU-001"

        z_comps = get_student_weekly_z_composite(stu_df, student_id)
        cusum = detect_cusum(z_comps, min_std=0.25)
        div = compute_divergence(stu_df, student_id)
        ponr_rows = [
            calculate_subject_ponr(
                int(sgrp["attended_sessions"].sum()),
                int(sgrp["total_sessions"].sum()),
                int(sgrp["sessions_per_week"].iloc[0]),
                week,
                settings.TOTAL_WEEKS,
                settings.ATTENDANCE_THRESHOLD,
            )
            for _, sgrp in stu_df.groupby("subject_id", sort=True)
        ]
        subj_z = [
            {
                "z_att_mean": float(sgrp["z_att"].mean()),
                "z_internal_mean": float(sgrp["z_internal"].mean()),
            }
            for _, sgrp in stu_df.groupby("subject_id", sort=True)
        ]
        z_rec = float(sum(z_comps[-2:]) / max(1, len(z_comps[-2:])))
        arch = str(
            diagnose_archetypes(
                ponr_rows,
                div,
                cusum,
                z_rec,
                subj_z,
                float(stu_df["z_internal"].mean()),
                float(stu_df["z_att"].mean()),
            )["primary_archetype"]
        )

        probs, proj = ml_map[student_id]
        pg_tier = RISK_TIER_LABELS[int(np.argmax(probs))]
        pg_score = round(float(np.dot(probs, np.array([0.0, 35.0, 72.0, 100.0]))), 2)
        cusum_trig = bool(cusum["change_point_detected"])
        pg_flagged = pg_tier in ("AT_RISK", "CRITICAL") or cusum_trig

        feat_row = feat_df.loc[feat_df["student_id"] == student_id].iloc[0]
        cum_att_min = float(feat_row["att_min"])
        cum_marks = 0.5 * float(feat_row["assign_mean"]) + 0.5 * float(feat_row["internal_mean"])
        nv_tier, nv_score, nv_flagged = _naive_assessment(
            cum_att_min,
            cum_marks,
            float(wk_ia_min.get(student_id, 100.0)),
            float(wk_att_min.get(student_id, 100.0)),
        )

        pg_counts[pg_tier] += 1
        nv_counts[nv_tier] += 1
        if is_on_track and pg_flagged:
            pg_fa += 1
        if is_on_track and nv_flagged:
            nv_fa += 1
        if is_silent_slipper:
            slip_total += 1
            if pg_flagged:
                pg_slip_det += 1
            if nv_flagged:
                nv_slip_det += 1
        if is_aarav:
            aarav_pg = pg_flagged
            aarav_nv = nv_flagged

        points.append({
            "student_id": student_id,
            "roll_no": roll_no,
            "name": name,
            "risk_score": pg_score,
            "naive_risk_score": nv_score,
            "projected_score": round(proj, 2),
            "risk_tier": pg_tier,
            "naive_tier": nv_tier,
            "archetype": arch,
            "cusum_triggered": cusum_trig,
            "naive_flagged": nv_flagged,
            "is_hero_aarav": is_aarav,
        })

    shock = _detect_week_shock(raw_df, week)
    prevented = max(0, nv_fa - pg_fa)
    if shock is not None and prevented > 0:
        callout = (
            f"PulseGrid prevented {prevented} false alarms during {shock.subject_code} "
            f"Week {week} exam shock"
        )
    elif week >= 7 and aarav_pg:
        callout = (
            f"PulseGrid caught STU-001 Aarav at Week {week} via CUSUM despite >80% cumulative marks"
        )
    else:
        callout = f"Week {week}: {prevented} false alarms avoided vs. static threshold rules"

    pg_metrics = EngineWeekMetrics(
        safe_count=pg_counts["SAFE"],
        watch_count=pg_counts["WATCH"],
        at_risk_count=pg_counts["AT_RISK"],
        critical_count=pg_counts["CRITICAL"],
        flagged_count=pg_counts["AT_RISK"] + pg_counts["CRITICAL"],
        false_alarms_on_track=pg_fa,
        silent_slipper_detected=pg_slip_det,
        silent_slipper_total=slip_total,
        aarav_detected=aarav_pg,
    )
    nv_metrics = EngineWeekMetrics(
        safe_count=nv_counts["SAFE"],
        watch_count=nv_counts["WATCH"],
        at_risk_count=nv_counts["AT_RISK"],
        critical_count=nv_counts["CRITICAL"],
        flagged_count=nv_counts["AT_RISK"] + nv_counts["CRITICAL"],
        false_alarms_on_track=nv_fa,
        silent_slipper_detected=nv_slip_det,
        silent_slipper_total=slip_total,
        aarav_detected=aarav_nv,
    )
    return TimeMachineResponse(
        week=week,
        active_week=active_week,
        available_weeks=available_weeks,
        shock_banner=shock,
        pulsegrid=pg_metrics,
        naive_static=nv_metrics,
        false_alarms_prevented=prevented,
        delta_callout=callout,
        points=[TimeMachinePoint(**p) for p in points],
    ).model_dump()


def rebuild_timeline_cache(
    db: Session,
    raw_df: pd.DataFrame,
    active_week: int,
    artifacts_dir: Path | None = None,
    commit: bool = False,
) -> int:
    """Build and store Week 4..active_week Time Machine snapshots inside weekly_timeline_cache."""
    settings = get_settings()
    art_dir = Path(artifacts_dir or DEFAULT_ARTIFACTS_DIR)
    students = db.scalars(select(Student)).all()
    meta_map = {int(s.id): (s.roll_no, s.name, s.persona_tag) for s in students}
    avail = list(range(MIN_TIME_MACHINE_WEEK, max(MIN_TIME_MACHINE_WEEK, active_week) + 1))

    rows: list[WeeklyTimelineCache] = []
    for wk in avail:
        payload = _compute_week_payload(raw_df, meta_map, wk, active_week, avail, settings, art_dir)
        rows.append(WeeklyTimelineCache(week=wk, payload_json=json.dumps(payload)))

    db.execute(delete(WeeklyTimelineCache))
    db.bulk_save_objects(rows)
    if commit:
        db.commit()
    else:
        db.flush()
    return len(rows)


def get_time_machine_week(db: Session, week: int | None = None) -> TimeMachineResponse:
    """Fetch precomputed Time Machine snapshot for week in <= 2 indexed SQL queries."""
    active_week = get_active_week(db)
    target_week = active_week if week is None else week
    if target_week < MIN_TIME_MACHINE_WEEK or target_week > active_week:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Week must be between {MIN_TIME_MACHINE_WEEK} and active week {active_week}.",
        )
    cached = db.scalar(
        select(WeeklyTimelineCache).where(WeeklyTimelineCache.week == target_week)
    )
    if cached is not None:
        return TimeMachineResponse(**safe_json_loads(cached.payload_json, {}))

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Time machine snapshot for week {target_week} not built yet.",
    )
