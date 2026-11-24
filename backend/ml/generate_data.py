"""Deterministic 240-student dataset generator with 4 pinned Hero Personas."""

from __future__ import annotations

import sys
from contextlib import nullcontext
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import delete
from sqlalchemy.orm import Session

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import get_settings  # noqa: E402
from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.models import Intervention, PredictionSnapshot, Student, Subject, WeeklyRecord  # noqa: E402

SEED = 42
TOTAL_STUDENTS = 240
TOTAL_WEEKS_GENERATED = 12
TRAINING_WEEKS_PATH = BACKEND_DIR / "ml" / "artifacts" / "cohort_training_weeks.csv"

SUBJECTS_SPEC = [
    ("MA101", "Mathematics", "THEORY", 3, 4),
    ("CS201", "Data Structures", "THEORY", 3, 4),
    ("CS301", "Computer Networks", "THEORY", 3, 3),
    ("CS301L", "Computer Networks Lab", "LAB", 2, 2),
    ("CS302", "DBMS", "THEORY", 3, 4),
    ("CS303", "Operating Systems", "THEORY", 3, 3),
]

FIRST_NAMES = [
    "Diya", "Kabir", "Ananya", "Vihaan", "Ishaan", "Sanya", "Reyansh", "Kavya",
    "Aditya", "Neha", "Siddharth", "Pooja", "Arjun", "Tanvi", "Nikhil", "Riya",
    "Pranav", "Shreya", "Varun", "Megha", "Karan", "Nandini", "Harsh", "Simran",
]
LAST_NAMES = [
    "Patel", "Verma", "Iyer", "Mehta", "Joshi", "Rao", "Gupta", "Singh",
    "Kapoor", "Bhat", "Menon", "Reddy", "Malhotra", "Choudhary", "Agarwal", "Pillai",
]


def _clamp(val: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return float(max(lo, min(hi, val)))


def _sessions_for_pct(pct: float, total_sessions: int) -> tuple[int, float]:
    attended = round(_clamp(pct, 0.0, 100.0) / 100.0 * total_sessions)
    attended = max(0, min(total_sessions, attended))
    return attended, round((attended / total_sessions) * 100.0, 2)


def _tough_exam_shock(subject_code: str, week: int) -> float:
    if subject_code == "CS201" and week == 5:
        return -20.0
    if subject_code == "MA101" and week == 8:
        return -18.0
    return 0.0


def _generate_hero_week(
    tag: str, subject_code: str, week: int, sessions_pw: int, rng: np.random.Generator
) -> tuple[int, int, float, float, float]:
    shock = _tough_exam_shock(subject_code, week)
    noise = float(rng.normal(0.0, 1.5))

    if tag == "SILENT_SLIPPER":  # STU-001 Aarav Kulkarni
        if week <= 5:
            att_target, assign, internal = 90.0, 89.0 + noise, 89.0 + noise
        elif week == 6:
            att_target, assign, internal = 82.0, 83.0 + noise, 80.0 + noise
        else:
            att_target, assign, internal = 58.0, 62.0 + noise, 56.0 + noise
    elif tag == "PASSIVE_COPIER_CONCEPT_GAP":  # STU-002 Meera Nair
        att_target = 86.0
        assign = 94.0 + rng.normal(0.0, 1.2)
        internal = 36.0 + rng.normal(0.0, 1.8)
    elif tag == "DETENTION_CLIFF":  # STU-003 Rohan Deshmukh
        if subject_code == "CS301L":
            # Weeks 1-3: 2/2 labs; Weeks 4-9: 1/2 labs => 12/18 = 66.67% (~67%)
            attended = 2 if week <= 3 else 1
            return attended, sessions_pw, round(attended / sessions_pw * 100.0, 2), 79.0, 77.0
        att_target, assign, internal = 85.0, 80.0 + noise, 78.0 + noise
    else:  # STU-004 Priya Sharma (RECOVERED_AFTER_INTERVENTION)
        if week <= 3:
            att_target, assign, internal = 75.0, 73.0 + noise, 71.0 + noise
        elif week <= 6:
            att_target, assign, internal = 58.0, 56.0 + noise, 54.0 + noise
        else:
            lift = (week - 6) * 8.5
            att_target = min(95.0, 66.0 + lift)
            assign = 66.0 + lift + noise
            internal = 64.0 + lift + noise

    attended, att_pct = _sessions_for_pct(att_target, sessions_pw)
    return (
        attended,
        sessions_pw,
        att_pct,
        round(_clamp(assign), 2),
        round(_clamp(internal + shock), 2),
    )


def _generate_cohort_week(
    archetype: str,
    subject_code: str,
    risk_subject_code: str,
    week: int,
    sessions_pw: int,
    rng: np.random.Generator,
    late_shift: float = 0.0,
) -> tuple[int, int, float, float, float]:
    shock = _tough_exam_shock(subject_code, week)
    sigma = 5.2 if week >= 9 else 3.8
    n1 = rng.normal(0, 4.2 if week >= 9 else 4.0)
    n2 = rng.normal(0, sigma)
    n3 = rng.normal(0, sigma)
    shift = late_shift if week >= 10 else 0.0

    if archetype == "ON_TRACK":
        att, assign, internal = 88.0 + n1 + 0.5 * shift, 82.0 + n2 + shift, 79.0 + n3 + shift
    elif archetype == "SILENT_SLIPPER":
        if week <= 5:
            att, assign, internal = 88.0 + n1, 87.0 + n2, 86.0 + n3
        else:
            att, assign, internal = 62.0 + n1 + 0.5 * shift, 64.0 + n2 + shift, 58.0 + n3 + shift
    elif archetype == "PASSIVE_COPIER_CONCEPT_GAP":
        att, assign, internal = 84.0 + n1, 91.0 + n2 + 0.4 * shift, 42.0 + n3 + shift
    elif archetype == "DETENTION_CLIFF":
        if subject_code == risk_subject_code:
            att, assign, internal = 55.0 + n1, 76.0 + n2 + shift, 74.0 + n3 + shift
        else:
            att, assign, internal = 85.0 + n1, 79.0 + n2 + shift, 77.0 + n3 + shift
    elif archetype == "CONCEPTUAL_STRUGGLER":
        att, assign, internal = 83.0 + n1, 52.0 + n2 + shift, 46.0 + n3 + shift
    else:  # BROAD_DISENGAGEMENT
        att, assign, internal = 52.0 + n1 + 0.5 * shift, 48.0 + n2 + shift, 42.0 + n3 + shift

    attended, att_pct = _sessions_for_pct(att, sessions_pw)
    return (
        attended,
        sessions_pw,
        att_pct,
        round(_clamp(assign), 2),
        round(_clamp(internal + shock), 2),
    )


def seed_database(db_session: Session | None = None) -> int:
    """Create schema if needed and deterministically seed 240 students in one transaction."""
    if db_session is None:
        Base.metadata.create_all(bind=engine)
    rng = np.random.default_rng(SEED)

    ctx = nullcontext(db_session) if db_session is not None else SessionLocal()
    with ctx as db:
        db.execute(delete(PredictionSnapshot))
        db.execute(delete(Intervention))
        db.execute(delete(WeeklyRecord))
        db.execute(delete(Student))
        db.execute(delete(Subject))
        db.flush()

        subjects: list[Subject] = []
        for code, name, stype, spw, credits in SUBJECTS_SPEC:
            subj = Subject(
                code=code, name=name, subject_type=stype, sessions_per_week=spw, credits=credits
            )
            db.add(subj)
            subjects.append(subj)
        db.flush()

        hero_specs = [
            ("STU-001", "Aarav Kulkarni", True, "SILENT_SLIPPER"),
            ("STU-002", "Meera Nair", True, "PASSIVE_COPIER_CONCEPT_GAP"),
            ("STU-003", "Rohan Deshmukh", True, "DETENTION_CLIFF"),
            ("STU-004", "Priya Sharma", True, "RECOVERED_AFTER_INTERVENTION"),
        ]

        archetype_pool = (
            ["ON_TRACK"] * 130
            + ["SILENT_SLIPPER"] * 28
            + ["PASSIVE_COPIER_CONCEPT_GAP"] * 24
            + ["DETENTION_CLIFF"] * 24
            + ["CONCEPTUAL_STRUGGLER"] * 18
            + ["BROAD_DISENGAGEMENT"] * 12
        )
        rng.shuffle(archetype_pool)

        students: list[Student] = []
        for idx in range(TOTAL_STUDENTS):
            if idx < len(hero_specs):
                roll_no, name, is_hero, tag = hero_specs[idx]
            else:
                roll_no = f"STU-{idx + 1:03d}"
                fn = FIRST_NAMES[idx % len(FIRST_NAMES)]
                ln = LAST_NAMES[(idx // len(FIRST_NAMES)) % len(LAST_NAMES)]
                name = f"{fn} {ln}"
                is_hero = False
                tag = archetype_pool[idx - len(hero_specs)]

            stu = Student(
                roll_no=roll_no,
                name=name,
                program="B.Tech CSE",
                year=3,
                is_hero_persona=is_hero,
                persona_tag=tag,
            )
            db.add(stu)
            students.append(stu)
        db.flush()

        settings = get_settings()
        live_cutoff = int(settings.CURRENT_WEEK)
        records: list[WeeklyRecord] = []
        training_rows: list[dict[str, object]] = []
        for idx, stu in enumerate(students):
            risk_subj = subjects[idx % len(subjects)].code
            # Student-level stochastic outcome drift + ~8% realistic late-semester regime shifts
            base_w10_drift = float(rng.normal(0.0, 3.6))
            if not stu.is_hero_persona and rng.random() < 0.08:
                regime_jump = 9.0 if (stu.persona_tag or "ON_TRACK") != "ON_TRACK" else -9.0
                late_shift = base_w10_drift + regime_jump
            else:
                late_shift = base_w10_drift

            for subj in subjects:
                for week in range(1, TOTAL_WEEKS_GENERATED + 1):
                    if stu.is_hero_persona and stu.persona_tag:
                        att, tot, att_pct, assign, internal = _generate_hero_week(
                            stu.persona_tag, subj.code, week, subj.sessions_per_week, rng
                        )
                    else:
                        att, tot, att_pct, assign, internal = _generate_cohort_week(
                            stu.persona_tag or "ON_TRACK",
                            subj.code,
                            risk_subj,
                            week,
                            subj.sessions_per_week,
                            rng,
                            late_shift=late_shift,
                        )
                    training_rows.append(
                        {
                            "student_id": stu.id,
                            "subject_id": subj.id,
                            "week": week,
                            "attended_sessions": att,
                            "total_sessions": tot,
                            "attendance_pct": att_pct,
                            "assignment_score": assign,
                            "internal_score": internal,
                            "subject_code": subj.code,
                            "subject_name": subj.name,
                            "subject_type": subj.subject_type,
                            "sessions_per_week": subj.sessions_per_week,
                        }
                    )
                    if week <= live_cutoff:
                        records.append(
                            WeeklyRecord(
                                student_id=stu.id,
                                subject_id=subj.id,
                                week=week,
                                attended_sessions=att,
                                total_sessions=tot,
                                attendance_pct=att_pct,
                                assignment_score=assign,
                                internal_score=internal,
                            )
                        )

        db.bulk_save_objects(records)
        if db_session is None:
            TRAINING_WEEKS_PATH.parent.mkdir(parents=True, exist_ok=True)
            pd.DataFrame(training_rows).to_csv(TRAINING_WEEKS_PATH, index=False)

        # Pinned Week 7 intervention for Priya Sharma (STU-004)
        priya = students[3]
        db.add(
            Intervention(
                student_id=priya.id,
                faculty_id="FAC-001",
                week=7,
                intervention_type="Remedial Mentoring",
                notes="Weekly 1-on-1 problem solving & study plan after Week 6 drop.",
                outcome="Trajectory recovered (+22% average lift by Week 9)",
                pre_risk_tier="AT_RISK",
            )
        )
        db.commit()
    return len(students)


if __name__ == "__main__":
    count = seed_database()
    print(f"Seeded {count} students")
