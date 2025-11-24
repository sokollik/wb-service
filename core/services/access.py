from sqlalchemy import and_, exists, select
from sqlalchemy.orm import Session

from core.models.employee import EmployeeOrm, DepartmentOrm
from core.models.profile import ProfileOrm


class AccessService:

    def __init__(self, session: Session, current_user_eid: int):
        self.session = session
        self.current_user_eid = current_user_eid

    def can_view_personal_phone(self, target_employee_eid: int) -> bool:
        same_department = exists().where(
            and_(
                EmployeeOrm.eid == self.current_user_eid,
                EmployeeOrm.department_id == (
                    select(EmployeeOrm.department_id)
                    .where(EmployeeOrm.eid == target_employee_eid)
                    .scalar_subquery()
                )
            )
        )
        is_manager = exists().where(
            and_(
                EmployeeOrm.eid == target_employee_eid,
                EmployeeOrm.manager_eid == self.current_user_eid
            )
        )
        is_hrbp = exists().where(
            and_(
                EmployeeOrm.eid == target_employee_eid,
                EmployeeOrm.hrbp_eid == self.current_user_eid
            )
        )

        query = select(1).where(
            same_department | is_manager | is_hrbp
        )

        return self.session.execute(query).first() is not None

    def get_employees_with_access_to_personal_phone(self):
        current_user_dept = (
            select(EmployeeOrm.department_id)
            .where(EmployeeOrm.eid == self.current_user_eid)
            .scalar_subquery()
        )
        same_department_cond = EmployeeOrm.department_id == current_user_dept
        managed_by_user_cond = EmployeeOrm.manager_eid == self.current_user_eid
        hrbp_for_user_cond = EmployeeOrm.hrbp_eid == self.current_user_eid

        query = select(EmployeeOrm.eid).where(
            same_department_cond | managed_by_user_cond | hrbp_for_user_cond
        )

        result = self.session.execute(query)
        return [row[0] for row in result]