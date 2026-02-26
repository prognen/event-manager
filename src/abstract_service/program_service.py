from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from models.program import Program


class IProgramService(ABC):
    @abstractmethod
    async def get_by_id(self, program_id: int) -> Program | None:
        pass

    @abstractmethod
    async def add(self, program: Program) -> Program:
        pass

    @abstractmethod
    async def update(self, updated_program: Program) -> Program:
        pass

    @abstractmethod
    async def delete(self, program_id: int) -> None:
        pass
