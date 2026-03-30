import sqlalchemy as sa
from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Table,
    func,
)
from core.models.base import Base

class RoleEnum(str, Enum):
    EMPLOYEE = "EMPLOYEE"
    CURATOR = "CURATOR"
    ADMIN = "ADMIN"

class RoleOrm(Base):
    __tablename__ = "roles"

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    name = Column(String(50), unique=True, nullable=False, comment="Название роли (EMPLOYEE/CURATOR/ADMIN)")
    description = Column(String(255), nullable=True, comment="Описание роли")
    created_at = Column(DateTime, nullable=False, server_default=func.now(), comment="Дата создания роли")

class PermissionOrm(Base):
    __tablename__ = "permissions"

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    name = Column(String(100), unique=True, nullable=False, comment="Уникальное имя разрешения (news:create, news:edit)")
    resource = Column(String(50), nullable=False, comment="Ресурс (news, comments, profile, documents)")
    action = Column(String(20), nullable=False, comment="Действие (create, read, update, delete, manage)")
    description = Column(String(255), nullable=True, comment="Описание разрешения")

class RolePermissionOrm(Base):
    __tablename__ = "role_permissions"

    role_id = Column(
        BigInteger,
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        comment="ID роли"
    )
    permission_id = Column(
        BigInteger,
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        comment="ID разрешения"
    )

class UserRoleOrm(Base):
    __tablename__ = "user_roles"

    user_eid = Column(
        String,
        ForeignKey("employee.eid", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        comment="EID пользователя"
    )
    role_id = Column(
        BigInteger,
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        comment="ID роли"
    )
    granted_by = Column(
        String,
        ForeignKey("employee.eid"),
        nullable=True,
        comment="EID сотрудника, выдавшего роль"
    )
    granted_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        comment="Дата выдачи роли"
    )

class CuratorScopeOrm(Base):
    __tablename__ = "curator_scopes"

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    curator_eid = Column(
        String,
        ForeignKey("employee.eid", ondelete="CASCADE"),
        nullable=False,
        comment="EID куратора"
    )
    org_unit_id = Column(
        BigInteger,
        ForeignKey("organization_unit.id", ondelete="CASCADE"),
        nullable=False,
        comment="ID подразделения, к которому есть доступ"
    )

    __table_args__ = (
        sa.UniqueConstraint("curator_eid", "org_unit_id", name="uq_curator_scope"),
    )
