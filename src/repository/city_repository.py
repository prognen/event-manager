from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from abstract_repository.icity_repository import ICityRepository
from models.city import City


logger = logging.getLogger(__name__)


class CityRepository(ICityRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
        logger.debug("Инициализация CityRepository")

    async def get_list(self) -> list[City]:
        query = text("SELECT * FROM city")
        try:
            result = await self.session.execute(query)
            cities = [
                City(city_id=row["city_id"], name=row["name"])
                for row in result.mappings()
            ]
            logger.debug("Успешно получено %d городов", len(cities))
            return cities
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при получении списка городов: %s", str(e), exc_info=True
            )
            raise

    async def get_by_id(self, city_id: int) -> City | None:
        query = text("SELECT * FROM city WHERE city_id = :city_id")
        try:
            result = await self.session.execute(query, {"city_id": city_id})
            city_data = result.mappings().first()
            if city_data:
                logger.debug("Найден город ID %d: %s", city_id, city_data["name"])
                return City(city_id=city_data["city_id"], name=city_data["name"])
            logger.warning("Город с ID %d не найден", city_id)
            return None
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при получении города по ID %d: %s",
                city_id,
                str(e),
                exc_info=True,
            )
            return None

    async def add(self, city: City) -> City:
        query = text(
            """
            INSERT INTO city (name)
            VALUES (:name)
            RETURNING city_id
        """
        )
        try:
            row = await self.session.execute(query, {"name": city.name})
            new_id = row.scalar_one()
            await self.session.commit()
            logger.debug("Город '%s' успешно добавлен", city.name)
            city.city_id = new_id
        except IntegrityError:
            logger.warning("Город '%s' уже существует в базе данных", city.name)
            await self.session.rollback()
            raise
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при добавлении города '%s': %s",
                city.name,
                str(e),
                exc_info=True,
            )
            await self.session.rollback()
            raise
        return city

    async def update(self, update_city: City) -> None:
        query = text(
            """
            UPDATE city
            SET name = :name
            WHERE city_id = :city_id
        """
        )
        try:
            await self.session.execute(
                query, {"city_id": update_city.city_id, "name": update_city.name}
            )
            await self.session.commit()
            logger.debug("Город ID %d успешно обновлен", update_city.city_id)
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(
                "Ошибка при обновлении города ID %d: %s",
                update_city.city_id,
                str(e),
                exc_info=True,
            )

    async def delete(self, city_id: int) -> None:
        query = text("DELETE FROM city WHERE city_id = :city_id")
        try:
            await self.session.execute(query, {"city_id": city_id})
            await self.session.commit()
            logger.debug("Город ID %d успешно удален", city_id)
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при удалении города ID %d: %s", city_id, str(e), exc_info=True
            )
            await self.session.rollback()
