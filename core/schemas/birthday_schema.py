from datetime import date
from typing import List
from pydantic import BaseModel, Field


class BirthdaySchema(BaseModel):
    eid: int = Field(..., description="ID работника")
    full_name: str = Field(...)
    department: str = Field(...)
    birth_date: date = Field(...)
    
class BirthdayListSchema(BaseModel):
    birthdays: List[BirthdaySchema]