from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from abstract_repository.icity_repository import ICityRepository
from abstract_repository.ientertainment_repository import IEntertainmentRepository
from models.entertainment import Entertainment


logger = logging.getLogger(__name__)


class EntertainmentRepository(IEntertainmentRepository):
    def __init__(self, session: AsyncSession, city_repo: ICityRepository):
        self.session = session
        self.city_repo = city_repo
        logger.debug("Инициализация EntertainmentRepository")

    async def get_list(self) -> list[Entertainment]:
        query = text("SELECT * FROM entertainment ORDER BY id")
        try:
            result = await self.session.execute(query)
            rows = result.mappings()
            entertainments = [
                Entertainment(
                    entertainment_id=row["id"],
                    duration=row["duration"],
                    address=row["address"],
                    event_name=row["event_name"],
                    event_time=row["event_time"],
                    city=await self.city_repo.get_by_id(row["city"]),
                )
                for row in rows
            ]
            logger.debug("Успешно получено %d развлечений", len(entertainments))
            return entertainments
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при получении списка развлечений: %s", str(e), exc_info=True
            )
            return []

    async def get_by_id(self, entertainment_id: int) -> Entertainment | None:
        query = text("SELECT * FROM entertainment WHERE id = :entertainment_id")
        try:
            result = await self.session.execute(
                query, {"entertainment_id": entertainment_id}
            )
            row = result.mappings().first()
            if row:
                logger.debug(
                    "Найдено развлечение ID %d: %s", entertainment_id, row["event_name"]
                )
                return Entertainment(
                    entertainment_id=row["id"],
                    duration=row["duration"],
                    address=row["address"],
                    event_name=row["event_name"],
                    event_time=row["event_time"],
                    city=await self.city_repo.get_by_id(row["city"]),
                )
            return None
            logger.warning("Развлечение с ID %d не найдено", entertainment_id)
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при получении развлечения по ID %d: %s", entertainment_id, e
            )
            return None

    async def add(self, entertainment: Entertainment) -> Entertainment:
        query = text(
            """
            INSERT INTO entertainment (duration, address, event_name, event_time, city)
            VALUES (:duration, :address, :event_name, :event_time, :city)
            RETURNING id
        """
        )
        try:
            if entertainment.city is None:
                logger.error("Отсутствуют данные о городе")
                raise ValueError(
                    "Невозможно добавить развлечение: отсутствуют данные о городе"
                )
            row = await self.session.execute(
                query,
                {
                    "duration": entertainment.duration,
                    "address": entertainment.address,
                    "event_name": entertainment.event_name,
                    "event_time": entertainment.event_time,
                    "city": entertainment.city.city_id,
                },
            )
            new_id = row.scalar_one()
            await self.session.commit()
            logger.debug("Развлечение '%s' успешно добавлено", entertainment.event_name)
            entertainment.entertainment_id = new_id
        except IntegrityError:
            logger.warning(
                "Развлечение '%s' уже существует в базе данных",
                entertainment.event_name,
            )
            await self.session.rollback()
            raise ValueError("Развлечение уже существует в базе данных")
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при добавлении развлечения '%s': %s",
                entertainment.event_name,
                str(e),
                exc_info=True,
            )
            await self.session.rollback()
        return entertainment

    async def update(self, update_entertainment: Entertainment) -> None:
        if update_entertainment.city is None:
            logger.error("Отсутствуют данные о городе")
            return
        query = text(
            """
            UPDATE entertainment
            SET duration = :duration,
                address = :address,
                event_name = :event_name,
                event_time = :event_time,
                city = :city
            WHERE id = :entertainment_id
        """
        )
        try:
            await self.session.execute(
                query,
                {
                    "entertainment_id": update_entertainment.entertainment_id,
                    "duration": update_entertainment.duration,
                    "address": update_entertainment.address,
                    "event_name": update_entertainment.event_name,
                    "event_time": update_entertainment.event_time,
                    "city": update_entertainment.city.city_id,
                },
            )
            await self.session.commit()
            logger.debug(
                "Развлечение ID %d успешно обновлено", update_entertainment.event_name
            )
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при обновлении развлечения ID %d: %s",
                update_entertainment.entertainment_id,
                str(e),
                exc_info=True,
            )

    async def delete(self, entertainment_id: int) -> None:
        query = text("DELETE FROM entertainment WHERE id = :entertainment_id")
        try:
            await self.session.execute(query, {"entertainment_id": entertainment_id})
            await self.session.commit()
            logger.debug("Развлечение ID %d успешно удалено", entertainment_id)
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при удалении развлечения ID %d: %s",
                entertainment_id,
                str(e),
                exc_info=True,
            )
            await self.session.rollback()
