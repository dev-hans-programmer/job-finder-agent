"""add password recovery verification and lockout state

Revision ID: 20260913_009
Revises: 20260913_008
"""

import sqlalchemy as sa

from alembic import op

revision = "20260913_009"
down_revision = "20260913_008"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("email_verified_at", sa.DateTime(timezone=True)))
    op.add_column(
        "users",
        sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("users", sa.Column("locked_until", sa.DateTime(timezone=True)))
    op.create_table(
        "verification_codes",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("purpose", sa.String(32), nullable=False),
        sa.Column("code_hash", sa.String(128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_verification_codes_user_id", "verification_codes", ["user_id"])
    op.create_index("ix_verification_codes_purpose", "verification_codes", ["purpose"])


def downgrade():
    op.drop_index("ix_verification_codes_purpose", table_name="verification_codes")
    op.drop_index("ix_verification_codes_user_id", table_name="verification_codes")
    op.drop_table("verification_codes")
    op.drop_column("users", "locked_until")
    op.drop_column("users", "failed_login_attempts")
    op.drop_column("users", "email_verified_at")
