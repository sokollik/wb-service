from sqlalchemy.ext.asyncio import AsyncSession

from core.common.common_exc import NotFoundHttpException
from core.common.common_repo import CommonRepository
from core.models.document import FolderOrm
from core.repositories.folder_repo import FolderRepository
from core.schemas.folder_schema import FolderCreateSchema, FolderUpdateSchema


class FolderService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.folder_repo = FolderRepository(session=session)
        self.common_repo = CommonRepository(session=session)

    async def get_folder(self, folder_id: int) -> FolderOrm:
        folder = await self.folder_repo.get_by_id(folder_id)
        if not folder:
            raise NotFoundHttpException(name="folder")
        return folder

    async def get_children(self, parent_id: int | None) -> list[FolderOrm]:
        return await self.folder_repo.get_children(parent_id)

    async def get_tree(self, root_id: int | None = None) -> list[dict]:
        if root_id:
            root = await self.get_folder(root_id)
            folders = await self.folder_repo.get_descendants(root.path)
        else:
            folders = await self.common_repo.get_all_scalars(FolderOrm)

        nodes = {f.id: {"id": f.id, "name": f.name, "path": f.path, "children": []} for f in folders}
        tree = []
        for f in folders:
            node = nodes[f.id]
            if f.parent_id and f.parent_id in nodes:
                nodes[f.parent_id]["children"].append(node)
            else:
                tree.append(node)
        return tree

    async def create_folder(self, data: FolderCreateSchema, created_by: str) -> int:
        parent_path = "/"
        if data.parent_id:
            parent = await self.get_folder(data.parent_id)
            parent_path = parent.path

        folder = await self.common_repo.add(
            orm_instance=FolderOrm(
                name=data.name,
                parent_id=data.parent_id,
                path="/",
                created_by=created_by,
            )
        )

        folder.path = f"{parent_path}{folder.id}/"
        await self.session.flush()
        return folder.id

    async def update_folder(self, folder_id: int, data: FolderUpdateSchema) -> FolderOrm:
        folder = await self.get_folder(folder_id)

        if data.name is not None:
            folder.name = data.name

        if data.parent_id is not None:
            parent = await self.get_folder(data.parent_id)
            old_path = folder.path
            new_path = f"{parent.path}{folder.id}/"
            folder.parent_id = data.parent_id
            folder.path = new_path

            descendants = await self.folder_repo.get_descendants(old_path)
            for desc in descendants:
                if desc.id != folder.id:
                    desc.path = desc.path.replace(old_path, new_path, 1)

        await self.session.flush()
        return folder

    async def delete_folder(self, folder_id: int):
        await self.get_folder(folder_id)
        await self.common_repo.delete(FolderOrm, FolderOrm.id == folder_id)
