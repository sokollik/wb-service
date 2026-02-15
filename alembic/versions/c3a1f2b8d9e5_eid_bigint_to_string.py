"""eid BigInteger to String + drop auth_token

Revision ID: c3a1f2b8d9e5
Revises: 208df640331b
Create Date: 2026-02-14

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = 'c3a1f2b8d9e5'
down_revision = '208df640331b'
branch_labels = None
depends_on = None

FK_CONSTRAINTS = [
    ('fk_employee_hrbp_eid_employee', 'employee'),
    ('fk_organization_unit_manager_eid_employee', 'organization_unit'),
    ('fk_organization_change_log_changed_by_eid_employee', 'organization_change_log'),
    ('fk_profile_employee_id_employee', 'profile'),
    ('fk_profile_change_log_changed_by_eid_employee', 'profile_change_log'),
    ('fk_profile_vacation_substitute_eid_employee', 'profile_vacation'),
    ('fk_notifications_user_eid_employee', 'notifications'),
    ('fk_notification_preferences_user_eid_employee', 'notification_preferences'),
    ('fk_news_author_id_employee', 'news'),
    ('fk_comments_author_id_employee', 'comments'),
    ('fk_news_likes_user_id_employee', 'news_likes'),
    ('fk_comments_likes_user_id_employee', 'comments_likes'),
    ('fk_user_followed_categories_user_eid_employee', 'user_followed_categories'),
    ('fk_mentions_mentioned_user_id_employee', 'mentions'),
]


COLUMNS_TO_ALTER = [
    ('employee', 'eid'),
    ('employee', 'hrbp_eid'),
    ('organization_unit', 'manager_eid'),
    ('organization_change_log', 'changed_by_eid'),
    ('profile', 'employee_id'),
    ('profile_change_log', 'changed_by_eid'),
    ('profile_vacation', 'substitute_eid'),
    ('notifications', 'user_eid'),
    ('notification_preferences', 'user_eid'),
    ('news', 'author_id'),
    ('comments', 'author_id'),
    ('news_likes', 'user_id'),
    ('comments_likes', 'user_id'),
    ('user_followed_categories', 'user_eid'),
    ('mentions', 'mentioned_user_id'),
    ('file', 'created_by'),
]

FK_RECREATE = [
    ('fk_employee_hrbp_eid_employee', 'employee', ['hrbp_eid'], 'employee', ['eid'], None),
    ('fk_organization_unit_manager_eid_employee', 'organization_unit', ['manager_eid'], 'employee', ['eid'], None),
    ('fk_organization_change_log_changed_by_eid_employee', 'organization_change_log', ['changed_by_eid'], 'employee', ['eid'], None),
    ('fk_profile_employee_id_employee', 'profile', ['employee_id'], 'employee', ['eid'], 'CASCADE'),
    ('fk_profile_change_log_changed_by_eid_employee', 'profile_change_log', ['changed_by_eid'], 'employee', ['eid'], None),
    ('fk_profile_vacation_substitute_eid_employee', 'profile_vacation', ['substitute_eid'], 'employee', ['eid'], None),
    ('fk_notifications_user_eid_employee', 'notifications', ['user_eid'], 'employee', ['eid'], 'CASCADE'),
    ('fk_notification_preferences_user_eid_employee', 'notification_preferences', ['user_eid'], 'employee', ['eid'], 'CASCADE'),
    ('fk_news_author_id_employee', 'news', ['author_id'], 'employee', ['eid'], None),
    ('fk_comments_author_id_employee', 'comments', ['author_id'], 'employee', ['eid'], None),
    ('fk_news_likes_user_id_employee', 'news_likes', ['user_id'], 'employee', ['eid'], None),
    ('fk_comments_likes_user_id_employee', 'comments_likes', ['user_id'], 'employee', ['eid'], None),
    ('fk_user_followed_categories_user_eid_employee', 'user_followed_categories', ['user_eid'], 'employee', ['eid'], None),
    ('fk_mentions_mentioned_user_id_employee', 'mentions', ['mentioned_user_id'], 'employee', ['eid'], None),
]


def upgrade() -> None:
    op.drop_table('auth_token')

    for fk_name, table_name in FK_CONSTRAINTS:
        op.execute(f'ALTER TABLE {table_name} DROP CONSTRAINT IF EXISTS {fk_name}')

    for table_name, column_name in COLUMNS_TO_ALTER:
        op.alter_column(
            table_name,
            column_name,
            type_=sa.String(),
            existing_type=sa.BigInteger(),
            postgresql_using=f'{column_name}::varchar',
        )

    for fk_name, source_table, source_cols, ref_table, ref_cols, ondelete in FK_RECREATE:
        op.create_foreign_key(
            fk_name,
            source_table,
            ref_table,
            source_cols,
            ref_cols,
            ondelete=ondelete,
        )


def downgrade() -> None:
    for fk_name, source_table, source_cols, ref_table, ref_cols, ondelete in FK_RECREATE:
        op.drop_constraint(fk_name, source_table, type_='foreignkey')

    for table_name, column_name in COLUMNS_TO_ALTER:
        op.alter_column(
            table_name,
            column_name,
            type_=sa.BigInteger(),
            existing_type=sa.String(),
            postgresql_using=f'{column_name}::bigint',
        )

    for fk_name, table_name in FK_CONSTRAINTS:
        if table_name == 'auth_token':
            continue
    for fk_name, source_table, source_cols, ref_table, ref_cols, ondelete in FK_RECREATE:
        op.create_foreign_key(
            fk_name,
            source_table,
            ref_table,
            source_cols,
            ref_cols,
            ondelete=ondelete,
        )

    op.create_table('auth_token',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('employee_eid', sa.BigInteger(), nullable=False,
                   comment='Связь с таблицей Employee (EID) - владелец токена'),
        sa.Column('token', sa.String(length=512), nullable=False,
                   comment='Token или Session ID'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True,
                   comment='Дата и время истечения срока действия токена'),
        sa.Column('created_at', sa.DateTime(timezone=True),
                   server_default=sa.text('now()'), nullable=True,
                   comment='Время создания записи'),
        sa.ForeignKeyConstraint(['employee_eid'], ['employee.eid'],
                                 name='fk_auth_token_employee_eid_employee',
                                 ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name='pk_auth_token'),
        sa.UniqueConstraint('employee_eid', name='uq_auth_token_employee_eid'),
        sa.UniqueConstraint('token', name='uq_auth_token_token'),
    )
