"""create canonical jobs and source records

Revision ID: 20260910_003
Revises: 20260910_002
"""

import sqlalchemy as sa

from alembic import op

revision = "20260910_003"
down_revision = "20260910_002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("company_normalized", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("description_hash", sa.String(length=64), nullable=False),
        sa.Column("locations", sa.JSON(), nullable=False),
        sa.Column("work_mode", sa.String(length=16), nullable=False),
        sa.Column("experience_min", sa.Integer(), nullable=True),
        sa.Column("experience_max", sa.Integer(), nullable=True),
        sa.Column("salary_min", sa.Float(), nullable=True),
        sa.Column("salary_max", sa.Float(), nullable=True),
        sa.Column("salary_currency", sa.String(length=8), nullable=True),
        sa.Column("salary_unit", sa.String(length=32), nullable=True),
        sa.Column("extracted_skills", sa.JSON(), nullable=False),
        sa.Column("application_url", sa.Text(), nullable=False),
        sa.Column(
            "last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_jobs_company_normalized", "jobs", ["company_normalized"])
    op.create_index("ix_jobs_description_hash", "jobs", ["description_hash"])
    op.create_index("ix_jobs_status", "jobs", ["status"])
    op.create_table(
        "job_source_records",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("job_id", sa.UUID(), nullable=False),
        sa.Column("source_id", sa.UUID(), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("raw_payload_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_job_source_records_job_id", "job_source_records", ["job_id"])
    op.create_index("ix_job_source_records_source_id", "job_source_records", ["source_id"])


def downgrade() -> None:
    op.drop_index("ix_job_source_records_source_id", table_name="job_source_records")
    op.drop_index("ix_job_source_records_job_id", table_name="job_source_records")
    op.drop_table("job_source_records")
    op.drop_index("ix_jobs_status", table_name="jobs")
    op.drop_index("ix_jobs_description_hash", table_name="jobs")
    op.drop_index("ix_jobs_company_normalized", table_name="jobs")
    op.drop_table("jobs")
