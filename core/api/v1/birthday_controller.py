from typing import Literal
from fastapi import APIRouter, Depends
from fastapi_restful.cbv import cbv
from sqlalchemy.ext.asyncio import AsyncSession

from core.schemas.birthday_schema import BirthdayListSchema, BirthdaySchema
from core.services.birthday_service import BirthdayService
from core.utils.common_util import exception_handler
from core.utils.db_util import get_session_obj


birthday_controller = APIRouter()


@cbv(birthday_controller)
class BirthdayController:

    def __init__(
        self,
        session: AsyncSession = Depends(get_session_obj),
    ):
        self.session = session
        self.birthday_service = BirthdayService(session=session)

    @birthday_controller.get("/upcoming")
    async def view_upcoming_birthday(
        self, time_unit: Literal["day", "week", "month"] = "month"
    ) -> BirthdayListSchema:

        birthdays = await self.birthday_service.get_upcoming_birthdays(
            time_unit=time_unit
        )
        return BirthdayListSchema(birthdays=birthdays)
