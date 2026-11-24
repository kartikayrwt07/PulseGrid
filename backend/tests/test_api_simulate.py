"""Integration and Pydantic boundary validation tests for /simulate endpoint."""


def test_simulate_valid_improvement_reduces_risk(client, faculty_headers):
    res = client.post(
        "/api/v1/simulate",
        json={
            "student_id": 1,
            "attendance_pct": 92.0,
            "assignment_score": 88.0,
            "internal_score": 85.0,
            "weeks_remaining": 5,
        },
        headers=faculty_headers,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["simulated_projected_score"] > body["baseline_projected_score"]
    assert body["simulated_tier"] in ("SAFE", "WATCH")
    assert len(body["shap_values"]) > 0


def test_simulate_clamps_or_rejects_impossible_sliders_422(client, faculty_headers):
    bad_high = client.post(
        "/api/v1/simulate",
        json={
            "student_id": 1,
            "attendance_pct": 110.0,
            "assignment_score": 80.0,
            "internal_score": 80.0,
        },
        headers=faculty_headers,
    )
    assert bad_high.status_code == 422

    bad_neg = client.post(
        "/api/v1/simulate",
        json={
            "student_id": 1,
            "attendance_pct": 80.0,
            "assignment_score": -5.0,
            "internal_score": 80.0,
        },
        headers=faculty_headers,
    )
    assert bad_neg.status_code == 422


def test_student_cannot_simulate_other_student(client, student1_headers):
    res = client.post(
        "/api/v1/simulate",
        json={
            "student_id": 2,
            "attendance_pct": 90.0,
            "assignment_score": 90.0,
            "internal_score": 90.0,
        },
        headers=student1_headers,
    )
    assert res.status_code == 403
