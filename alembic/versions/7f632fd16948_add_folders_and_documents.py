"""add_folders_and_documents

Revision ID: 7f632fd16948
Revises: b5c2d7e9f3a1
Create Date: 2026-03-15 07:14:00.950229

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7f632fd16948'
down_revision = 'b5c2d7e9f3a1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('folders',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(), nullable=False, comment='Название папки'),
    sa.Column('parent_id', sa.BigInteger(), nullable=True, comment='Родительская папка'),
    sa.Column('path', sa.String(), nullable=False, comment='Материализованный путь, например /1/5/12/'),
    sa.Column('created_by', sa.String(), nullable=False, comment='Создатель папки'),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['employee.eid'], name=op.f('fk_folders_created_by_employee')),
    sa.ForeignKeyConstraint(['parent_id'], ['folders.id'], name=op.f('fk_folders_parent_id_folders'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_folders'))
    )
    op.create_index(op.f('ix_folders_path'), 'folders', ['path'], unique=False)

    op.create_table('documents',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('folder_id', sa.BigInteger(), nullable=True, comment='Папка, в которой лежит документ'),
    sa.Column('title', sa.String(), nullable=False, comment='Название документа'),
    sa.Column('type', sa.String(), nullable=False, comment='Тип файла (pdf, docx, xlsx, ...)'),
    sa.Column('status', sa.Enum('DRAFT', 'PUBLISHED', 'ARCHIVED', name='documentstatus'), nullable=False, comment='Статус документа'),
    sa.Column('description', sa.Text(), nullable=True, comment='Описание документа'),
    sa.Column('author_id', sa.String(), nullable=False, comment='Автор документа'),
    sa.Column('curator_id', sa.String(), nullable=True, comment='Куратор документа'),
    sa.Column('current_version', sa.Integer(), nullable=False),
    sa.Column('s3_key', sa.String(), nullable=False, comment='UUID-ключ объекта в MinIO'),
    sa.Column('original_filename', sa.String(), nullable=False, comment='Оригинальное имя файла'),
    sa.Column('file_size', sa.BigInteger(), nullable=False, comment='Размер файла в байтах'),
    sa.Column('mime_type', sa.String(), nullable=False, comment='MIME-тип файла'),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['author_id'], ['employee.eid'], name=op.f('fk_documents_author_id_employee')),
    sa.ForeignKeyConstraint(['curator_id'], ['employee.eid'], name=op.f('fk_documents_curator_id_employee')),
    sa.ForeignKeyConstraint(['folder_id'], ['folders.id'], name=op.f('fk_documents_folder_id_folders'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_documents'))
    )
    op.create_index(op.f('ix_documents_author_id'), 'documents', ['author_id'], unique=False)
    op.create_index(op.f('ix_documents_folder_id'), 'documents', ['folder_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_documents_folder_id'), table_name='documents')
    op.drop_index(op.f('ix_documents_author_id'), table_name='documents')
    op.drop_table('documents')
    op.drop_index(op.f('ix_folders_path'), table_name='folders')
    op.drop_table('folders')
