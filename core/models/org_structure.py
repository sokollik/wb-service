import sqlalchemy as sa
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    String,
    func,
)

from core.models.base import Base
from core.models.enums import OrgUnitType, ProfileOperationType


class OrgUnitOrm(Base):
    __tablename__ = "organization_unit"

    id = Column(sa.BigInteger, primary_key=True, autoincrement=True, nullable=False)

    name = Column(String, nullable=False, comment="Название структурной единицы")

    unit_type = Column(
        Enum(OrgUnitType),
        nullable=False,
        comment="Тип структурной единицы (Департамент, Отдел, Группа и т.д.)",
    )

    parent_id = Column(
        BigInteger,
        ForeignKey("organization_unit.id", ondelete="CASCADE"),
        nullable=True,
        comment="Родительская структурная единица",
    )

    manager_eid = Column(
        BigInteger,
        ForeignKey("employee.eid"),
        nullable=True,
        comment="Руководитель данной структурной единицы",
    )

    is_temporary = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="Флаг временного подразделения/проектной команды",
    )

    start_date = Column(
        Date,
        nullable=True,
        comment="Дата начала действия (для временных)",
    )

    end_date = Column(
        Date,
        nullable=True,
        comment="Дата окончания действия (для временных)",
    )


class OrgChangeLogOrm(Base):
    __tablename__ = "organization_change_log"

    id = Column(sa.BigInteger, primary_key=True, autoincrement=True, nullable=False)

    org_unit_id = Column(
        sa.BigInteger,
        ForeignKey("organization_unit.id"),
        nullable=True,
        comment="ID подразделения, которое было изменено",
    )

    changed_by_eid = Column(
        sa.BigInteger,
        ForeignKey("employee.eid"),
        nullable=False,
        comment="EID сотрудника, который внес изменение",
    )

    changed_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        comment="Дата и время изменения",
    )

    field_name = Column(
        String,
        nullable=False,
        comment="Название измененного поля",
    )

    old_value = Column(
        String,
        nullable=True,
        comment="Старое значение (JSON или строка)",
    )

    new_value = Column(
        String,
        nullable=True,
        comment="Новое значение (JSON или строка)",
    )

    operation = Column(
        Enum(ProfileOperationType), nullable=False, comment="Тип операции"
    )
