from __future__ import annotations

import logging

from typing import Any

from abstract_repository.isession_repository import ISessionRepository
from abstract_service.session_service import ISessionService
from models.session import Session


logger = logging.getLogger(__name__)

Session.model_rebuild()


class SessionService(ISessionService):
    def __init__(self, repository: ISessionRepository) -> None:
        self.repository = repository
        logger.debug("SessionService инициализирован")

    async def get_by_id(self, session_id: int) -> Session | None:
        logger.debug("Получение сессии по ID %d", session_id)
        return await self.repository.get_by_id(session_id)

    async def get_all_sessions(self) -> list[Session]:
        logger.debug("Получение списка всех сессий")
        return await self.repository.get_list()

    async def add(self, session: Session) -> Session:
        try:
            logger.debug("Добавление сессии с ID %d", session.session_id)
            session = await self.repository.add(session)
        except Exception:
            logger.error("Сессия c таким ID %d уже существует.", session.session_id)
            raise ValueError("Сессия c таким ID уже существует.")
        return session

    async def update(self, updated_session: Session) -> Session:
        try:
            logger.debug("Обновление сессии с ID %d", updated_session.session_id)
            await self.repository.update(updated_session)
        except Exception:
            logger.error("Сессия с ID %d не найдена.", updated_session.session_id)
            raise ValueError("Сессия не найдена.")
        return updated_session

    async def delete(self, session_id: int) -> None:
        try:
            logger.debug("Удаление сессии с ID %d", session_id)
            await self.repository.delete(session_id)
        except Exception:
            logger.error("Сессия с ID %d не найдена.", session_id)
            raise ValueError("Сессия не найдена.")

    async def insert_venue_after(
        self, event_id: int, new_venue_id: int, after_venue_id: int, transport: str
    ) -> None:
        try:
            logger.debug(
                "Добавление площадки %d после площадки %d в мероприятии %d",
                new_venue_id,
                after_venue_id,
                event_id,
            )
            await self.repository.insert_venue_after(
                event_id, new_venue_id, after_venue_id, transport
            )
        except Exception:
            logger.error("Не удалось добавить площадку %d в сессию", new_venue_id)
            raise ValueError("Площадку не получилось добавить.")

    async def delete_venue_from_session(self, event_id: int, venue_id: int) -> None:
        try:
            logger.debug("Удаление площадки %d из сессии", venue_id)
            await self.repository.delete_venue_from_session(event_id, venue_id)
        except Exception:
            logger.error("Не удалось удалить площадку %d из сессии", venue_id)
            raise ValueError("Площадку не получилось удалить из сессии.")

    async def change_transport(
        self, program_id: int, session_id: int, new_transport: str
    ) -> Session | None:
        try:
            logger.debug(
                "Изменение транспорта в сессии %d на %s", session_id, new_transport
            )
            return await self.repository.change_transport(
                program_id, session_id, new_transport
            )
        except Exception:
            logger.error("Не удалось изменить транспорт в сессии %d", session_id)
            raise ValueError("Не удалось изменить транспорт в сессии.")

    async def get_sessions_by_user_and_status_and_type(
        self, user_id: int, status: str, type_session: str
    ) -> list[Session]:
        logger.debug(
            "Получение сессии по user_id %d, status %s, type: %s",
            user_id,
            status,
            type_session,
        )
        return await self.repository.get_sessions_by_user_and_status_and_type(
            user_id, status, type_session
        )

    async def get_sessions_by_type(self, type_session: str) -> list[Session]:
        logger.debug("Получение сессии по type: %s", type_session)
        return await self.repository.get_sessions_by_type(type_session)

    async def get_sessions_by_event_id(self, event_id: int) -> list[Session]:
        logger.debug("Получение сессий для мероприятия ID %d", event_id)
        return await self.repository.get_sessions_by_event_id_ordered(event_id)

    async def get_session_parts(self, session_id: int) -> list[dict[str, Any]]:
        return await self.repository.get_session_parts(session_id)
