"""trackers module

Revision ID: 0005_trackers
Revises: 0004_forms_long_field_labels
Create Date: 2026-05-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_trackers"
down_revision: str | None = "0004_forms_long_field_labels"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "social_trackers",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("guild_id", sa.String(length=32), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("label", sa.String(length=100), nullable=False),
        sa.Column("source_id", sa.String(length=256), nullable=False),
        sa.Column("source_url", sa.String(length=512), nullable=True),
        sa.Column("notification_channel_id", sa.String(length=32), nullable=False),
        sa.Column("custom_message", sa.Text(), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False),
        sa.Column("last_seen_external_id", sa.String(length=256), nullable=True),
        sa.Column("last_seen_url", sa.String(length=512), nullable=True),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_social_trackers")),
    )
    op.create_index(op.f("ix_social_trackers_guild_id"), "social_trackers", ["guild_id"])
    op.create_index(op.f("ix_social_trackers_is_enabled"), "social_trackers", ["is_enabled"])
    op.create_index(op.f("ix_social_trackers_provider"), "social_trackers", ["provider"])

    op.create_table(
        "game_suggestion_settings",
        sa.Column("guild_id", sa.String(length=32), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("announcement_channel_id", sa.String(length=32), nullable=True),
        sa.Column("reward_role_id", sa.String(length=32), nullable=True),
        sa.Column("mention_everyone", sa.Boolean(), nullable=False),
        sa.Column("announcement_weekday", sa.Integer(), nullable=False),
        sa.Column("announcement_hour_utc", sa.Integer(), nullable=False),
        sa.Column("custom_message", sa.Text(), nullable=False),
        sa.Column("last_announced_week", sa.String(length=16), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("guild_id", name=op.f("pk_game_suggestion_settings")),
    )

    op.create_table(
        "game_activity_snapshots",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("guild_id", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.String(length=32), nullable=False),
        sa.Column("username", sa.String(length=128), nullable=False),
        sa.Column("game_name", sa.String(length=128), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_game_activity_snapshots")),
        sa.UniqueConstraint("guild_id", "user_id", "game_name", name="uq_game_activity_seen"),
    )
    op.create_index(
        op.f("ix_game_activity_snapshots_game_name"),
        "game_activity_snapshots",
        ["game_name"],
    )
    op.create_index(
        op.f("ix_game_activity_snapshots_guild_id"),
        "game_activity_snapshots",
        ["guild_id"],
    )
    op.create_index(
        op.f("ix_game_activity_snapshots_user_id"),
        "game_activity_snapshots",
        ["user_id"],
    )

    op.create_table(
        "game_suggestion_picks",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("guild_id", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.String(length=32), nullable=False),
        sa.Column("username", sa.String(length=128), nullable=False),
        sa.Column("game_name", sa.String(length=128), nullable=False),
        sa.Column("channel_id", sa.String(length=32), nullable=True),
        sa.Column("message_id", sa.String(length=32), nullable=True),
        sa.Column("announced_week", sa.String(length=16), nullable=False),
        sa.Column("announced_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_game_suggestion_picks")),
    )
    op.create_index(
        op.f("ix_game_suggestion_picks_announced_week"),
        "game_suggestion_picks",
        ["announced_week"],
    )
    op.create_index(
        op.f("ix_game_suggestion_picks_guild_id"),
        "game_suggestion_picks",
        ["guild_id"],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_game_suggestion_picks_guild_id"), table_name="game_suggestion_picks")
    op.drop_index(
        op.f("ix_game_suggestion_picks_announced_week"), table_name="game_suggestion_picks"
    )
    op.drop_table("game_suggestion_picks")
    op.drop_index(op.f("ix_game_activity_snapshots_user_id"), table_name="game_activity_snapshots")
    op.drop_index(op.f("ix_game_activity_snapshots_guild_id"), table_name="game_activity_snapshots")
    op.drop_index(
        op.f("ix_game_activity_snapshots_game_name"),
        table_name="game_activity_snapshots",
    )
    op.drop_table("game_activity_snapshots")
    op.drop_table("game_suggestion_settings")
    op.drop_index(op.f("ix_social_trackers_provider"), table_name="social_trackers")
    op.drop_index(op.f("ix_social_trackers_is_enabled"), table_name="social_trackers")
    op.drop_index(op.f("ix_social_trackers_guild_id"), table_name="social_trackers")
    op.drop_table("social_trackers")
