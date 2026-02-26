from __future__ import annotations

import logging

from typing import Any

from bson import Int64
from motor.motor_asyncio import AsyncIOMotorClient
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError
from pymongo.errors import PyMongoError

from abstract_repository.ivenue_repository import IVenueRepository
from abstract_repository.iactivity_repository import IActivityRepository
from models.activity import Activity


logger = logging.getLogger(__name__)


class ActivityRepository(IActivityRepository):
    def __init__(self, client: AsyncIOMotorClient[Any], venue_repo: IVenueRepository):
        self.db: AsyncIOMotorDatabase[Any] = client["event_db"]
        self.activities = self.db["activities"]
        self.venue_repo = venue_repo
        logger.debug("Инициализация ActivityRepository для MongoDB")

    async def get_list(self) -> list[Activity]:
        try:
            activities = []
            async for doc in self.activities.find().sort("_id"):
                venue = await self.venue_repo.get_by_id(doc["venue_id"])
                activities.append(
                    Activity(
                        activity_id=int(doc["_id"]),
                        duration=doc["duration"],
                        address=doc["address"],
                        activity_type=doc["activity_type"],
                        activity_time=doc["activity_time"],
                        venue=venue,
                    )
                )
            logger.debug("Успешно получено %d активностей", len(activities))
            return activities
        except PyMongoError as e:
            logger.error(
                "Ошибка при получении списка активностей: %s", str(e), exc_info=True
            )
            return []

    async def get_by_id(self, activity_id: int) -> Activity | None:
        try:
            doc = await self.activities.find_one({"_id": activity_id})
            if doc:
                venue = await self.venue_repo.get_by_id(doc["venue_id"])
                logger.debug(
                    "Найдена активность ID %d: %s", activity_id, doc["activity_type"]
                )
                return Activity(
                    activity_id=int(doc["_id"]),
                    duration=doc["duration"],
                    address=doc["address"],
                    activity_type=doc["activity_type"],
                    activity_time=doc["activity_time"],
                    venue=venue,
                )
            logger.warning("Активность с ID %d не найдена", activity_id)
            return None
        except PyMongoError as e:
            logger.error(
                "Ошибка при получении активности по ID %d: %s", activity_id, e
            )
            return None

    async def add(self, activity: Activity) -> Activity:
        try:
            if not activity.venue:
                logger.error("Отсутствуют данные о площадке")
                return activity

            venue = await self.venue_repo.get_by_id(activity.venue.venue_id)
            if not venue:
                logger.error("Площадка '%s' не найдена в базе данных", activity.venue)
                return activity

            last_id = await self.activities.find().sort("_id", -1).limit(1).next()
            new_id = Int64(last_id["_id"] + 1) if last_id else Int64(1)

            doc = {
                "_id": int(new_id),
                "duration": activity.duration,
                "address": activity.address,
                "activity_type": activity.activity_type,
                "activity_time": activity.activity_time,
                "venue_id": venue.venue_id,
            }

            result = await self.activities.insert_one(doc)
            activity.activity_id = result.inserted_id
            logger.debug(
                "Активность '%s' успешно добавлена с ID %s",
                activity.activity_type,
                str(result.inserted_id),
            )
            return activity

        except DuplicateKeyError:
            logger.warning("Активность с таким ID уже существует")
            return activity
        except PyMongoError as e:
            logger.error(
                "Ошибка при добавлении активности '%s': %s",
                activity.activity_type,
                str(e),
                exc_info=True,
            )
            return activity

    async def update(self, update_activity: Activity) -> None:
        try:
            if not update_activity.venue:
                logger.error("Отсутствуют данные о площадке")
                return

            venue = await self.venue_repo.get_by_id(update_activity.venue.venue_id)
            if not venue:
                logger.error(
                    "Площадка '%s' не найдена в базе данных", update_activity.venue
                )
                return

            result = await self.activities.update_one(
                {"_id": update_activity.activity_id},
                {
                    "$set": {
                        "duration": update_activity.duration,
                        "address": update_activity.address,
                        "activity_type": update_activity.activity_type,
                        "activity_time": update_activity.activity_time,
                        "venue_id": venue.venue_id,
                    }
                },
            )

            if result.modified_count == 0:
                logger.warning(
                    "Активность с ID %d не найдена для обновления",
                    update_activity.activity_id,
                )
            else:
                logger.debug(
                    "Активность ID %d успешно обновлена",
                    update_activity.activity_id,
                )

        except PyMongoError as e:
            logger.error(
                "Ошибка при обновлении активности ID %d: %s",
                update_activity.activity_id,
                str(e),
                exc_info=True,
            )

    async def delete(self, activity_id: int) -> None:
        try:
            result = await self.activities.delete_one({"_id": activity_id})
            if result.deleted_count == 0:
                logger.warning(
                    "Активность с ID %d не найдена для удаления", activity_id
                )
            else:
                logger.debug("Активность ID %d успешно удалена", activity_id)
        except PyMongoError as e:
            logger.error(
                "Ошибка при удалении активности ID %d: %s",
                activity_id,
                str(e),
                exc_info=True,
            )
