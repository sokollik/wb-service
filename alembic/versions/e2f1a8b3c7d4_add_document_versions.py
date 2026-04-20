"""add_document_versions

Revision ID: e2f1a8b3c7d4
Revises: 7f632fd16948
Create Date: 2026-03-23 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e2f1a8b3c7d4'
down_revision = '7f632fd16948'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'document_versions',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('document_id', sa.BigInteger(), nullable=False, comment='Документ, к которому относится версия'),
        sa.Column('version_major', sa.Integer(), nullable=False, comment='Мажорная версия'),
        sa.Column('version_minor', sa.Integer(), nullable=False, comment='Минорная версия'),
        sa.Column('s3_key', sa.String(), nullable=False, comment='UUID-ключ объекта версии в MinIO'),
        sa.Column('original_filename', sa.String(), nullable=False, comment='Оригинальное имя файла версии'),
        sa.Column('file_size', sa.BigInteger(), nullable=False, comment='Размер файла версии в байтах'),
        sa.Column('mime_type', sa.String(), nullable=False, comment='MIME-тип файла версии'),
        sa.Column('uploaded_by', sa.String(), nullable=False, comment='Кто загрузил эту версию'),
        sa.Column('upload_comment', sa.String(), nullable=True, comment='Комментарий к версии'),
        sa.Column('is_current', sa.Boolean(), nullable=False, comment='Является ли версия актуальной'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], name=op.f('fk_document_versions_document_id_documents'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by'], ['employee.eid'], name=op.f('fk_document_versions_uploaded_by_employee')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_document_versions')),
    )
    op.create_index(op.f('ix_document_versions_document_id'), 'document_versions', ['document_id'], unique=False)

    # Переносим данные существующих документов: создаём начальную версию 1.0 для каждого
    op.execute("""
        INSERT INTO document_versions
            (document_id, version_major, version_minor, s3_key, original_filename,
             file_size, mime_type, uploaded_by, is_current, created_at)
        SELECT
            id, 1, 0, s3_key, original_filename,
            file_size, mime_type, author_id, true, created_at
        FROM documents
    """)

    # Удаляем устаревшую колонку current_version из documents
    op.drop_column('documents', 'current_version')


def downgrade() -> None:
    op.add_column('documents', sa.Column('current_version', sa.Integer(), nullable=False, server_default='1'))
    op.drop_index(op.f('ix_document_versions_document_id'), table_name='document_versions')
    op.drop_table('document_versions')
