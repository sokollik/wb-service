from sqlalchemy.ext.asyncio import AsyncSession

from core.common.common_exc import (
    NotFoundHttpException,
    WrongParametersHttpException,
)
from core.common.common_repo import CommonRepository
from core.models.org_structure import OrgUnitOrm
from core.repositories.org_structure_repo import OrgStructureRepository
from core.schemas.org_structure_schema import (
    OrgUnitHierarchySchema,
    OrgUnitManagerSchema,
)
from core.services.elastic_sync_service import EmployeeSyncService
from core.services.elastic_search_service import EmployeeElasticsearchService

class OrgStructureService:

    def __init__(self, session: AsyncSession, es_service: EmployeeElasticsearchService):
        self.session = session
        self.common = CommonRepository(session=self.session)
        self.org_structure_repo = OrgStructureRepository(session=self.session)
        self.es_service = es_service
        self.sync_service = EmployeeSyncService(
            db_session=self.session,
            es_service=self.es_service
        )

    async def get_org_structure_hierarchy(self):
        all_units_mappings = await self.org_structure_repo.get_org_units()

        if not all_units_mappings:
            return []
        units_by_id = {}
        root_units = []

        for row_mapping in all_units_mappings:

            unit_dict = dict(row_mapping)

            manager_data = None
            if unit_dict["manager_eid"] is not None:
                manager_data = OrgUnitManagerSchema(
                    eid=unit_dict["manager_eid"],
                    full_name=unit_dict["manager_full_name"],
                    position=unit_dict["manager_position"],
                ).model_dump()

            del unit_dict["manager_eid"]
            del unit_dict["manager_full_name"]
            del unit_dict["manager_position"]

            unit_dict["manager"] = manager_data
            unit_dict["children"] = []

            units_by_id[unit_dict["id"]] = unit_dict
        for unit_id, unit_dict in units_by_id.items():
            parent_id = unit_dict.get("parent_id")

            if parent_id is None:
                root_units.append(unit_dict)

            elif parent_id in units_by_id:
                units_by_id[parent_id]["children"].append(unit_dict)
        return [
            OrgUnitHierarchySchema.model_validate(unit) for unit in root_units
        ]

    async def move_org_unit(
        self, unit_id: int, new_parent_id: int | None = None
    ):
        if unit_id == new_parent_id:
            raise WrongParametersHttpException(params="new_parent_id")

        unit = await self.org_structure_repo.get_org_units(id=unit_id)
        if not unit:
            raise NotFoundHttpException(name="org_unit")

        if new_parent_id is not None:
            new_parent = await self.org_structure_repo.get_org_units(
                id=new_parent_id
            )
            if not new_parent:
                raise NotFoundHttpException(name="org_unit")

            is_cycle = await self.org_structure_repo.is_parent(
                parent_id=unit_id, child_id=new_parent_id
            )
            if is_cycle:
                raise WrongParametersHttpException(params="new_parent_id")

        await self.common.update_stmt(
            table=OrgUnitOrm,
            where_stmt=(OrgUnitOrm.id == unit_id),
            values={"parent_id": new_parent_id},
        )

        await self.sync_service.sync_all_employees()
 