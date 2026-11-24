"""
Deterministic test fixtures for 4 Hero Personas and cohort scenarios.

All fixtures use hand-crafted data derived from the seeded behaviour in
generate_data.py (noise=0 / representative values) so math tests are
reproducible across any machine without touching the database.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Subject IDs used in fixtures (match generate_data.py SUBJECTS_SPEC order)
# ---------------------------------------------------------------------------
SUBJ_MA = 1   # Mathematics       THEORY 3/wk
SUBJ_DS = 2   # Data Structures   THEORY 3/wk
SUBJ_CN = 3   # Computer Networks THEORY 3/wk
SUBJ_CNL = 4  # CN Lab            LAB    2/wk
SUBJ_DB = 5   # DBMS              THEORY 3/wk
SUBJ_OS = 6   # Operating Systems THEORY 3/wk

WEEKS = list(range(1, 10))  # Weeks 1–9 (current semester state)
TOTAL_WEEKS = 14
CURRENT_WEEK = 9


# ---------------------------------------------------------------------------
# Utility: build a cohort DataFrame for a single subject & week range
# ---------------------------------------------------------------------------

def _make_cohort_row(
    student_id: int, subject_id: int, week: int,
    att: float, assign: float, internal: float,
    sessions_pw: int = 3,
) -> dict:
    attended = round(att / 100.0 * sessions_pw)
    return {
        "student_id": student_id,
        "subject_id": subject_id,
        "week": week,
        "attended_sessions": attended,
        "total_sessions": sessions_pw,
        "attendance_pct": att,
        "assignment_score": assign,
        "internal_score": internal,
    }


# ---------------------------------------------------------------------------
# STU-001 Aarav Kulkarni — SILENT_SLIPPER
# High baseline Weeks 1–5 (≈89%), subtle dip Week 6 (≈87%), sharp drop 7–9
# CUSUM with h_factor=4.0 fires at Week 7.
# ---------------------------------------------------------------------------
_AARAV_WEEKLY = [
    # (att, assign, internal)  — composite ≈ mean of these 3
    (90.0, 89.0, 89.0),  # Week 1 — composite 89.33
    (91.0, 90.0, 90.0),  # Week 2 — composite 90.33
    (88.0, 88.0, 88.0),  # Week 3 — composite 88.00
    (90.0, 89.0, 89.0),  # Week 4 — composite 89.33 | baseline mean≈89.25 std≈0.96
    (89.0, 89.0, 89.0),  # Week 5 — S=0 (no shift)
    (87.0, 88.0, 86.0),  # Week 6 — composite≈87.0, shift=2.3; S<h=3.84 ✓
    (58.0, 62.0, 56.0),  # Week 7 — composite≈58.7; cumulative S>>h → trigger ✓
    (57.0, 61.0, 55.0),  # Week 8
    (56.0, 60.0, 54.0),  # Week 9
]


@pytest.fixture(scope="session")
def aarav_weekly_composites() -> list[float]:
    """Per-week composite (mean of att, assign, internal) for Aarav — 9 weeks."""
    return [round((a + b + c) / 3.0, 4) for a, b, c in _AARAV_WEEKLY]


@pytest.fixture(scope="session")
def aarav_df() -> pd.DataFrame:
    """Single-student DataFrame for Aarav across 5 theory subjects."""
    rows = []
    for week_idx, (att, assign, internal) in enumerate(_AARAV_WEEKLY, start=1):
        for subj_id in [SUBJ_MA, SUBJ_DS, SUBJ_CN, SUBJ_DB, SUBJ_OS]:
            rows.append(_make_cohort_row(1, subj_id, week_idx, att, assign, internal))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# STU-002 Meera Nair — PASSIVE_COPIER_CONCEPT_GAP
# 94% assignments, 86% attendance, 39% closed-book internals
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def meera_df() -> pd.DataFrame:
    """
    Cohort DataFrame including Meera (stu_id=2) and 19 average students (stu_id=10–28)
    so Z-scores are computed against a realistic cohort of 20 students.
    """
    rows = []
    for week in WEEKS:
        # Cohort of 19 average students
        for sid in range(10, 29):
            for subj_id in [SUBJ_MA, SUBJ_DS, SUBJ_CN, SUBJ_DB, SUBJ_OS]:
                rows.append(_make_cohort_row(sid, subj_id, week, 82.0, 80.0, 78.0))
        # Meera: high assign, decent att, very low internals
        for subj_id in [SUBJ_MA, SUBJ_DS, SUBJ_CN, SUBJ_DB, SUBJ_OS]:
            rows.append(_make_cohort_row(2, subj_id, week, 86.0, 94.0, 39.0))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# STU-003 Rohan Deshmukh — DETENTION_CLIFF (CN Lab)
# CN Lab: Weeks 1–3 → 2/2 attended; Weeks 4–9 → 1/2 attended ⇒ 12/18 = 66.7%
# Total after 9 weeks: attended=12, total_so_far=18, bunk_budget=1 → WINDOW_CLOSING
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def rohan_cn_lab_ponr_input() -> dict:
    """PONR inputs for Rohan's Computer Networks Lab after Week 9."""
    attended_so_far = 3 * 2 + 6 * 1  # weeks 1-3: 2/session, weeks 4-9: 1/session = 12
    return {
        "attended_so_far": attended_so_far,  # 12
        "total_sessions_so_far": CURRENT_WEEK * 2,  # 18
        "sessions_per_week": 2,
        "current_week": CURRENT_WEEK,  # 9
        "total_weeks": TOTAL_WEEKS,  # 14
    }


# ---------------------------------------------------------------------------
# Tough-exam cohort wave fixture
# CS201 Week 5: entire cohort gets internal_score ≈ 42 (shock -20 from base 62)
# Z-scores should stay near 0 — no individual false flags.
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def tough_exam_cohort_df() -> pd.DataFrame:
    """
    30-student cohort with a tough-exam shock on DS (subject_id=2) in Week 5.
    Everyone drops equally → all z_internal ≈ 0 at Week 5.
    """
    rows = []
    rng = np.random.default_rng(99)
    for sid in range(1, 31):
        for week in WEEKS:
            att = float(rng.normal(82.0, 3.0))
            assign = float(rng.normal(80.0, 4.0))
            # Tough exam: everybody gets the EXACT same internal score so the
            # cohort std → 0 and all z_internal → 0 (perfect normalization).
            # This is the purest test that cohort-normalization suppresses
            # uniform drops regardless of their magnitude.
            internal = 42.0 if week == 5 else 78.0
            rows.append(_make_cohort_row(sid, SUBJ_DS, week, att, assign, internal))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# PONR — safe student (always attending)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def safe_student_ponr_input() -> dict:
    return {
        "attended_so_far": 27,         # 9 weeks × 3 sessions = 27 possible; attended all
        "total_sessions_so_far": 27,
        "sessions_per_week": 3,
        "current_week": CURRENT_WEEK,
        "total_weeks": TOTAL_WEEKS,
    }
