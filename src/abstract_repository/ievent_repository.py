from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Any

from models.activity import Activity
from models.lodging import Lodging
from models.event import Event
from models.user import User


class IEventRepository(ABC):
    @abstractmethod
    async def get_list(self) -> list[Event]:
        pass

    @abstractmethod
    async def get_by_id(self, event_id: int) -> Event | None:
        pass

    @abstractmethod
    async def add(self, event: Event) -> Event:
        pass

    @abstractmethod
    async def update(self, update_event: Event) -> None:
        pass

    @abstractmethod
    async def delete(self, event_id: int) -> None:
        pass

    @abstractmethod
    async def get_lodgings_by_event(self, event_id: int) -> list[Lodging]:
        pass

    @abstractmethod
    async def get_users_by_event(self, event_id: int) -> list[User]:
        pass

    @abstractmethod
    async def get_activities_by_event(self, event_id: int) -> list[Activity]:
        pass

    @abstractmethod
    async def get_event_by_session_id(self, session_id: int) -> Event | None:
        pass

    @abstractmethod
    async def search(self, event_dict: dict[str, Any]) -> list[Event]:
        pass

    @abstractmethod
    async def complete(self, event_id: int) -> None:
        pass

    @abstractmethod
    async def link_activities(
        self, event_id: int, activity_ids: list[int]
    ) -> None:
        pass

    @abstractmethod
    async def link_lodgings(
        self, event_id: int, lodging_ids: list[int]
    ) -> None:
        pass

    @abstractmethod
    async def get_events_for_user(self, user_id: int, status: str) -> list[Event]:
        pass

    @abstractmethod
    async def link_users(self, event_id: int, user_ids: list[int]) -> None:
        pass
