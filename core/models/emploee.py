from sqlalchemy import BigInteger, Boolean, Column, Date, ForeignKey, String

from core.models.base import Base


class EmployeeOrm(Base):
    __tablename__ = "employee"

    eid = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        nullable=False,
        comment="EID/ID (read-only HR)",
    )

    full_name = Column(String, nullable=False, comment="ФИО (read-only HR)")

    position = Column(
        String, nullable=False, comment="Должность (read-only HR)"
    )

    organization_unit = Column(
        BigInteger,
        ForeignKey("organization_unit.id"),
        nullable=True,
        comment="Подразделение",
    )

    birth_date = Column(
        Date, nullable=False, comment="Дата рождения (read-only HR)"
    )

    hire_date = Column(
        Date, nullable=False, comment="Дата найма (read-only HR)"
    )

    work_phone = Column(String, comment="Рабочий телефон (read-only HR)")

    work_email = Column(
        String,
        unique=True,
        nullable=False,
        comment="Корпоративный email (read-only HR)",
    )

    work_band = Column(String, comment="Band (read-only HR)")
    hrbp_eid = Column(
        BigInteger,
        ForeignKey("employee.eid"),
        nullable=True,
        comment="HR-бизнес-партнёр (read-only HR)",
    )
    is_fired = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="Флаг уволенного/архивного сотрудника",
    )

