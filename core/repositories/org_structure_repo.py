from sqlalchemy import alias, exists, select
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

    async def get_org_units(self, id: int | None = None):
        ManagerORM = alias(EmployeeOrm, name="manager")

        stmt = (
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
        if id is not None:
            stmt = stmt.where(OrgUnitOrm.id == id)

        result = await self.session.execute(stmt)

        return result.mappings().all()

    async def is_parent(self, parent_id: int, child_id: int) -> bool:
        recursive_cte = (
            select(OrgUnitOrm.id)
            .where(OrgUnitOrm.id == parent_id)
            .cte(name="descendants", recursive=True)
        )

        recursive_cte = recursive_cte.union_all(
            select(OrgUnitOrm.id).join(
                recursive_cte, OrgUnitOrm.parent_id == recursive_cte.c.id
            )
        )

        query = select(exists().where(recursive_cte.c.id == child_id))
        result = await self.session.execute(query)
        return result.scalar()
