from __future__ import annotations

import logging

from typing import Any

from bson import Int64
from motor.motor_asyncio import AsyncIOMotorClient
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import PyMongoError

from abstract_repository.ilodging_repository import ILodgingRepository
from abstract_repository.ivenue_repository import IVenueRepository
from models.lodging import Lodging


logger = logging.getLogger(__name__)


class LodgingRepository(ILodgingRepository):
    def __init__(self, client: AsyncIOMotorClient[Any], venue_repo: IVenueRepository):
        self.db: AsyncIOMotorDatabase[Any] = client["event_db"]
        self.collection = self.db["lodgings"]
        self.venue_repo = venue_repo
        logger.debug("Инициализация LodgingRepository для MongoDB")

    async def get_list(self) -> list[Lodging]:
        try:
            lodgings = []
            async for doc in self.collection.find().sort("_id"):
                venue = await self.venue_repo.get_by_id(doc["venue_id"])
                if not venue:
                    logger.warning(
                        f"Площадка с ID {doc['venue_id']} не найдена для размещения {doc['_id']}"
                    )
                    continue

                lodgings.append(
                    Lodging(
                        lodging_id=int(doc["_id"]),
                        price=doc["price"],
                        address=doc["address"],
                        name=doc["name"],
                        type=doc["type"],
                        rating=doc["rating"],
                        check_in=doc["check_in"],
                        check_out=doc["check_out"],
                        venue=venue,
                    )
                )

            logger.debug("Успешно получено %d размещений", len(lodgings))
            return lodgings
        except PyMongoError as e:
            logger.error(
                "Ошибка при получении списка размещений: %s", str(e), exc_info=True
            )
            raise

    async def get_by_id(self, lodging_id: int) -> Lodging | None:
        try:
            doc = await self.collection.find_one({"_id": int(lodging_id)})
            if not doc:
                logger.warning("Размещение с ID %d не найдено", lodging_id)
                return None

            venue = await self.venue_repo.get_by_id(doc["venue_id"])
            if not venue:
                logger.warning(
                    f"Площадка с ID {doc['venue_id']} не найдена для размещения {doc['_id']}"
                )
                return None

            logger.debug("Найдено размещение ID %d: %s", lodging_id, doc["name"])
            return Lodging(
                lodging_id=int(doc["_id"]),
                price=doc["price"],
                address=doc["address"],
                name=doc["name"],
                type=doc["type"],
                rating=doc["rating"],
                check_in=doc["check_in"],
                check_out=doc["check_out"],
                venue=venue,
            )
        except PyMongoError as e:
            logger.error(
                "Ошибка при получении размещения по ID %s: %s",
                lodging_id,
                str(e),
                exc_info=True,
            )
            return None

    async def add(self, lodging: Lodging) -> Lodging:
        try:
            if lodging.venue is None:
                logger.error("Отсутствуют данные о площадке")
                raise ValueError("Venue is required")
            last_id = await self.collection.find().sort("_id", -1).limit(1).next()
            new_id = Int64(last_id["_id"] + 1) if last_id else Int64(1)
            doc = {
                "_id": int(new_id),
                "price": lodging.price,
                "address": lodging.address,
                "name": lodging.name,
                "type": lodging.type,
                "rating": lodging.rating,
                "check_in": lodging.check_in,
                "check_out": lodging.check_out,
                "venue_id": lodging.venue.venue_id,
            }

            result = await self.collection.insert_one(doc)
            new_id = result.inserted_id
            logger.debug(
                "Размещение '%s' успешно добавлено с ID %d", lodging.name, new_id
            )
            lodging.lodging_id = new_id
            return lodging
        except PyMongoError as e:
            logger.error(
                "Ошибка при добавлении размещения '%s': %s",
                lodging.name,
                str(e),
                exc_info=True,
            )
            raise

    async def update(self, update_lodging: Lodging) -> None:
        try:
            if update_lodging.venue is None:
                logger.error("Отсутствуют данные о площадке")
                raise ValueError("Venue is required")

            if not update_lodging.lodging_id:
                logger.error("Отсутствует ID размещения для обновления")
                raise ValueError("Lodging ID is required")

            await self.collection.update_one(
                {"_id": int(str(update_lodging.lodging_id))},
                {
                    "$set": {
                        "price": update_lodging.price,
                        "address": update_lodging.address,
                        "name": update_lodging.name,
                        "type": update_lodging.type,
                        "rating": update_lodging.rating,
                        "check_in": update_lodging.check_in,
                        "check_out": update_lodging.check_out,
                        "venue_id": update_lodging.venue.venue_id,
                    }
                },
            )
            logger.debug(
                "Размещение ID %s успешно обновлено",
                update_lodging.lodging_id,
            )
        except PyMongoError as e:
            logger.error(
                "Ошибка при обновлении размещения ID %s: %s",
                update_lodging.lodging_id,
                str(e),
                exc_info=True,
            )
            raise

    async def delete(self, lodging_id: int) -> None:
        try:
            result = await self.collection.delete_one(
                {"_id": int(str(lodging_id))}
            )
            if result.deleted_count == 0:
                logger.warning(
                    "Размещение с ID %d не найдено для удаления", lodging_id
                )
            else:
                logger.debug("Размещение ID %d успешно удалено", lodging_id)
        except PyMongoError as e:
            logger.error(
                "Ошибка при удалении размещения ID %d: %s",
                lodging_id,
                str(e),
                exc_info=True,
            )
            raise
