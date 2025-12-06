import os
import shutil
from uuid import uuid4

from PIL import Image, ImageOps
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.models.static import FileOrm


class StaticRepository:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def find_index(self, path: str, format: str) -> int:
        x = True
        z = str(uuid4())

        while x:
            try:
                os.stat(f"{path}/{z}.{format}")
                z = str(uuid4())
            except Exception:
                x = False

        return z

    async def save_video(
        self,
        file: bytes,
        path: str,
    ):
        try:
            os.stat(path)
            shutil.rmtree(path)
        except Exception:
            os.makedirs(
                "/".join(path.split("/")[0:-1]),
                exist_ok=True,
            )

        open(path, "wb").write(file)

    async def save_img(
        self,
        file: bytes,
        path: str,
    ):
        try:
            os.stat(path)
            shutil.rmtree(path)
        except Exception:
            os.makedirs(
                "/".join(path.split("/")[0:-1]),
                exist_ok=True,
            )

        open(path, "wb").write(file)

        ImageOps.exif_transpose(Image.open(path)).save(
            fp=path,
            format="webp",
            optimize=True,
        )

    async def save_audio(
        self,
        file: bytes,
        path: str,
    ):
        try:
            os.stat(path)
            shutil.rmtree(path)
        except Exception:
            os.makedirs(
                "/".join(path.split("/")[0:-1]),
                exist_ok=True,
            )

        open(path, "wb").write(file)

    async def save_doc(
        self,
        file: bytes,
        path: str,
    ):
        try:
            os.stat(path)
            shutil.rmtree(path)
        except Exception:
            os.makedirs(
                "/".join(path.split("/")[0:-1]),
                exist_ok=True,
            )

        open(path, "wb").write(file)

    async def get(
        self,
        id: int,
    ) -> FileOrm | None:
        return (
            await self.session.execute(select(FileOrm).where(FileOrm.id == id))
        ).scalar()

    async def delete(
        self,
        id: int,
    ):
        file_orm = (
            await self.session.execute(select(FileOrm).where(FileOrm.id == id))
        ).scalar()

        if file_orm:
            try:
                if os.path.exists(file_orm.path):
                    if os.path.isfile(file_orm.path):
                        os.remove(file_orm.path)
                    else:
                        shutil.rmtree(file_orm.path)

            except OSError:
                pass

            await self.session.delete(file_orm)
            await self.session.flush()
