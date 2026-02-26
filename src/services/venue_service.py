from __future__ import annotations

import logging

from abstract_repository.ivenue_repository import IVenueRepository
from abstract_service.venue_service import IVenueService
from models.venue import Venue


logger = logging.getLogger(__name__)


class VenueService(IVenueService):
    def __init__(self, repository: IVenueRepository) -> None:
        self.repository = repository
        logger.debug("VenueService инициализирован")

    async def get_by_id(self, venue_id: int) -> Venue | None:
        logger.debug("Получение площадки по ID %d", venue_id)
        return await self.repository.get_by_id(venue_id)

    async def get_all_venues(self) -> list[Venue]:
        logger.debug("Получение списка всех площадок")
        return await self.repository.get_list()

    async def add(self, venue: Venue) -> Venue:
        try:
            logger.debug("Добавление площадки с ID %d", venue.venue_id)
            venue = await self.repository.add(venue)
        except Exception:
            logger.error("Площадка c таким ID %d уже существует.", venue.venue_id)
            raise ValueError("Площадка c таким ID уже существует.")
        return venue

    async def update(self, updated_venue: Venue) -> Venue:
        try:
            logger.debug("Обновление площадки с ID %d", updated_venue.venue_id)
            await self.repository.update(updated_venue)
        except Exception:
            logger.error("Площадка с ID %d не найдена.", updated_venue.venue_id)
            raise ValueError("Площадка не найдена.")
        return updated_venue

    async def delete(self, venue_id: int) -> None:
        try:
            logger.debug("Удаление площадки с ID %d", venue_id)
            await self.repository.delete(venue_id)
        except Exception:
            logger.error("Площадка с ID %d не найдена.", venue_id)
            raise ValueError("Площадка не найдена.")
