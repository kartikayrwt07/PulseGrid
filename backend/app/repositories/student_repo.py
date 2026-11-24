"""Zero-N+1 repository queries for students and full analytics snapshots."""

from __future__ import annotations

from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.orm import Session

from app.analytics.ml_inference import group_shap_entries
from app.core.config import get_settings
from app.models.snapshot import PredictionSnapshot
from app.models.student import Student
from app.repositories.snapshot_repo import (
    extract_projected_score_after,
    get_active_week,
    safe_json_loads,
)
from app.schemas.analytics import (
    CUSUMResult,
    PONRSubjectStatus,
    SHAPEntry,
    StudentAnalyticsResponse,
    SubjectZSummary,
    WeeklyTrajectoryPoint,
)
from app.schemas.recovery import RecoveryPlanResponse
from app.schemas.student import StudentListResponse, StudentSummary


def _parse_shap_payload(raw_payload: object) -> tuple[list[SHAPEntry], list[SHAPEntry]]:
    if isinstance(raw_payload, dict):
        raw_list = list(raw_payload.get("raw_shap", []))
        grouped_list = list(raw_payload.get("grouped_shap", [])) or group_shap_entries(raw_list)
    elif isinstance(raw_payload, list):
        raw_list = list(raw_payload)
        grouped_list = group_shap_entries(raw_list)
    else:
        raw_list, grouped_list = [], []
    return [SHAPEntry(**s) for s in raw_list], [SHAPEntry(**g) for g in grouped_list]


def to_student_summary(student: Student, snap: PredictionSnapshot | None) -> StudentSummary:
    proj_after = extract_projected_score_after(snap)
    primary = snap.archetype if snap else "ON_TRACK"
    flags = [str(f) for f in safe_json_loads(snap.secondary_flags_json, [])] if snap else []
    return StudentSummary(
        id=student.id,
        roll_no=student.roll_no,
        name=student.name,
        program=student.program,
        year=student.year,
        is_hero_persona=student.is_hero_persona,
        risk_tier=snap.risk_tier if snap else "SAFE",
        risk_score=round(float(snap.risk_score), 2) if snap else 0.0,
        projected_final_score=round(float(snap.projected_final_score), 2) if snap else 0.0,
        projected_score_after=round(proj_after, 2),
        ponr_days_left=int(snap.ponr_days_left) if snap else 99,
        archetype=primary,
        primary_archetype=primary,
        secondary_flags=flags,
        divergence_index=round(float(snap.divergence_index), 3) if snap else 0.0,
        cusum_triggered=bool(snap.cusum_triggered) if snap else False,
        cusum_week=snap.cusum_week if snap else None,
    )


def list_students_with_snapshots(
    db: Session,
    risk_tier: str | None = None,
    archetype: str | None = None,
    search: str | None = None,
    sort_by: str = "urgency",
    limit: int = 50,
    offset: int = 0,
) -> StudentListResponse:
    """List students joined with PredictionSnapshot in two indexed SQL statements."""
    filters = []
    if risk_tier:
        filters.append(PredictionSnapshot.risk_tier == risk_tier)
    if archetype:
        filters.append(PredictionSnapshot.archetype == archetype)
    if search:
        term = f"%{search.strip()}%"
        filters.append(or_(Student.name.ilike(term), Student.roll_no.ilike(term)))

    count_stmt = (
        select(func.count())
        .select_from(Student)
        .outerjoin(PredictionSnapshot, PredictionSnapshot.student_id == Student.id)
    )
    if filters:
        count_stmt = count_stmt.where(*filters)
    total = int(db.scalar(count_stmt) or 0)

    order_clauses = {
        "urgency": [desc(PredictionSnapshot.risk_score), asc(PredictionSnapshot.ponr_days_left)],
        "ponr": [asc(PredictionSnapshot.ponr_days_left), desc(PredictionSnapshot.risk_score)],
        "name": [asc(Student.name)],
        "roll_no": [asc(Student.roll_no)],
    }.get(sort_by, [desc(PredictionSnapshot.risk_score), asc(PredictionSnapshot.ponr_days_left)])

    rows_stmt = (
        select(Student, PredictionSnapshot)
        .outerjoin(PredictionSnapshot, PredictionSnapshot.student_id == Student.id)
        .order_by(*order_clauses, asc(Student.id))
        .limit(limit)
        .offset(offset)
    )
    if filters:
        rows_stmt = rows_stmt.where(*filters)

    rows = db.execute(rows_stmt).all()
    items = [to_student_summary(stu, snap) for stu, snap in rows]
    return StudentListResponse(total=total, limit=limit, offset=offset, items=items)


def get_student_analytics_detail(
    db: Session, student_id: int
) -> StudentAnalyticsResponse | None:
    """Fetch a single student + snapshot in one joined query and parse JSON blocks."""
    stmt = (
        select(Student, PredictionSnapshot)
        .outerjoin(PredictionSnapshot, PredictionSnapshot.student_id == Student.id)
        .where(Student.id == student_id)
    )
    row = db.execute(stmt).first()
    if row is None:
        return None
    student, snap = row
    if snap is None:
        return None

    z_data = safe_json_loads(snap.z_scores_json, {})
    cusum_data = safe_json_loads(snap.cusum_json, {})
    ponr_data = safe_json_loads(snap.ponr_json, [])
    shap_data = safe_json_loads(snap.shap_json, {})
    shap_entries, grouped_entries = _parse_shap_payload(shap_data)
    secondary_flags = [str(f) for f in safe_json_loads(snap.secondary_flags_json, [])]
    recovery_data = safe_json_loads(snap.recovery_path_json, {})
    settings = get_settings()
    active_week = get_active_week(db)

    return StudentAnalyticsResponse(
        student_id=student.id,
        roll_no=student.roll_no,
        name=student.name,
        program=student.program,
        year=student.year,
        risk_tier=snap.risk_tier,
        risk_score=round(float(snap.risk_score), 2),
        projected_final_score=round(float(snap.projected_final_score), 2),
        ponr_days_left=int(snap.ponr_days_left),
        active_week=active_week,
        total_weeks=int(settings.TOTAL_WEEKS),
        archetype=snap.archetype,
        primary_archetype=snap.archetype,
        secondary_flags=secondary_flags,
        divergence_index=round(float(snap.divergence_index), 3),
        cusum_triggered=bool(snap.cusum_triggered),
        cusum_week=snap.cusum_week,
        z_att_avg=float(z_data.get("z_att_avg", 0.0)),
        z_assign_avg=float(z_data.get("z_assign_avg", 0.0)),
        z_internal_avg=float(z_data.get("z_internal_avg", 0.0)),
        baseline_features={
            str(k): float(v) for k, v in z_data.get("features", {}).items()
        },
        weekly_trajectory=[WeeklyTrajectoryPoint(**pt) for pt in z_data.get("weekly", [])],
        subject_z_summary=[SubjectZSummary(**s) for s in z_data.get("subjects", [])],
        cusum=CUSUMResult(
            change_point_detected=bool(cusum_data.get("change_point_detected", False)),
            change_point_week=cusum_data.get("change_point_week"),
            shift_magnitude=cusum_data.get("shift_magnitude"),
            cusum_series=list(cusum_data.get("cusum_series", [])),
            baseline_mean=float(cusum_data.get("baseline_mean", 0.0)),
            baseline_std=float(cusum_data.get("baseline_std", 0.0)),
            ewma=cusum_data.get("ewma"),
            z_composites=list(cusum_data.get("z_composites", [])),
        ),
        ponr=[
            PONRSubjectStatus(
                **{
                    **p,
                    "bunk_budget_sessions": int(
                        p.get("bunk_budget_sessions", p.get("bunk_budget", 0))
                    ),
                }
            )
            for p in ponr_data
        ],
        shap_values=shap_entries,
        grouped_shap=grouped_entries,
        recovery_plan=RecoveryPlanResponse(
            student_id=student.id,
            feasible=bool(recovery_data.get("feasible", False)),
            current_tier=str(recovery_data.get("current_tier", snap.risk_tier)),
            target_tier=str(recovery_data.get("target_tier", snap.risk_tier)),
            projected_score_before=float(
                recovery_data.get("projected_score_before", snap.projected_final_score)
            ),
            projected_score_after=float(
                recovery_data.get("projected_score_after", snap.projected_final_score)
            ),
            waiver_required=bool(recovery_data.get("waiver_required", False)),
            requires_waiver=bool(
                recovery_data.get("requires_waiver", recovery_data.get("waiver_required", False))
            ),
            recovery_steps=list(recovery_data.get("recovery_steps", [])),
            summary=str(recovery_data.get("summary", "")),
        ),
    )
