from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ProfileSchema(BaseModel):
    eid: int = Field(..., description="ID работника")
    full_name: str = Field(...)
    position: str = Field(...)