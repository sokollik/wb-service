import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models.emploee import EmployeeOrm
from core.models.org_structure import OrgUnitOrm
from core.models.profile import ProfileOrm
from core.services.elastic_search_service import EmployeeElasticsearchService

logger = logging.getLogger(__name__)


class EmployeeSyncService:
    def __init__(
        self,
        db_session: AsyncSession,
        es_service: EmployeeElasticsearchService,
    ):
        self.db = db_session
        self.es = es_service

    async def prepare_employee_for_indexing(
        self,
        employee: EmployeeOrm,
        profile: ProfileOrm = None,
        org_unit: OrgUnitOrm = None,
    ):
        if profile is None:
            profile_result = await self.db.execute(
                select(ProfileOrm).where(
                    ProfileOrm.employee_id == employee.eid
                )
            )
            profile = profile_result.scalar_one_or_none()

        if org_unit is None and employee.organization_unit:
            org_unit_result = await self.db.execute(
                select(OrgUnitOrm).where(
                    OrgUnitOrm.id == employee.organization_unit
                )
            )
            org_unit = org_unit_result.scalar_one_or_none()

        return {
            "eid": str(employee.eid),
            "full_name": employee.full_name,
            "position": employee.position,
            "work_email": employee.work_email,
            "work_phone": employee.work_phone or "",
            "organization_unit_id": (
                str(employee.organization_unit)
                if employee.organization_unit
                else ""
            ),
            "organization_unit_name": org_unit.name if org_unit else "",
            "work_band": employee.work_band or "",
            "is_fired": employee.is_fired,
            "hire_date": (
                employee.hire_date.isoformat() if employee.hire_date else ""
            ),
            "indexed_at": datetime.now().isoformat(),
        }

    async def sync_employee(self, eid: int):
        try:
            emp_result = await self.db.execute(
                select(EmployeeOrm).where(EmployeeOrm.eid == eid)
            )
            employee = emp_result.scalar_one_or_none()

            if not employee:
                self.es.delete_employee(eid)
                return

            emp_data = await self.prepare_employee_for_indexing(employee)
            self.es.index_employee(emp_data)

        except Exception as e:
            logger.error(f"Error syncing employee {eid}: {e}")

    async def sync_all_employees(self):
        try:
            result = await self.db.execute(
                select(EmployeeOrm).where(EmployeeOrm.is_fired == False)
            )
            employees = result.scalars().all()

            if not employees:
                logger.warning("No active employees found")
                return 0

            employees_data = []
            for emp in employees:
                try:
                    emp_data = await self.prepare_employee_for_indexing(emp)
                    employees_data.append(emp_data)
                except Exception as e:
                    logger.error(f"Error preparing employee {emp.eid}: {e}")

            if employees_data:
                self.es.bulk_index_employees(employees_data)
                return len(employees_data)

            return 0

        except Exception as e:
            logger.error(f"Error during sync: {e}")
            return 0

    async def sync_if_empty(self):
        try:
            stats = self.es.get_index_stats()

            if stats.get("document_count", 0) == 0:
                logger.info("Index is empty, starting auto-sync")
                count = await self.sync_all_employees()
                if count > 0:
                    logger.info(f"Auto-sync completed: {count} employees")
                return count
            else:
                return stats["document_count"]

        except Exception as e:
            logger.error(f"Error in sync if empty: {e}")
            return 0

    async def update_employee_on_profile_change(self, employee_id: int):
        await self.sync_employee(employee_id)

    async def update_employee_on_unit_change(self, unit_id: int):
        try:
            result = await self.db.execute(
                select(EmployeeOrm).where(
                    EmployeeOrm.organization_unit == unit_id
                )
            )
            employees = result.scalars().all()

            for emp in employees:
                await self.sync_employee(emp.eid)

        except Exception as e:
            logger.error(f"Error updating employees for unit {unit_id}: {e}")