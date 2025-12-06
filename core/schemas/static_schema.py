from pydantic import BaseModel
from core.models.enums import FileType


class UploadSchema(BaseModel):
    type: FileType
    name: str | None = None
    created_for: int | None = None


class FileInfoSchema(BaseModel):
    file_id: int
