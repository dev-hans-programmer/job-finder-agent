# ruff: noqa: E501, E701
"""add notification deliveries

Revision ID: 20260913_006
Revises: 20260911_005
"""

import sqlalchemy as sa

from alembic import op

revision = "20260913_006"
down_revision = "20260911_005"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "notification_deliveries",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("job_id", sa.UUID(), nullable=False),
        sa.Column("profile_id", sa.UUID(), nullable=False),
        sa.Column("channel", sa.String(16), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("provider_message_id", sa.String(255)),
        sa.Column("error", sa.Text()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["profile_id"], ["preference_profiles.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "user_id", "job_id", "profile_id", "channel", name="uq_notification_delivery"
        ),
    )
    for name, column in [
        ("user_id", "user_id"),
        ("job_id", "job_id"),
        ("profile_id", "profile_id"),
    ]:
        op.create_index(f"ix_notification_deliveries_{name}", "notification_deliveries", [column])


def downgrade():
    for name in ("user_id", "job_id", "profile_id"):
        op.drop_index(f"ix_notification_deliveries_{name}", table_name="notification_deliveries")
    op.drop_table("notification_deliveries")
