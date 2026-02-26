from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Any

from models.session import Session


class ISessionRepository(ABC):
    @abstractmethod
    async def get_list(self) -> list[Session]:
        pass

    @abstractmethod
    async def get_by_id(self, session_id: int) -> Session | None:
        pass

    @abstractmethod
    async def add(self, session: Session) -> Session:
        pass

    @abstractmethod
    async def update(self, update_session: Session) -> None:
        pass

    @abstractmethod
    async def delete(self, session_id: int) -> None:
        pass

    @abstractmethod
    async def get_sessions_by_event_id_ordered(self, event_id: int) -> list[Session]:
        pass

    @abstractmethod
    async def get_sessions_by_venue(self, venue_id: int) -> list[Session]:
        pass

    @abstractmethod
    async def delete_venue_from_session(self, event_id: int, venue_id: int) -> None:
        pass

    @abstractmethod
    async def change_transport(
        self, program_id: int, session_id: int, new_transport: str
    ) -> Session | None:
        pass

    @abstractmethod
    async def insert_venue_after(
        self, event_id: int, new_venue_id: int, after_venue_id: int, transport: str
    ) -> None:
        pass

    @abstractmethod
    async def get_sessions_by_user_and_status_and_type(
        self, user_id: int, status: str, type_session: str
    ) -> list[Session]:
        pass

    @abstractmethod
    async def get_sessions_by_type(self, type_session: str) -> list[Session]:
        pass

    @abstractmethod
    async def get_session_parts(self, event_id: int) -> list[dict[str, Any]]:
        pass
