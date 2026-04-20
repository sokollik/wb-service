import sqlalchemy as sa
from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, ForeignKey, String, func, Index, Text
)
from sqlalchemy.orm import relationship

from core.models.base import Base


class KeycloakUserSyncOrm(Base):
    __tablename__ = "keycloak_user_sync"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_eid = Column(
        String,
        ForeignKey("employee.eid", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
        comment="EID пользователя из Keycloak",
    )
    
    email = Column(String, nullable=True, index=True, comment="Email из Keycloak")
    username = Column(String, nullable=True, comment="Username из Keycloak")
    full_name = Column(String, nullable=True, comment="ФИО из Keycloak")
    
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Активен ли пользователь (не уволен)",
    )
    is_fired = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Флаг уволенного сотрудника",
    )
    fired_at = Column(DateTime, nullable=True, comment="Дата увольнения")
    
    last_sync_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        comment="Время последней синхронизации",
    )
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        Index("ix_keycloak_sync_is_active_fired", "is_active", "is_fired"),
    )


class ThesisIntegrationLogOrm(Base):

    __tablename__ = "thesis_integration_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    user_eid = Column(
        String,
        ForeignKey("employee.eid", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="EID пользователя, перешедшего в Тезис",
    )
    
    thesis_document_id = Column(
        String,
        nullable=True,
        index=True,
        comment="ID документа в Тезис",
    )
    local_document_id = Column(
        BigInteger,
        nullable=True,
        comment="ID локального документа",
    )
    
    access_token = Column(
        Text,
        nullable=True,
        comment="Временный access token для Тезис",
    )
    token_expires_at = Column(
        DateTime,
        nullable=True,
        comment="Время истечения токена",
    )
    redirect_url = Column(
        Text,
        nullable=True,
        comment="URL для редиректа в Тезис",
    )
    
    status = Column(
        String,
        default="pending",
        nullable=False,
        index=True,
        comment="Статус перехода (pending, success, failed)",
    )
    error_message = Column(
        Text,
        nullable=True,
        comment="Сообщение об ошибке",
    )
    
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    completed_at = Column(
        DateTime,
        nullable=True,
        comment="Время завершения перехода",
    )
    
    user_agent = Column(String, nullable=True, comment="User Agent браузера")
    ip_address = Column(String, nullable=True, comment="IP адрес пользователя")
    session_id = Column(String, nullable=True, comment="ID сессии")

    __table_args__ = (
        Index("ix_thesis_logs_user_created", "user_eid", "created_at"),
        Index("ix_thesis_logs_status", "status"),
    )


class ThesisCredentialsOrm(Base):

    __tablename__ = "thesis_credentials"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    client_id = Column(
        String,
        nullable=False,
        comment="Client ID для OAuth2",
    )
    client_secret = Column(
        String,
        nullable=False,
        comment="Client Secret для OAuth2",
    )
    
    saml_entity_id = Column(
        String,
        nullable=True,
        comment="SAML Entity ID",
    )
    saml_acs_url = Column(
        String,
        nullable=True,
        comment="SAML Assertion Consumer Service URL",
    )
    saml_certificate = Column(
        Text,
        nullable=True,
        comment="SAML сертификат",
    )
    
    access_token = Column(
        Text,
        nullable=True,
        comment="Текущий access token",
    )
    refresh_token = Column(
        Text,
        nullable=True,
        comment="Refresh token",
    )
    token_expires_at = Column(
        DateTime,
        nullable=True,
        comment="Время истечения токена",
    )
    
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Активны ли учетные данные",
    )
    last_used_at = Column(
        DateTime,
        nullable=True,
        comment="Время последнего использования",
    )
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
