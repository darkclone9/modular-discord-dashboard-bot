"""forms viewer roles

Revision ID: 0003_forms_viewer_roles
Revises: 0002_forms
Create Date: 2026-05-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_forms_viewer_roles"
down_revision: str | None = "0002_forms"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "forms",
        sa.Column(
            "viewer_role_ids",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'"),
        ),
    )


def downgrade() -> None:
    op.drop_column("forms", "viewer_role_ids")
