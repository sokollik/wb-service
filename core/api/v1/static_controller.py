from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, Query, UploadFile
from fastapi.responses import FileResponse
from fastapi_restful.cbv import cbv
from sqlalchemy.ext.asyncio import AsyncSession
from core.common.common_exc import NotAllowedHttpException
from core.schemas.static_schema import UploadSchema
from core.services.static_service import StaticService
from core.utils.common_util import exception_handler
from core.utils.db_util import get_session_obj

static_router = APIRouter()


@cbv(static_router)
class StaticController:
    def __init__(
        self,
        back: BackgroundTasks,
        lang: Literal["ru", "en"] = Query(
            default="ru",
            description="Language code",
        ),
        session: AsyncSession = Depends(get_session_obj),
    ):
        self.lang = lang
        self.back = back
        self.session = session

        self.static_service = StaticService(
            lang=lang,
            back=back,
            session=session,
        )

    @static_router.post(
        "/add",
        tags=["static"],
    )
    @exception_handler
    async def static_upload(
        self,
        eid: int,
        file: UploadFile,
        data: UploadSchema = Depends(),
        
    ) -> int:
        """
        info:
        - route for uploading static files
        - type is either "video", "image", "audio", or "document"

        types:
        - document: pdf
        - image: webp, jpg, jpeg, png
        - video: mp4
        - audio: mp3, mpeg
        """

        # if data.created_for:
        #     if _.role.name not in ["admin", "expert"]:
        #         raise NotAllowedHttpException(lang=self.lang)

        #     created_for = data.created_for

        # else:
        #     created_for = _.id

        file_ext = await self.static_service.validate(
            file=file,
            type=data.type,
        )

        return await self.static_service.upload(
            created_by=eid,
            # created_for=created_for,
            type=data.type,
            name=data.name,
            file=file,
            file_ext=file_ext,
        )

    @static_router.get(
        "/get",
        tags=["static"],
    )
    @exception_handler
    async def static_get(
        self,
        id: int,
        # _: UserSchema = Depends(token_service.login_required),
    ) -> FileResponse:
        """
        info:
        - route for getting static files
        """

        return await self.static_service.get(
            id=id,
            # client=_,
        )

    @static_router.delete(
        "/delete",
        tags=["static"],
    )
    @exception_handler
    async def static_delete(
        self,
        id: int,
        eid: int,
    ):
        """
        info:
        - route for deleting static files
        """

        if not await self.static_service.can_delete(
            id=id,
            client_id=eid,
        ):
            raise NotAllowedHttpException(lang=self.lang)

        await self.static_service.delete(id=id)
