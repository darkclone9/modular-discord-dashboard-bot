"""forms module

Revision ID: 0002_forms
Revises: 0001_initial
Create Date: 2026-05-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_forms"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "forms",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("guild_id", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("post_channel_id", sa.String(length=32), nullable=False),
        sa.Column("review_channel_id", sa.String(length=32), nullable=False),
        sa.Column("reviewer_role_ids", sa.JSON(), nullable=False),
        sa.Column("auto_role_id", sa.String(length=32), nullable=True),
        sa.Column("approval_message", sa.Text(), nullable=False),
        sa.Column("denial_message", sa.Text(), nullable=False),
        sa.Column("is_archived", sa.Boolean(), nullable=False),
        sa.Column("is_published", sa.Boolean(), nullable=False),
        sa.Column("published_message_id", sa.String(length=32), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_forms")),
    )
    op.create_index(op.f("ix_forms_guild_id"), "forms", ["guild_id"], unique=False)
    op.create_index(op.f("ix_forms_is_archived"), "forms", ["is_archived"], unique=False)
    op.create_index(op.f("ix_forms_is_published"), "forms", ["is_published"], unique=False)

    op.create_table(
        "form_fields",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("form_id", sa.String(length=32), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(length=100), nullable=False),
        sa.Column("field_type", sa.String(length=32), nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False),
        sa.Column("options", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["form_id"],
            ["forms.id"],
            name=op.f("fk_form_fields_form_id_forms"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_form_fields")),
        sa.UniqueConstraint("form_id", "position", name="uq_form_fields_form_position"),
    )
    op.create_index(op.f("ix_form_fields_form_id"), "form_fields", ["form_id"], unique=False)

    op.create_table(
        "form_submissions",
        sa.Column("id", sa.String(length=12), nullable=False),
        sa.Column("form_id", sa.String(length=32), nullable=False),
        sa.Column("guild_id", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.String(length=32), nullable=False),
        sa.Column("username", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("answers", sa.JSON(), nullable=False),
        sa.Column("thread_id", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["form_id"],
            ["forms.id"],
            name=op.f("fk_form_submissions_form_id_forms"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_form_submissions")),
    )
    op.create_index(
        "ix_form_submissions_form_user_status",
        "form_submissions",
        ["form_id", "user_id", "status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_form_submissions_form_id"), "form_submissions", ["form_id"], unique=False
    )
    op.create_index(
        op.f("ix_form_submissions_guild_id"), "form_submissions", ["guild_id"], unique=False
    )
    op.create_index(
        op.f("ix_form_submissions_status"), "form_submissions", ["status"], unique=False
    )
    op.create_index(
        op.f("ix_form_submissions_user_id"), "form_submissions", ["user_id"], unique=False
    )

    op.create_table(
        "form_submission_actions",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("submission_id", sa.String(length=12), nullable=False),
        sa.Column("actor_id", sa.String(length=32), nullable=False),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["submission_id"],
            ["form_submissions.id"],
            name=op.f("fk_form_submission_actions_submission_id_form_submissions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_form_submission_actions")),
    )
    op.create_index(
        op.f("ix_form_submission_actions_submission_id"),
        "form_submission_actions",
        ["submission_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_form_submission_actions_submission_id"), table_name="form_submission_actions"
    )
    op.drop_table("form_submission_actions")
    op.drop_index(op.f("ix_form_submissions_user_id"), table_name="form_submissions")
    op.drop_index(op.f("ix_form_submissions_status"), table_name="form_submissions")
    op.drop_index(op.f("ix_form_submissions_guild_id"), table_name="form_submissions")
    op.drop_index(op.f("ix_form_submissions_form_id"), table_name="form_submissions")
    op.drop_index("ix_form_submissions_form_user_status", table_name="form_submissions")
    op.drop_table("form_submissions")
    op.drop_index(op.f("ix_form_fields_form_id"), table_name="form_fields")
    op.drop_table("form_fields")
    op.drop_index(op.f("ix_forms_is_published"), table_name="forms")
    op.drop_index(op.f("ix_forms_is_archived"), table_name="forms")
    op.drop_index(op.f("ix_forms_guild_id"), table_name="forms")
    op.drop_table("forms")
