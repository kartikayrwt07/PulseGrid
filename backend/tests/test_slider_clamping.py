"""Boundary clamping and Pydantic validation tests for /simulate endpoint."""

import pytest


@pytest.mark.parametrize(
    "payload",
    [
        {"student_id": 1, "attendance_pct": 105, "assignment_score": 80, "internal_score": 80},
        {"student_id": 1, "attendance_pct": -1, "assignment_score": 80, "internal_score": 80},
        {"student_id": 1, "attendance_pct": 85, "assignment_score": 150, "internal_score": 80},
        {"student_id": 1, "attendance_pct": 85, "assignment_score": 80, "internal_score": -10},
        {
            "student_id": 1,
            "attendance_pct": 85.0,
            "assignment_score": 80.0,
            "internal_score": 80.0,
            "weeks_remaining": 0,
        },
        {
            "student_id": 1,
            "attendance_pct": 85.0,
            "assignment_score": 80.0,
            "internal_score": 80.0,
            "weeks_remaining": 20,
        },
        {"student_id": 0, "attendance_pct": 85.0, "assignment_score": 80.0, "internal_score": 80.0},
    ],
)
def test_simulate_rejects_out_of_bound_inputs_422(client, faculty_headers, payload):
    res = client.post("/api/v1/simulate", json=payload, headers=faculty_headers)
    assert res.status_code == 422


def test_simulate_accepts_exact_boundary_values(client, faculty_headers):
    res = client.post(
        "/api/v1/simulate",
        json={
            "student_id": 1,
            "attendance_pct": 100.0,
            "assignment_score": 100.0,
            "internal_score": 100.0,
            "weeks_remaining": 14,
        },
        headers=faculty_headers,
    )
    assert res.status_code == 200
    assert 0.0 <= res.json()["simulated_projected_score"] <= 100.0
