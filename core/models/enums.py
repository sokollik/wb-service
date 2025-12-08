from enum import Enum


class ProfileOperationType(Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class FileType(Enum):
    video = "video"
    image = "image"
    audio = "audio"
    document = "document"
