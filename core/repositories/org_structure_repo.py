from sqlalchemy import alias, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.common.common_repo import CommonRepository
from core.models.emploee import EmployeeOrm
from core.models.org_structure import OrgUnitOrm


class OrgStructureRepository:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session
        self.common = CommonRepository(session=self.session)

    async def get_org_units(self):
        ManagerORM = alias(EmployeeOrm, name="manager")

        query = (
            select(
                OrgUnitOrm.id.label("id"),
                OrgUnitOrm.name.label("name"),
                OrgUnitOrm.unit_type.label("unit_type"),
                OrgUnitOrm.parent_id.label("parent_id"),
                OrgUnitOrm.is_temporary.label("is_temporary"),
                OrgUnitOrm.start_date.label("start_date"),
                OrgUnitOrm.end_date.label("end_date"),
                ManagerORM.c.eid.label("manager_eid"),
                ManagerORM.c.full_name.label("manager_full_name"),
                ManagerORM.c.position.label("manager_position"),
            )
            .outerjoin(ManagerORM, ManagerORM.c.eid == OrgUnitOrm.manager_eid)
            .order_by(OrgUnitOrm.parent_id.is_(None).desc(), OrgUnitOrm.id)
        )

        result = await self.session.execute(query)

        return result.mappings().all()
