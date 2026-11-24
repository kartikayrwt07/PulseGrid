"""Tests for fuzzy CSV/XLSX column auto-mapper and data health checks."""

from pathlib import Path

import pandas as pd

from app.services.csv_mapper import inspect_data_health, map_columns_fuzzy

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def test_messy_xlsx_maps_all_canonical_columns():
    df = pd.read_excel(DATA_DIR / "messy_sample.xlsx", engine="openpyxl")
    entries, rename_map = map_columns_fuzzy([str(c) for c in df.columns])

    mapped_targets = set(rename_map.values())
    assert len(mapped_targets) >= 6
    assert "roll_no" in mapped_targets
    assert "subject_code" in mapped_targets
    assert "assignment_score" in mapped_targets
    assert "internal_score" in mapped_targets
    assert all(e.confidence >= 0.62 for e in entries if e.canonical_column)


def test_fuzzy_typos_map_without_exact_match():
    messy_headers = [
        "Stdnt Roll No",
        "Student_FullName",
        "Course_Cod",
        "Week_No",
        "Attended_Sess",
        "Total_Sess",
        "Assignment_Scroe",
        "Internal_Score_Pct",
    ]
    _entries, rename_map = map_columns_fuzzy(messy_headers)
    assert rename_map["Course_Cod"] == "subject_code"
    assert rename_map["Assignment_Scroe"] == "assignment_score"
    assert rename_map["Internal_Score_Pct"] == "internal_score"


def test_data_health_flags_out_of_range_and_attendance_errors():
    bad_df = pd.DataFrame(
        [
            {
                "roll_no": "STU-001",
                "student_name": "Aarav",
                "subject_code": "MA101",
                "week": 10,
                "attended_sessions": 5,
                "total_sessions": 3,
                "assignment_score": 115.0,
                "internal_score": 60.0,
            }
        ]
    )
    warnings = inspect_data_health(bad_df)
    assert any("out-of-range assignment_score" in w for w in warnings)
    assert any("attended_sessions exceeding total_sessions" in w for w in warnings)
