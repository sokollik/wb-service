import json
from datetime import date
from io import BytesIO

import pandas as pd
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from core.common.common_exc import NotFoundHttpException
from core.common.common_repo import CommonRepository
from core.models.enums import ProfileOperationType
from core.models.profile import (
    ProfileChangeLogOrm,
    ProfileOrm,
    ProfileProjectOrm,
)
from core.repositories.profile_repo import ProfileRepository
from core.schemas.profile_schema import (
    ProfileExportFilter,
    ProfileUpdateSchema,
)


class ProfileService:

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session
        self.common = CommonRepository(session=self.session)
        self.profile_repo = ProfileRepository(session=self.session)

    async def get_my_profile(self, eid: int):
        profiles = await self.profile_repo.get_profile(eid=eid)
        if not profiles:
            raise NotFoundHttpException(name="profile")
        return profiles[0]

    async def _serialize_value(self, value):
        if value is None:
            return None
        if isinstance(value, (date, int, float, bool)):
            return str(value)
        return str(value)

    async def update_profile(
        self,
        eid: int,
        profile_data: ProfileUpdateSchema,
    ):
        profile = await self.common.get_one(
            ProfileOrm, where_stmt=ProfileOrm.employee_id == eid
        )
        if profile is None:
            raise NotFoundHttpException(name="profile")

        if (
            profile_data.personal_phone is not None
            and profile_data.personal_phone != profile.personal_phone
        ):
            await self.common.add(
                ProfileChangeLogOrm(
                    profile_id=profile.id,
                    changed_by_eid=eid,
                    table_name="profile",
                    record_id=profile.id,
                    field_name="personal_phone",
                    old_value=await self._serialize_value(
                        profile.personal_phone
                    ),
                    new_value=await self._serialize_value(
                        profile_data.personal_phone
                    ),
                    operation=ProfileOperationType.UPDATE,
                )
            )

        if (
            profile_data.telegram is not None
            and profile_data.telegram != profile.telegram
        ):
            await self.common.add(
                ProfileChangeLogOrm(
                    profile_id=profile.id,
                    changed_by_eid=eid,
                    table_name="profile",
                    record_id=profile.id,
                    field_name="telegram",
                    old_value=await self._serialize_value(profile.telegram),
                    new_value=await self._serialize_value(
                        profile_data.telegram
                    ),
                    operation=ProfileOperationType.UPDATE,
                )
            )

        if (
            profile_data.about_me is not None
            and profile_data.about_me != profile.about_me
        ):
            await self.common.add(
                ProfileChangeLogOrm(
                    profile_id=profile.id,
                    changed_by_eid=eid,
                    table_name="profile",
                    record_id=profile.id,
                    field_name="about_me",
                    old_value=await self._serialize_value(profile.about_me),
                    new_value=await self._serialize_value(
                        profile_data.about_me
                    ),
                    operation=ProfileOperationType.UPDATE,
                )
            )

        if (
            profile_data.avatar_id is not None
            and profile_data.avatar_id != profile.avatar_id
        ):
            await self.common.add(
                ProfileChangeLogOrm(
                    profile_id=profile.id,
                    changed_by_eid=eid,
                    table_name="profile",
                    record_id=profile.id,
                    field_name="avatar_id",
                    old_value=await self._serialize_value(profile.avatar_id),
                    new_value=await self._serialize_value(
                        profile_data.avatar_id
                    ),
                    operation=ProfileOperationType.UPDATE,
                )
            )

        await self.common.update(
            orm_instance=ProfileOrm(
                id=profile.id,
                avatar_id=profile_data.avatar_id,
                personal_phone=profile_data.personal_phone
                or profile.personal_phone,
                telegram=profile_data.telegram or profile.telegram,
                about_me=profile_data.about_me or profile.about_me,
            )
        )

        if profile_data.projects is not None:
            old_projects = await self.common.get_all_scalars(
                ProfileProjectOrm,
                where_stmt=ProfileProjectOrm.profile_id == profile.id,
            )

            for old_project in old_projects:
                await self.common.add(
                    ProfileChangeLogOrm(
                        profile_id=profile.id,
                        changed_by_eid=eid,
                        table_name="profile_project",
                        record_id=old_project.id,
                        field_name="all",
                        old_value=json.dumps(
                            {
                                "name": old_project.name,
                                "start_d": (
                                    str(old_project.start_d)
                                    if old_project.start_d
                                    else None
                                ),
                                "end_d": (
                                    str(old_project.end_d)
                                    if old_project.end_d
                                    else None
                                ),
                                "position": old_project.position,
                                "link": old_project.link,
                            }
                        ),
                        new_value=None,
                        operation=ProfileOperationType.DELETE,
                    )
                )

            await self.common.delete(
                ProfileProjectOrm, ProfileProjectOrm.profile_id == profile.id
            )

            new_projects = [
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

            await self.common.add_all(new_projects)

            for project in new_projects:
                await self.common.add(
                    ProfileChangeLogOrm(
                        profile_id=profile.id,
                        changed_by_eid=eid,
                        table_name="profile_project",
                        record_id=project.id,
                        field_name="all",
                        old_value=None,
                        new_value=json.dumps(
                            {
                                "name": project.name,
                                "start_d": (
                                    str(project.start_d)
                                    if project.start_d
                                    else None
                                ),
                                "end_d": (
                                    str(project.end_d)
                                    if project.end_d
                                    else None
                                ),
                                "position": project.position,
                                "link": project.link,
                            }
                        ),
                        operation=ProfileOperationType.CREATE,
                    )
                )

        await self.session.commit()

    def _deserialize_log_value(self, value):
        if value is None:
            return None

        try:
            decoded = json.loads(value)
            return decoded
        except (json.JSONDecodeError, TypeError):
            return value

    async def get_profile_edit_log(self, eid: int):
        profile = await self.common.get_one(
            ProfileOrm, where_stmt=ProfileOrm.employee_id == eid
        )
        if profile is None:
            raise NotFoundHttpException(name="profile")

        logs = await self.common.get_all_scalars(
            ProfileChangeLogOrm,
            where_stmt=ProfileChangeLogOrm.profile_id == profile.id,
        )

        processed_logs = []
        for log in logs:
            log_data = {
                "id": log.id,
                "profile_id": log.profile_id,
                "changed_by_eid": log.changed_by_eid,
                "changed_at": log.changed_at,
                "table_name": log.table_name,
                "record_id": log.record_id,
                "field_name": log.field_name,
                "operation": log.operation,
                "old_value": self._deserialize_log_value(log.old_value),
                "new_value": self._deserialize_log_value(log.new_value),
            }
            processed_logs.append(log_data)
        return processed_logs

    async def export_profiles_to_excel(self, config: ProfileExportFilter):
        FIELD_MAPPING = {
            "eid": ("ID сотрудника", "eid"),
            "full_name": ("ФИО", "full_name"),
            "position": ("Должность", "position"),
            "org_unit": ("Подразделение", "org_unit"),
            "birth_date": ("Дата рождения", "birth_date"),
            "hire_date": ("Дата найма", "hire_date"),
            "work_phone": ("Рабочий телефон", "work_phone"),
            "personal_phone": ("Личный телефон", "personal_phone"),
            "work_email": ("Корпоративный Email", "work_email"),
            "work_band": ("Грейд/Band", "work_band"),
            "telegram": ("Telegram", "telegram"),
            "manager_name": ("Руководитель", "manager_name"),
            "hr_name": ("HRBP", "hr_name"),
            "about_me": ("О себе", "about_me"),
        }

        raw_data = await self.profile_repo.get_profile()

        requested_fields = config.fields if config.fields else list(FIELD_MAPPING.keys())
        
        show_projects = "projects" in requested_fields
        show_vacations = "vacations" in requested_fields

        employees_list = []
        projects_list = []
        vacations_list = []

        for row in raw_data:
            current_eid = row["eid"]
            
            entry = {}
            for field in requested_fields:
                if field in FIELD_MAPPING:
                    label, attr = FIELD_MAPPING[field]
                    entry[label] = row[attr]
            employees_list.append(entry)

            if show_projects and row.get("projects"):
                for prj in row["projects"]:
                    projects_list.append({
                        "EID Сотрудника": current_eid,
                        "Название": prj.get("name"),
                        "Роль": prj.get("position"),
                        "Начало": str(prj.get("start_d")) if prj.get("start_d") else None,
                        "Конец": str(prj.get("end_d")) if prj.get("end_d") else None,
                        "Ссылка": prj.get("link")
                    })

            if show_vacations and row.get("vacations"):
                for vac in row["vacations"]:
                    vacations_list.append({
                        "EID Сотрудника": current_eid,
                        "Начало": str(vac.get("start_date")),
                        "Конец": str(vac.get("end_date")),
                        "Планируемый": "Да" if vac.get("is_planned") else "Нет",
                        "Замещающий": vac.get("substitute"),
                        "Комментарий": vac.get("comment"),
                        "Официальный": "Да" if vac.get("is_official") else "Нет"
                    })

        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df_emp = pd.DataFrame(employees_list)
            df_emp.to_excel(writer, index=False, sheet_name="Сотрудники")

            if show_projects:
                df_prj = pd.DataFrame(projects_list)
                df_prj.to_excel(writer, index=False, sheet_name="Проекты")
                
            if show_vacations:
                df_vac = pd.DataFrame(vacations_list)
                df_vac.to_excel(writer, index=False, sheet_name="Отпуска")

            workbook = writer.book
            header_fmt = workbook.add_format({"bold": True, "bg_color": "#B159B0", "border": 1})
            
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                if sheet_name == "Сотрудники": cur_df = df_emp
                elif sheet_name == "Проекты": cur_df = df_prj
                else: cur_df = df_vac

                for col_num, value in enumerate(cur_df.columns.values):
                    worksheet.write(0, col_num, value, header_fmt)
                    worksheet.set_column(col_num, col_num, 20)

        output.seek(0)
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": 'attachment; filename="export.xlsx"'}
        )