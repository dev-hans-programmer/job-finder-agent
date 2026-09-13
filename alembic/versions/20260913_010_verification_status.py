"""support pending verification user status

Revision ID: 20260913_010
Revises: 20260913_009
"""

import sqlalchemy as sa

from alembic import op

revision = "20260913_010"
down_revision = "20260913_009"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("users", "status", type_=sa.String(32), existing_type=sa.String(16))


def downgrade():
    op.alter_column("users", "status", type_=sa.String(16), existing_type=sa.String(32))
