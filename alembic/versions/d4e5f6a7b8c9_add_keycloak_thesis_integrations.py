import sqlalchemy as sa
from alembic import op

revision = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    
    op.create_table(
        "keycloak_user_sync",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "user_eid",
            sa.String(),
            nullable=False,
            comment="EID пользователя из Keycloak",
        ),
        sa.Column(
            "email",
            sa.String(),
            nullable=True,
            comment="Email из Keycloak",
        ),
        sa.Column(
            "username",
            sa.String(),
            nullable=True,
            comment="Username из Keycloak",
        ),
        sa.Column(
            "full_name",
            sa.String(),
            nullable=True,
            comment="ФИО из Keycloak",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            default=True,
            comment="Активен ли пользователь (не уволен)",
        ),
        sa.Column(
            "is_fired",
            sa.Boolean(),
            nullable=False,
            default=False,
            comment="Флаг уволенного сотрудника",
        ),
        sa.Column(
            "fired_at",
            sa.DateTime(),
            nullable=True,
            comment="Дата увольнения",
        ),
        sa.Column(
            "last_sync_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
            comment="Время последней синхронизации",
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
            name=op.f("fk_keycloak_user_sync_user_eid_employee"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_keycloak_user_sync")),
        sa.UniqueConstraint("user_eid", name=op.f("uq_keycloak_user_sync_user_eid")),
    )
    
    op.create_index(
        op.f("ix_keycloak_user_sync_user_eid"),
        "keycloak_user_sync",
        ["user_eid"],
        unique=False,
    )
    op.create_index(
        op.f("ix_keycloak_user_sync_email"),
        "keycloak_user_sync",
        ["email"],
        unique=False,
    )
    op.create_index(
        op.f("ix_keycloak_user_sync_is_active"),
        "keycloak_user_sync",
        ["is_active"],
        unique=False,
    )
    op.create_index(
        op.f("ix_keycloak_user_sync_is_fired"),
        "keycloak_user_sync",
        ["is_fired"],
        unique=False,
    )
    op.create_index(
        op.f("ix_keycloak_sync_is_active_fired"),
        "keycloak_user_sync",
        ["is_active", "is_fired"],
        unique=False,
    )
    
    op.create_table(
        "thesis_integration_logs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "user_eid",
            sa.String(),
            nullable=True,
            comment="EID пользователя, перешедшего в Тезис",
        ),
        sa.Column(
            "thesis_document_id",
            sa.String(),
            nullable=True,
            comment="ID документа в Тезис",
        ),
        sa.Column(
            "local_document_id",
            sa.BigInteger(),
            nullable=True,
            comment="ID локального документа",
        ),
        sa.Column(
            "access_token",
            sa.Text(),
            nullable=True,
            comment="Временный access token для Тезис",
        ),
        sa.Column(
            "token_expires_at",
            sa.DateTime(),
            nullable=True,
            comment="Время истечения токена",
        ),
        sa.Column(
            "redirect_url",
            sa.Text(),
            nullable=True,
            comment="URL для редиректа в Тезис",
        ),
        sa.Column(
            "status",
            sa.String(),
            nullable=False,
            default="pending",
            comment="Статус перехода (pending, success, failed)",
        ),
        sa.Column(
            "error_message",
            sa.Text(),
            nullable=True,
            comment="Сообщение об ошибке",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(),
            nullable=True,
            comment="Время завершения перехода",
        ),
        sa.Column(
            "user_agent",
            sa.String(),
            nullable=True,
            comment="User Agent браузера",
        ),
        sa.Column(
            "ip_address",
            sa.String(),
            nullable=True,
            comment="IP адрес пользователя",
        ),
        sa.Column(
            "session_id",
            sa.String(),
            nullable=True,
            comment="ID сессии",
        ),
        sa.ForeignKeyConstraint(
            ["user_eid"],
            ["employee.eid"],
            name=op.f("fk_thesis_integration_logs_user_eid_employee"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_thesis_integration_logs")),
    )
    
    op.create_index(
        op.f("ix_thesis_integration_logs_user_eid"),
        "thesis_integration_logs",
        ["user_eid"],
        unique=False,
    )
    op.create_index(
        op.f("ix_thesis_integration_logs_thesis_document_id"),
        "thesis_integration_logs",
        ["thesis_document_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_thesis_integration_logs_status"),
        "thesis_integration_logs",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_thesis_integration_logs_created_at"),
        "thesis_integration_logs",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_thesis_logs_user_created"),
        "thesis_integration_logs",
        ["user_eid", "created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_thesis_logs_status"),
        "thesis_integration_logs",
        ["status"],
        unique=False,
    )
    
    op.create_table(
        "thesis_credentials",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "client_id",
            sa.String(),
            nullable=False,
            comment="Client ID для OAuth2",
        ),
        sa.Column(
            "client_secret",
            sa.String(),
            nullable=False,
            comment="Client Secret для OAuth2",
        ),
        sa.Column(
            "saml_entity_id",
            sa.String(),
            nullable=True,
            comment="SAML Entity ID",
        ),
        sa.Column(
            "saml_acs_url",
            sa.String(),
            nullable=True,
            comment="SAML Assertion Consumer Service URL",
        ),
        sa.Column(
            "saml_certificate",
            sa.Text(),
            nullable=True,
            comment="SAML сертификат",
        ),
        sa.Column(
            "access_token",
            sa.Text(),
            nullable=True,
            comment="Текущий access token",
        ),
        sa.Column(
            "refresh_token",
            sa.Text(),
            nullable=True,
            comment="Refresh token",
        ),
        sa.Column(
            "token_expires_at",
            sa.DateTime(),
            nullable=True,
            comment="Время истечения токена",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            default=True,
            comment="Активны ли учетные данные",
        ),
        sa.Column(
            "last_used_at",
            sa.DateTime(),
            nullable=True,
            comment="Время последнего использования",
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_thesis_credentials")),
    )


def downgrade() -> None:
    
    op.drop_table("thesis_credentials")
    op.drop_index(op.f("ix_thesis_logs_status"), table_name="thesis_integration_logs")
    op.drop_index(op.f("ix_thesis_logs_user_created"), table_name="thesis_integration_logs")
    op.drop_index(op.f("ix_thesis_integration_logs_created_at"), table_name="thesis_integration_logs")
    op.drop_index(op.f("ix_thesis_integration_logs_status"), table_name="thesis_integration_logs")
    op.drop_index(op.f("ix_thesis_integration_logs_thesis_document_id"), table_name="thesis_integration_logs")
    op.drop_index(op.f("ix_thesis_integration_logs_user_eid"), table_name="thesis_integration_logs")
    
    op.drop_table("thesis_integration_logs")

    op.drop_index(op.f("ix_keycloak_sync_is_active_fired"), table_name="keycloak_user_sync")
    op.drop_index(op.f("ix_keycloak_user_sync_is_fired"), table_name="keycloak_user_sync")
    op.drop_index(op.f("ix_keycloak_user_sync_is_active"), table_name="keycloak_user_sync")
    op.drop_index(op.f("ix_keycloak_user_sync_email"), table_name="keycloak_user_sync")
    op.drop_index(op.f("ix_keycloak_user_sync_user_eid"), table_name="keycloak_user_sync")
    
    op.drop_table("keycloak_user_sync")
