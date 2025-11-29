from sqlalchemy.ext.asyncio import AsyncSession

from core.repositories.profile_repo import ProfileRepository


class ProfileService:

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

        self.profile_repo = ProfileRepository(session=self.session)
        
        
    async def get_my_profile(self, eid: int):
        return await self.profile_repo.get_profile(eid=eid)