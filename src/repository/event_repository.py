from __future__ import annotations

import logging

from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from abstract_repository.iactivity_repository import IActivityRepository
from abstract_repository.ievent_repository import IEventRepository
from abstract_repository.ilodging_repository import ILodgingRepository
from abstract_repository.iuser_repository import IUserRepository
from models.activity import Activity
from models.event import Event
from models.lodging import Lodging
from models.user import User


logger = logging.getLogger(__name__)


class EventRepository(IEventRepository):
    def __init__(
        self,
        session: AsyncSession,
        user_repo: IUserRepository,
        activity_repo: IActivityRepository,
        lodging_repo: ILodgingRepository,
    ) -> None:
        self.session = session
        self.user_repo = user_repo
        self.activity_repo = activity_repo
        self.lodging_repo = lodging_repo
        logger.debug("Инициализация EventRepository")

    async def get_lodgings_by_event(self, event_id: int) -> list[Lodging]:
        query = text("SELECT lodging_id FROM event_lodgings WHERE event_id = :event_id")
        try:
            result = await self.session.execute(query, {"event_id": event_id})
            lodgings = []
            for row in result.fetchall():
                lodging = await self.lodging_repo.get_by_id(row[0])
                if lodging:
                    lodgings.append(lodging)
            return lodgings
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении размещений для мероприятия ID %d: %s", event_id, str(e), exc_info=True)
            return []

    async def get_users_by_event(self, event_id: int) -> list[User]:
        query = text("SELECT users_id FROM users_event WHERE event_id = :event_id")
        try:
            result = await self.session.execute(query, {"event_id": event_id})
            users = []
            for row in result.fetchall():
                user = await self.user_repo.get_by_id(row[0])
                if user:
                    users.append(user)
            return users
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении пользователей для мероприятия ID %d: %s", event_id, str(e), exc_info=True)
            return []

    async def get_activities_by_event(self, event_id: int) -> list[Activity]:
        query = text("SELECT activity_id FROM event_activity WHERE event_id = :event_id")
        try:
            result = await self.session.execute(query, {"event_id": event_id})
            activities = []
            for row in result.fetchall():
                activity = await self.activity_repo.get_by_id(row[0])
                if activity:
                    activities.append(activity)
            return activities
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении активностей для мероприятия ID %d: %s", event_id, str(e), exc_info=True)
            return []

    async def get_list(self) -> list[Event]:
        query = text("SELECT * FROM Event ORDER BY id")
        try:
            result = await self.session.execute(query)
            events = []
            for row in result.mappings():
                users = await self.get_users_by_event(row["id"])
                if not users:
                    continue
                activities = await self.get_activities_by_event(row["id"])
                lodgings = await self.get_lodgings_by_event(row["id"])
                events.append(Event(
                    event_id=row["id"],
                    status=row["status"],
                    users=users,
                    activities=activities,
                    lodgings=lodgings,
                ))
            logger.debug("Получено %d мероприятий", len(events))
            return events
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении списка мероприятий: %s", str(e), exc_info=True)
            return []

    async def get_by_id(self, event_id: int) -> Event | None:
        query = text("SELECT * FROM Event WHERE id = :event_id")
        try:
            result = await self.session.execute(query, {"event_id": event_id})
            row = result.mappings().first()
            if row:
                users = await self.get_users_by_event(row["id"])
                if not users:
                    return None
                activities = await self.get_activities_by_event(row["id"])
                lodgings = await self.get_lodgings_by_event(row["id"])
                logger.debug("Найдено мероприятие ID %d", event_id)
                return Event(
                    event_id=row["id"],
                    status=row["status"],
                    users=users,
                    activities=activities,
                    lodgings=lodgings,
                )
            logger.warning("Мероприятие ID %d не найдено", event_id)
            return None
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении мероприятия по ID %d: %s", event_id, str(e), exc_info=True)
            return None

    async def get_event_by_session_id(self, session_id: int) -> Event | None:
        query = text("SELECT event_id FROM session WHERE id = :session_id")
        try:
            result = await self.session.execute(query, {"session_id": session_id})
            row = result.mappings().first()
            if row:
                return await self.get_by_id(row["event_id"])
            return None
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении мероприятия по session_id %d: %s", session_id, str(e), exc_info=True)
            return None

    async def add(self, event: Event) -> Event:
        query = text("INSERT INTO Event (status) VALUES (:status) RETURNING id")
        activity_query = text("INSERT INTO event_activity (event_id, activity_id) VALUES (:event_id, :activity_id)")
        lodging_query = text("INSERT INTO event_lodgings (event_id, lodging_id) VALUES (:event_id, :lodging_id)")
        user_query = text("INSERT INTO users_event (event_id, users_id) VALUES (:event_id, :users_id)")
        try:
            result = await self.session.execute(query, {"status": event.status})
            event_id = result.scalar_one()
            event.event_id = event_id

            for user in event.users:
                await self.session.execute(user_query, {"event_id": event_id, "users_id": user.user_id})

            for activity in event.activities:
                await self.session.execute(activity_query, {"event_id": event_id, "activity_id": activity.activity_id})

            for lodging in event.lodgings:
                await self.session.execute(lodging_query, {"event_id": event_id, "lodging_id": lodging.lodging_id})

            await self.session.commit()
            logger.debug("Мероприятие создано с ID %d", event_id)
        except IntegrityError:
            await self.session.rollback()
            logger.warning("Дублирующееся мероприятие")
            raise ValueError("Мероприятие с такими данными уже существует")
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error("Ошибка при добавлении мероприятия: %s", str(e), exc_info=True)
            raise
        return event

    async def update(self, update_event: Event) -> None:
        check_query = text("SELECT 1 FROM Event WHERE id = :event_id")
        update_query = text("UPDATE Event SET status = :status WHERE id = :event_id")
        try:
            result = await self.session.execute(check_query, {"event_id": update_event.event_id})
            if result.fetchone() is None:
                raise ValueError(f"Мероприятие ID {update_event.event_id} не найдено")

            await self.session.execute(update_query, {"status": update_event.status, "event_id": update_event.event_id})
            await self.session.execute(text("DELETE FROM users_event WHERE event_id = :event_id"), {"event_id": update_event.event_id})
            await self.session.execute(text("DELETE FROM event_activity WHERE event_id = :event_id"), {"event_id": update_event.event_id})
            await self.session.execute(text("DELETE FROM event_lodgings WHERE event_id = :event_id"), {"event_id": update_event.event_id})

            for user in update_event.users:
                await self.session.execute(text("INSERT INTO users_event (event_id, users_id) VALUES (:event_id, :users_id)"), {"event_id": update_event.event_id, "users_id": user.user_id})
            for activity in update_event.activities:
                await self.session.execute(text("INSERT INTO event_activity (event_id, activity_id) VALUES (:event_id, :activity_id)"), {"event_id": update_event.event_id, "activity_id": activity.activity_id})
            for lodging in update_event.lodgings:
                await self.session.execute(text("INSERT INTO event_lodgings (event_id, lodging_id) VALUES (:event_id, :lodging_id)"), {"event_id": update_event.event_id, "lodging_id": lodging.lodging_id})

            await self.session.commit()
            logger.debug("Мероприятие ID %d успешно обновлено", update_event.event_id)
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error("Ошибка при обновлении мероприятия ID %d: %s", update_event.event_id, str(e), exc_info=True)
            raise

    async def delete(self, event_id: int) -> None:
        try:
            await self.session.execute(text("DELETE FROM users_event WHERE event_id = :event_id"), {"event_id": event_id})
            await self.session.execute(text("DELETE FROM event_activity WHERE event_id = :event_id"), {"event_id": event_id})
            await self.session.execute(text("DELETE FROM event_lodgings WHERE event_id = :event_id"), {"event_id": event_id})
            result = await self.session.execute(text("DELETE FROM Event WHERE id = :event_id"), {"event_id": event_id})
            if result.rowcount == 0:
                raise ValueError(f"Мероприятие с ID {event_id} не найдено")
            await self.session.commit()
            logger.debug("Мероприятие ID %d удалено", event_id)
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error("Ошибка при удалении мероприятия ID %d: %s", event_id, str(e), exc_info=True)
            raise

    async def search(self, event_dict: dict[str, Any]) -> list[Event]:
        sql = """SELECT DISTINCT e.*
            FROM Event e
            JOIN session s ON e.id = s.event_id
            JOIN program p ON s.program_id = p.id
            WHERE e.status != 'Завершено'
        """
        params: dict[str, Any] = {}
        if "start_time" in event_dict:
            sql += " AND s.start_time >= :start_time"
            params["start_time"] = event_dict["start_time"]
        if "end_time" in event_dict:
            sql += " AND s.end_time <= :end_time"
            params["end_time"] = event_dict["end_time"]
        if "from_venue" in event_dict:
            sql += " AND p.from_venue = :from_venue"
            params["from_venue"] = event_dict["from_venue"]
        if "to_venue" in event_dict:
            sql += " AND p.to_venue = :to_venue"
            params["to_venue"] = event_dict["to_venue"]
        try:
            result = await self.session.execute(text(sql), params)
            events = []
            for row in result.mappings():
                users = await self.get_users_by_event(row["id"])
                if not users:
                    continue
                events.append(Event(
                    event_id=row["id"],
                    status=row["status"],
                    users=users,
                    activities=await self.get_activities_by_event(row["id"]),
                    lodgings=await self.get_lodgings_by_event(row["id"]),
                ))
            return events
        except SQLAlchemyError as e:
            logger.error("Ошибка при поиске мероприятия: %s", str(e), exc_info=True)
            return []

    async def complete(self, event_id: int) -> None:
        try:
            await self.session.execute(text("UPDATE Event SET status = 'Завершено' WHERE id = :event_id"), {"event_id": event_id})
            await self.session.commit()
            logger.debug("Мероприятие ID %d завершено", event_id)
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error("Ошибка при завершении мероприятия ID %d: %s", event_id, str(e), exc_info=True)

    async def link_activities(self, event_id: int, activity_ids: list[int]) -> None:
        try:
            await self.session.execute(text("DELETE FROM event_activity WHERE event_id = :event_id"), {"event_id": event_id})
            for activity_id in activity_ids:
                await self.session.execute(text("INSERT INTO event_activity (event_id, activity_id) VALUES (:event_id, :activity_id)"), {"event_id": event_id, "activity_id": activity_id})
            await self.session.commit()
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error("Ошибка при связывании активностей: %s", str(e), exc_info=True)
            raise

    async def link_lodgings(self, event_id: int, lodging_ids: list[int]) -> None:
        try:
            await self.session.execute(text("DELETE FROM event_lodgings WHERE event_id = :event_id"), {"event_id": event_id})
            for lodging_id in lodging_ids:
                await self.session.execute(text("INSERT INTO event_lodgings (event_id, lodging_id) VALUES (:event_id, :lodging_id)"), {"event_id": event_id, "lodging_id": lodging_id})
            await self.session.commit()
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error("Ошибка при связывании размещений: %s", str(e), exc_info=True)
            raise

    async def get_events_for_user(self, user_id: int, status: str) -> list[Event]:
        try:
            sql = """SELECT e.* FROM Event e
                    JOIN users_event ue ON ue.event_id = e.id
                    WHERE e.status = :status AND ue.users_id = :user_id"""
            result = await self.session.execute(text(sql), {"user_id": user_id, "status": status})
            events = []
            for row in result.fetchall():
                users = await self.get_users_by_event(row.id)
                if not users:
                    continue
                events.append(Event(
                    event_id=row.id,
                    status=status,
                    users=users,
                    activities=await self.get_activities_by_event(row.id),
                    lodgings=await self.get_lodgings_by_event(row.id),
                ))
            return events
        except SQLAlchemyError as e:
            logger.error("Ошибка при поиске мероприятий: %s", str(e), exc_info=True)
            return []

    async def link_users(self, event_id: int, user_ids: list[int]) -> None:
        try:
            await self.session.execute(text("DELETE FROM users_event WHERE event_id = :event_id"), {"event_id": event_id})
            for user_id in user_ids:
                await self.session.execute(text("INSERT INTO users_event (event_id, users_id) VALUES (:event_id, :users_id)"), {"event_id": event_id, "users_id": user_id})
            await self.session.commit()
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error("Ошибка при связывании пользователей: %s", str(e), exc_info=True)
            raise
