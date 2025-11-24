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
from core.models.enums import ProfileOperationType


class ProfileOrm(Base):
    __tablename__ = "profile"

    id = Column(
        sa.BigInteger, primary_key=True, autoincrement=True, nullable=False
    )

    employee_id = Column(
        sa.BigInteger,
        ForeignKey("employee.eid", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        comment="Связь с таблицей Employee (EID)",
    )

    avatar_id = Column(
        ForeignKey("file.id"),
        comment="Файл с аватаром (Редактируемый)",
        nullable=True,
    )

    personal_phone = Column(String, comment="Личный телефон (Редактируемый)")

    telegram = Column(String, comment="Telegram (Редактируемый)")

    about_me = Column(
        String(1000),
        comment="О себе (текст, до 1 000 символов, Редактируемый)",
    )


class ProfileProjectOrm(Base):
    __tablename__ = "profile_project"

    id = Column(
        sa.BigInteger, primary_key=True, autoincrement=True, nullable=False
    )

    profile_id = Column(
        sa.BigInteger,
        ForeignKey("profile.id", ondelete="CASCADE"),
        nullable=False,
        comment="Профиль",
    )

    name = Column(
        String,
        nullable=False,
        comment="Краткое название проекта (Редактируемый)",
    )

    start_d = Column(
        Date, comment="Период: Дата начала проекта (Редактируемый)"
    )

    end_d = Column(Date, comment="Период: Дата конца проекта (Редактируемый)")

    position = Column(String, comment="Роль в проекте (Редактируемый)")

    link = Column(String, comment="Ссылка (YouTrack/другое) (Редактируемый)")


class ProfileVacationOrm(Base):
    __tablename__ = "profile_vacation"

    id = Column(
        sa.BigInteger, primary_key=True, autoincrement=True, nullable=False
    )

    profile_id = Column(
        sa.BigInteger,
        ForeignKey("profile.id", ondelete="CASCADE"),
        nullable=False,
        comment="Профиль сотрудника",
    )

    is_planned = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="Статус: True - планируется, False - текущий/завершенный",
    )

    start_date = Column(Date, nullable=False, comment="Дата начала отпуска")
    end_date = Column(Date, nullable=False, comment="Дата конца отпуска")

    substitute_eid = Column(
        BigInteger,
        ForeignKey("employee.eid"),
        nullable=True,
        comment="Замещающий сотрудник",
    )

    comment = Column(String, comment="Комментарий к отпуску (Редактируемый)")

    is_official = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="Официальный статус из HR (read-only, контролирует фактический флаг 'в отпуске')",
    )


class ProfileChangeLogOrm(Base):
    __tablename__ = "profile_change_log"

    id = Column(
        sa.BigInteger, primary_key=True, autoincrement=True, nullable=False
    )

    profile_id = Column(
        sa.BigInteger,
        ForeignKey("profile.id", ondelete="CASCADE"),
        nullable=False,
        comment="ID профиля, который был изменен",
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

    table_name = Column(
        String(50),
        nullable=False,
        comment="Название таблицы",
    )

    record_id = Column(
        sa.BigInteger,
        nullable=True,
        comment="ID записи в таблице",
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
