"""add secondary_flags_json to prediction_snapshots

Revision ID: 002_add_secondary_flags
Revises: 001_initial_schema
Create Date: 2026-11-25 00:40:00
"""

import sqlalchemy as sa

from alembic import op

revision = "002_add_secondary_flags"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "prediction_snapshots",
        sa.Column("secondary_flags_json", sa.Text(), nullable=False, server_default="[]"),
    )


def downgrade() -> None:
    op.drop_column("prediction_snapshots", "secondary_flags_json")
