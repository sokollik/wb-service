"""add targeted acknowledgement

Revision ID: b5c2d7e9f3a1
Revises: a7b3c5d8f1e2
Create Date: 2026-02-24 12:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "b5c2d7e9f3a1"
down_revision = "a7b3c5d8f1e2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "news",
        sa.Column(
            "ack_target_all",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )

    op.create_table(
        "news_acknowledgement_targets",
        sa.Column("news_id", sa.BigInteger(), nullable=False),
        sa.Column("user_eid", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["news_id"], ["news.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_eid"], ["employee.eid"]),
        sa.PrimaryKeyConstraint("news_id", "user_eid"),
    )
    op.create_index(
        "ix_news_ack_targets_news_id",
        "news_acknowledgement_targets",
        ["news_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_news_ack_targets_news_id",
        table_name="news_acknowledgement_targets",
    )
    op.drop_table("news_acknowledgement_targets")
    op.drop_column("news", "ack_target_all")
