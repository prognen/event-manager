from __future__ import annotations

import logging

from typing import Any

from bson import Int64
from motor.motor_asyncio import AsyncIOMotorClient
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError
from pymongo.errors import PyMongoError

from abstract_repository.ivenue_repository import IVenueRepository
from models.venue import Venue


logger = logging.getLogger(__name__)


class VenueRepository(IVenueRepository):
    def __init__(self, client: AsyncIOMotorClient[Any]):
        self.db: AsyncIOMotorDatabase[Any] = client["event_db"]
        self.collection = self.db["venues"]
        logger.debug("Инициализация VenueRepository для MongoDB")

    async def get_list(self) -> list[Venue]:
        try:
            venues = []
            async for doc in self.collection.find().sort("_id"):
                venues.append(Venue(venue_id=int(doc["_id"]), name=doc["name"]))

            logger.debug("Успешно получено %d площадок", len(venues))
            return venues
        except PyMongoError as e:
            logger.error(
                "Ошибка при получении списка площадок: %s", str(e), exc_info=True
            )
            raise

    async def get_by_id(self, venue_id: int) -> Venue | None:
        try:
            doc = await self.collection.find_one({"_id": int(str(venue_id))})
            if not doc:
                logger.warning("Площадка с ID %s не найдена", venue_id)
                return None

            logger.debug("Найдена площадка ID %d: %s", venue_id, doc["name"])
            return Venue(venue_id=int(doc["_id"]), name=doc["name"])
        except PyMongoError as e:
            logger.error(
                "Ошибка при получении площадки по ID %s: %s",
                venue_id,
                str(e),
                exc_info=True,
            )
            return None

    async def add(self, venue: Venue) -> Venue:
        try:
            last_id = await self.collection.find().sort("_id", -1).limit(1).next()
            new_id = Int64(last_id["_id"] + 1) if last_id else Int64(1)
            doc = {"_id": int(new_id), "name": venue.name}

            result = await self.collection.insert_one(doc)
            new_id = result.inserted_id
            logger.debug("Площадка '%s' успешно добавлена с ID %d", venue.name, new_id)
            venue.venue_id = new_id
            return venue
        except DuplicateKeyError:
            logger.warning("Площадка с именем '%s' уже существует", venue.name)
            raise
        except PyMongoError as e:
            logger.error(
                "Ошибка при добавлении площадки '%s': %s",
                venue.name,
                str(e),
                exc_info=True,
            )
            raise

    async def update(self, update_venue: Venue) -> None:
        try:
            if not update_venue.venue_id:
                logger.error("Отсутствует ID площадки для обновления")
                raise ValueError("Venue ID is required")

            await self.collection.update_one(
                {"_id": int(str(update_venue.venue_id))},
                {"$set": {"name": update_venue.name}},
            )
            logger.debug("Площадка ID %s успешно обновлена", update_venue.venue_id)
        except PyMongoError as e:
            logger.error(
                "Ошибка при обновлении площадки ID %s: %s",
                update_venue.venue_id,
                str(e),
                exc_info=True,
            )
            raise

    async def delete(self, venue_id: int) -> None:
        try:
            result = await self.collection.delete_one({"_id": int(str(venue_id))})
            if result.deleted_count == 0:
                logger.warning("Площадка с ID %d не найдена для удаления", venue_id)
            else:
                logger.debug("Площадка ID %d успешно удалена", venue_id)
        except PyMongoError as e:
            logger.error(
                "Ошибка при удалении площадки ID %d: %s", venue_id, str(e), exc_info=True
            )
            raise
