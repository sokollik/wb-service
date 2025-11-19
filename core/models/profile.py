import sqlalchemy as sa
from sqlalchemy import Column, Date, ForeignKey, String

from core.models.base import Base


class ProfileOrm(Base):
    __tablename__ = "profile"

    id = Column(
        sa.BigInteger, primary_key=True, autoincrement=True, nullable=False
    )

    employee_id = Column(
        sa.BigInteger,
        ForeignKey("employee.eid", ondelete="CASCADE"),
        primary_key=True,
        comment="Связь с таблицей Employee (EID)",
    )

    personal_phone = Column(String, comment="Личный телефон")
    telegram = Column(String, unique=True, comment="Telegram")
    about_me = Column(String, comment="О себе (текст)")

    vacation_info = Column(String, comment="Информация об отпуске")

    avatar_id = Column(
        ForeignKey("file.id"), comment="Файл с аватаром", nullable=True
    )


class ProfileProjectOrm(Base):
    __tablename__ = "profile_project"

    id = Column(
        sa.BigInteger, primary_key=True, autoincrement=True, nullable=False
    )

    profile_id = Column(
        ForeignKey("profile.id"), comment="Профиль", nullable=False
    )

    name = Column(String, comment="Название проекта")
    start_d = Column(Date, comment="Дата начала проекта")
    end_d = Column(Date, comment="Дата конца проекта")
    position = Column(String, comment="Роль в проекте")
