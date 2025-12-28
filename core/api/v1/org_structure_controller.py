from typing import List

from fastapi import APIRouter, Depends
from fastapi_restful.cbv import cbv
from sqlalchemy.ext.asyncio import AsyncSession

from core.schemas.org_structure_schema import OrgUnitHierarchySchema
from core.services.org_structure_service import OrgStructureService
from core.utils.common_util import exception_handler
from core.utils.db_util import get_session_obj
from core.services.elastic_search_service import EmployeeElasticsearchService
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
    async def move_org_unit(
        self, unit_id: int, new_parent_id: int | None = None
    ):
        return await self.org_structure_service.move_org_unit(
            unit_id=unit_id, new_parent_id=new_parent_id
        )
