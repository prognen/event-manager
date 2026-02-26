from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from models.event import Event


Event.model_rebuild()


class IEventService(ABC):
    @abstractmethod
    async def get_by_id(self, event_id: int) -> Event | None:
        pass

    @abstractmethod
    async def get_all_events(self) -> list[Event]:
        pass

    @abstractmethod
    async def add(self, event: Event) -> Event:
        pass

    @abstractmethod
    async def update(self, update_event: Event) -> Event:
        pass

    @abstractmethod
    async def delete(self, event_id: int) -> None:
        pass
