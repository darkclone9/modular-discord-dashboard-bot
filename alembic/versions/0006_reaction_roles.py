"""reaction roles module

Revision ID: 0006_reaction_roles
Revises: 0005_trackers
Create Date: 2026-05-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_reaction_roles"
down_revision: str | None = "0005_trackers"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "reaction_role_menus",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("guild_id", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("channel_id", sa.String(length=32), nullable=False),
        sa.Column("message_id", sa.String(length=32), nullable=True),
        sa.Column("message_mode", sa.String(length=32), nullable=False),
        sa.Column("picker_style", sa.String(length=32), nullable=False),
        sa.Column("behavior", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reaction_role_menus")),
    )
    op.create_index(op.f("ix_reaction_role_menus_guild_id"), "reaction_role_menus", ["guild_id"])
    op.create_index(
        op.f("ix_reaction_role_menus_is_enabled"),
        "reaction_role_menus",
        ["is_enabled"],
    )
    op.create_index(
        op.f("ix_reaction_role_menus_message_id"),
        "reaction_role_menus",
        ["message_id"],
    )

    op.create_table(
        "reaction_role_options",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("menu_id", sa.String(length=32), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(length=100), nullable=False),
        sa.Column("role_id", sa.String(length=32), nullable=False),
        sa.Column("emoji", sa.String(length=128), nullable=True),
        sa.Column("description", sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(
            ["menu_id"],
            ["reaction_role_menus.id"],
            name=op.f("fk_reaction_role_options_menu_id_reaction_role_menus"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reaction_role_options")),
        sa.UniqueConstraint(
            "menu_id",
            "position",
            name="uq_reaction_role_options_menu_position",
        ),
    )
    op.create_index(
        op.f("ix_reaction_role_options_menu_id"),
        "reaction_role_options",
        ["menu_id"],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_reaction_role_options_menu_id"), table_name="reaction_role_options")
    op.drop_table("reaction_role_options")
    op.drop_index(op.f("ix_reaction_role_menus_message_id"), table_name="reaction_role_menus")
    op.drop_index(op.f("ix_reaction_role_menus_is_enabled"), table_name="reaction_role_menus")
    op.drop_index(op.f("ix_reaction_role_menus_guild_id"), table_name="reaction_role_menus")
    op.drop_table("reaction_role_menus")
