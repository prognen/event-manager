from __future__ import annotations

import logging

from datetime import timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from abstract_repository.ievent_repository import IEventRepository
from abstract_repository.iprogram_repository import IProgramRepository
from abstract_repository.isession_repository import ISessionRepository
from models.program import Program
from models.session import Session


logger = logging.getLogger(__name__)


class SessionRepository(ISessionRepository):
    def __init__(
        self,
        session: AsyncSession,
        program_repo: IProgramRepository,
        event_repo: IEventRepository,
    ) -> None:
        self.session = session
        self.program_repo = program_repo
        self.event_repo = event_repo
        logger.debug("Инициализация SessionRepository")

    async def get_list(self) -> list[Session]:
        query = text("SELECT * FROM session")
        try:
            result = await self.session.execute(query)
            sessions = []
            for row in result.mappings():
                program = await self.program_repo.get_by_id(row["program_id"])
                event = await self.event_repo.get_by_id(row["event_id"])
                sessions.append(Session(
                    session_id=row["id"],
                    program=program,
                    event=event,
                    start_time=row["start_time"],
                    end_time=row["end_time"],
                    type=row["type"],
                ))
            logger.debug("Успешно получено %d сессий", len(sessions))
            return sessions
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении списка сессий: %s", str(e), exc_info=True)
            return []

    async def get_by_id(self, session_id: int) -> Session | None:
        query = text("SELECT * FROM session WHERE id = :session_id")
        try:
            result = await self.session.execute(query, {"session_id": session_id})
            row = result.mappings().first()
            if row:
                program = await self.program_repo.get_by_id(row["program_id"])
                event = await self.event_repo.get_by_id(row["event_id"])
                logger.debug("Найдена сессия ID %d", session_id)
                return Session(
                    session_id=row["id"],
                    program=program,
                    event=event,
                    start_time=row["start_time"],
                    end_time=row["end_time"],
                    type=row["type"],
                )
            logger.warning("Сессия с ID %d не найдена", session_id)
            return None
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении сессии по ID %d: %s", session_id, str(e), exc_info=True)
            return None

    async def add(self, session: Session) -> Session:
        query = text("""
            INSERT INTO session (program_id, event_id, start_time, end_time, type)
            VALUES (:program_id, :event_id, :start_time, :end_time, :type)
            RETURNING id
        """)
        try:
            if session.program is None or session.event is None:
                raise ValueError("Программа и мероприятие обязательны")
            result = await self.session.execute(query, {
                "program_id": session.program.program_id,
                "event_id": session.event.event_id,
                "start_time": session.start_time,
                "end_time": session.end_time,
                "type": session.type,
            })
            new_id = result.scalar_one()
            await self.session.commit()
            logger.debug("Сессия успешно добавлена")
            session.session_id = new_id
        except IntegrityError:
            await self.session.rollback()
            logger.warning("Сессия уже существует")
            raise ValueError("Сессия с такими данными уже существует")
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error("Ошибка при добавлении сессии: %s", str(e), exc_info=True)
            raise
        return session

    async def update(self, update_session: Session) -> None:
        if update_session.program is None or update_session.event is None:
            raise ValueError("Программа и мероприятие обязательны")
        query = text("""
            UPDATE session
            SET program_id = :program_id,
                event_id = :event_id,
                start_time = :start_time,
                end_time = :end_time,
                type = :type
            WHERE id = :session_id
        """)
        try:
            result = await self.session.execute(query, {
                "program_id": update_session.program.program_id,
                "event_id": update_session.event.event_id,
                "start_time": update_session.start_time,
                "end_time": update_session.end_time,
                "type": update_session.type,
                "session_id": update_session.session_id,
            })
            if result.rowcount == 0:
                raise ValueError(f"Сессия с ID {update_session.session_id} не найдена")
            await self.session.commit()
            logger.debug("Сессия ID %d успешно обновлена", update_session.session_id)
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error("Ошибка при обновлении сессии ID %d: %s", update_session.session_id, str(e), exc_info=True)
            raise

    async def delete(self, session_id: int) -> None:
        query = text("DELETE FROM session WHERE id = :session_id")
        try:
            result = await self.session.execute(query, {"session_id": session_id})
            if result.rowcount == 0:
                raise ValueError(f"Сессия с ID {session_id} не найдена")
            await self.session.commit()
            logger.debug("Сессия ID %d успешно удалена", session_id)
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error("Ошибка при удалении сессии ID %d: %s", session_id, str(e), exc_info=True)
            raise

    async def get_sessions_by_event_id_ordered(self, event_id: int) -> list[Session]:
        query = text("SELECT * FROM session WHERE event_id = :event_id ORDER BY start_time")
        try:
            result = await self.session.execute(query, {"event_id": event_id})
            sessions = []
            for row in result.mappings():
                program = await self.program_repo.get_by_id(row["program_id"])
                event = await self.event_repo.get_by_id(row["event_id"])
                sessions.append(Session(
                    session_id=row["id"],
                    program=program,
                    event=event,
                    start_time=row["start_time"],
                    end_time=row["end_time"],
                    type=row["type"],
                ))
            return sessions
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении сессий для мероприятия ID %d: %s", event_id, str(e), exc_info=True)
            return []

    async def get_sessions_by_venue(self, venue_id: int) -> list[Session]:
        query = text("""
            SELECT s.* FROM session s
            JOIN program p ON s.program_id = p.id
            WHERE p.from_venue = :venue_id OR p.to_venue = :venue_id
        """)
        try:
            result = await self.session.execute(query, {"venue_id": venue_id})
            sessions = []
            for row in result.mappings():
                program = await self.program_repo.get_by_id(row["program_id"])
                event = await self.event_repo.get_by_id(row["event_id"])
                sessions.append(Session(
                    session_id=row["id"],
                    program=program,
                    event=event,
                    start_time=row["start_time"],
                    end_time=row["end_time"],
                    type=row["type"],
                ))
            return sessions
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении сессий по площадке ID %d: %s", venue_id, str(e), exc_info=True)
            return []

    async def delete_venue_from_session(self, event_id: int, venue_id: int) -> None:
        sessions = await self.get_sessions_by_event_id_ordered(event_id)
        if not sessions:
            raise ValueError("Сессии пусты")

        segments_to_remove = []
        for i, s in enumerate(sessions):
            if s.program is None:
                continue
            if (s.program.from_venue and s.program.from_venue.venue_id == venue_id) or \
               (s.program.to_venue and s.program.to_venue.venue_id == venue_id):
                segments_to_remove.append(i)

        if not segments_to_remove:
            raise ValueError(f"Площадка {venue_id} не найдена в сессии")

        prev_venue_id = None
        next_venue_id = None
        first_idx = segments_to_remove[0]
        if first_idx > 0:
            prev_s = sessions[first_idx - 1]
            if prev_s.program and prev_s.program.from_venue:
                prev_venue_id = prev_s.program.from_venue.venue_id
        last_idx = segments_to_remove[-1]
        if last_idx < len(sessions) - 1:
            next_s = sessions[last_idx + 1]
            if next_s.program and next_s.program.to_venue:
                next_venue_id = next_s.program.to_venue.venue_id

        for i in sorted(segments_to_remove, reverse=True):
            await self.delete(sessions[i].session_id)

        if prev_venue_id and next_venue_id:
            first_removed = sessions[segments_to_remove[0]]
            if first_removed.program is None:
                raise ValueError("Не удалось определить транспорт")
            transport = first_removed.program.type_transport
            new_program = await self.program_repo.get_by_venues(prev_venue_id, next_venue_id, transport)
            if new_program and first_removed.event:
                new_session = Session(
                    session_id=1,
                    program=new_program,
                    event=first_removed.event,
                    start_time=first_removed.start_time,
                    end_time=first_removed.start_time + timedelta(hours=2),
                    type=first_removed.type,
                )
                await self.add(new_session)

    async def change_transport(
        self, program_id: int, session_id: int, new_transport: str
    ) -> Session | None:
        try:
            result = await self.session.execute(text("SELECT * FROM session WHERE id = :session_id"), {"session_id": session_id})
            row = result.mappings().first()
            if not row:
                return None
            new_program = await self.program_repo.change_transport(program_id, new_transport)
            if not new_program:
                return None
            await self.session.execute(
                text("UPDATE session SET program_id = :new_program_id WHERE id = :session_id RETURNING id"),
                {"new_program_id": new_program.program_id, "session_id": session_id},
            )
            await self.session.commit()
            return await self.get_by_id(session_id)
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error("Ошибка при изменении транспорта сессии ID %d: %s", session_id, str(e), exc_info=True)
            raise

    async def insert_venue_after(
        self, event_id: int, new_venue_id: int, after_venue_id: int, transport: str
    ) -> None:
        sessions = await self.get_sessions_by_event_id_ordered(event_id)
        if not sessions:
            raise ValueError("Сессии пусты")

        target_session = None
        insert_after = False
        for s in sessions:
            if s.program is None:
                continue
            if s.program.to_venue and s.program.to_venue.venue_id == after_venue_id:
                target_session = s
                insert_after = True
                break
            if s.program.from_venue and s.program.from_venue.venue_id == after_venue_id:
                target_session = s
                break

        if target_session is None or target_session.program is None:
            raise ValueError(f"Площадка {after_venue_id} не найдена в сессиях")

        if insert_after:
            new_program = await self.program_repo.get_by_venues(after_venue_id, new_venue_id, transport)
            if new_program and target_session.event:
                new_s = Session(
                    session_id=1,
                    program=new_program,
                    event=target_session.event,
                    start_time=target_session.end_time,
                    end_time=target_session.end_time + timedelta(hours=2),
                    type=target_session.type,
                )
                await self.add(new_s)
        await self.session.commit()

    async def get_sessions_by_user_and_status_and_type(
        self, user_id: int, status: str, type_session: str
    ) -> list[Session]:
        try:
            sql = text("""
                SELECT s.* FROM session s
                JOIN Event e ON s.event_id = e.id
                JOIN users_event ue ON e.id = ue.event_id
                WHERE ue.users_id = :user_id AND e.status = :status AND s.type = :type
            """)
            result = await self.session.execute(sql, {"user_id": user_id, "status": status, "type": type_session})
            sessions = []
            for row in result.mappings():
                program = await self.program_repo.get_by_id(row["program_id"])
                event = await self.event_repo.get_by_id(row["event_id"])
                sessions.append(Session(
                    session_id=row["id"],
                    program=program,
                    event=event,
                    start_time=row["start_time"],
                    end_time=row["end_time"],
                    type=row["type"],
                ))
            return sessions
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении сессий: %s", str(e), exc_info=True)
            raise

    async def get_sessions_by_type(self, type_session: str) -> list[Session]:
        query = text("SELECT * FROM session WHERE type = :type")
        try:
            result = await self.session.execute(query, {"type": type_session})
            sessions = []
            for row in result.mappings():
                program = await self.program_repo.get_by_id(row["program_id"])
                event = await self.event_repo.get_by_id(row["event_id"])
                sessions.append(Session(
                    session_id=row["id"],
                    program=program,
                    event=event,
                    start_time=row["start_time"],
                    end_time=row["end_time"],
                    type=row["type"],
                ))
            return sessions
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении сессий по типу %s: %s", type_session, str(e), exc_info=True)
            return []

    async def get_session_parts(self, event_id: int) -> list[dict[str, Any]]:
        query = text("""
            SELECT
                s.id as session_id,
                p.id as program_id,
                fv.venue_id as from_venue_id,
                fv.name as from_venue_name,
                tv.venue_id as to_venue_id,
                tv.name as to_venue_name,
                p.type_transport as transport,
                p.price as price,
                s.start_time,
                s.end_time,
                s.type
            FROM session s
            JOIN program p ON s.program_id = p.id
            JOIN Venue fv ON p.from_venue = fv.venue_id
            JOIN Venue tv ON p.to_venue = tv.venue_id
            WHERE s.event_id = :event_id
            ORDER BY s.start_time
        """)
        try:
            result = await self.session.execute(query, {"event_id": event_id})
            parts = []
            for row in result.mappings():
                parts.append({
                    "session_id": row["session_id"],
                    "program_id": row["program_id"],
                    "from_venue": {"venue_id": row["from_venue_id"], "name": row["from_venue_name"]},
                    "to_venue": {"venue_id": row["to_venue_id"], "name": row["to_venue_name"]},
                    "transport": row["transport"],
                    "start_time": row["start_time"],
                    "end_time": row["end_time"],
                    "type": row["type"],
                    "price": row["price"],
                })
            return parts
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении частей сессии для event_id=%d: %s", event_id, str(e), exc_info=True)
            raise
