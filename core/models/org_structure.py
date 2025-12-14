import sqlalchemy as sa
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    Enum,
    ForeignKey,
    String,
)

from core.models.base import Base
from core.models.enums import OrgUnitType


class OrgUnitOrm(Base):
    __tablename__ = "organization_unit"

    id = Column(
        sa.BigInteger, primary_key=True, autoincrement=True, nullable=False
    )

    name = Column(String, nullable=False, comment="Название структурной единицы")

    unit_type = Column(
        Enum(OrgUnitType), 
        nullable=False, 
        comment="Тип структурной единицы (Департамент, Отдел, Группа и т.д.)"
    )

    parent_id = Column(
        BigInteger,
        ForeignKey("organization_unit.id"),
        nullable=True,
        comment="Родительская структурная единица",
    )
    
    manager_eid = Column(
        BigInteger,
        ForeignKey("employee.eid"),
        nullable=True,
        comment="Руководитель данной структурной единицы",
    )

    manager_eid = Column(
        BigInteger,
        ForeignKey("employee.eid"),
        nullable=True,
        comment="Руководитель подразделения",
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