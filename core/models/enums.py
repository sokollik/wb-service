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

    from enum import Enum

class NewsCategory(Enum):
    OFFICIAL = "Официальные документы"
    HR = "HR-новости"
    IT = "IT-обновления"
    EVENTS = "События"
    TECH = "Технические работы"

class NewsStatus(Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"