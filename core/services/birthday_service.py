from datetime import date, timedelta
from typing import List, Literal
from urllib.parse import quote_plus
from sqlalchemy.ext.asyncio import AsyncSession
from core.repositories.birthday_repo import BirthdayRepository
from core.schemas.birthday_schema import BirthdaySchema

BIRTHDAY_MESSAGE = (
    "Привет, c днём рождения! Желаю счастья, успехов и исполнения всех желаний!"
)


class BirthdayService:

    def __init__(self, session: AsyncSession):
        self.session = session
        self.birthday_repo = BirthdayRepository(session=self.session)

    async def get_upcoming_birthdays(
        self, time_unit: Literal["day", "week", "month"]
    ) -> List[BirthdaySchema]:

        today = date.today()

        if time_unit == "day":
            delta_days = 0
        elif time_unit == "week":
            delta_days = 7
        elif time_unit == "month":
            delta_days = 30
        else:
            delta_days = 0

        end_window = today + timedelta(days=delta_days)

        birthdays_data = await self.birthday_repo.get_all_birthdays_sorted()

        upcoming_birthdays = []
        for item in birthdays_data:
            birth_date: date = item["birth_date"]

            future_bday = date(today.year, birth_date.month, birth_date.day)

            if future_bday < today:
                future_bday = date(today.year + 1, birth_date.month, birth_date.day)

            if today <= future_bday <= end_window:
                upcoming_birthdays.append(BirthdaySchema(**dict(item)))

        return upcoming_birthdays

    async def get_telegram_link_for_birthday(self, eid: int) -> str:
        telegram_username = await self.birthday_repo.get_telegram(eid)
        if telegram_username:
            encoded_message = quote_plus(BIRTHDAY_MESSAGE)
            link = (
                f"https://t.me/{telegram_username.lstrip('@')}?&text={encoded_message}"
            )
            return link

        return None
