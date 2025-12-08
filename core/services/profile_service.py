import json
from datetime import date

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
                    old_value=await self._serialize_value(profile.personal_phone),
                    new_value=await self._serialize_value(profile_data.personal_phone),
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
                    new_value=await self._serialize_value(profile_data.telegram),
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
                    new_value=await self._serialize_value(profile_data.about_me),
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
                    new_value=await self._serialize_value(profile_data.avatar_id),
                    operation=ProfileOperationType.UPDATE,
                )
            )
        

        await self.common.update(
            orm_instance=ProfileOrm(
                id=profile.id,
                avatar_id=profile_data.avatar_id,
                personal_phone=profile_data.personal_phone or profile.personal_phone,
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
                                    str(project.start_d) if project.start_d else None
                                ),
                                "end_d": (
                                    str(project.end_d) if project.end_d else None
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
        """
        Универсально конвертирует строковое значение из БД в объект Python (словарь/список),
        если это валидный JSON. Иначе возвращает строку.
        """
        if value is None:
            return None

        try:
            # Пытаемся декодировать JSON.
            # Добавлено исключение TypeError для обработки не-строковых значений.
            decoded = json.loads(value)
            return decoded
        except (json.JSONDecodeError, TypeError):
            # Если декодирование не удалось (невалидный JSON) или 'value' не был строкой,
            # возвращаем исходное значение.
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

        # Преобразуем ORM-объекты в словари, выполняя десериализацию JSON
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
        print(processed_logs)
        # Возвращаем список словарей. Pydantic сможет обработать этот список
        # и корректно сериализовать вложенные словари/списки в JSON.
        return processed_logs
