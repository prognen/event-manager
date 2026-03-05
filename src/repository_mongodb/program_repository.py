from __future__ import annotations

import logging

from typing import Any

from bson import Int64
from motor.motor_asyncio import AsyncIOMotorClient
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError
from pymongo.errors import PyMongoError

from abstract_repository.ivenue_repository import IVenueRepository
from abstract_repository.iprogram_repository import IProgramRepository
from models.program import Program


logger = logging.getLogger(__name__)


class ProgramRepository(IProgramRepository):
    def __init__(self, client: AsyncIOMotorClient[Any], venue_repo: IVenueRepository):
        self.db: AsyncIOMotorDatabase[Any] = client["event_db"]
        self.collection = self.db["programs"]
        self.venue_repo = venue_repo
        logger.debug("Инициализация ProgramRepository для MongoDB")

    async def get_list(self) -> list[Program]:
        try:
            programs = []
            async for doc in self.collection.find().sort("_id"):
                start_venue = await self.venue_repo.get_by_id(
                    doc["start_venue_id"]
                )
                end_venue = await self.venue_repo.get_by_id(
                    doc["end_venue_id"]
                )

                if not start_venue or not end_venue:
                    logger.warning(f"Не удалось найти площадки для программы {doc['_id']}")
                    continue

                programs.append(
                    Program(
                        program_id=int(doc["_id"]),
                        transfer_type=doc["transfer_type"],
                        cost=doc["price"],
                        transfer_duration_minutes=doc["transfer_duration_minutes"],
                        start_venue=start_venue,
                        end_venue=end_venue,
                    )
                )

            logger.debug("Успешно получено %d программ", len(programs))
            return programs
        except PyMongoError as e:
            logger.error(
                "Ошибка при получении списка программ: %s", str(e), exc_info=True
            )
            return []

    async def get_by_id(self, program_id: int) -> Program | None:
        try:
            doc = await self.collection.find_one({"_id": program_id})
            if not doc:
                logger.warning("Программа с ID %d не найдена", program_id)
                return None

            start_venue = await self.venue_repo.get_by_id(doc["start_venue_id"])
            end_venue = await self.venue_repo.get_by_id(doc["end_venue_id"])

            if not start_venue or not end_venue:
                logger.warning(f"Не удалось найти площадки для программы {doc['_id']}")
                return None

            logger.debug("Найдена программа ID %d", program_id)
            return Program(
                program_id=int(doc["_id"]),
                transfer_type=doc["transfer_type"],
                cost=doc["price"],
                transfer_duration_minutes=doc["transfer_duration_minutes"],
                start_venue=start_venue,
                end_venue=end_venue,
            )
        except PyMongoError as e:
            logger.error(
                "Ошибка при получении программы по ID %d: %s",
                program_id,
                str(e),
                exc_info=True,
            )
            return None

    async def add(self, program: Program) -> Program:
        try:
            if (
                not program.start_venue
                or not program.end_venue
            ):
                logger.error("Отсутствуют данные о площадках")
                raise ValueError("Both venues are required")

            last_id = await self.collection.find().sort("_id", -1).limit(1).next()
            new_id = Int64(last_id["_id"] + 1) if last_id else Int64(1)

            doc = {
                "_id": int(new_id),
                "transfer_type": program.transfer_type,
                "price": int(program.cost),
                "transfer_duration_minutes": int(program.transfer_duration_minutes),
                "start_venue_id": program.start_venue.venue_id,
                "end_venue_id": program.end_venue.venue_id,
            }

            await self.collection.insert_one(doc)
            logger.debug("Программа успешно добавлена с ID %s", new_id)
            program.program_id = new_id
            return program
        except DuplicateKeyError:
            logger.warning("Такая программа уже существует")
            raise
        except PyMongoError as e:
            logger.error("Ошибка при добавлении программы: %s", str(e), exc_info=True)
            raise

    async def update(self, update_program: Program) -> None:
        try:
            if not update_program.program_id:
                logger.error("Отсутствует ID программы для обновления")
                raise ValueError("Program ID is required")

            if (
                not update_program.start_venue
                or not update_program.end_venue
            ):
                logger.error("Отсутствуют данные о площадках")
                raise ValueError("Both venues are required")

            await self.collection.update_one(
                {"_id": int(update_program.program_id)},
                {
                    "$set": {
                        "transfer_type": update_program.transfer_type,
                        "price": int(update_program.cost),
                        "transfer_duration_minutes": int(update_program.transfer_duration_minutes),
                        "start_venue_id": update_program.start_venue.venue_id,
                        "end_venue_id": update_program.end_venue.venue_id,
                    }
                },
            )
            logger.debug("Программа успешно обновлена")
        except PyMongoError as e:
            logger.error(
                "Ошибка при обновлении программы с ID %s: %s",
                update_program.program_id,
                str(e),
                exc_info=True,
            )
            raise

    async def delete(self, program_id: int) -> None:
        try:
            result = await self.collection.delete_one({"_id": program_id})
            if result.deleted_count == 0:
                logger.warning(
                    "Программа с ID %d не найдена для удаления", program_id
                )
            else:
                logger.debug("Программа ID %d успешно удалена", program_id)
        except PyMongoError as e:
            logger.error(
                "Ошибка при удалении программы с ID %d: %s",
                program_id,
                str(e),
                exc_info=True,
            )
            raise

    async def get_by_venues(
        self, start_venue_id: int, end_venue_id: int, transfer_type: str
    ) -> Program | None:
        try:
            doc = await self.collection.find_one(
                {
                    "start_venue_id": start_venue_id,
                    "end_venue_id": end_venue_id,
                    "transfer_type": transfer_type,
                }
            )

            if not doc:
                logger.warning(
                    "Программа между площадками %d и %d не найдена",
                    start_venue_id,
                    end_venue_id,
                )
                return None

            start_venue = await self.venue_repo.get_by_id(doc["start_venue_id"])
            end_venue = await self.venue_repo.get_by_id(doc["end_venue_id"])

            if not start_venue or not end_venue:
                logger.warning(f"Не удалось найти площадки для программы {doc['_id']}")
                return None

            logger.debug("Найдена программа ID %s", str(doc["_id"]))
            return Program(
                program_id=int(doc["_id"]),
                transfer_type=transfer_type,
                cost=doc["price"],
                transfer_duration_minutes=doc["transfer_duration_minutes"],
                start_venue=start_venue,
                end_venue=end_venue,
            )
        except PyMongoError as e:
            logger.error(
                "Ошибка при получении программы по площадкам: %s",
                str(e),
                exc_info=True,
            )
            return None

    async def change_transfer_type(
        self, program_id: int, new_transfer_type: str
    ) -> Program | None:
        current_program = await self.get_by_id(program_id)
        if not current_program:
            logger.warning("Программа с ID %d не найдена", program_id)
            return None
        if not current_program.start_venue or not current_program.end_venue:
            logger.warning("Площадки в программе с ID %d не найдены", program_id)
            return None

        return await self.get_by_venues(
            start_venue_id=current_program.start_venue.venue_id,
            end_venue_id=current_program.end_venue.venue_id,
            transfer_type=new_transfer_type,
        )
