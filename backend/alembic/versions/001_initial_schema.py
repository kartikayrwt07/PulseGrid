"""initial schema

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-11-24 22:55:00
"""

from alembic import op
import sqlalchemy as sa

revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "students",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("roll_no", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("program", sa.String(length=60), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("is_hero_persona", sa.Boolean(), nullable=False),
        sa.Column("persona_tag", sa.String(length=60), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_students_roll_no", "students", ["roll_no"], unique=True)

    op.create_table(
        "subjects",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("subject_type", sa.String(length=16), nullable=False),
        sa.Column("sessions_per_week", sa.Integer(), nullable=False),
        sa.Column("credits", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_subjects_code", "subjects", ["code"], unique=True)

    op.create_table(
        "weekly_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.Column("week", sa.Integer(), nullable=False),
        sa.Column("attended_sessions", sa.Integer(), nullable=False),
        sa.Column("total_sessions", sa.Integer(), nullable=False),
        sa.Column("attendance_pct", sa.Float(), nullable=False),
        sa.Column("assignment_score", sa.Float(), nullable=False),
        sa.Column("internal_score", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", "subject_id", "week", name="uq_weekly_student_subject_week"),
    )
    op.create_index("ix_weekly_student_week", "weekly_records", ["student_id", "week"])
    op.create_index("ix_weekly_student_subject", "weekly_records", ["student_id", "subject_id"])

    op.create_table(
        "interventions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("faculty_id", sa.String(length=40), nullable=False),
        sa.Column("week", sa.Integer(), nullable=False),
        sa.Column("intervention_type", sa.String(length=80), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("outcome", sa.String(length=120), nullable=True),
        sa.Column("pre_risk_tier", sa.String(length=24), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_intervention_student_week", "interventions", ["student_id", "week"])

    op.create_table(
        "prediction_snapshots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("risk_tier", sa.String(length=24), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("projected_final_score", sa.Float(), nullable=False),
        sa.Column("ponr_days_left", sa.Integer(), nullable=False),
        sa.Column("archetype", sa.String(length=48), nullable=False),
        sa.Column("divergence_index", sa.Float(), nullable=False),
        sa.Column("cusum_triggered", sa.Boolean(), nullable=False),
        sa.Column("cusum_week", sa.Integer(), nullable=True),
        sa.Column("z_scores_json", sa.Text(), nullable=False),
        sa.Column("cusum_json", sa.Text(), nullable=False),
        sa.Column("ponr_json", sa.Text(), nullable=False),
        sa.Column("shap_json", sa.Text(), nullable=False),
        sa.Column("recovery_path_json", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_prediction_snapshots_student_id", "prediction_snapshots", ["student_id"], unique=True)
    op.create_index("ix_snapshot_tier_ponr", "prediction_snapshots", ["risk_tier", "ponr_days_left"])


def downgrade() -> None:
    op.drop_index("ix_snapshot_tier_ponr", table_name="prediction_snapshots")
    op.drop_index("ix_prediction_snapshots_student_id", table_name="prediction_snapshots")
    op.drop_table("prediction_snapshots")
    op.drop_index("ix_intervention_student_week", table_name="interventions")
    op.drop_table("interventions")
    op.drop_index("ix_weekly_student_subject", table_name="weekly_records")
    op.drop_index("ix_weekly_student_week", table_name="weekly_records")
    op.drop_table("weekly_records")
    op.drop_index("ix_subjects_code", table_name="subjects")
    op.drop_table("subjects")
    op.drop_index("ix_students_roll_no", table_name="students")
    op.drop_table("students")
