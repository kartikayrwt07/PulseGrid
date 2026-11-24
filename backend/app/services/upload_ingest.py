"""Transactional CSV/XLSX upsert and snapshot recomputation helper."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd
from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Student, Subject, WeeklyRecord
from app.repositories.snapshot_repo import get_active_week
from app.schemas.upload import UploadedRecordRow
from app.services.csv_mapper import REQUIRED_CANONICAL
from app.services.snapshot_service import recompute_all_snapshots


@dataclass(frozen=True)
class CommitSummary:
    students_upserted: int
    records_upserted: int
    snapshots_recomputed: int
    extra_warnings: list[str]


def _coerce_clean_str(val: Any) -> str:
    if val is None or pd.isna(val):
        return ""
    return str(val).strip()


def _coerce_int(val: Any, field: str) -> int:
    if val is None or pd.isna(val):
        raise ValueError(f"{field} is required")
    num = float(val)
    if not num.is_integer():
        raise ValueError(f"{field} must be a whole integer")
    return int(num)


def _coerce_float(val: Any, field: str) -> float:
    if val is None or pd.isna(val):
        raise ValueError(f"{field} is required")
    return float(val)


def validate_uploaded_rows(df: pd.DataFrame) -> list[UploadedRecordRow]:
    """Validate every non-empty row strictly via Pydantic before touching the database."""
    missing = [col for col in REQUIRED_CANONICAL if col not in df.columns]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Cannot commit upload; missing required columns: {', '.join(missing)}.",
        )

    clean_df = df.dropna(how="all")
    if clean_df.empty:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Cannot commit upload with zero non-empty data rows.",
        )

    validated: dict[tuple[str, str, int], UploadedRecordRow] = {}
    for idx, (_, raw) in enumerate(clean_df.iterrows(), start=1):
        try:
            row = UploadedRecordRow(
                roll_no=_coerce_clean_str(raw.get("roll_no")),
                student_name=_coerce_clean_str(raw.get("student_name")),
                subject_code=_coerce_clean_str(raw.get("subject_code")),
                week=_coerce_int(raw.get("week"), "week"),
                attended_sessions=_coerce_int(raw.get("attended_sessions"), "attended_sessions"),
                total_sessions=_coerce_int(raw.get("total_sessions"), "total_sessions"),
                assignment_score=_coerce_float(raw.get("assignment_score"), "assignment_score"),
                internal_score=_coerce_float(raw.get("internal_score"), "internal_score"),
            )
        except (ValueError, TypeError, ValidationError) as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Row {idx} failed validation: {exc}",
            ) from exc
        validated[(row.roll_no, row.subject_code, row.week)] = row

    return list(validated.values())


def commit_uploaded_records(
    db: Session, normalized_df: pd.DataFrame, current_week: int | None = None
) -> CommitSummary:
    """Validate and upsert students, subjects, and weekly records atomically."""
    rows = validate_uploaded_rows(normalized_df)
    roll_nos = sorted({r.roll_no for r in rows})
    subj_codes = sorted({r.subject_code for r in rows})
    weeks = sorted({r.week for r in rows})

    try:
        stu_map = {
            s.roll_no: s
            for s in db.scalars(select(Student).where(Student.roll_no.in_(roll_nos))).all()
        }
        for r in rows:
            existing = stu_map.get(r.roll_no)
            if existing is None:
                stu = Student(roll_no=r.roll_no, name=r.student_name)
                db.add(stu)
                stu_map[r.roll_no] = stu
            elif existing.name != r.student_name:
                existing.name = r.student_name

        subj_map = {
            s.code: s
            for s in db.scalars(select(Subject).where(Subject.code.in_(subj_codes))).all()
        }
        added_subjects = False
        for r in rows:
            if r.subject_code not in subj_map:
                added_subjects = True
                stype = "LAB" if r.subject_code.upper().endswith("L") else "THEORY"
                subj = Subject(
                    code=r.subject_code,
                    name=r.subject_code,
                    subject_type=stype,
                    sessions_per_week=max(1, r.total_sessions),
                )
                db.add(subj)
                subj_map[r.subject_code] = subj

        db.flush()

        touched_sids = {stu_map[r.roll_no].id for r in rows}
        touched_subj_ids = {subj_map[r.subject_code].id for r in rows}
        rec_map = {
            (rec.student_id, rec.subject_id, rec.week): rec
            for rec in db.scalars(
                select(WeeklyRecord).where(
                    WeeklyRecord.student_id.in_(touched_sids),
                    WeeklyRecord.subject_id.in_(touched_subj_ids),
                    WeeklyRecord.week.in_(weeks),
                )
            ).all()
        }

        for r in rows:
            sid = stu_map[r.roll_no].id
            subjid = subj_map[r.subject_code].id
            att_pct = round((r.attended_sessions / r.total_sessions) * 100.0, 2)
            rec = rec_map.get((sid, subjid, r.week))
            if rec is None:
                rec = WeeklyRecord(
                    student_id=sid,
                    subject_id=subjid,
                    week=r.week,
                    attended_sessions=r.attended_sessions,
                    total_sessions=r.total_sessions,
                    attendance_pct=att_pct,
                    assignment_score=round(r.assignment_score, 2),
                    internal_score=round(r.internal_score, 2),
                )
                db.add(rec)
                rec_map[(sid, subjid, r.week)] = rec
            else:
                rec.attended_sessions = r.attended_sessions
                rec.total_sessions = r.total_sessions
                rec.attendance_pct = att_pct
                rec.assignment_score = round(r.assignment_score, 2)
                rec.internal_score = round(r.internal_score, 2)

        db.flush()
        active_week = current_week if current_week is not None else get_active_week(db)
        recompute_targets = None if added_subjects else touched_sids
        snaps_count = recompute_all_snapshots(
            db=db,
            current_week=active_week,
            student_ids=recompute_targets,
            commit=False,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise

    return CommitSummary(
        students_upserted=len(roll_nos),
        records_upserted=len(rows),
        snapshots_recomputed=snaps_count,
        extra_warnings=[],
    )
