import sqlalchemy as sa
from sqlalchemy import Column, ForeignKey, String

from core.models.base import Base


class AuthTokenOrm(Base):
    __tablename__ = "auth_token"

    id = Column(
        sa.BigInteger, primary_key=True, autoincrement=True, nullable=False
    )

    employee_eid = Column(
        sa.BigInteger,
        ForeignKey("employee.eid", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        comment="Связь с таблицей Employee (EID) - владелец токена",
    )

    token = Column(
        String(512),
        nullable=False,
        unique=True,
        comment="Token или Session ID",
    )

    expires_at = Column(
        sa.DateTime(timezone=True),
        nullable=True,
        comment="Дата и время истечения срока действия токена",
    )

    created_at = Column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        comment="Время создания записи",
    )
