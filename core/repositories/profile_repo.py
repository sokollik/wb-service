from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models.emploee import EmployeeOrm

class ProfileRepository:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session
        
    async def get_profile(self, eid:int):
        profile = (await self.session.execute(select(EmployeeOrm).where(EmployeeOrm.eid == eid))).scalar()
        return profile
        
        