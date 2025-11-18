import sqlalchemy as sa
from sqlalchemy import Column, ForeignKey, String, Text

from core.models.base import Base


class Profile(Base):
    __tablename__ = "profile"

    employee_id = Column(
        sa.BigInteger,
        ForeignKey("employee.eid", ondelete="CASCADE"),
        primary_key=True,
        comment="Связь с таблицей Employee (EID)",
    )

    avatar_url = Column(String, comment="URL аватара")
    personal_phone = Column(String, comment="Личный телефон")
    telegram_handle = Column(String, unique=True, comment="Telegram хендл")
    about_me = Column(Text, comment="О себе (текст)")

    projects_list = Column(
        Text, comment="Список проектов (например, JSON-массив)"
    )
    vacation_info = Column(Text, comment="Информация об отпуске")
