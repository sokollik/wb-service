from io import BytesIO
from typing import List

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from fastapi_restful.cbv import cbv
from sqlalchemy.ext.asyncio import AsyncSession

from core.api.deps import CheckPermissionDep, CurrentUser
from core.schemas.org_structure_schema import (
    OrgChangeLogShema,
    OrgUnitCreateSchema,
    OrgUnitHierarchySchema,
    OrgUnitUpdateSchema,
)
from core.services.elastic_search_service import EmployeeElasticsearchService
from core.services.org_structure_service import OrgStructureService
from core.utils.common_util import exception_handler
from core.utils.db_util import get_session_obj
from core.utils.elastic_search_util import get_elasticsearch_service

org_structure_controller = APIRouter()


@cbv(org_structure_controller)
class OrgStructureController:
    def __init__(
        self,
        session: AsyncSession = Depends(get_session_obj),
        es_service: EmployeeElasticsearchService = Depends(
            get_elasticsearch_service
        ),
    ):
        self.session = session
        self.es_service = es_service
        self.org_structure_service = OrgStructureService(
            session=session, es_service=self.es_service
        )

    @org_structure_controller.get("/hierarchy")
    @exception_handler
    async def get_full_org_hierarchy(
        self,
        _current_user: CurrentUser = Depends(CheckPermissionDep("org", "read")),
    ) -> List[OrgUnitHierarchySchema]:
        return await self.org_structure_service.get_org_structure_hierarchy()

    @org_structure_controller.get(
        "/hierarchy/export",
        summary="Экспорт иерархии подразделений и сотрудников в Excel",
        response_class=StreamingResponse,
    )
    @exception_handler
    async def export_org_hierarchy(
        self,
        _current_user: CurrentUser = Depends(CheckPermissionDep("org", "read")),
    ):
        excel_bytes = (
            await self.org_structure_service.export_org_hierarchy_to_excel()
        )
        return StreamingResponse(
            BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": 'attachment; filename="org_hierarchy.xlsx"'
            },
        )

    @org_structure_controller.put("/move")
    @exception_handler
    async def move_org_unit(
        self,
        unit_id: int,
        new_parent_id: int | None = None,
        _current_user: CurrentUser = Depends(CheckPermissionDep("org", "manage")),
    ):
        return await self.org_structure_service.move_org_unit(
            unit_id=unit_id, new_parent_id=new_parent_id, changed_by_eid=_current_user.eid
        )

    @org_structure_controller.post(
        "/units/add", summary="Создать подразделение"
    )
    @exception_handler
    async def create_org_unit(
        self,
        data: OrgUnitCreateSchema,
        current_user: CurrentUser = Depends(CheckPermissionDep("org", "manage")),
    ):
        return await self.org_structure_service.create_org_unit(
            data, current_user.eid
        )

    @org_structure_controller.get(
        "/units/get", summary="Получить подразделение по ID"
    )
    @exception_handler
    async def get_org_unit(
        self,
        unit_id: int,
        _current_user: CurrentUser = Depends(CheckPermissionDep("org", "read")),
    ):
        return await self.org_structure_service.get_org_unit(unit_id)

    @org_structure_controller.patch(
        "/units/update", summary="Обновить подразделение", status_code=204
    )
    @exception_handler
    async def update_org_unit(
        self,
        unit_id: int,
        data: OrgUnitUpdateSchema,
        current_user: CurrentUser = Depends(CheckPermissionDep("org", "manage")),
    ):
        await self.org_structure_service.update_org_unit(
            unit_id, data, current_user.eid
        )
        return

    @org_structure_controller.delete(
        "/units/delete", summary="Удалить подразделение", status_code=204
    )
    @exception_handler
    async def delete_org_unit(
        self,
        unit_id: int,
        current_user: CurrentUser = Depends(CheckPermissionDep("org", "manage")),
    ):
        await self.org_structure_service.delete_org_unit(
            unit_id, current_user.eid
        )
        return

    @org_structure_controller.patch(
        "/units/set_manager", summary="Назначить руководителя подразделения"
    )
    @exception_handler
    async def set_manager(
        self,
        unit_id: int,
        manager_eid: str,
        current_user: CurrentUser = Depends(CheckPermissionDep("org", "manage")),
    ):
        return await self.org_structure_service.set_manager(
            unit_id, manager_eid, current_user.eid
        )

    @org_structure_controller.delete(
        "/units/remove_manager",
        summary="Удалить назначенного руководителя подразделения",
    )
    @exception_handler
    async def remove_manager(
        self,
        unit_id: int,
        current_user: CurrentUser = Depends(
            CheckPermissionDep("org", "manage")
        ),
    ):
        return await self.org_structure_service.remove_manager(
            unit_id, current_user.eid
        )

    @org_structure_controller.post(
        "/units/add_employee",
        summary="Добавить сотрудника в подразделение",
        status_code=204,
    )
    @exception_handler
    async def add_employee(
        self,
        unit_id: int,
        employee_eid: str,
        current_user: CurrentUser = Depends(
            CheckPermissionDep("org", "manage")
        ),
    ):
        await self.org_structure_service.add_employee(
            unit_id, employee_eid, current_user.eid
        )
        return

    @org_structure_controller.delete(
        "/units/remove_employee",
        summary="Удалить сотрудника из подразделения",
        status_code=204,
    )
    @exception_handler
    async def remove_employee(
        self,
        unit_id: int,
        employee_eid: str,
        current_user: CurrentUser = Depends(
            CheckPermissionDep("org", "manage")
        ),
    ):
        await self.org_structure_service.remove_employee(
            unit_id, employee_eid, current_user.eid
        )
        return

    @org_structure_controller.get(
        "/units/log", summary="История изменений подразделения"
    )
    @exception_handler
    async def get_org_unit_edit_log(
        self,
        unit_id: int,
        _current_user: CurrentUser = Depends(CheckPermissionDep("org", "manage")),
    ) -> list[OrgChangeLogShema]:
        return await self.org_structure_service.get_org_unit_edit_log(unit_id)
