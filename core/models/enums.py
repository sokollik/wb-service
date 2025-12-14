from enum import Enum


class ProfileOperationType(Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"

class OrgUnitType(Enum):
    DEPARTMENT = 'Department'
    MANAGEMENT = 'Management'
    DIVISION = 'Division'
    GROUP = 'Group'
    PROJECT_TEAM = 'ProjectTeam'

class FileType(Enum):
    video = "video"
    image = "image"
    audio = "audio"
    document = "document"