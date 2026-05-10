"""initial dashboard sessions

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "dashboard_sessions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("discord_user_id", sa.String(length=32), nullable=False),
        sa.Column("username", sa.String(length=128), nullable=False),
        sa.Column("avatar", sa.String(length=256), nullable=True),
        sa.Column("csrf_token", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_dashboard_sessions")),
    )
    op.create_index(
        op.f("ix_dashboard_sessions_discord_user_id"),
        "dashboard_sessions",
        ["discord_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_dashboard_sessions_expires_at"),
        "dashboard_sessions",
        ["expires_at"],
        unique=False,
    )
    op.create_table(
        "discord_oauth_tokens",
        sa.Column("session_id", sa.String(length=64), nullable=False),
        sa.Column("access_token", sa.Text(), nullable=False),
        sa.Column("refresh_token", sa.Text(), nullable=True),
        sa.Column("token_type", sa.String(length=32), nullable=False),
        sa.Column("scope", sa.String(length=256), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["dashboard_sessions.id"],
            name=op.f("fk_discord_oauth_tokens_session_id_dashboard_sessions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("session_id", name=op.f("pk_discord_oauth_tokens")),
    )


def downgrade() -> None:
    op.drop_table("discord_oauth_tokens")
    op.drop_index(op.f("ix_dashboard_sessions_expires_at"), table_name="dashboard_sessions")
    op.drop_index(op.f("ix_dashboard_sessions_discord_user_id"), table_name="dashboard_sessions")
    op.drop_table("dashboard_sessions")
