import os
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from fastapi_restful.cbv import cbv
from sqlalchemy.ext.asyncio import AsyncSession

from core.api.deps import CurrentUser, require_roles
from core.schemas.profile_schema import (
    ProfileChangeLogSchema,
    ProfileExportFilter,
    ProfileSchema,
    ProfileUpdateSchema,
    SearchResponse,
    SuggestResponse,
)
from core.services.elastic_search_service import EmployeeElasticsearchService
from core.services.profile_service import ProfileService
from core.utils.common_util import exception_handler
from core.utils.db_util import get_session_obj
from core.utils.elastic_search_util import get_elasticsearch_service

profile_controller = APIRouter()


@cbv(profile_controller)
class ProfileController:

    def __init__(
        self,
        session: AsyncSession = Depends(get_session_obj),
        es_service: EmployeeElasticsearchService = Depends(
            get_elasticsearch_service
        ),
    ):
        self.session = session
        self.es_service = es_service
        self.profile_service = ProfileService(
            session=session, es_service=es_service
        )

    @profile_controller.get("/me")
    @exception_handler
    async def view_profile(
        self,
        current_user: CurrentUser = Depends(
            require_roles(["employee", "hr", "admin"])
        ),
    ) -> ProfileSchema:
        return await self.profile_service.get_my_profile(eid=current_user.eid)

    @profile_controller.get("/share")
    @exception_handler
    async def share_profile(
        self,
        current_user: CurrentUser = Depends(require_roles(["employee"])),
    ) -> str:
        web_url = os.getenv("WEB_URL")
        return web_url + f"/profile/{current_user.eid}"

    @profile_controller.patch("/me")
    @exception_handler
    async def edit_profile(
        self,
        profile_data: ProfileUpdateSchema,
        current_user: CurrentUser = Depends(require_roles(["employee"])),
    ):
        return await self.profile_service.update_profile(
            eid=current_user.eid, profile_data=profile_data
        )

    @profile_controller.get("/log")
    @exception_handler
    async def get_profile_edit_log(
        self,
        current_user: CurrentUser = Depends(require_roles(["employee"])),
    ) -> List[ProfileChangeLogSchema]:
        return await self.profile_service.get_profile_edit_log(
            eid=current_user.eid
        )

    @profile_controller.get("/export")
    @exception_handler
    async def export_profiles(
        self,
        config: ProfileExportFilter = Depends(),
        _current_user: CurrentUser = Depends(require_roles(["hr", "admin"])),
    ):
        return await self.profile_service.export_profiles_to_excel(config)

    @profile_controller.get("/search")
    @exception_handler
    async def search(
        self,
        q: Optional[str] = Query(
            None,
            description="Поисковый запрос (ФИО, должность, подразделение, email и т.д.)",
            min_length=0,
        ),
        from_: int = Query(0, ge=0, description="Offset для пагинации"),
        size: int = Query(
            10, ge=1, le=100, description="Количество результатов"
        ),
        _current_user: CurrentUser = Depends(require_roles(["employee"])),
    ) -> SearchResponse:
        result = self.es_service.search_employees(
            query=q,
            from_=from_,
            size=size,
        )
        return SearchResponse(**result)

    @profile_controller.get("/suggest")
    @exception_handler
    async def suggest_employees(
        self,
        q: str = Query(..., min_length=2, description="Начало поиска по ФИО"),
        size: int = Query(10, ge=1, le=50, description="Количество подсказок"),
        _current_user: CurrentUser = Depends(require_roles(["employee"])),
    ) -> SuggestResponse:
        suggestions = self.es_service.suggest_employees(query=q, size=size)
        return SuggestResponse(suggestions=suggestions)

    @profile_controller.get("/stats", name="search_stats")
    @exception_handler
    async def get_search_stats(
        self,
        _current_user: CurrentUser = Depends(require_roles(["employee"])),
    ):
        stats = self.es_service.get_index_stats()
        return stats
