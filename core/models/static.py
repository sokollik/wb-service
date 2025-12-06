import sqlalchemy as sa
from sqlalchemy import Column, Integer, String

from core.models.base import Base


class FileOrm(Base):
    __tablename__ = "file"
    id = Column(
        sa.BigInteger, primary_key=True, autoincrement=True, nullable=False
    )
    name = Column(String)
    path = Column(String)
    created_by = Column(Integer)
