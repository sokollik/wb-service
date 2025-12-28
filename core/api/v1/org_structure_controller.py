from typing import List

from fastapi import APIRouter, Depends
from fastapi_restful.cbv import cbv
from sqlalchemy.ext.asyncio import AsyncSession

from core.schemas.org_structure_schema import (
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
        self.org_structure_service = OrgStructureService(session=session, es_service=self.es_service)

    @org_structure_controller.get(
        "/hierarchy",
    )
    @exception_handler
    async def get_full_org_hierarchy(self) -> List[OrgUnitHierarchySchema]:
        return await self.org_structure_service.get_org_structure_hierarchy()

    @org_structure_controller.put(
        "/move",
    )
    @exception_handler
    async def move_org_unit(self, unit_id: int, new_parent_id: int | None = None):
        return await self.org_structure_service.move_org_unit(
            unit_id=unit_id, new_parent_id=new_parent_id
        )

    @org_structure_controller.post("/units/add", summary="Создать подразделение")
    @exception_handler
    async def create_org_unit(self, data: OrgUnitCreateSchema):
        return await self.org_structure_service.create_org_unit(data)

    @org_structure_controller.get("/units/get", summary="Получить подразделение по ID")
    @exception_handler
    async def get_org_unit(self, unit_id: int):
        return await self.org_structure_service.get_org_unit(unit_id)

    @org_structure_controller.patch(
        "/units/update", summary="Обновить подразделение", status_code=204
    )
    @exception_handler
    async def update_org_unit(self, unit_id: int, data: OrgUnitUpdateSchema):
        await self.org_structure_service.update_org_unit(unit_id, data)
        return

    @org_structure_controller.delete(
        "/units/delete", summary="Удалить подразделение", status_code=204
    )
    @exception_handler
    async def delete_org_unit(self, unit_id: int):
        await self.org_structure_service.delete_org_unit(unit_id)
        return

    @org_structure_controller.patch(
        "/units/set_manager", summary="Назначить руководителя подразделения"
    )
    @exception_handler
    async def set_manager(self, unit_id: int, manager_eid: int):
        return await self.org_structure_service.set_manager(unit_id, manager_eid)
