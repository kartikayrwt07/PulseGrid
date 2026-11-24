"""Edge-case hardening tests for CSV/XLSX upload validation & sanitization."""


def test_upload_headers_only_csv_returns_422(client, faculty_headers):
    res = client.post(
        "/api/v1/upload/csv",
        files={"file": ("headers_only.csv", b"roll_no,student_name,week\n", "text/csv")},
        headers=faculty_headers,
    )
    assert res.status_code == 422


def test_upload_corrupted_xlsx_returns_422_without_traceback(client, faculty_headers):
    res = client.post(
        "/api/v1/upload/csv",
        files={
            "file": (
                "broken.xlsx",
                b"not-a-valid-zip-excel-stream",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        headers=faculty_headers,
    )
    assert res.status_code == 422
    body = res.json()
    assert "Traceback" not in str(body)
    assert body["code"] == "HTTP_422"


def test_upload_unicode_and_path_traversal_filename_sanitized(client, faculty_headers):
    csv_data = (
        b"roll_no,student_name,subject_code,week,attended_sessions,"
        b"total_sessions,assignment_score,internal_score\n"
        b"STU-001,Aarav Kulkarni,MA101,10,3,3,85,80\n"
    )
    res = client.post(
        "/api/v1/upload/csv",
        files={"file": ("../../छात्र_résumé.csv", csv_data, "text/csv")},
        headers=faculty_headers,
    )
    assert res.status_code == 200
    assert res.json()["filename"] == "छात्र_résumé.csv"


def test_upload_all_null_column_and_out_of_range_flagged_in_warnings(client, faculty_headers):
    csv_data = (
        b"roll_no,student_name,subject_code,week,attended_sessions,"
        b"total_sessions,assignment_score,internal_score\n"
        b"STU-001,Aarav,MA101,10,4,3,125,\n"
    )
    res = client.post(
        "/api/v1/upload/csv",
        files={"file": ("bad_values.csv", csv_data, "text/csv")},
        headers=faculty_headers,
    )
    assert res.status_code == 200
    warnings = res.json()["warnings"]
    assert any("out-of-range assignment_score" in w for w in warnings)
    assert any("missing internal_score" in w for w in warnings)
    assert any("attended_sessions exceeding total_sessions" in w for w in warnings)
