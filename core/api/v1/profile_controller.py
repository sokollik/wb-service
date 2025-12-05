import os
from typing import List

from fastapi import APIRouter, Depends
from fastapi_restful.cbv import cbv
from sqlalchemy.ext.asyncio import AsyncSession

from core.schemas.profile_schema import (
    ProfileChangeLogSchema,
    ProfileSchema,
    ProfileUpdateSchema,
)
from core.services.profile_service import ProfileService
from core.utils.common_util import exception_handler
from core.utils.db_util import get_session_obj

profile_controller = APIRouter()


@cbv(profile_controller)
class ProfileController:

    def __init__(
        self,
        session: AsyncSession = Depends(get_session_obj),
    ):
        self.session = session
        self.profile_service = ProfileService(session=session)

    @profile_controller.get("/me")
    @exception_handler
    async def view_profile(self, eid: int) -> ProfileSchema:
        return await self.profile_service.get_my_profile(eid=eid)

    @profile_controller.get("/share")
    @exception_handler
    async def share_profile(self, eid: int) -> str:
        web_url = os.getenv("WEB_URL")
        return web_url + f"/profile/{eid}"

    @profile_controller.patch("/me")
    @exception_handler
    async def edit_profile(self, eid: int, profile_data: ProfileUpdateSchema):

        return await self.profile_service.update_profile(
            eid=eid, profile_data=profile_data
        )

    @profile_controller.get("/log")
    @exception_handler
    async def get_profile_edit_log(self, eid: int) -> List[ProfileChangeLogSchema]:
        return await self.profile_service.get_profile_edit_log(eid=eid)
