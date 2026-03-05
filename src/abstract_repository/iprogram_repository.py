from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from models.program import Program


class IProgramRepository(ABC):
    @abstractmethod
    async def get_list(self) -> list[Program]:
        pass

    @abstractmethod
    async def get_by_id(self, program_id: int) -> Program | None:
        pass

    @abstractmethod
    async def add(self, program: Program) -> Program:
        pass

    @abstractmethod
    async def update(self, update_program: Program) -> None:
        pass

    @abstractmethod
    async def delete(self, program_id: int) -> None:
        pass

    @abstractmethod
    async def get_by_venues(
        self, start_venue_id: int, end_venue_id: int, transfer_type: str
    ) -> Program | None:
        pass

    @abstractmethod
    async def change_transfer_type(
        self, program_id: int, new_transfer_type: str
    ) -> Program | None:
        pass
