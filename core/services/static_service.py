from typing import Literal

from fastapi import BackgroundTasks, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from core.common.common_exc import (
    NotFoundHttpException,
    WrongParametersHttpException,
)
from core.common.common_repo import CommonRepository
from core.config.settings import get_settings
from core.models.enums import FileType
from core.models.static import FileOrm
from core.exceptions.static_exc import (
    IncorrectFileTypeHttpException,
    UploadingFileTooBigHttpException,
)
from core.repositories.static_repo import StaticRepository
from core.utils.text_util import get_extension, get_mime_type

settings = get_settings()


class StaticService:
    def __init__(
        self,
        session: AsyncSession,
        back: BackgroundTasks,
        lang: Literal["ru", "en"],
    ):
        self.lang = lang
        self.back = back
        self.session = session

        self.static_repo = StaticRepository(session=session)
        self.common_repo = CommonRepository(session=session)

    async def get(
        self,
        id: int,
        # client: ClientOrm,
    ) -> FileResponse:
        file_orm = await self.static_repo.get(id=id)

        if file_orm == None:
            raise NotFoundHttpException(
                lang=self.lang,
                name="file",
            )

        # if file_orm.created_for != client.id:
        #     raise NotAllowedHttpException(
        #         lang=self.lang,
        #         name="file",
        #     )

        path: str = file_orm.path
        file_ext = path.split(".")[-1].lower()

        if file_orm.name is not None:
            filename = file_orm.name + "." + file_ext

        else:
            filename = None

        media_type = await get_mime_type(extension=file_ext)

        return FileResponse(
            path=path,
            filename=filename,
            media_type=media_type,
        )

    async def validate(
        self,
        file: UploadFile,
        type: FileType,
    ):
        match type:
            case FileType.document:
                allowed_types = [
                    "pdf",
                    (
                        "vnd.openxmlformats-officedocument"
                        + ".wordprocessingml.document"
                    ),  # .docx
                    (
                        "vnd.openxmlformats-officedocument" + ".spreadsheetml.sheet"
                    ),  # .xlsx
                    (
                        "vnd.openxmlformats-officedocument"
                        + ".presentationml.presentation"
                    ),  # .pptx
                ]
                if file.content_type not in ["application/" + x for x in allowed_types]:
                    raise IncorrectFileTypeHttpException(
                        allowed_types=allowed_types,
                        lang=self.lang,
                    )

            case FileType.image:
                allowed_types = [
                    "webp",
                    "jpg",
                    "jpeg",
                    "png",
                ]

                if file.content_type not in ["image/" + x for x in allowed_types]:
                    raise IncorrectFileTypeHttpException(
                        allowed_types=allowed_types,
                        lang=self.lang,
                    )

            case FileType.video:
                allowed_types = [
                    "mp4",
                ]
                if file.content_type not in ["video/" + x for x in allowed_types]:
                    raise IncorrectFileTypeHttpException(
                        allowed_types=allowed_types,
                        lang=self.lang,
                    )

            case FileType.audio:
                allowed_types = [
                    "mp3",
                    "mpeg",
                ]

                if file.content_type not in ["audio/" + x for x in allowed_types]:
                    raise IncorrectFileTypeHttpException(
                        allowed_types=allowed_types,
                        lang=self.lang,
                    )

            case _:
                raise WrongParametersHttpException(params="type", lang=self.lang)

        return await get_extension(content_type=file.content_type)

    async def upload(
        self,
        created_by: int,
        # created_for: int | None,
        type: FileType,
        name: str | None,
        file: UploadFile,
        file_ext: str,
    ) -> int:
        path = None

        size = file.size / 10**6  # MB

        if size > 50:
            raise UploadingFileTooBigHttpException(lang=self.lang)

        filename = name or ".".join(file.filename.split(".")[:-1])
        base_path = f"{settings.STATIC_PATH}/{type.value}"
        # format = await type_handler(type=type.name)
        index = await self.static_repo.find_index(
            path=base_path,
            format=file_ext,
        )

        match type:
            case FileType.video:
                path = f"{base_path}/{index}.{file_ext}"

                self.back.add_task(
                    self.static_repo.save_video,
                    **{
                        "file": file.file.read(),
                        "path": path,
                    },
                )

            case FileType.image:
                path = f"{base_path}/{index}.webp"

                self.back.add_task(
                    self.static_repo.save_img,
                    **{
                        "file": file.file.read(),
                        "path": path,
                    },
                )

            case FileType.audio:
                path = f"{base_path}/{index}.{file_ext}"

                self.back.add_task(
                    self.static_repo.save_audio,
                    **{
                        "file": file.file.read(),
                        "path": path,
                    },
                )

            case FileType.document:
                path = f"{base_path}/{index}.{file_ext}"

                self.back.add_task(
                    self.static_repo.save_doc,
                    **{
                        "file": file.file.read(),
                        "path": path,
                    },
                )

            case _:
                raise WrongParametersHttpException(lang=self.lang)

        return (
            await self.common_repo.add(
                orm_instance=FileOrm(
                    path=path,
                    name=filename,
                    # created_for=created_for,
                    created_by=created_by,
                ),
                where_stmt=FileOrm.path == path,
            )
        ).id

    async def can_delete(
        self,
        id: int,
        client_id: int,
    ) -> bool:
        file_orm = await self.static_repo.get(id=id)

        if file_orm == None:
            raise NotFoundHttpException(
                lang=self.lang,
                name="file",
            )

        if client_id == file_orm.created_by:
            return True

        return False

    async def delete(self, id: int):
        await self.static_repo.delete(id=id)
