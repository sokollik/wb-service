"""fix notifications user_eid type

Revision ID: a1b2c3d4e5f7
Revises: 54d9e998ba5c
Create Date: 2026-04-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'a1b2c3d4e5f7'
down_revision = '54d9e998ba5c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Исправляем тип user_eid с BigInteger на String
    op.alter_column(
        'notifications',
        'user_eid',
        existing_type=sa.BigInteger(),
        type_=sa.String(),
        existing_nullable=False,
    )
    
    # Удаляем неправильный unique constraint
    op.drop_constraint('uq_notifications_user_eid', 'notifications', type_='unique')
    
    # Добавляем autoincrement к id
    # PostgreSQL не позволяет изменить existing primary key на autoincrement напрямую,
    # поэтому создаём sequence и привязываем её
    op.execute("""
        CREATE SEQUENCE IF NOT EXISTS notifications_id_seq;
        SELECT setval('notifications_id_seq', COALESCE((SELECT MAX(id) FROM notifications), 1));
        ALTER TABLE notifications ALTER COLUMN id SET DEFAULT nextval('notifications_id_seq');
        ALTER SEQUENCE notifications_id_seq OWNED BY notifications.id;
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE notifications ALTER COLUMN id DROP DEFAULT;
        DROP SEQUENCE IF EXISTS notifications_id_seq;
    """)
    
    op.create_unique_constraint(
        'uq_notifications_user_eid',
        'notifications',
        ['user_eid'],
    )
    
    op.alter_column(
        'notifications',
        'user_eid',
        existing_type=sa.String(),
        type_=sa.BigInteger(),
        existing_nullable=False,
    )
