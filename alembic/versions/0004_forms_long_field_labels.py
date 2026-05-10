"""forms long field labels

Revision ID: 0004_forms_long_field_labels
Revises: 0003_forms_viewer_roles
Create Date: 2026-05-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_forms_long_field_labels"
down_revision: str | None = "0003_forms_viewer_roles"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("form_fields") as batch_op:
        batch_op.alter_column(
            "label",
            existing_type=sa.String(length=100),
            type_=sa.String(length=300),
            existing_nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("form_fields") as batch_op:
        batch_op.alter_column(
            "label",
            existing_type=sa.String(length=300),
            type_=sa.String(length=100),
            existing_nullable=False,
        )
