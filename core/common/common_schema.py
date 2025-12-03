from typing import TypeVar


T = TypeVar("T")

class DependencyCheckSchema:
    def __init__(
        self,
        table: T,
        id: int,
    ):
        self.table = table
        self.id = id

