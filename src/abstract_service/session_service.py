from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from models.session import Session


Session.model_rebuild()


class ISessionService(ABC):
    @abstractmethod
    async def get_by_id(self, session_id: int) -> Session | None:
        pass

    @abstractmethod
    async def get_all_sessions(self) -> list[Session]:
        pass

    @abstractmethod
    async def add(self, session: Session) -> Session:
        pass

    @abstractmethod
    async def update(self, updated_session: Session) -> Session:
        pass

    @abstractmethod
    async def delete(self, session_id: int) -> None:
        pass
