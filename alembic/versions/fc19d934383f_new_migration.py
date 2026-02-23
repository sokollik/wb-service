"""news_acknowledgements

Revision ID: fc19d934383f
Revises: d4a1f3c2e5d8
Create Date: 2026-02-23 05:47:12.504873

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'fc19d934383f'
down_revision = 'd4a1f3c2e5d8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('news_acknowledgements',
        sa.Column('news_id', sa.BigInteger(), nullable=False),
        sa.Column('user_eid', sa.String(), nullable=False),
        sa.Column('acknowledged_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['news_id'], ['news.id'], name=op.f('fk_news_acknowledgements_news_id_news'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_eid'], ['employee.eid'], name=op.f('fk_news_acknowledgements_user_eid_employee')),
        sa.PrimaryKeyConstraint('news_id', 'user_eid', name=op.f('pk_news_acknowledgements'))
    )


def downgrade() -> None:
    op.drop_table('news_acknowledgements')
