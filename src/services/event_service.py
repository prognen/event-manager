from __future__ import annotations

import logging

from typing import Any

from abstract_repository.ievent_repository import IEventRepository
from abstract_service.event_service import IEventService
from models.activity import Activity
from models.event import Event
from models.lodging import Lodging
from models.user import User


logger = logging.getLogger(__name__)

Event.model_rebuild()


class EventService(IEventService):
    def __init__(self, repository: IEventRepository) -> None:
        self.repository = repository
        logger.debug("EventService инициализирован")

    async def get_by_id(self, event_id: int) -> Event | None:
        logger.debug("Получение мероприятия по ID %d", event_id)
        return await self.repository.get_by_id(event_id)

    async def get_all_events(self) -> list[Event]:
        logger.debug("Получение списка всех мероприятий")
        return await self.repository.get_list()

    async def add(self, event: Event) -> Event:
        try:
            logger.debug("Добавление мероприятия с ID %d", event.event_id)
            event = await self.repository.add(event)
        except Exception:
            logger.error("Мероприятие c таким ID %d уже существует.", event.event_id)
            raise ValueError("Мероприятие c таким ID уже существует.")
        return event

    async def update(self, update_event: Event) -> Event:
        try:
            logger.debug("Обновление мероприятия с ID %d", update_event.event_id)
            await self.repository.update(update_event)
        except Exception:
            logger.error("Мероприятие с ID %d не найдено.", update_event.event_id)
            raise ValueError("Мероприятие не найдено.")
        return update_event

    async def delete(self, event_id: int) -> None:
        try:
            logger.debug("Удаление мероприятия с ID %d", event_id)
            await self.repository.delete(event_id)
        except Exception:
            logger.error("Мероприятие с ID %d не найдено.", event_id)
            raise ValueError("Мероприятие не найдено.")

    async def search(self, event_dict: dict[str, Any]) -> list[Event]:
        try:
            logger.debug("Поиск мероприятий по параметрам: %s", event_dict)
            return await self.repository.search(event_dict)
        except Exception:
            logger.error("Мероприятия по параметрам %s не найдены", event_dict)
            raise ValueError("Мероприятие по переданным параметрам не найдено.")

    async def complete(self, event_id: int) -> None:
        try:
            logger.debug("Завершение мероприятия с ID %d", event_id)
            await self.repository.complete(event_id)
        except Exception:
            logger.error("Ошибка при завершении мероприятия %d", event_id)
            raise ValueError("Ошибка при завершении мероприятия")

    async def get_users_by_event(self, event_id: int) -> list[User]:
        try:
            logger.debug("Получение пользователей для мероприятия %d", event_id)
            return await self.repository.get_users_by_event(event_id)
        except Exception:
            logger.error(
                "Ошибка при получении пользователей для мероприятия %d", event_id
            )
            raise ValueError("Ошибка при получении пользователей")

    async def get_activities_by_event(self, event_id: int) -> list[Activity]:
        try:
            logger.debug("Получение активностей для мероприятия %d", event_id)
            return await self.repository.get_activities_by_event(event_id)
        except Exception:
            logger.error(
                "Ошибка при получении активностей для мероприятия %d", event_id
            )
            raise ValueError("Ошибка при получении активностей для мероприятий")

    async def get_lodgings_by_event(self, event_id: int) -> list[Lodging]:
        try:
            logger.debug("Получение размещений для мероприятия %d", event_id)
            return await self.repository.get_lodgings_by_event(event_id)
        except Exception:
            logger.error(
                "Ошибка при получении размещений для мероприятия %d", event_id
            )
            raise ValueError("Ошибка при получении размещений для мероприятий")

    async def link_activities(
        self, event_id: int, activity_ids: list[int]
    ) -> None:
        try:
            logger.debug(
                "Связывание активностей %s с мероприятием %d",
                activity_ids,
                event_id,
            )
            await self.repository.link_activities(event_id, activity_ids)
        except Exception:
            logger.error(
                "Ошибка при связывании активностей %s с мероприятием %d",
                activity_ids,
                event_id,
            )
            raise ValueError("Ошибка при связывании активностей с мероприятием.")

    async def link_users(self, event_id: int, user_ids: list[int]) -> None:
        try:
            logger.debug(
                "Связывание пользователей %s с мероприятием %d", user_ids, event_id
            )
            await self.repository.link_users(event_id, user_ids)
        except Exception:
            logger.error(
                "Ошибка при связывании пользователей %s с мероприятием %d",
                user_ids,
                event_id,
            )
            raise ValueError("Ошибка при связывании пользователей с мероприятием.")

    async def link_lodgings(
        self, event_id: int, lodging_ids: list[int]
    ) -> None:
        try:
            logger.debug(
                "Связывание размещений %s с мероприятием %d",
                lodging_ids,
                event_id,
            )
            await self.repository.link_lodgings(event_id, lodging_ids)
        except Exception:
            logger.error(
                "Ошибка при связывании размещений %s с мероприятием %d",
                lodging_ids,
                event_id,
            )
            raise ValueError("Ошибка при связывании размещений с мероприятием.")

    async def get_events_for_user(
        self, user_id: int, event_status: str
    ) -> list[Event]:
        try:
            logger.debug("Получение активных мероприятий")
            return await self.repository.get_events_for_user(user_id, event_status)
        except Exception:
            logger.error("Ошибка при получении активных мероприятий")
            raise ValueError("Ошибка при получении активных мероприятий")

    async def get_event_by_session_id(self, session_id: int) -> Event | None:
        try:
            logger.debug("Получение мероприятий по session ID %d", session_id)
            return await self.repository.get_event_by_session_id(session_id)
        except Exception:
            logger.error("Мероприятие по session ID %d не найдено", session_id)
            raise ValueError(
                "Ошибка при получении мероприятий по session ID %d", session_id
            )
