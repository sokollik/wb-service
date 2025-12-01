from fastapi import APIRouter, Depends
from fastapi_restful.cbv import cbv

from core.schemas.profile_schema import ProfileSchema
from core.services.profile_service import ProfileService
from core.utils.db_util import get_session_obj
from sqlalchemy.ext.asyncio import AsyncSession


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
    async def view_profile(self, eid:int) -> ProfileSchema:
        return await self.profile_service.get_my_profile(eid=eid)