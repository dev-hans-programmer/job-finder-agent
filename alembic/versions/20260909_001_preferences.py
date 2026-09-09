"""create users and preference profiles

Revision ID: 20260909_001
Revises:
"""

import sqlalchemy as sa

from alembic import op

revision = "20260909_001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "preference_profiles",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("matching_weights", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "version", name="uq_preference_user_version"),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_preference_profiles_user_id", "preference_profiles", ["user_id"])
    op.create_index("ix_preference_profiles_is_active", "preference_profiles", ["is_active"])
    op.create_index(
        "uq_preference_active_user",
        "preference_profiles",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("is_active = true"),
    )


def downgrade() -> None:
    op.drop_index("uq_preference_active_user", table_name="preference_profiles")
    op.drop_index("ix_preference_profiles_is_active", table_name="preference_profiles")
    op.drop_index("ix_preference_profiles_user_id", table_name="preference_profiles")
    op.drop_table("preference_profiles")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")
