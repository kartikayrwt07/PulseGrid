"""Tests for intervention logging and before/after risk-tier lift tracking."""


def test_priya_pinned_intervention_shows_positive_lift(client, faculty_headers):
    res = client.get("/api/v1/interventions?student_id=4", headers=faculty_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["total"] >= 1
    priya_iv = body["items"][0]
    assert priya_iv["student_roll_no"] == "STU-004"
    assert priya_iv["pre_risk_tier"] == "AT_RISK"
    assert priya_iv["current_risk_tier"] == "SAFE"
    assert priya_iv["risk_improved"] is True


def test_faculty_logs_new_intervention_with_baseline_capture(client, faculty_headers):
    res = client.post(
        "/api/v1/interventions",
        json={
            "student_id": 2,
            "week": 9,
            "intervention_type": "Concept Gap Remediation",
            "notes": "Assigned supervised closed-book problem drills for Meera.",
            "outcome": "In progress",
        },
        headers=faculty_headers,
    )
    assert res.status_code == 201
    created = res.json()
    assert created["student_roll_no"] == "STU-002"
    assert created["pre_risk_tier"] == "CRITICAL"
    assert created["current_risk_tier"] == "CRITICAL"
    assert created["risk_improved"] is False
