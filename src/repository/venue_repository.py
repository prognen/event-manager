from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from abstract_repository.ivenue_repository import IVenueRepository
from models.venue import Venue


logger = logging.getLogger(__name__)


class VenueRepository(IVenueRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        logger.debug("Инициализация VenueRepository")

    async def get_list(self) -> list[Venue]:
        query = text("SELECT * FROM Venue ORDER BY venue_id")
        try:
            result = await self.session.execute(query)
            venues = [
                Venue(venue_id=row["venue_id"], name=row["name"])
                for row in result.mappings()
            ]
            logger.debug("Успешно получено %d площадок", len(venues))
            return venues
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении списка площадок: %s", str(e), exc_info=True)
            raise

    async def get_by_id(self, venue_id: int) -> Venue | None:
        query = text("SELECT * FROM Venue WHERE venue_id = :venue_id")
        try:
            result = await self.session.execute(query, {"venue_id": venue_id})
            row = result.mappings().first()
            if row:
                logger.debug("Найдена площадка ID %d: %s", venue_id, row["name"])
                return Venue(venue_id=row["venue_id"], name=row["name"])
            logger.warning("Площадка с ID %d не найдена", venue_id)
            return None
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении площадки по ID %d: %s", venue_id, str(e), exc_info=True)
            return None

    async def add(self, venue: Venue) -> Venue:
        query = text("INSERT INTO Venue (name) VALUES (:name) RETURNING venue_id")
        try:
            result = await self.session.execute(query, {"name": venue.name})
            new_id = result.scalar_one()
            await self.session.commit()
            logger.debug("Площадка '%s' успешно добавлена", venue.name)
            venue.venue_id = new_id
        except IntegrityError:
            logger.warning("Площадка '%s' уже существует", venue.name)
            await self.session.rollback()
            raise
        except SQLAlchemyError as e:
            logger.error("Ошибка при добавлении площадки '%s': %s", venue.name, str(e), exc_info=True)
            await self.session.rollback()
            raise
        return venue

    async def update(self, update_venue: Venue) -> None:
        query = text("UPDATE Venue SET name = :name WHERE venue_id = :venue_id")
        try:
            await self.session.execute(query, {"name": update_venue.name, "venue_id": update_venue.venue_id})
            await self.session.commit()
            logger.debug("Площадка ID %d успешно обновлена", update_venue.venue_id)
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error("Ошибка при обновлении площадки ID %d: %s", update_venue.venue_id, str(e), exc_info=True)
            raise

    async def delete(self, venue_id: int) -> None:
        query = text("DELETE FROM Venue WHERE venue_id = :venue_id")
        try:
            result = await self.session.execute(query, {"venue_id": venue_id})
            if result.rowcount == 0:
                logger.warning("Площадка с ID %d не найдена для удаления", venue_id)
                raise ValueError(f"Площадка с ID {venue_id} не найдена")
            await self.session.commit()
            logger.debug("Площадка ID %d успешно удалена", venue_id)
        except SQLAlchemyError as e:
            logger.error("Ошибка при удалении площадки ID %d: %s", venue_id, str(e), exc_info=True)
            await self.session.rollback()
            raise
