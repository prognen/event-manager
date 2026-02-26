from __future__ import annotations

import logging

from datetime import timedelta
from typing import Any

from bson import Int64
from motor.motor_asyncio import AsyncIOMotorClient
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError
from pymongo.errors import PyMongoError

from abstract_repository.iprogram_repository import IProgramRepository
from abstract_repository.isession_repository import ISessionRepository
from abstract_repository.ievent_repository import IEventRepository
from models.program import Program
from models.session import Session


logger = logging.getLogger(__name__)


class SessionRepository(ISessionRepository):
    def __init__(
        self,
        client: AsyncIOMotorClient[Any],
        program_repo: IProgramRepository,
        event_repo: IEventRepository,
    ):
        self.db: AsyncIOMotorDatabase[Any] = client["event_db"]
        self.sessions = self.db["sessions"]
        self.program_repo = program_repo
        self.event_repo = event_repo
        logger.debug("Инициализация SessionRepository для MongoDB")

    async def get_list(self) -> list[Session]:
        try:
            sessions = []
            async for doc in self.sessions.find():
                program_doc = await self.program_repo.get_by_id(doc["program"]["_id"])
                event_doc = await self.event_repo.get_by_id(doc["event"]["_id"])

                sessions.append(
                    Session(
                        session_id=int(doc["_id"]),
                        program=program_doc,
                        event=event_doc,
                        start_time=doc["start_time"],
                        end_time=doc["end_time"],
                        type=doc["type"],
                    )
                )
            logger.debug("Успешно получено %d сессий", len(sessions))
            return sessions
        except PyMongoError as e:
            logger.error(
                "Ошибка при получении списка сессий: %s", str(e), exc_info=True
            )
            return []

    async def get_by_id(self, session_id: int) -> Session | None:
        try:
            doc = await self.sessions.find_one({"_id": session_id})
            if doc:
                program_doc = await self.program_repo.get_by_id(doc["program"]["_id"])
                event_doc = await self.event_repo.get_by_id(doc["event"]["_id"])

                logger.debug("Найдена сессия ID %d", session_id)
                return Session(
                    session_id=int(doc["_id"]),
                    program=program_doc,
                    event=event_doc,
                    start_time=doc["start_time"],
                    end_time=doc["end_time"],
                    type=doc["type"],
                )
            logger.warning("Сессия с ID %d не найдена", session_id)
            return None
        except PyMongoError as e:
            logger.error(
                "Ошибка при получении сессии по ID %d: %s",
                session_id,
                str(e),
                exc_info=True,
            )
            return None

    async def add(self, session: Session) -> Session:
        try:
            if not session.event:
                logger.error("Отсутствуют данные о мероприятии")
                return session
            if not session.program:
                logger.error("Отсутствуют данные о программе")
                return session

            last_id = await self.sessions.find().sort("_id", -1).limit(1).next()
            new_id = Int64(last_id["_id"] + 1) if last_id else Int64(1)

            doc = {
                "_id": int(new_id),
                "program": {"_id": session.program.program_id},
                "event": {"_id": session.event.event_id},
                "start_time": session.start_time,
                "end_time": session.end_time,
                "type": session.type,
            }

            result = await self.sessions.insert_one(doc)
            session.session_id = int(str(result.inserted_id))
            logger.debug("Сессия успешно добавлена с ID %s", str(result.inserted_id))
            return session

        except DuplicateKeyError:
            logger.warning("Сессия уже существует в базе данных")
            return session
        except PyMongoError as e:
            logger.error("Ошибка при добавлении сессии: %s", str(e), exc_info=True)
            return session

    async def update(self, update_session: Session) -> None:
        try:
            if not update_session.event:
                logger.error("Отсутствуют данные о мероприятии для обновления")
                return
            if not update_session.program:
                logger.error(
                    "Отсутствуют данные о программе для обновления"
                )
                return

            result = await self.sessions.update_one(
                {"_id": update_session.session_id},
                {
                    "$set": {
                        "program": {"_id": update_session.program.program_id},
                        "event": {"_id": update_session.event.event_id},
                        "start_time": update_session.start_time,
                        "end_time": update_session.end_time,
                        "type": update_session.type,
                    }
                },
            )

            if result.modified_count == 0:
                logger.warning(
                    "Сессия с ID %d не найдена для обновления", update_session.session_id
                )
            else:
                logger.debug("Сессия ID %d успешно обновлена", update_session.session_id)

        except PyMongoError as e:
            logger.error(
                "Ошибка при обновлении сессии ID %d: %s",
                update_session.session_id,
                str(e),
                exc_info=True,
            )

    async def delete(self, session_id: int) -> None:
        try:
            result = await self.sessions.delete_one({"_id": session_id})
            if result.deleted_count == 0:
                logger.warning("Сессия с ID %d не найдена для удаления", session_id)
            else:
                logger.debug("Сессия ID %d успешно удалена", session_id)
        except PyMongoError as e:
            logger.error(
                "Ошибка при удалении сессии ID %d: %s",
                session_id,
                str(e),
                exc_info=True,
            )

    async def get_sessions_by_event_id_ordered(self, event_id: int) -> list[Session]:
        try:
            sessions = []
            async for doc in self.sessions.find({"event._id": event_id}).sort(
                "start_time"
            ):
                program_doc = await self.program_repo.get_by_id(doc["program"]["_id"])
                event_doc = await self.event_repo.get_by_id(doc["event"]["_id"])

                sessions.append(
                    Session(
                        session_id=int(doc["_id"]),
                        program=program_doc,
                        event=event_doc,
                        start_time=doc["start_time"],
                        end_time=doc["end_time"],
                        type=doc["type"],
                    )
                )

            logger.debug("Сессия с event ID %d успешно найдена", event_id)
            return sessions
        except PyMongoError as e:
            logger.error(
                "Ошибка при получении сессии с event ID %d: %s",
                event_id,
                str(e),
                exc_info=True,
            )
            return []

    async def get_sessions_by_venue(self, venue_id: int) -> list[Session]:
        try:
            all_programs = await self.program_repo.get_list()
            program_ids = []
            for program in all_programs:
                if (
                    program.from_venue
                    and program.to_venue
                    and venue_id
                    in {program.from_venue.venue_id, program.to_venue.venue_id}
                ):
                    program_ids.append(program.program_id)

            sessions = []
            async for doc in self.sessions.find({"program._id": {"$in": program_ids}}):
                program_doc = await self.program_repo.get_by_id(doc["program"]["_id"])
                event_doc = await self.event_repo.get_by_id(doc["event"]["_id"])

                sessions.append(
                    Session(
                        session_id=int(doc["_id"]),
                        program=program_doc,
                        event=event_doc,
                        start_time=doc["start_time"],
                        end_time=doc["end_time"],
                        type=doc["type"],
                    )
                )

            logger.debug("Сессия с venue ID %d успешно найдена", venue_id)
            return sessions
        except PyMongoError as e:
            logger.error(
                "Ошибка при получении сессии с venue ID %d: %s",
                venue_id,
                str(e),
                exc_info=True,
            )
            return []

    async def delete_venue_from_session(self, event_id: int, venue_id: int) -> None:
        try:
            sessions = await self.get_sessions_by_event_id_ordered(event_id)
            if not sessions:
                raise ValueError("Список сессий пуст")

            segments_to_remove = []
            for i, session in enumerate(sessions):
                if not session.program:
                    continue

                if venue_id in {
                    (
                        session.program.from_venue.venue_id
                        if session.program.from_venue
                        else None
                    ),
                    (
                        session.program.to_venue.venue_id
                        if session.program.to_venue
                        else None
                    ),
                }:
                    segments_to_remove.append(i)

            if not segments_to_remove:
                raise ValueError(f"Площадка {venue_id} не найдена в сессии")

            prev_venue_id = None
            next_venue_id = None

            first_segment_idx = segments_to_remove[0]
            if first_segment_idx > 0:
                prev_session = sessions[first_segment_idx - 1]
                if prev_session.program and prev_session.program.from_venue:
                    prev_venue_id = prev_session.program.from_venue.venue_id

            last_segment_idx = segments_to_remove[-1]
            if last_segment_idx < len(sessions) - 1:
                next_session = sessions[last_segment_idx + 1]
                if next_session.program and next_session.program.to_venue:
                    next_venue_id = next_session.program.to_venue.venue_id

            for i in sorted(segments_to_remove, reverse=True):
                await self.delete(sessions[i].session_id)

            if prev_venue_id and next_venue_id:
                first_removed_session = sessions[segments_to_remove[0]]
                if not first_removed_session.program:
                    raise ValueError(
                        "Не удалось определить транспорт для нового сегмента"
                    )

                transport = first_removed_session.program.type_transport
                start_time = first_removed_session.start_time

                program = await self._get_program_between(
                    prev_venue_id, next_venue_id, transport
                )
                new_session = Session(
                    session_id=1,
                    program=program,
                    event=sessions[0].event,
                    start_time=start_time,
                    end_time=start_time + timedelta(hours=2),
                    type=sessions[0].type,
                )
                await self.add(new_session)
        except PyMongoError as e:
            logger.error(
                "Ошибка при удалении площадки из сессии: %s", str(e), exc_info=True
            )
            raise

    async def change_transport(
        self, program_id: int, session_id: int, new_transport: str
    ) -> Session | None:
        try:
            session_doc = await self.sessions.find_one({"_id": session_id})
            logger.debug("session_doc: %s", session_doc)
            if not session_doc:
                logger.error(
                    "Невозможно поменять транспорт, сессия с ID %d не найдена", session_id
                )
                return None

            old_program = await self.program_repo.get_by_id(program_id)
            if (
                not old_program
                or not old_program.from_venue
                or not old_program.to_venue
            ):
                logger.error("Программа с ID %d не найдена", program_id)
                return None

            new_program = await self.program_repo.get_by_venues(
                old_program.from_venue.venue_id,
                old_program.to_venue.venue_id,
                new_transport,
            )
            if (
                not new_program
                or not new_program.from_venue
                or not new_program.to_venue
            ):
                logger.error(
                    "Программа с транспортом %s не найдена", new_transport
                )
                return None

            result = await self.sessions.update_one(
                {"_id": session_id},
                {
                    "$set": {
                        "program": {
                            "_id": new_program.program_id,
                            "type_transport": new_program.type_transport,
                            "from_venue_id": new_program.from_venue.venue_id,
                            "to_venue_id": new_program.to_venue.venue_id,
                            "price": new_program.cost,
                            "distance": new_program.distance,
                        }
                    }
                },
            )

            if result.modified_count == 0:
                logger.error("Не удалось обновить сессию")
                return None

            logger.debug(
                "Транспорт %s в сессии ID %d успешно обновлён",
                new_transport,
                session_id,
            )
            return await self.get_by_id(session_id)
        except PyMongoError as e:
            logger.error(
                "Ошибка при изменении транспорта сессии с ID %d: %s",
                session_id,
                str(e),
                exc_info=True,
            )
            raise

    async def _get_program_between(
        self, from_venue_id: int, to_venue_id: int, transport: str
    ) -> Program:
        program_doc = await self.program_repo.get_by_venues(
            from_venue_id, to_venue_id, transport
        )

        if not program_doc:
            raise ValueError(
                f"Нет программы между площадками {from_venue_id} и {to_venue_id}"
            )

        return program_doc

    async def insert_venue_after(
        self, event_id: int, new_venue_id: int, after_venue_id: int, transport: str
    ) -> None:
        try:
            sessions = await self.get_sessions_by_event_id_ordered(event_id)
            if not sessions:
                raise ValueError("Список сессий пуст")

            target_session = None
            insert_after = False

            for session in sessions:
                if not session.program:
                    continue

                if (
                    session.program.to_venue
                    and session.program.to_venue.venue_id == after_venue_id
                ):
                    target_session = session
                    insert_after = True
                    break
                if (
                    session.program.from_venue
                    and session.program.from_venue.venue_id == after_venue_id
                ):
                    target_session = session
                    break

            if not target_session or not target_session.program:
                raise ValueError(f"Площадка {after_venue_id} не найдена в сессии")

            if insert_after:
                program_new = await self._get_program_between(
                    after_venue_id, new_venue_id, transport
                )

                new_session = Session(
                    session_id=1,
                    program=program_new,
                    event=target_session.event,
                    start_time=target_session.end_time,
                    end_time=target_session.end_time + timedelta(hours=2),
                    type=target_session.type,
                )
                await self.add(new_session)
            else:
                program_new = await self._get_program_between(
                    new_venue_id, after_venue_id, transport
                )
                if not program_new.from_venue or not program_new.to_venue:
                    raise ValueError(
                        "program_new.from_venue/program_new.to_venue не найдены"
                    )
                await self.sessions.update_one(
                    {"_id": target_session.session_id},
                    {
                        "$set": {
                            "program": {
                                "_id": program_new.program_id,
                                "type_transport": program_new.type_transport,
                                "from_venue_id": program_new.from_venue.venue_id,
                                "to_venue_id": program_new.to_venue.venue_id,
                                "price": program_new.cost,
                                "distance": program_new.distance,
                            }
                        },
                        "end_time": target_session.start_time + timedelta(hours=2),
                    },
                )
        except PyMongoError as e:
            logger.error(
                "Ошибка при вставке площадки в сессию: %s", str(e), exc_info=True
            )
            raise

    async def get_sessions_by_user_and_status_and_type(
        self, user_id: int, status: str, type_session: str
    ) -> list[Session]:
        try:
            event_ids = [
                e.event_id
                for e in await self.event_repo.get_events_for_user(user_id, status)
            ]

            sessions = []
            async for doc in self.sessions.find(
                {"event._id": {"$in": event_ids}, "type": type_session}
            ):
                program_doc = await self.program_repo.get_by_id(doc["program"]["_id"])
                event_doc = await self.event_repo.get_by_id(doc["event"]["_id"])

                sessions.append(
                    Session(
                        session_id=int(doc["_id"]),
                        program=program_doc,
                        event=event_doc,
                        start_time=doc["start_time"],
                        end_time=doc["end_time"],
                        type=doc["type"],
                    )
                )

            logger.debug(
                "Найдено %d сессий для user_id=%d со статусом %s",
                len(sessions),
                user_id,
                status,
            )
            return sessions
        except PyMongoError as e:
            logger.error(
                "Ошибка при получении сессий по user_id=%d и статусу %s: %s",
                user_id,
                status,
                str(e),
                exc_info=True,
            )
            raise

    async def get_sessions_by_type(self, type_session: str) -> list[Session]:
        try:
            sessions = []
            async for doc in self.sessions.find({"type": type_session}):
                program_doc = await self.program_repo.get_by_id(doc["program"]["_id"])
                event_doc = await self.event_repo.get_by_id(doc["event"]["_id"])

                sessions.append(
                    Session(
                        session_id=int(doc["_id"]),
                        program=program_doc,
                        event=event_doc,
                        start_time=doc["start_time"],
                        end_time=doc["end_time"],
                        type=doc["type"],
                    )
                )

            logger.debug("Найдено %d сессий с типом %s", len(sessions), type_session)
            return sessions
        except PyMongoError as e:
            logger.error(
                "Ошибка при получении сессий с типом %s: %s",
                type_session,
                str(e),
                exc_info=True,
            )
            return []

    async def get_session_parts(self, event_id: int) -> list[dict[str, Any]]:
        try:
            session_parts = []
            async for session_doc in self.sessions.find({"_id": event_id}).sort(
                "start_time"
            ):
                logger.debug("session_doc %s/n", session_doc)
                program_doc = await self.program_repo.get_by_id(
                    session_doc["program"]["_id"]
                )
                if not program_doc:
                    continue

                session_parts.append(
                    {
                        "session_id": int(session_doc["_id"]),
                        "program_id": program_doc.program_id,
                        "from_venue": program_doc.from_venue,
                        "to_venue": program_doc.to_venue,
                        "transport": program_doc.type_transport,
                        "start_time": session_doc["start_time"],
                        "end_time": session_doc["end_time"],
                        "type": session_doc["type"],
                        "price": program_doc.cost,
                    }
                )

            logger.debug(
                "Получено %d частей сессии для event_id=%d",
                len(session_parts),
                event_id,
            )
            return session_parts

        except PyMongoError as e:
            logger.error(
                "Ошибка при получении частей сессии для event_id=%d: %s",
                event_id,
                str(e),
                exc_info=True,
            )
            raise
