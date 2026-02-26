from __future__ import annotations

import logging

from typing import Any

from fastapi import Request

from models.venue import Venue
from services.venue_service import VenueService


logger = logging.getLogger(__name__)


class VenueController:
    def __init__(self, venue_service: VenueService) -> None:
        self.venue_service = venue_service
        logger.debug("Инициализация VenueController")

    async def create_new_venue(self, request: Request) -> dict[str, Any]:
        try:
            data = await request.json()
            data["venue_id"] = 1
            venue = Venue(**data)
            await self.venue_service.add(venue)
            logger.info("Площадка успешно создана: %s", venue)
            return {"message": "Venue created successfully"}
        except Exception as e:
            logger.error("Ошибка при создании площадки: %s", str(e), exc_info=True)
            return {"message": "Error creating venue", "error": str(e)}

    async def update_venue(self, venue_id: int, request: Request) -> dict[str, Any]:
        try:
            data = await request.json()
            data["venue_id"] = venue_id
            venue = Venue(**data)
            await self.venue_service.update(venue)
            logger.info("Площадка ID %d успешно обновлена", venue_id)
            return {"message": "Venue updated successfully"}
        except Exception as e:
            logger.error(
                "Ошибка при обновлении площадки ID %d: %s",
                venue_id,
                str(e),
                exc_info=True,
            )
            return {"message": "Error updating venue", "error": str(e)}

    async def get_venue_details(self, request: Request) -> dict[str, Any]:
        try:
            data = await request.json()
            venue_id = data.get("id")
            if venue_id is None:
                logger.warning("ID площадки не передан в запросе")
                return {"message": "Missing 'id' in request"}
            venue = await self.venue_service.get_by_id(venue_id)
            if venue:
                logger.info("Площадка ID %d найдена: %s", venue_id, venue)
                return {"venue": {"id": venue.venue_id, "name": venue.name}}
            logger.warning("Площадка ID %d не найдена", venue_id)
            return {"message": "Venue not found"}
        except Exception as e:
            logger.error(
                "Ошибка при получении информации о площадке: %s", str(e), exc_info=True
            )
            return {"message": "Error fetching details", "error": str(e)}

    async def get_all_venues(self) -> dict[str, Any]:
        try:
            venue_list = await self.venue_service.get_all_venues()
            logger.info("Получено %d площадок", len(venue_list))
            return {
                "venues": [{"id": v.venue_id, "name": v.name} for v in venue_list]
            }
        except Exception as e:
            logger.error(
                "Ошибка при получении списка площадок: %s", str(e), exc_info=True
            )
            return {"message": "Error fetching venues", "error": str(e)}

    async def delete_venue(self, venue_id: int) -> dict[str, Any]:
        try:
            await self.venue_service.delete(venue_id)
            logger.info("Площадка ID %d успешно удалена", venue_id)
            return {"message": "Venue deleted successfully"}
        except Exception as e:
            logger.error(
                "Ошибка при удалении площадки ID %d: %s",
                venue_id,
                str(e),
                exc_info=True,
            )
            return {"message": "Error deleting venue", "error": str(e)}
