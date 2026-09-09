"""create match results

Revision ID: 20260910_004
Revises: 20260910_003
"""

import sqlalchemy as sa

from alembic import op

revision = "20260910_004"
down_revision = "20260910_003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "match_results",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("job_id", sa.UUID(), nullable=False),
        sa.Column("preference_profile_id", sa.UUID(), nullable=False),
        sa.Column("job_description_hash", sa.String(length=64), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("decision", sa.String(length=16), nullable=False),
        sa.Column("component_scores", sa.JSON(), nullable=False),
        sa.Column("matched_criteria", sa.JSON(), nullable=False),
        sa.Column("missing_criteria", sa.JSON(), nullable=False),
        sa.Column("concerns", sa.JSON(), nullable=False),
        sa.Column("reasoning", sa.Text(), nullable=False),
        sa.Column("matcher_version", sa.String(length=64), nullable=False),
        sa.Column("embedding_model", sa.String(length=128), nullable=True),
        sa.Column("llm_model", sa.String(length=128), nullable=True),
        sa.Column("prompt_version", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["preference_profile_id"], ["preference_profiles.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_match_results_job_id", "match_results", ["job_id"])
    op.create_index(
        "ix_match_results_preference_profile_id", "match_results", ["preference_profile_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_match_results_preference_profile_id", table_name="match_results")
    op.drop_index("ix_match_results_job_id", table_name="match_results")
    op.drop_table("match_results")
