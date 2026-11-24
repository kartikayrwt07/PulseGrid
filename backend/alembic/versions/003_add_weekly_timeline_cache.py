"""add weekly_timeline_cache table

Revision ID: 003_add_weekly_timeline_cache
Revises: 002_add_secondary_flags
Create Date: 2026-11-25 01:20:00
"""

import sqlalchemy as sa

from alembic import op

revision = "003_add_weekly_timeline_cache"
down_revision = "002_add_secondary_flags"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "weekly_timeline_cache",
        sa.Column("week", sa.Integer(), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("week"),
    )


def downgrade() -> None:
    op.drop_table("weekly_timeline_cache")
