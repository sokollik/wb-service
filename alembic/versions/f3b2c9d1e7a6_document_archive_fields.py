"""document_archive_fields

Revision ID: f3b2c9d1e7a6
Revises: e2f1a8b3c7d4
Create Date: 2026-03-29 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f3b2c9d1e7a6'
down_revision = 'e2f1a8b3c7d4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Добавляем значение ACTIVE в enum (PUBLISHED переименовываем)
    op.execute(sa.text("ALTER TYPE documentstatus ADD VALUE IF NOT EXISTS 'ACTIVE'"))

    # PostgreSQL не позволяет использовать новое значение enum в той же транзакции —
    # делаем COMMIT чтобы зафиксировать ADD VALUE, затем открываем новую транзакцию
    op.get_bind().execute(sa.text("COMMIT"))
    op.get_bind().execute(sa.text("BEGIN"))

    # Переводим существующие PUBLISHED → ACTIVE
    op.get_bind().execute(sa.text("UPDATE documents SET status = 'ACTIVE' WHERE status = 'PUBLISHED'"))

    # Добавляем поля архивирования
    op.add_column('documents', sa.Column(
        'archived_at', sa.DateTime(), nullable=True,
        comment='Дата архивирования',
    ))
    op.add_column('documents', sa.Column(
        'archived_by', sa.String(), nullable=True,
        comment='Кто архивировал',
    ))
    op.add_column('documents', sa.Column(
        'archive_comment', sa.String(), nullable=True,
        comment='Основание архивирования',
    ))
    op.create_foreign_key(
        op.f('fk_documents_archived_by_employee'),
        'documents', 'employee',
        ['archived_by'], ['eid'],
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f('fk_documents_archived_by_employee'),
        'documents', type_='foreignkey',
    )
    op.drop_column('documents', 'archive_comment')
    op.drop_column('documents', 'archived_by')
    op.drop_column('documents', 'archived_at')
    # Возвращаем ACTIVE → PUBLISHED (enum значение ACTIVE остаётся, но не используется)
    op.execute(sa.text("UPDATE documents SET status = 'PUBLISHED' WHERE status = 'ACTIVE'"))
