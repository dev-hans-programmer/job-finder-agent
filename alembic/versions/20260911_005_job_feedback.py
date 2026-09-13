"""add job feedback

Revision ID: 20260911_005
Revises: 20260910_004
"""

import sqlalchemy as sa

from alembic import op

revision = "20260911_005"
down_revision = "20260910_004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "job_feedback",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("job_id", sa.UUID(), nullable=False),
        sa.Column("label", sa.String(32), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "job_id", name="uq_job_feedback_user_job"),
    )
    op.create_index("ix_job_feedback_user_id", "job_feedback", ["user_id"])
    op.create_index("ix_job_feedback_job_id", "job_feedback", ["job_id"])


def downgrade() -> None:
    op.drop_index("ix_job_feedback_job_id", table_name="job_feedback")
    op.drop_index("ix_job_feedback_user_id", table_name="job_feedback")
    op.drop_table("job_feedback")
