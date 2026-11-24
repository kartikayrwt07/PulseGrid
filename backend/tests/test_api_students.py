"""Integration and zero-N+1 SQL query verification tests for student & model endpoints."""

from sqlalchemy import event

from app.core.database import engine


def test_list_students_returns_240_with_zero_n_plus_1(client, faculty_headers):
    queries: list[str] = []

    def _capture(_conn, _cursor, statement, _params, _context, _execmany):
        queries.append(statement)

    event.listen(engine, "before_cursor_execute", _capture)
    try:
        res = client.get("/api/v1/students?limit=240", headers=faculty_headers)
    finally:
        event.remove(engine, "before_cursor_execute", _capture)

    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 240
    assert len(body["items"]) == 240
    # Strictly count + joined select (must NOT scale with 240 rows)
    assert len(queries) <= 3, f"Expected <=3 SQL statements, executed {len(queries)}"


def test_filter_and_search_students(client, faculty_headers):
    res = client.get("/api/v1/students?search=Aarav", headers=faculty_headers)
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 1
    assert items[0]["roll_no"] == "STU-001"
    assert items[0]["archetype"] == "SILENT_SLIPPER"


def test_hero_aarav_analytics_complete(client, faculty_headers):
    res = client.get("/api/v1/students/1/analytics", headers=faculty_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["cusum_triggered"] is True
    assert data["cusum_week"] == 7
    assert len(data["weekly_trajectory"]) == 9
    assert len(data["ponr"]) == 6
    assert len(data["shap_values"]) >= 5
    assert data["recovery_plan"]["feasible"] is True


def test_missing_student_returns_404(client, faculty_headers):
    res = client.get("/api/v1/students/9999/analytics", headers=faculty_headers)
    assert res.status_code == 404


def test_model_audit_endpoint(client, faculty_headers):
    res = client.get("/api/v1/model/audit", headers=faculty_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["at_risk_recall"] > 0.7
    assert body["macro_f1"] > 0.5
    assert len(body["model_comparison"]) == 3
