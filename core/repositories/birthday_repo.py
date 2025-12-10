from typing import List
from sqlalchemy import extract, select
from sqlalchemy.ext.asyncio import AsyncSession
from core.common.common_repo import CommonRepository

from core.models.emploee import EmployeeOrm, DepartmentOrm


class BirthdayRepository:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session
        self.common = CommonRepository(session=self.session)

    async def get_all_birthdays_sorted(self) -> List:
        birthdays = (
            select(
                EmployeeOrm.eid.label("eid"),
                EmployeeOrm.full_name.label("full_name"),
                DepartmentOrm.name.label("department"),
                EmployeeOrm.birth_date.label("birth_date"),
            )
            .join(DepartmentOrm, DepartmentOrm.id == EmployeeOrm.department_id)
            .order_by(
                extract("month", EmployeeOrm.birth_date).asc(),
                extract("day", EmployeeOrm.birth_date).asc(),
            )
        )

        result = await self.session.execute(birthdays)
        return result.mappings().all()
