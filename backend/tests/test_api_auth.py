"""Role-based access control, JWT, and scoped data access API tests."""


def test_demo_token_issues_faculty_and_student_tokens(client):
    res_fac = client.post("/api/v1/auth/demo-token?role=faculty")
    assert res_fac.status_code == 200
    assert res_fac.json()["role"] == "faculty"
    assert res_fac.json()["access_token"]

    res_stu = client.post("/api/v1/auth/demo-token?role=student&student_id=3")
    assert res_stu.status_code == 200
    assert res_stu.json()["role"] == "student"
    assert res_stu.json()["student_id"] == 3


def test_unauthenticated_requests_rejected_401(client):
    assert client.get("/api/v1/students").status_code == 401
    assert client.get("/api/v1/dashboard/summary").status_code == 401
    assert client.get("/api/v1/students/1/analytics").status_code == 401
    assert client.get("/api/v1/model/audit").status_code == 401


def test_student_cannot_access_all_students(client, student1_headers):
    res = client.get("/api/v1/students", headers=student1_headers)
    assert res.status_code == 403


def test_student_cannot_access_dashboard_summary(client, student1_headers):
    res = client.get("/api/v1/dashboard/summary", headers=student1_headers)
    assert res.status_code == 403


def test_student_cannot_access_other_student_analytics_or_recovery(client, student1_headers):
    res_a = client.get("/api/v1/students/2/analytics", headers=student1_headers)
    res_r = client.get("/api/v1/students/2/recovery-plan", headers=student1_headers)
    assert res_a.status_code == 403
    assert res_r.status_code == 403


def test_student_can_access_own_analytics_and_recovery(client, student1_headers):
    res_a = client.get("/api/v1/students/1/analytics", headers=student1_headers)
    res_r = client.get("/api/v1/students/1/recovery-plan", headers=student1_headers)
    assert res_a.status_code == 200
    assert res_a.json()["roll_no"] == "STU-001"
    assert res_r.status_code == 200
    assert res_r.json()["student_id"] == 1


def test_student_interventions_scoped_to_self(client, student1_headers):
    denied = client.get("/api/v1/interventions?student_id=4", headers=student1_headers)
    assert denied.status_code == 403
    own = client.get("/api/v1/interventions", headers=student1_headers)
    assert own.status_code == 200
    post_res = client.post(
        "/api/v1/interventions",
        json={"student_id": 1, "week": 9, "intervention_type": "Note", "notes": "Blocked"},
        headers=student1_headers,
    )
    assert post_res.status_code == 403
