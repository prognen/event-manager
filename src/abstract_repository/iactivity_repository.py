from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from models.activity import Activity


class IActivityRepository(ABC):
    @abstractmethod
    async def get_list(self) -> list[Activity]:
        pass

    @abstractmethod
    async def get_by_id(self, activity_id: int) -> Activity | None:
        pass

    @abstractmethod
    async def add(self, activity: Activity) -> Activity:
        pass

    @abstractmethod
    async def update(self, update_activity: Activity) -> None:
        pass

    @abstractmethod
    async def delete(self, activity_id: int) -> None:
        pass
