"""Tests for Week 4-9 Time Machine endpoint, caching speed, and shock resilience."""

from sqlalchemy import event

from app.core.database import engine


def test_time_machine_week5_shock_vs_pulsegrid_and_query_budget(client, faculty_headers):
    queries: list[str] = []

    def _capture(_conn, _cursor, statement, _params, _context, _execmany):
        queries.append(statement)

    event.listen(engine, "before_cursor_execute", _capture)
    try:
        res = client.get("/api/v1/dashboard/time-machine?week=5", headers=faculty_headers)
    finally:
        event.remove(engine, "before_cursor_execute", _capture)

    assert res.status_code == 200
    assert len(queries) <= 2, f"Expected <=2 SQL queries, executed {len(queries)}"
    body = res.json()
    assert body["week"] == 5
    assert body["shock_banner"] is not None
    assert body["shock_banner"]["subject_code"] == "CS201"
    assert (
        body["naive_static"]["false_alarms_on_track"]
        > body["pulsegrid"]["false_alarms_on_track"]
    )
    assert body["false_alarms_prevented"] > 0


def test_time_machine_week7_catches_aarav_via_cusum(client, faculty_headers):
    res = client.get("/api/v1/dashboard/time-machine?week=7", headers=faculty_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["pulsegrid"]["aarav_detected"] is True
    aarav_pts = [p for p in body["points"] if p["roll_no"] == "STU-001"]
    assert len(aarav_pts) == 1
    assert aarav_pts[0]["cusum_triggered"] is True


def test_time_machine_rbac_and_bounds(client, faculty_headers, student1_headers):
    assert (
        client.get("/api/v1/dashboard/time-machine?week=5", headers=student1_headers).status_code
        == 403
    )
    assert (
        client.get("/api/v1/dashboard/time-machine?week=2", headers=faculty_headers).status_code
        == 422
    )
    assert (
        client.get("/api/v1/dashboard/time-machine?week=15", headers=faculty_headers).status_code
        == 422
    )
