import sqlalchemy as sa
from sqlalchemy import Column, Date, String

from core.models.base import Base


class EmployeeOrm(Base):
    __tablename__ = "employee"

    eid = Column(
        sa.BigInteger, primary_key=True, autoincrement=True, nullable=False
    )

    full_name = Column(String, nullable=False, comment="ФИО")
    position = Column(String, nullable=False, comment="Должность")
    department = Column(String, nullable=False, comment="Подразделение")
    birth_date = Column(Date, nullable=False, comment="Дата рождения")
    hire_date = Column(Date, nullable=False, comment="Дата найма")
    work_phone = Column(String, comment="Рабочий телефон")
    work_email = Column(
        String, unique=True, nullable=False, comment="Корпоративный email"
    )
