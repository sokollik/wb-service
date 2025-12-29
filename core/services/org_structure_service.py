from sqlalchemy.ext.asyncio import AsyncSession
import json
from pydantic.json import pydantic_encoder

from core.common.common_exc import (
    NotFoundHttpException,
    WrongParametersHttpException,
)
from core.common.common_repo import CommonRepository
from core.models.org_structure import OrgUnitOrm, OrgChangeLogOrm
from core.models.enums import ProfileOperationType
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

    async def _log_change(
        self,
        org_unit_id: int,
        changed_by_eid: int,
        field_name: str,
        old_value,
        new_value,
        operation: ProfileOperationType,
    ):
        def to_json(val):
            if isinstance(val, str):
                return val
            return json.dumps(val, default=pydantic_encoder, ensure_ascii=False)

        await self.common.add(
            OrgChangeLogOrm(
                org_unit_id=org_unit_id,
                changed_by_eid=changed_by_eid,
                field_name=field_name,
                old_value=to_json(old_value) if old_value is not None else None,
                new_value=to_json(new_value) if new_value is not None else None,
                operation=operation,
            )
        )
        
    async def create_org_unit(
        self, data: OrgUnitCreateSchema, changed_by_eid: int
    ) -> dict:
        org_unit = OrgUnitOrm(**data.model_dump())
        
        await self.common.add(org_unit)
        await self._log_change(
            org_unit_id=org_unit.id,
            changed_by_eid=changed_by_eid,
            field_name="all",
            old_value=None,
            new_value=data.model_dump(),
            operation=ProfileOperationType.CREATE,
        )
        return {"id": org_unit.id}

    async def get_org_unit(self, unit_id: int) -> OrgUnitBaseSchema:
        units = await self.org_structure_repo.get_org_units(id=unit_id)
        if not units:
            raise NotFoundHttpException(name="org_unit")
        unit_dict = dict(units[0])
        unit_dict = self._map_manager(unit_dict)
        return OrgUnitBaseSchema.model_validate(unit_dict)

    async def update_org_unit(
        self, unit_id: int, data: OrgUnitUpdateSchema, changed_by_eid: int
    ) -> None:
        org_unit = await self.common.get_one(OrgUnitOrm, OrgUnitOrm.id == unit_id)
        if not org_unit:
            raise NotFoundHttpException(name="org_unit")

        update_data = data.model_dump(exclude_unset=True)
        if update_data:
            for field, new_value in update_data.items():
                old_value = getattr(org_unit, field)
                if old_value != new_value:
                    await self._log_change(
                        org_unit_id=unit_id,
                        changed_by_eid=changed_by_eid,
                        field_name=field,
                        old_value=old_value,
                        new_value=new_value,
                        operation=ProfileOperationType.UPDATE,
                    )
            await self.common.update_stmt(
                table=OrgUnitOrm,
                where_stmt=(OrgUnitOrm.id == unit_id),
                values=update_data,
            )

    async def delete_org_unit(self, unit_id: int, changed_by_eid: int) -> None:
        all_units = await self.org_structure_repo.get_org_units()
        units_by_id = {u["id"]: u for u in all_units}

        def collect_descendants(current_id):
            descendants = []
            for unit in all_units:
                if unit["parent_id"] == current_id:
                    descendants.append(unit)
                    descendants.extend(collect_descendants(unit["id"]))
            return descendants

        org_unit = units_by_id.get(unit_id)
        if not org_unit:
            raise NotFoundHttpException(name="org_unit")

        descendants = collect_descendants(unit_id)
        
        for unit in descendants:
            await self._log_change(
                org_unit_id=unit["id"],
                changed_by_eid=changed_by_eid,
                field_name="all",
                old_value={
                    "name": unit["name"],
                    "unit_type": str(unit["unit_type"]),
                    "parent_id": unit["parent_id"],
                    "manager_eid": unit.get("manager_eid"),
                    "is_temporary": unit["is_temporary"],
                    "start_date": str(unit["start_date"]) if unit["start_date"] else None,
                    "end_date": str(unit["end_date"]) if unit["end_date"] else None,
                },
                new_value=None,
                operation=ProfileOperationType.DELETE,
            )

        await self._log_change(
            org_unit_id=unit_id,
            changed_by_eid=changed_by_eid,
            field_name="all",
            old_value={
                "name": org_unit["name"],
                "unit_type": str(org_unit["unit_type"]),
                "parent_id": org_unit["parent_id"],
                "manager_eid": org_unit.get("manager_eid"),
                "is_temporary": org_unit["is_temporary"],
                "start_date": str(org_unit["start_date"]) if org_unit["start_date"] else None,
                "end_date": str(org_unit["end_date"]) if org_unit["end_date"] else None,
            },
            new_value=None,
            operation=ProfileOperationType.DELETE,
        )

        deleted = await self.common.delete(OrgUnitOrm, OrgUnitOrm.id == unit_id)
        if not deleted:
            raise NotFoundHttpException(name="org_unit")
        return None

    async def get_org_unit_edit_log(self, unit_id: int):
        logs = await self.common.get_all_scalars(
            OrgChangeLogOrm,
            where_stmt=OrgChangeLogOrm.org_unit_id == unit_id,
        )
        processed_logs = []
        for log in logs:

            def try_json(val):
                if val is None:
                    return None
                try:
                    return json.loads(val)
                except (TypeError, json.JSONDecodeError):
                    return val

            log_data = {
                "id": log.id,
                "org_unit_id": log.org_unit_id,
                "changed_by_eid": log.changed_by_eid,
                "changed_at": log.changed_at,
                "field_name": log.field_name,
                "operation": log.operation,
                "old_value": try_json(log.old_value),
                "new_value": try_json(log.new_value),
            }
            processed_logs.append(log_data)
        return processed_logs

    async def set_manager(
        self, unit_id: int, manager_eid: int, changed_by_eid: int
    ) -> OrgUnitBaseSchema:
        org_unit = await self.common.get_one(OrgUnitOrm, OrgUnitOrm.id == unit_id)
        if not org_unit:
            raise NotFoundHttpException(name="org_unit")

        old_manager_eid = org_unit.manager_eid
        org_unit.manager_eid = manager_eid
        await self.common.update(org_unit)

        await self._log_change(
            org_unit_id=unit_id,
            changed_by_eid=changed_by_eid,
            field_name="manager_eid",
            old_value=old_manager_eid,
            new_value=manager_eid,
            operation=ProfileOperationType.UPDATE,
        )

        rows = await self.org_structure_repo.get_org_units(id=unit_id)
        unit_dict = dict(rows[0])
        unit_dict = self._map_manager(unit_dict)
        return OrgUnitBaseSchema.model_validate(unit_dict)
