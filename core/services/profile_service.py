from sqlalchemy.ext.asyncio import AsyncSession

from core.repositories.profile_repo import ProfileRepository
from core.schemas.profile_schema import ProfileSchema, ProfileUpdateSchema


class ProfileService:

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

        self.profile_repo = ProfileRepository(session=self.session)

    async def get_my_profile(self, eid: int):
        return await self.profile_repo.get_profile(eid=eid)

    async def update_my_profile(
        self, eid: int, profile_data: ProfileUpdateSchema
    ) -> ProfileSchema:

        updated_profile = await self.profile_repo.update_profile(
            eid=eid, profile_data=profile_data
        )

        await self.session.commit()
        return ProfileSchema.model_validate(updated_profile)
