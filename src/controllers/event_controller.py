from __future__ import annotations

import logging

from typing import Any

from fastapi import Request

from models.event import Event
from services.activity_service import ActivityService
from services.event_service import EventService
from services.lodging_service import LodgingService
from services.user_service import UserService


logger = logging.getLogger(__name__)


class EventController:
    def __init__(
        self,
        event_service: EventService,
        user_service: UserService,
        activity_service: ActivityService,
        lodging_service: LodgingService,
    ) -> None:
        self.event_service = event_service
        self.user_service = user_service
        self.activity_service = activity_service
        self.lodging_service = lodging_service
        logger.debug("Инициализация EventController")

    async def create_new_event(self, request: Request) -> dict[str, Any]:
        try:
            data = await request.json()
            users = []
            for user_id in data["user_ids"]:
                if user := await self.user_service.get_by_id(user_id):
                    users.append(user)
            activities = [
                a
                for aid in data["activity_ids"]
                if (a := await self.activity_service.get_by_id(aid)) is not None
            ]

            lodgings = [
                ldg
                for lid in data["lodging_ids"]
                if (ldg := await self.lodging_service.get_by_id(lid)) is not None
            ]
            event = Event(
                event_id=1,
                status=data["status"],
                users=users,
                activities=activities,
                lodgings=lodgings,
            )

            await self.event_service.add(event)
            logger.info("Мероприятие успешно создано: %s", event)
            return {"message": "Event created successfully"}
        except Exception as e:
            logger.error("Ошибка при создании мероприятия: %s", str(e), exc_info=True)
            raise e

    async def get_event_details(self, event_id: int) -> dict[str, Any]:
        try:
            event = await self.event_service.get_by_id(event_id)
            activity_list = await self.event_service.get_activities_by_event(event_id)
            lodging_list = await self.event_service.get_lodgings_by_event(event_id)
            user_list = await self.event_service.get_users_by_event(event_id)
            if event and event.users:
                logger.info("Мероприятие ID %d найдено: %s", event_id, event)
                return {
                    "event": {
                        "id": event.event_id,
                        "status": event.status,
                        "users": [
                            {"user_id": u.user_id, "fio": u.fio, "email": u.email}
                            for u in user_list
                        ],
                        "activities": [
                            {
                                "id": a.activity_id,
                                "duration": a.duration,
                                "address": a.address,
                                "activity_type": a.activity_type,
                                "activity_time": a.activity_time.isoformat(),
                                "venue": a.venue,
                            }
                            for a in activity_list
                        ],
                        "lodgings": [
                            {
                                "id": ldg.lodging_id,
                                "price": ldg.price,
                                "address": ldg.address,
                                "name": ldg.name,
                                "type": ldg.type,
                                "rating": ldg.rating,
                                "check_in": ldg.check_in.isoformat(),
                                "check_out": ldg.check_out.isoformat(),
                                "venue": ldg.venue,
                            }
                            for ldg in lodging_list
                        ],
                    }
                }
            logger.warning("Мероприятие ID %d не найдено", event_id)
            return {"message": "Event not found"}
        except Exception as e:
            logger.error(
                "Ошибка при получении информации о мероприятии ID: %s",
                str(e),
                exc_info=True,
            )
            return {"message": "Error fetching details", "error": str(e)}

    async def complete_event(self, event_id: int) -> dict[str, Any]:
        try:
            await self.event_service.complete(event_id)
            logger.info("Мероприятие ID %d успешно завершено", event_id)
            return {"message": "Event completed successfully"}
        except Exception as e:
            logger.error(
                "Ошибка при завершении мероприятия ID %d: %s",
                event_id,
                str(e),
                exc_info=True,
            )
            return {"message": "Error completing event", "error": str(e)}

    async def update_event(self, event_id: int, request: Request) -> dict[str, Any]:
        try:
            data = await request.json()
            users = []
            for user_id in data["user_ids"]:
                if user := await self.user_service.get_by_id(user_id):
                    users.append(user)
            activities = [
                a
                for aid in data["activity_ids"]
                if (a := await self.activity_service.get_by_id(aid)) is not None
            ]

            lodgings = [
                ldg
                for lid in data["lodging_ids"]
                if (ldg := await self.lodging_service.get_by_id(lid)) is not None
            ]

            event = Event(
                event_id=event_id,
                status=data["status"],
                users=users,
                activities=activities,
                lodgings=lodgings,
            )
            await self.event_service.update(event)
            logger.info("Мероприятие ID %d успешно обновлено", event_id)
            return {"message": "Event updated successfully"}
        except Exception as e:
            logger.error(
                "Ошибка при обновлении мероприятия ID %d: %s",
                event_id,
                str(e),
                exc_info=True,
            )
            return {"message": "Error updating event", "error": str(e)}

    async def delete_event(self, event_id: int) -> dict[str, Any]:
        try:
            await self.event_service.delete(event_id)
            logger.info("Мероприятие ID %d успешно удалено", event_id)
            return {"message": "Event deleted successfully"}
        except Exception as e:
            logger.error(
                "Ошибка при удалении мероприятия ID %d: %s",
                event_id,
                str(e),
                exc_info=True,
            )
            return {"message": "Error deleting event", "error": str(e)}

    async def search_event(self, request: Request) -> dict[str, Any]:
        try:
            data = await request.json()
            event_dict = data.get("search")

            if not event_dict:
                logger.warning("Отсутствуют параметры поиска в запросе")
                return {"message": "Missing search parameters"}

            search_results = await self.event_service.search(event_dict)
            logger.info("Найдено %d результатов поиска", len(search_results))
            return {"search_results": search_results}

        except Exception as e:
            logger.error("Ошибка при поиске мероприятий: %s", str(e), exc_info=True)
            return {"message": "Error searching for events", "error": str(e)}

    async def get_all_events(self) -> dict[str, Any]:
        try:
            event_list = await self.event_service.get_all_events()
            events = []
            for t in event_list:
                activity_list = (
                    await self.event_service.get_activities_by_event(t.event_id)
                )
                lodging_list = (
                    await self.event_service.get_lodgings_by_event(t.event_id)
                )
                user_list = await self.event_service.get_users_by_event(t.event_id)
                if t.users:
                    events.append(
                        {
                            "id": t.event_id,
                            "status": t.status,
                            "users": [
                                {"user_id": u.user_id, "fio": u.fio} for u in user_list
                            ],
                            "activities": [
                                {
                                    "id": a.activity_id,
                                    "duration": a.duration,
                                    "address": a.address,
                                    "activity_type": a.activity_type,
                                    "activity_time": a.activity_time.isoformat(),
                                    "venue": a.venue,
                                }
                                for a in activity_list
                            ],
                            "lodgings": [
                                {
                                    "id": ldg.lodging_id,
                                    "price": ldg.price,
                                    "address": ldg.address,
                                    "name": ldg.name,
                                    "type": ldg.type,
                                    "rating": ldg.rating,
                                    "check_in": ldg.check_in.isoformat(),
                                    "check_out": ldg.check_out.isoformat(),
                                    "venue": ldg.venue,
                                }
                                for ldg in lodging_list
                            ],
                        }
                    )

            logger.info("Получено %d мероприятий", len(events))
            return {"events": events}

        except Exception as e:
            logger.error(
                "Ошибка при получении списка мероприятий: %s", str(e), exc_info=True
            )
            return {"message": "Error fetching events", "error": str(e)}
