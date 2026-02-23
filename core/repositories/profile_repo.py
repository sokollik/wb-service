from datetime import date
from typing import Optional

from sqlalchemy import alias, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models.emploee import EmployeeOrm
from core.models.org_structure import OrgUnitOrm
from core.models.profile import (
    ProfileOrm,
    ProfileProjectOrm,
    ProfileVacationOrm,
)


class ProfileRepository:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def get_profile(self, eid: str | None = None):
        ManagerORM = alias(EmployeeOrm, name="manager")
        HrORM = alias(EmployeeOrm, name="Hr")

        vacations_subq = (
            select(
                ProfileVacationOrm.profile_id.label("profile_id"),
                func.json_agg(
                    func.json_build_object(
                        "id",
                        ProfileVacationOrm.id,
                        "is_planned",
                        ProfileVacationOrm.is_planned,
                        "start_date",
                        ProfileVacationOrm.start_date,
                        "end_date",
                        ProfileVacationOrm.end_date,
                        "substitute",
                        EmployeeOrm.full_name,
                        "comment",
                        ProfileVacationOrm.comment,
                        "is_official",
                        ProfileVacationOrm.is_official,
                    )
                ).label("vacations"),
            )
            .outerjoin(
                EmployeeOrm,
                EmployeeOrm.eid == ProfileVacationOrm.substitute_eid,
            )
            .group_by(ProfileVacationOrm.profile_id)
            .subquery()
        )

        projects_subq = (
            select(
                ProfileProjectOrm.profile_id.label("profile_id"),
                func.json_agg(
                    func.json_build_object(
                        "id",
                        ProfileProjectOrm.id,
                        "name",
                        ProfileProjectOrm.name,
                        "start_d",
                        ProfileProjectOrm.start_d,
                        "end_d",
                        ProfileProjectOrm.end_d,
                        "position",
                        ProfileProjectOrm.position,
                        "link",
                        ProfileProjectOrm.link,
                    )
                ).label("projects"),
            )
            .group_by(ProfileProjectOrm.profile_id)
            .subquery()
        )

        query = (
            select(
                EmployeeOrm.eid.label("eid"),
                EmployeeOrm.full_name.label("full_name"),
                EmployeeOrm.position.label("position"),
                EmployeeOrm.birth_date.label("birth_date"),
                EmployeeOrm.hire_date.label("hire_date"),
                EmployeeOrm.work_phone.label("work_phone"),
                EmployeeOrm.work_email.label("work_email"),
                EmployeeOrm.work_band.label("work_band"),
                OrgUnitOrm.name.label("org_unit"),
                ProfileOrm.personal_phone.label("personal_phone"),
                ProfileOrm.avatar_id.label("avatar_id"),
                ProfileOrm.telegram.label("telegram"),
                ProfileOrm.about_me.label("about_me"),
                ManagerORM.c.full_name.label("manager_name"),
                HrORM.c.full_name.label("hr_name"),
                func.coalesce(
                    projects_subq.c.projects, func.json_build_array()
                ).label("projects"),
                func.coalesce(
                    vacations_subq.c.vacations, func.json_build_array()
                ).label("vacations"),
            )
            .outerjoin(
                OrgUnitOrm,
                OrgUnitOrm.id == EmployeeOrm.organization_unit,
            )
            .outerjoin(ProfileOrm, ProfileOrm.employee_id == EmployeeOrm.eid)
            .outerjoin(
                ManagerORM,
                ManagerORM.c.eid == OrgUnitOrm.manager_eid,
            )
            .outerjoin(HrORM, HrORM.c.eid == EmployeeOrm.hrbp_eid)
            .outerjoin(
                projects_subq,
                ProfileOrm.id == projects_subq.c.profile_id,
            )
            .outerjoin(
                vacations_subq,
                ProfileOrm.id == vacations_subq.c.profile_id,
            )
        )
        if eid is not None:
            query = query.where(EmployeeOrm.eid == eid)

        profile = (await self.session.execute(query)).mappings().all()

        return profile

    async def get_profiles_list(
        self,
        eid: Optional[str] = None,
        full_name: Optional[str] = None,
        position: Optional[str] = None,
        work_email: Optional[str] = None,
        work_band: Optional[str] = None,
        is_fired: Optional[bool] = None,
        hire_date_from: Optional[date] = None,
        hire_date_to: Optional[date] = None,
        page: int = 1,
        size: int = 20,
    ):
        query = (
            select(
                EmployeeOrm.eid.label("eid"),
                EmployeeOrm.full_name.label("full_name"),
                EmployeeOrm.position.label("position"),
                EmployeeOrm.birth_date.label("birth_date"),
                EmployeeOrm.hire_date.label("hire_date"),
                EmployeeOrm.work_phone.label("work_phone"),
                EmployeeOrm.work_email.label("work_email"),
                EmployeeOrm.work_band.label("work_band"),
                EmployeeOrm.is_fired.label("is_fired"),
                OrgUnitOrm.name.label("org_unit"),
            )
            .outerjoin(
                OrgUnitOrm,
                OrgUnitOrm.id == EmployeeOrm.organization_unit,
            )
        )

        if eid is not None:
            query = query.where(EmployeeOrm.eid == eid)
        if full_name is not None:
            query = query.where(EmployeeOrm.full_name.ilike(f"%{full_name}%"))
        if position is not None:
            query = query.where(EmployeeOrm.position.ilike(f"%{position}%"))
        if work_email is not None:
            query = query.where(EmployeeOrm.work_email.ilike(f"%{work_email}%"))
        if work_band is not None:
            query = query.where(EmployeeOrm.work_band == work_band)
        if is_fired is not None:
            query = query.where(EmployeeOrm.is_fired == is_fired)
        if hire_date_from is not None:
            query = query.where(EmployeeOrm.hire_date >= hire_date_from)
        if hire_date_to is not None:
            query = query.where(EmployeeOrm.hire_date <= hire_date_to)

        offset = (page - 1) * size
        query = query.order_by(EmployeeOrm.full_name).limit(size).offset(offset)

        result = await self.session.execute(query)
        return result.mappings().all()
