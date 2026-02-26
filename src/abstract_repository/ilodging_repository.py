from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from models.lodging import Lodging


class ILodgingRepository(ABC):
    @abstractmethod
    async def get_list(self) -> list[Lodging]:
        pass

    @abstractmethod
    async def get_by_id(self, lodging_id: int) -> Lodging | None:
        pass

    @abstractmethod
    async def add(self, lodging: Lodging) -> Lodging:
        pass

    @abstractmethod
    async def update(self, update_lodging: Lodging) -> None:
        pass

    @abstractmethod
    async def delete(self, lodging_id: int) -> None:
        pass
