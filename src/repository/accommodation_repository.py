from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from abstract_repository.iaccommodation_repository import IAccommodationRepository
from abstract_repository.icity_repository import ICityRepository
from models.accommodation import Accommodation


logger = logging.getLogger(__name__)


class AccommodationRepository(IAccommodationRepository):
    def __init__(self, session: AsyncSession, city_repo: ICityRepository):
        self.session = session
        self.city_repo = city_repo
        logger.debug("Инициализация AccommodationRepository")

    async def get_list(self) -> list[Accommodation]:
        query = text("SELECT * FROM accommodations ORDER BY id")
        try:
            result = await self.session.execute(query)
            rows = result.mappings()
            accommodations = [
                Accommodation(
                    accommodation_id=row["id"],
                    price=row["price"],
                    address=row["address"],
                    name=row["name"],
                    type=row["type"],
                    rating=row["rating"],
                    check_in=row["check_in"],
                    check_out=row["check_out"],
                    city=await self.city_repo.get_by_id(row["city"]),
                )
                for row in rows
            ]
            logger.debug("Успешно получено %d размещений", len(accommodations))
            return accommodations
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при получении списка размещений: %s", str(e), exc_info=True
            )
            raise

    async def get_by_id(self, accommodation_id: int) -> Accommodation | None:
        query = text("SELECT * FROM accommodations WHERE id = :accommodation_id")
        try:
            result = await self.session.execute(
                query, {"accommodation_id": accommodation_id}
            )
            row = result.mappings().first()
            if row:
                logger.debug(
                    "Найдено размещение ID %d: %s", accommodation_id, row["name"]
                )
                return Accommodation(
                    accommodation_id=row["id"],
                    price=row["price"],
                    address=row["address"],
                    name=row["name"],
                    type=row["type"],
                    rating=row["rating"],
                    check_in=row["check_in"],
                    check_out=row["check_out"],
                    city=await self.city_repo.get_by_id(row["city"]),
                )
            logger.warning("Размещение с ID %d не найдено", accommodation_id)
            return None
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при получении размещения по ID %d: %s",
                accommodation_id,
                str(e),
                exc_info=True,
            )
            return None

    async def add(self, accommodation: Accommodation) -> Accommodation:
        query = text(
            """
            INSERT INTO accommodations (price, address, name, type, rating, check_in, check_out, city)
            VALUES (:price, :address, :name, :type, :rating, :check_in, :check_out, :city)
            RETURNING id
        """
        )
        try:
            if accommodation.city is None:
                logger.error("Отсутствуют данные о городе")
                raise ValueError(
                    "Невозможно добавить размещение: отсутствуют данные о городе"
                )
            row = await self.session.execute(
                query,
                {
                    "price": accommodation.price,
                    "address": accommodation.address,
                    "name": accommodation.name,
                    "type": accommodation.type,
                    "rating": accommodation.rating,
                    "check_in": accommodation.check_in,
                    "check_out": accommodation.check_out,
                    "city": accommodation.city.city_id,
                },
            )
            new_id = row.scalar_one()
            await self.session.commit()
            logger.debug("Размещение '%s' успешно добавлено", accommodation.name)
            accommodation.accommodation_id = new_id
        except IntegrityError:
            logger.warning(
                "Размещение '%s' уже существует в базе данных", accommodation.name
            )
            await self.session.rollback()
            raise ValueError("Размещение с такими данными уже существует")
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при добавлении размещения '%s': %s",
                accommodation.name,
                str(e),
                exc_info=True,
            )
            await self.session.rollback()
            raise
        return accommodation

    async def update(self, update_accommodation: Accommodation) -> None:
        if update_accommodation.city is None:
            logger.error("Отсутствуют данные о городе")
            return
        query = text(
            """
            UPDATE accommodations
            SET price = :price,
                address = :address,
                name = :name,
                type = :type,
                rating = :rating,
                check_in = :check_in,
                check_out = :check_out,
                city = :city
            WHERE id = :accommodation_id
        """
        )
        try:
            await self.session.execute(
                query,
                {
                    "price": update_accommodation.price,
                    "address": update_accommodation.address,
                    "name": update_accommodation.name,
                    "type": update_accommodation.type,
                    "rating": update_accommodation.rating,
                    "check_in": update_accommodation.check_in,
                    "check_out": update_accommodation.check_out,
                    "city": update_accommodation.city.city_id,
                    "accommodation_id": update_accommodation.accommodation_id,
                },
            )
            logger.debug(
                "Размещение ID %d успешно обновлено",
                update_accommodation.accommodation_id,
            )
            await self.session.commit()
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при обновлении размещения ID %d: %s",
                update_accommodation.accommodation_id,
                str(e),
                exc_info=True,
            )
            await self.session.rollback()

    async def delete(self, accommodation_id: int) -> None:
        query = text("DELETE FROM accommodations WHERE id = :accommodation_id")
        try:
            await self.session.execute(query, {"accommodation_id": accommodation_id})
            await self.session.commit()
            logger.debug("Размещение ID %d успешно удалено", accommodation_id)
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при удалении размещения ID %d: %s",
                accommodation_id,
                str(e),
                exc_info=True,
            )
