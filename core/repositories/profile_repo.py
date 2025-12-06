from sqlalchemy import alias, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models.emploee import EmployeeOrm, DepartmentOrm
from core.models.profile import ProfileOrm, ProfileProjectOrm, ProfileVacationOrm


class ProfileRepository:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def get_profile(self, eid: int):
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
                EmployeeOrm, EmployeeOrm.eid == ProfileVacationOrm.substitute_eid
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

        profile = (
            (
                await self.session.execute(
                    select(
                        EmployeeOrm.eid.label("eid"),
                        EmployeeOrm.full_name.label("full_name"),
                        EmployeeOrm.position.label("position"),
                        EmployeeOrm.birth_date.label("birth_date"),
                        EmployeeOrm.hire_date.label("hire_date"),
                        EmployeeOrm.work_phone.label("work_phone"),
                        EmployeeOrm.work_email.label("work_email"),
                        EmployeeOrm.work_band.label("work_band"),
                        DepartmentOrm.name.label("department"),
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
                    .where(EmployeeOrm.eid == eid)
                    .join(DepartmentOrm, DepartmentOrm.id == EmployeeOrm.department_id)
                    .join(ProfileOrm, ProfileOrm.employee_id == EmployeeOrm.eid)
                    .outerjoin(ManagerORM, ManagerORM.c.eid == EmployeeOrm.manager_eid)
                    .outerjoin(HrORM, HrORM.c.eid == EmployeeOrm.hrbp_eid)
                    .outerjoin(
                        projects_subq, ProfileOrm.id == projects_subq.c.profile_id
                    )
                    .outerjoin(
                        vacations_subq, ProfileOrm.id == vacations_subq.c.profile_id
                    )
                )
            )
            .mappings()
            .one_or_none()
        )
        return profile
