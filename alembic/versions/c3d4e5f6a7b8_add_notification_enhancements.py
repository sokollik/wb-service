import sqlalchemy as sa
from alembic import op

revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade() -> None:

    op.create_index(
        op.f("ix_notifications_user_eid"),
        "notifications",
        ["user_eid"],
        unique=False,
    )
    op.create_index(
        op.f("ix_notifications_event_type"),
        "notifications",
        ["event_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_notifications_is_read"),
        "notifications",
        ["is_read"],
        unique=False,
    )
    op.create_index(
        op.f("ix_notifications_created_at"),
        "notifications",
        ["created_at"],
        unique=False,
    )
    
    op.create_index(
        op.f("ix_notifications_user_type_read"),
        "notifications",
        ["user_eid", "event_type", "is_read"],
        unique=False,
    )
    op.create_index(
        op.f("ix_notifications_created_is_read"),
        "notifications",
        ["created_at", "is_read"],
        unique=False,
    )

    op.add_column(
        "notifications",
        sa.Column(
            "sent_at",
            sa.DateTime(),
            nullable=True,
            comment="Время отправки push-уведомления",
        ),
    )
    op.add_column(
        "notifications",
        sa.Column(
            "delivered_at",
            sa.DateTime(),
            nullable=True,
            comment="Время доставки push-уведомления",
        ),
    )
    
    op.alter_column(
        "notifications",
        "event_type",
        existing_type=sa.String(),
        existing_nullable=False,
        comment="Тип события (NEWS_PUBLISHED, DOCUMENT_ACKNOWLEDGMENT_ASSIGNED, etc.)",
    )
    
    op.alter_column(
        "notifications",
        "payload",
        existing_type=sa.JSON(),
        existing_nullable=True,
        comment="Дополнительные данные (document_id, news_id, acknowledgment_id, etc.)",
    )

    op.alter_column(
        "notifications",
        "is_read",
        existing_type=sa.Boolean(),
        existing_nullable=True,
        server_default=None,
        comment="Флаг прочтения",
    )
    
    op.create_table(
        "user_bot_mappings",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "user_eid",
            sa.String(),
            nullable=False,
            comment="EID пользователя",
        ),
        sa.Column(
            "band_chat_id",
            sa.String(),
            nullable=False,
            comment="Chat ID в Band Bot для отправки уведомлений",
        ),
        sa.Column(
            "band_user_id",
            sa.String(),
            nullable=True,
            comment="User ID в Band",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            default=True,
            comment="Активен ли маппинг",
        ),
        sa.Column(
            "last_delivery_at",
            sa.DateTime(),
            nullable=True,
            comment="Время последней успешной доставки",
        ),
        sa.Column(
            "delivery_error_count",
            sa.Integer(),
            nullable=False,
            default=0,
            comment="Количество последовательных ошибок доставки",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["user_eid"],
            ["employee.eid"],
            name=op.f("fk_user_bot_mappings_user_eid_employee"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_bot_mappings")),
        sa.UniqueConstraint("user_eid", name=op.f("uq_user_bot_mappings_user_eid")),
    )
    
    op.create_index(
        op.f("ix_user_bot_mappings_user_eid"),
        "user_bot_mappings",
        ["user_eid"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_bot_mappings_band_chat_id"),
        "user_bot_mappings",
        ["band_chat_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_bot_mappings_is_active"),
        "user_bot_mappings",
        ["is_active"],
        unique=False,
    )
    
    op.add_column(
        "notification_preferences",
        sa.Column(
            "receive_news",
            sa.Boolean(),
            nullable=False,
            default=True,
            comment="Получать уведомления о новостях",
        ),
    )
    op.add_column(
        "notification_preferences",
        sa.Column(
            "receive_documents",
            sa.Boolean(),
            nullable=False,
            default=True,
            comment="Получать уведомления о документах",
        ),
    )
    op.add_column(
        "notification_preferences",
        sa.Column(
            "receive_birthdays",
            sa.Boolean(),
            nullable=False,
            default=True,
            comment="Получать уведомления о днях рождения",
        ),
    )
    op.add_column(
        "notification_preferences",
        sa.Column(
            "receive_comments",
            sa.Boolean(),
            nullable=False,
            default=True,
            comment="Получать уведомления о комментариях",
        ),
    )
    
    op.alter_column(
        "notification_preferences",
        "channel_messenger",
        existing_type=sa.Boolean(),
        existing_nullable=False,
        comment="Отправлять ли уведомления в Band Bot",
    )


def downgrade() -> None:

    op.drop_column("notification_preferences", "receive_comments")
    op.drop_column("notification_preferences", "receive_birthdays")
    op.drop_column("notification_preferences", "receive_documents")
    op.drop_column("notification_preferences", "receive_news")

    op.drop_index(op.f("ix_user_bot_mappings_is_active"), table_name="user_bot_mappings")
    op.drop_index(op.f("ix_user_bot_mappings_band_chat_id"), table_name="user_bot_mappings")
    op.drop_index(op.f("ix_user_bot_mappings_user_eid"), table_name="user_bot_mappings")
    op.drop_table("user_bot_mappings")
    
    op.drop_column("notifications", "delivered_at")
    op.drop_column("notifications", "sent_at")
    
    op.drop_index(op.f("ix_notifications_created_is_read"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_user_type_read"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_created_at"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_is_read"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_event_type"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_user_eid"), table_name="notifications")
