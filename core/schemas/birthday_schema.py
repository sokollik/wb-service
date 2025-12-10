from datetime import date
from typing import List
from pydantic import BaseModel, Field


class BirthdaySchema(BaseModel):
    eid: int = Field(..., description="ID работника")
    full_name: str = Field(...)
    department: str = Field(...)
    birth_date: date = Field(...)
    telegram: str | None = Field(None)
    telegram_birthday_link: str | None = Field(None)


class BirthdayListSchema(BaseModel):
    birthdays: List[BirthdaySchema]


class TelegramLinkSchema(BaseModel):
    telegram_link: str = Field(...)
