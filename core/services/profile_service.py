from sqlalchemy.ext.asyncio import AsyncSession

from core.common.common_exc import NotFoundHttpException
from core.common.common_repo import CommonRepository
from core.models.profile import ProfileOrm, ProfileProjectOrm
from core.repositories.profile_repo import ProfileRepository
from core.schemas.profile_schema import ProfileUpdateSchema


class ProfileService:

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session
        self.common = CommonRepository(session=self.session)
        self.profile_repo = ProfileRepository(session=self.session)

    async def get_my_profile(self, eid: int):
        return await self.profile_repo.get_profile(eid=eid)
    
    async def update_profile(self, eid: int, profile_data: ProfileUpdateSchema):
        profile = await self.common.get_one(
            ProfileOrm, where_stmt=ProfileOrm.employee_id == eid
        )
        if profile is None:
            raise NotFoundHttpException(name="profile")
        await self.common.update(
            orm_instance=ProfileOrm(
                id=profile.id,
                personal_phone=profile_data.personal_phone,
                telegram=profile_data.telegram,
                about_me=profile_data.about_me,
            )
        )
        if profile_data.projects is not None:
            await self.common.delete(
                ProfileProjectOrm, ProfileProjectOrm.profile_id == profile.id
            )
            await self.common.add_all(
                [
                    ProfileProjectOrm(
                        profile_id=profile.id,
                        name=project.name,
                        start_d=project.start_d,
                        end_d=project.end_d,
                        position=project.position,
                        link=project.link,
                    )
                    for project in profile_data.projects
                ]
            )
