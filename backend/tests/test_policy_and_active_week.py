"""Tests for dynamic active-week inference, PONR margin fields, and 40% per-subject IA copy."""

from sqlalchemy import delete

from app.core.database import SessionLocal
from app.models.weekly_record import WeeklyRecord
from app.repositories.snapshot_repo import get_active_week


def test_get_active_week_seeded_is_9_and_advances_to_10_on_insert(client, faculty_headers):
    with SessionLocal() as db:
        assert get_active_week(db) == 9

    health_before = client.get("/api/v1/health").json()
    assert health_before["active_week"] == 9
    assert health_before["total_weeks"] == 14

    dash_before = client.get("/api/v1/dashboard/summary", headers=faculty_headers).json()
    assert dash_before["active_week"] == 9
    assert dash_before["current_week"] == 9

    with SessionLocal() as db:
        db.add(
            WeeklyRecord(
                student_id=1,
                subject_id=1,
                week=10,
                attended_sessions=3,
                total_sessions=3,
                attendance_pct=100.0,
                assignment_score=88.0,
                internal_score=86.0,
            )
        )
        db.commit()
        assert get_active_week(db) == 10

    try:
        health_after = client.get("/api/v1/health").json()
        assert health_after["active_week"] == 10

        dash_after = client.get("/api/v1/dashboard/summary", headers=faculty_headers).json()
        assert dash_after["active_week"] == 10
        assert dash_after["current_week"] == 10
    finally:
        with SessionLocal() as db:
            db.execute(delete(WeeklyRecord).where(WeeklyRecord.week == 10))
            db.commit()
            assert get_active_week(db) == 9


def test_ponr_payload_exposes_bunk_budget_sessions(client, faculty_headers):
    res = client.get("/api/v1/students/3/analytics", headers=faculty_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["active_week"] == 9
    for subj in body["ponr"]:
        assert "bunk_budget_sessions" in subj
        assert subj["bunk_budget_sessions"] == subj["bunk_budget"]
