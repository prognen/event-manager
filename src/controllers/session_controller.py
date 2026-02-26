from __future__ import annotations

import logging

from datetime import datetime
from typing import Any

from fastapi import HTTPException
from fastapi import Request

from models.session import Session
from models.event import Event
from services.activity_service import ActivityService
from services.lodging_service import LodgingService
from services.program_service import ProgramService
from services.session_service import SessionService
from services.event_service import EventService
from services.user_service import UserService


logger = logging.getLogger(__name__)


class SessionController:
    def __init__(
        self,
        session_service: SessionService,
        event_service: EventService,
        program_service: ProgramService,
        user_service: UserService,
        activity_service: ActivityService,
        lodging_service: LodgingService,
    ) -> None:
        self.session_service = session_service
        self.event_service = event_service
        self.program_service = program_service
        self.user_service = user_service
        self.activity_service = activity_service
        self.lodging_service = lodging_service
        logger.debug("Инициализация SessionController")

    async def create_new_session_user(self, request: Request) -> dict[str, Any]:
        try:
            data = await request.json()
            try:
                data["start_time"] = datetime.strptime(data["start_date"], "%d.%m.%Y")
                data["end_time"] = datetime.strptime(data["end_date"], "%d.%m.%Y")
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Неверный формат даты. Используйте ДД.ММ.ГГГГ",
                )

            program = await self.program_service.get_by_venues(
                int(data["from_venue"]),
                int(data["to_venue"]),
                data["transport"],
            )

            if not program:
                raise HTTPException(
                    status_code=400,
                    detail=f"Программа между площадками {data['from_venue']} и {data['to_venue']} не найдена",
                )

            data["program"] = program
            data["session_id"] = 1
            data["type"] = "Личные"
            logger.info("Создание сессии с данными: %s", data)
            user = await self.user_service.get_by_id(int(data.get("user_id")))
            if not user:
                raise
            event = Event(
                event_id=1,
                status="Активное",
                users=[user],
                activities=[
                    a
                    for aid in data.get("activities[]")
                    if (a := await self.activity_service.get_by_id(int(aid))) is not None
                ],
                lodgings=[
                    ldg
                    for lid in data.get("lodgings[]")
                    if (ldg := await self.lodging_service.get_by_id(int(lid))) is not None
                ],
            )
            data["event"] = await self.event_service.add(event)

            session = Session(**data)
            created_session = await self.session_service.add(session)

            logger.info("Сессия успешно создана, ID: %d", created_session.session_id)
            return {
                "message": "Session created successfully",
                "session_id": created_session.session_id,
                "program_id": program.program_id,
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Ошибка при создании сессии: %s", str(e), exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"Ошибка при создании сессии: {e!s}"
            )

    async def create_new_session(self, request: Request) -> dict[str, Any]:
        try:
            data = await request.json()
            program_id = data.get("program_id")
            data["program"] = await self.program_service.get_by_id(program_id)
            event_id = data.get("event_id")
            data["event"] = await self.event_service.get_by_id(event_id)
            data["session_id"] = 1
            session = Session(**data)
            await self.session_service.add(session)
            logger.info("Сессия успешно создана: %s", session)
            return {"message": "Session created successfully"}
        except Exception as e:
            logger.error("Ошибка при создании сессии: %s", str(e), exc_info=True)
            return {"message": "Error creating session", "error": str(e)}

    async def add_new_venue(self, request: Request) -> dict[str, Any]:
        try:
            data = await request.json()
            event_id = int(data.get("event_id"))
            new_venue_id = int(data.get("new_venue_id"))
            after_venue_id = int(data.get("after_venue_id"))
            transport = data.get("transport")

            if not event_id or not new_venue_id or not after_venue_id:
                logger.warning("Отсутствуют обязательные поля в запросе")
                return {"message": "Missing required fields in request"}

            await self.session_service.insert_venue_after(
                event_id, new_venue_id, after_venue_id, transport
            )
            logger.info(
                "Площадка ID %d успешно добавлена в сессию после площадки %d",
                new_venue_id,
                after_venue_id,
            )
            return {"message": "Venue added to session successfully"}
        except Exception as e:
            logger.error(
                "Ошибка при добавлении площадки в сессию: %s", str(e), exc_info=True
            )
            return {"message": "Error adding venue to session", "error": str(e)}

    async def get_session_parts(self, session_id: int) -> list[dict[str, Any]]:
        return await self.session_service.get_session_parts(session_id)

    async def delete_venue_from_session(self, request: Request) -> dict[str, Any]:
        try:
            data = await request.json()
            venue_id = data.get("venue_id")
            event_id = data.get("event_id")

            if not venue_id or not event_id:
                logger.warning(
                    "Недостаточно данных в запросе: venue_id=%s, event_id=%s",
                    venue_id,
                    event_id,
                )
                return {"success": False, "message": "Требуются venue_id и event_id"}

            try:
                venue_id = int(venue_id)
                event_id = int(event_id)
            except (TypeError, ValueError) as e:
                logger.warning("Некорректные ID в запросе: %s", str(e))
                return {"success": False, "message": "ID должны быть целыми числами"}

            await self.session_service.delete_venue_from_session(event_id, venue_id)

            logger.info(
                "Площадка ID %d успешно удалена из сессии event_id=%d",
                venue_id,
                event_id,
            )
            return {
                "success": True,
                "message": f"Площадка {venue_id} удалена из сессии",
            }

        except ValueError as e:
            logger.warning("Ошибка валидации: %s", str(e))
            return {"success": False, "message": str(e), "error": "validation_error"}
        except Exception as e:
            logger.error(
                "Ошибка при удалении площадки из сессии: %s", str(e), exc_info=True
            )
            return {
                "success": False,
                "message": "Внутренняя ошибка сервера",
                "error": str(e),
            }

    async def update_session(
        self, session_id: int, request: Request
    ) -> dict[str, Any]:
        try:
            data = await request.json()
            program_id = data.get("program_id")
            data["program"] = await self.program_service.get_by_id(program_id)
            event_id = data.get("event_id")
            data["event"] = await self.event_service.get_by_id(event_id)
            data["session_id"] = session_id
            session = Session(**data)
            await self.session_service.update(session)
            logger.info("Сессия ID %d успешно обновлена", session_id)
            return {"message": "Session updated successfully"}
        except Exception as e:
            logger.error(
                "Ошибка при обновлении сессии ID %d: %s",
                session_id,
                str(e),
                exc_info=True,
            )
            return {"message": "Error updating session", "error": str(e)}

    async def change_transport(
        self, session_id: int, request: Request
    ) -> dict[str, Any]:
        try:
            data = await request.json()
            new_transport = data.get("transport")
            program_id = data.get("program_id")
            if not session_id or not new_transport:
                logger.warning("Отсутствуют обязательные поля в запросе")
                return {"message": "Missing required fields in request"}
            new_session = await self.session_service.change_transport(
                program_id, session_id, new_transport
            )
            logger.info(
                "Транспорт в сессии ID %d успешно изменен на %s",
                session_id,
                new_transport,
            )
            if new_session is None or new_session.program is None:
                logger.error("Сессия с ID %d не была обновлена", session_id)
                return {"message": "Error updating transport, session not found"}
            return {
                "message": "Transport updated successfully",
                "program_id": new_session.program.program_id,
            }
        except Exception as e:
            logger.error(
                "Ошибка при изменении транспорта в сессии ID %d: %s",
                session_id,
                str(e),
                exc_info=True,
            )
            return {"message": "Error updating transport", "error": str(e)}

    async def get_session_details(self, request: Request) -> dict[str, Any]:
        try:
            data = await request.json()
            session_id = data.get("id")
            if session_id is None:
                logger.warning("ID сессии не передан в запросе")
                return {"message": "Missing 'id' in request"}
            session = await self.session_service.get_by_id(session_id)
            if session and session.program is not None and session.event is not None:
                logger.info("Сессия ID %d найдена: %s", session_id, session)
                return {
                    "session": {
                        "id": session.session_id,
                        "program_id": session.program.program_id,
                        "event_id": session.event.event_id,
                        "start_time": session.start_time,
                        "end_time": session.end_time,
                        "session_id": session.session_id,
                        "type": session.type,
                    }
                }
            logger.warning("Сессия ID %d не найдена", session_id)
            return {"message": "Session not found"}
        except Exception as e:
            logger.error(
                "Ошибка при получении информации о сессии ID: %s",
                str(e),
                exc_info=True,
            )
            return {"message": "Error fetching details", "error": str(e)}

    async def delete_session(self, session_id: int) -> dict[str, Any]:
        try:
            await self.session_service.delete(session_id)
            logger.info("Сессия ID %d успешно удалена", session_id)
            return {"message": "Session deleted successfully"}
        except Exception as e:
            logger.error(
                "Ошибка при удалении сессии ID %d: %s",
                session_id,
                str(e),
                exc_info=True,
            )
            return {"message": "Error deleting session", "error": str(e)}

    async def get_all_sessions(self) -> dict[str, Any]:
        try:
            session_list = await self.session_service.get_all_sessions()
            sessions = []
            for s in session_list:
                if s and s.program and s.event:
                    event_users = await self.event_service.get_users_by_event(
                        s.event.event_id
                    )
                    sessions.append(
                        {
                            "id": s.session_id,
                            "start_time": (
                                s.start_time.isoformat() if s.start_time else None
                            ),
                            "end_time": s.end_time.isoformat() if s.end_time else None,
                            "type": s.type,
                            "program": (
                                {
                                    "id": s.program.program_id,
                                    "type_transport": s.program.type_transport,
                                    "cost": s.program.cost,
                                    "distance": s.program.distance,
                                    "from_venue": (
                                        s.program.from_venue.name
                                        if s.program.from_venue
                                        else None
                                    ),
                                    "to_venue": (
                                        s.program.to_venue.name
                                        if s.program.to_venue
                                        else None
                                    ),
                                }
                                if s.program
                                else None
                            ),
                            "event": (
                                {
                                    "id": s.event.event_id,
                                    "status": s.event.status,
                                    "users": [
                                        {
                                            "id": u.user_id,
                                            "fio": u.fio,
                                            "email": u.email,
                                        }
                                        for u in event_users
                                    ],
                                    "activities": [
                                        {
                                            "id": a.activity_id,
                                            "activity_type": a.activity_type,
                                            "address": a.address,
                                            "duration": a.duration,
                                            "activity_time": a.activity_time.isoformat(),
                                            "venue": a.venue,
                                        }
                                        for a in (
                                            await self.event_service.get_activities_by_event(
                                                s.event.event_id
                                            )
                                        )
                                    ],
                                    "lodgings": [
                                        {
                                            "id": ldg.lodging_id,
                                            "name": ldg.name,
                                            "address": ldg.address,
                                            "price": ldg.price,
                                            "type": ldg.type,
                                            "rating": ldg.rating,
                                            "check_in": ldg.check_in.isoformat(),
                                            "check_out": ldg.check_out.isoformat(),
                                            "venue": ldg.venue,
                                        }
                                        for ldg in (
                                            await self.event_service.get_lodgings_by_event(
                                                s.event.event_id
                                            )
                                        )
                                    ],
                                }
                                if s.event
                                else None
                            ),
                        }
                    )
            logger.info("Получено %d сессий", len(sessions))
            return {"sessions": sessions}
        except Exception as e:
            logger.error(
                "Ошибка при получении списка сессий: %s", str(e), exc_info=True
            )
            return {"message": "Error fetching sessions", "error": str(e)}

    async def change_session_duration(
        self, session_id: int, request: Request
    ) -> dict[str, Any]:
        try:
            data = await request.json()
            new_end_date = data.get("new_end_date")
            if not new_end_date:
                raise HTTPException(status_code=400, detail="new_end_date is required")
            session_data = await self.session_service.get_by_id(session_id)
            if not session_data:
                return {
                    "message": "Session not found",
                    "error": f"Session with id {session_id} not found",
                }
            current_end_date = session_data.end_time
            try:
                new_end_date = datetime.strptime(new_end_date, "%Y-%m-%d")
            except ValueError:
                return {
                    "message": "Invalid date format",
                    "error": "new_end_date must be in YYYY-MM-DD format",
                }
            if new_end_date <= current_end_date:
                return {
                    "message": "Invalid date",
                    "error": f"New end date {new_end_date} must be after current end date {current_end_date}",
                }
            session_data.end_time = new_end_date
            await self.session_service.update(session_data)

            logger.info(
                "Сессия ID %d успешно продлена до %s", session_id, new_end_date
            )
            return {
                "message": "Session updated successfully",
                "session_id": session_id,
                "new_end_date": new_end_date,
            }
        except Exception as e:
            logger.error(
                "Ошибка при продлении сессии ID %d: %s",
                session_id,
                str(e),
                exc_info=True,
            )
            return {"message": "Error updating session", "error": str(e)}

    async def join_to_event(self, session_id: int, request: Request) -> dict[str, Any]:
        data = await request.json()
        user_id = data.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID is required")
        user = await self.user_service.get_by_id(user_id)
        session = await self.session_service.get_by_id(session_id)
        if not session:
            return {"message": "Session not found"}
        session.type = "Личные"
        if session.event:
            current_users = await self.event_service.get_users_by_event(
                session.event.event_id
            )

        if user is not None and any(
            u.user_id == user.user_id for u in current_users if u is not None
        ):
            raise HTTPException(
                status_code=400, detail="User already joined this event"
            )
        if session.event and user:
            await self.event_service.link_users(
                session.event.event_id,
                [u.user_id for u in current_users] + [user.user_id],
            )

        await self.session_service.add(session)

        logger.info(
            "Пользователь %d присоединился к сессии %d", user_id, session_id
        )
        return {
            "message": "Вы успешно присоединились к мероприятию",
            "session_id": session_id,
            "new_type": "Личные",
        }
