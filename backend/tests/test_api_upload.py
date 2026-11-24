"""Integration and error-handling tests for CSV/XLSX upload endpoint."""

from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def test_upload_clean_csv_succeeds(client, faculty_headers):
    csv_bytes = (DATA_DIR / "clean_sample.csv").read_bytes()
    res = client.post(
        "/api/v1/upload/csv",
        files={"file": ("clean_sample.csv", csv_bytes, "text/csv")},
        headers=faculty_headers,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["row_count"] == 10
    assert body["missing_required"] == []


def test_upload_messy_xlsx_maps_columns(client, faculty_headers):
    xlsx_bytes = (DATA_DIR / "messy_sample.xlsx").read_bytes()
    res = client.post(
        "/api/v1/upload/csv",
        files={
            "file": (
                "messy_sample.xlsx",
                xlsx_bytes,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        headers=faculty_headers,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["row_count"] == 10
    mapped_count = sum(1 for m in body["column_mappings"] if m["canonical_column"])
    assert mapped_count >= 4


def test_upload_empty_and_invalid_files_rejected(client, faculty_headers):
    res_empty = client.post(
        "/api/v1/upload/csv",
        files={"file": ("empty.csv", b"", "text/csv")},
        headers=faculty_headers,
    )
    assert res_empty.status_code == 400

    res_ext = client.post(
        "/api/v1/upload/csv",
        files={"file": ("notes.txt", b"hello", "text/plain")},
        headers=faculty_headers,
    )
    assert res_ext.status_code == 400


def test_student_forbidden_from_upload(client, student1_headers):
    csv_bytes = (DATA_DIR / "clean_sample.csv").read_bytes()
    res = client.post(
        "/api/v1/upload/csv",
        files={"file": ("clean_sample.csv", csv_bytes, "text/csv")},
        headers=student1_headers,
    )
    assert res.status_code == 403


def test_upload_preview_mode_does_not_mutate_db(client, faculty_headers):
    before = client.get("/api/v1/students?limit=5", headers=faculty_headers).json()["total"]
    csv_body = (
        b"roll_no,student_name,subject_code,week,attended_sessions,"
        b"total_sessions,assignment_score,internal_score\n"
        b"STU-991,Test Preview Learner,MA101,9,3,3,90.0,88.0\n"
    )
    res = client.post(
        "/api/v1/upload/csv?commit=false",
        files={"file": ("preview_only.csv", csv_body, "text/csv")},
        headers=faculty_headers,
    )
    assert res.status_code == 200
    assert res.json()["committed"] is False
    after = client.get("/api/v1/students?limit=5", headers=faculty_headers).json()["total"]
    assert after == before


def test_upload_invalid_rows_commit_returns_422_without_partial_writes(client, faculty_headers):
    before = client.get("/api/v1/students?limit=5", headers=faculty_headers).json()["total"]
    bad_csv = (
        b"roll_no,student_name,subject_code,week,attended_sessions,"
        b"total_sessions,assignment_score,internal_score\n"
        b"STU-992,Valid Row First,MA101,9,3,3,85.0,82.0\n"
        b"STU-993,Bad Row Second,MA101,9,3,3,85.0,150.0\n"
    )
    res = client.post(
        "/api/v1/upload/csv?commit=true",
        files={"file": ("invalid_batch.csv", bad_csv, "text/csv")},
        headers=faculty_headers,
    )
    assert res.status_code == 422
    after = client.get("/api/v1/students?limit=5", headers=faculty_headers).json()["total"]
    assert after == before


def test_upload_commit_upserts_and_reset_demo_restores_cohort(
    client, faculty_headers, student1_headers
):
    new_csv = (
        b"roll_no,student_name,subject_code,week,attended_sessions,"
        b"total_sessions,assignment_score,internal_score\n"
        b"STU-999,Uploaded Demo Scholar,MA101,9,3,3,91.0,89.0\n"
        b"STU-999,Uploaded Demo Scholar,CS201,9,3,3,90.0,87.0\n"
    )
    commit_res = client.post(
        "/api/v1/upload/csv?commit=true",
        files={"file": ("cohort_update.csv", new_csv, "text/csv")},
        headers=faculty_headers,
    )
    assert commit_res.status_code == 200
    body = commit_res.json()
    assert body["committed"] is True
    assert body["students_upserted"] == 1
    assert body["records_upserted"] == 2
    assert body["snapshots_recomputed"] == 1

    listed = client.get("/api/v1/students?search=STU-999", headers=faculty_headers).json()
    assert listed["total"] == 1
    assert listed["items"][0]["roll_no"] == "STU-999"

    # Student cannot invoke admin reset
    forbid = client.post("/api/v1/admin/reset-demo", headers=student1_headers)
    assert forbid.status_code == 403

    # Faculty resets cohort cleanly back to 240 students & 4 hero personas
    reset_res = client.post("/api/v1/admin/reset-demo", headers=faculty_headers)
    assert reset_res.status_code == 200
    reset_body = reset_res.json()
    assert reset_body["students_seeded"] == 240
    assert reset_body["snapshots_recomputed"] == 240

    students_after = client.get("/api/v1/students?limit=5", headers=faculty_headers).json()
    assert students_after["total"] == 240
    gone = client.get("/api/v1/students?search=STU-999", headers=faculty_headers).json()
    assert gone["total"] == 0

    aarav = client.get("/api/v1/students/1/analytics", headers=faculty_headers).json()
    assert aarav["roll_no"] == "STU-001"
    assert aarav["cusum_week"] == 7
    meera = client.get("/api/v1/students/2/analytics", headers=faculty_headers).json()
    assert meera["roll_no"] == "STU-002"
    rohan = client.get("/api/v1/students/3/analytics", headers=faculty_headers).json()
    assert rohan["roll_no"] == "STU-003"
    priya = client.get("/api/v1/students/4/analytics", headers=faculty_headers).json()
    assert priya["roll_no"] == "STU-004"
