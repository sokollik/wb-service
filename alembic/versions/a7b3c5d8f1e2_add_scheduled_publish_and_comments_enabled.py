"""add scheduled_publish_at and comments_enabled to news

Revision ID: a7b3c5d8f1e2
Revises: fc19d934383f
Create Date: 2026-02-23 12:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "a7b3c5d8f1e2"
down_revision = "fc19d934383f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "news",
        sa.Column(
            "comments_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )
    op.add_column(
        "news", sa.Column("scheduled_publish_at", sa.DateTime(), nullable=True)
    )
    op.create_index(
        op.f("ix_news_scheduled_publish_at"),
        "news",
        ["scheduled_publish_at"],
        unique=False,
    )

    op.execute("ALTER TYPE newsstatus ADD VALUE IF NOT EXISTS 'SCHEDULED'")


def downgrade() -> None:
    op.drop_index(op.f("ix_news_scheduled_publish_at"), table_name="news")
    op.drop_column("news", "scheduled_publish_at")
    op.drop_column("news", "comments_enabled")
