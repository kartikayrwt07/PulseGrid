"""Integration tests for Faculty Dashboard summary and Interventions endpoints."""

from sqlalchemy import event

from app.core.database import engine


def test_dashboard_summary_kpis_and_zero_n_plus_1(client, faculty_headers):
    queries: list[str] = []

    def _capture(_conn, _cursor, statement, _params, _context, _execmany):
        queries.append(statement)

    event.listen(engine, "before_cursor_execute", _capture)
    try:
        res = client.get("/api/v1/dashboard/summary", headers=faculty_headers)
    finally:
        event.remove(engine, "before_cursor_execute", _capture)

    assert res.status_code == 200
    body = res.json()
    assert body["total_students"] == 240
    assert (
        body["safe_count"] + body["watch_count"] + body["at_risk_count"] + body["critical_count"]
        == 240
    )
    assert len(body["triage_points"]) == 240
    assert len(body["urgent_queue"]) > 0
    assert len(queries) <= 2, f"Expected <=2 queries, executed {len(queries)}"


def test_interventions_list_and_create(client, faculty_headers):
    initial = client.get("/api/v1/interventions?student_id=4", headers=faculty_headers)
    assert initial.status_code == 200
    assert initial.json()["total"] >= 1
    assert initial.json()["items"][0]["risk_improved"] is True

    created = client.post(
        "/api/v1/interventions",
        json={
            "student_id": 1,
            "week": 9,
            "intervention_type": "1-on-1 Advising",
            "notes": "Scheduled recovery check-in after Week 7 CUSUM drop.",
            "outcome": "Plan assigned",
        },
        headers=faculty_headers,
    )
    assert created.status_code == 201
    row = created.json()
    assert row["student_id"] == 1
    assert row["pre_risk_tier"] == "AT_RISK"
