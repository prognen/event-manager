from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from abstract_repository.iactivity_repository import IActivityRepository
from abstract_repository.ivenue_repository import IVenueRepository
from models.activity import Activity


logger = logging.getLogger(__name__)


class ActivityRepository(IActivityRepository):
    def __init__(self, session: AsyncSession, venue_repo: IVenueRepository) -> None:
        self.session = session
        self.venue_repo = venue_repo
        logger.debug("Инициализация ActivityRepository")

    async def get_list(self) -> list[Activity]:
        query = text("SELECT * FROM Activity ORDER BY id")
        try:
            result = await self.session.execute(query)
            activities = []
            for row in result.mappings():
                venue = await self.venue_repo.get_by_id(row["venue"]) if row["venue"] else None
                activities.append(Activity(
                    activity_id=row["id"],
                    duration=row["duration"],
                    address=row["address"],
                    activity_type=row["activity_type"],
                    activity_time=row["activity_time"],
                    venue=venue,
                ))
            logger.debug("Успешно получено %d активностей", len(activities))
            return activities
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении списка активностей: %s", str(e), exc_info=True)
            return []

    async def get_by_id(self, activity_id: int) -> Activity | None:
        query = text("SELECT * FROM Activity WHERE id = :activity_id")
        try:
            result = await self.session.execute(query, {"activity_id": activity_id})
            row = result.mappings().first()
            if row:
                venue = await self.venue_repo.get_by_id(row["venue"]) if row["venue"] else None
                logger.debug("Найдена активность ID %d", activity_id)
                return Activity(
                    activity_id=row["id"],
                    duration=row["duration"],
                    address=row["address"],
                    activity_type=row["activity_type"],
                    activity_time=row["activity_time"],
                    venue=venue,
                )
            logger.warning("Активность с ID %d не найдена", activity_id)
            return None
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении активности по ID %d: %s", activity_id, str(e), exc_info=True)
            return None

    async def add(self, activity: Activity) -> Activity:
        query = text("""
            INSERT INTO Activity (duration, address, activity_type, activity_time, Venue)
            VALUES (:duration, :address, :activity_type, :activity_time, :venue)
            RETURNING id
        """)
        try:
            result = await self.session.execute(query, {
                "duration": activity.duration,
                "address": activity.address,
                "activity_type": activity.activity_type,
                "activity_time": activity.activity_time,
                "venue": activity.venue.venue_id if activity.venue else None,
            })
            new_id = result.scalar_one()
            await self.session.commit()
            logger.debug("Активность '%s' успешно добавлена", activity.activity_type)
            activity.activity_id = new_id
        except IntegrityError:
            logger.warning("Активность '%s' уже существует", activity.activity_type)
            await self.session.rollback()
            raise ValueError("Активность с таким типом уже существует")
        except SQLAlchemyError as e:
            logger.error("Ошибка при добавлении активности: %s", str(e), exc_info=True)
            await self.session.rollback()
            raise
        return activity

    async def update(self, update_activity: Activity) -> None:
        query = text("""
            UPDATE Activity
            SET duration = :duration,
                address = :address,
                activity_type = :activity_type,
                activity_time = :activity_time,
                Venue = :venue
            WHERE id = :activity_id
        """)
        try:
            await self.session.execute(query, {
                "duration": update_activity.duration,
                "address": update_activity.address,
                "activity_type": update_activity.activity_type,
                "activity_time": update_activity.activity_time,
                "venue": update_activity.venue.venue_id if update_activity.venue else None,
                "activity_id": update_activity.activity_id,
            })
            await self.session.commit()
            logger.debug("Активность ID %d успешно обновлена", update_activity.activity_id)
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error("Ошибка при обновлении активности ID %d: %s", update_activity.activity_id, str(e), exc_info=True)
            raise

    async def delete(self, activity_id: int) -> None:
        query = text("DELETE FROM Activity WHERE id = :activity_id")
        try:
            result = await self.session.execute(query, {"activity_id": activity_id})
            if result.rowcount == 0:
                raise ValueError(f"Активность с ID {activity_id} не найдена")
            await self.session.commit()
            logger.debug("Активность ID %d успешно удалена", activity_id)
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error("Ошибка при удалении активности ID %d: %s", activity_id, str(e), exc_info=True)
            raise
