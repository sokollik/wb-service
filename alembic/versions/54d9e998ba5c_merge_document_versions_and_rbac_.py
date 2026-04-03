"""merge document versions and rbac branches

Revision ID: 54d9e998ba5c
Revises: d4e5f6a7b8c9, f3b2c9d1e7a6
Create Date: 2026-04-03 23:42:20.711283

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '54d9e998ba5c'
down_revision = ('d4e5f6a7b8c9', 'f3b2c9d1e7a6')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
