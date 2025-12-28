from sqlalchemy.ext.asyncio import AsyncSession

from core.common.common_exc import (
    NotFoundHttpException,
    WrongParametersHttpException,
    AlreadyExistsHttpException,
)
from core.common.common_repo import CommonRepository
from core.models.org_structure import OrgUnitOrm
from core.repositories.org_structure_repo import OrgStructureRepository
from core.schemas.org_structure_schema import (
    OrgUnitHierarchySchema,
    OrgUnitManagerSchema,
    OrgUnitCreateSchema,
    OrgUnitUpdateSchema,
    OrgUnitBaseSchema,
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

    def _map_manager(self, unit_dict: dict) -> dict:
        if unit_dict.get("manager_eid") is not None:
            unit_dict["manager"] = OrgUnitManagerSchema(
                eid=unit_dict.pop("manager_eid"),
                full_name=unit_dict.pop("manager_full_name", ""),
                position=unit_dict.pop("manager_position", ""),
            )
        else:
            unit_dict.pop("manager_eid", None)
            unit_dict.pop("manager_full_name", None)
            unit_dict.pop("manager_position", None)
            unit_dict["manager"] = None
        return unit_dict

    async def get_org_structure_hierarchy(self):
        all_units_mappings = await self.org_structure_repo.get_org_units()

        if not all_units_mappings:
            return []
        units_by_id = {}
        root_units = []

        for row_mapping in all_units_mappings:

            unit_dict = dict(row_mapping)
            unit_dict = self._map_manager(unit_dict)
            unit_dict["children"] = []

            units_by_id[unit_dict["id"]] = unit_dict
        for unit_id, unit_dict in units_by_id.items():
            parent_id = unit_dict.get("parent_id")

            if parent_id is None:
                root_units.append(unit_dict)

            elif parent_id in units_by_id:
                units_by_id[parent_id]["children"].append(unit_dict)
        return [OrgUnitHierarchySchema.model_validate(unit) for unit in root_units]

    async def move_org_unit(self, unit_id: int, new_parent_id: int | None = None):
        if unit_id == new_parent_id:
            raise WrongParametersHttpException(params="new_parent_id")

        unit = await self.org_structure_repo.get_org_units(id=unit_id)
        if not unit:
            raise NotFoundHttpException(name="org_unit")

        if new_parent_id is not None:
            new_parent = await self.org_structure_repo.get_org_units(id=new_parent_id)
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
 
        
    async def create_org_unit(self, data: OrgUnitCreateSchema) -> dict:
        org_unit = OrgUnitOrm(**data.model_dump())
        await self.common.add(org_unit)
        return {"id": org_unit.id}

    async def get_org_unit(self, unit_id: int) -> OrgUnitBaseSchema:
        units = await self.org_structure_repo.get_org_units(id=unit_id)
        if not units:
            raise NotFoundHttpException(name="org_unit")
        unit_dict = dict(units[0])
        unit_dict = self._map_manager(unit_dict)
        return OrgUnitBaseSchema.model_validate(unit_dict)

    async def update_org_unit(self, unit_id: int, data: OrgUnitUpdateSchema) -> None:
        org_unit = await self.common.get_one(OrgUnitOrm, OrgUnitOrm.id == unit_id)
        if not org_unit:
            raise NotFoundHttpException(name="org_unit")

        update_data = data.model_dump(exclude_unset=True)
        if update_data:
            await self.common.update_stmt(
                table=OrgUnitOrm,
                where_stmt=(OrgUnitOrm.id == unit_id),
                values=update_data,
            )

    async def delete_org_unit(self, unit_id: int) -> None:
        deleted = await self.common.delete(OrgUnitOrm, OrgUnitOrm.id == unit_id)
        if not deleted:
            raise NotFoundHttpException(name="org_unit")
        return None

    async def set_manager(self, unit_id: int, manager_eid: int) -> OrgUnitBaseSchema:
        org_unit = await self.common.get_one(OrgUnitOrm, OrgUnitOrm.id == unit_id)
        if not org_unit:
            raise NotFoundHttpException(name="org_unit")

        org_unit.manager_eid = manager_eid
        await self.common.update(org_unit)

        rows = await self.org_structure_repo.get_org_units(id=unit_id)
        unit_dict = dict(rows[0])
        unit_dict = self._map_manager(unit_dict)
        return OrgUnitBaseSchema.model_validate(unit_dict)
