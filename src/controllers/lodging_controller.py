from __future__ import annotations

import logging

from datetime import datetime
from typing import Any

from fastapi import HTTPException
from fastapi import Request

from models.lodging import Lodging
from services.lodging_service import LodgingService
from services.venue_service import VenueService


logger = logging.getLogger(__name__)


class LodgingController:
    def __init__(
        self, lodging_service: LodgingService, venue_service: VenueService
    ) -> None:
        self.lodging_service = lodging_service
        self.venue_service = venue_service
        logger.debug("Инициализация LodgingController")

    async def create_new_lodging(self, request: Request) -> dict[str, Any]:
        try:
            data = await request.json()
            data["lodging_id"] = 1
            data["venue"] = await self.venue_service.get_by_id(data["venue"])
            lodging = Lodging(**data)
            await self.lodging_service.add(lodging)
            logger.info("Размещение успешно создано: %s", lodging)
            return {
                "message": "Lodging created successfully",
                "lodging_id": lodging.lodging_id,
            }
        except Exception as e:
            logger.error("Ошибка при создании размещения: %s", str(e), exc_info=True)
            return {"message": "Error creating lodging", "error": str(e)}

    async def update_lodging(
        self, lodging_id: int, request: Request
    ) -> dict[str, Any]:
        try:
            data = await request.json()
            data["lodging_id"] = lodging_id
            data["venue"] = await self.venue_service.get_by_id(data["venue"])
            lodging = Lodging(**data)
            await self.lodging_service.update(lodging)
            logger.info("Размещение ID %d успешно обновлено", lodging_id)
            return {"message": "Lodging updated successfully"}
        except Exception as e:
            logger.error(
                "Ошибка при обновлении размещения ID %d: %s",
                lodging_id,
                str(e),
                exc_info=True,
            )
            return {"message": "Error updating lodging", "error": str(e)}

    async def get_lodging_details(
        self,
        lodging_id: int,
    ) -> dict[str, Any]:
        try:
            lodging = await self.lodging_service.get_by_id(lodging_id)
            if lodging:
                logger.info("Размещение ID %d найдено: %s", lodging_id, lodging)
                return {
                    "lodging": {
                        "id": lodging.lodging_id,
                        "price": lodging.price,
                        "address": lodging.address,
                        "name": lodging.name,
                        "type": lodging.type,
                        "rating": lodging.rating,
                        "check_in": lodging.check_in.strftime("%Y-%m-%dT%H:%M"),
                        "check_out": lodging.check_out.strftime("%Y-%m-%dT%H:%M"),
                        "venue": lodging.venue,
                    }
                }
            logger.warning("Размещение ID %d не найдено", lodging_id)
            return {"message": "Lodging not found"}
        except Exception as e:
            logger.error(
                "Ошибка при получении информации о размещении: %s",
                str(e),
                exc_info=True,
            )
            return {"message": "Error fetching details", "error": str(e)}

    async def get_all_lodgings(self) -> dict[str, Any]:
        try:
            lodging_list = await self.lodging_service.get_list()
            logger.info("Получено %d записей о размещении", len(lodging_list))
            return {
                "lodgings": [
                    {
                        "id": l.lodging_id,
                        "price": l.price,
                        "address": l.address,
                        "name": l.name,
                        "type": l.type,
                        "rating": l.rating,
                        "check_in": l.check_in.isoformat(),
                        "check_out": l.check_out.isoformat(),
                        "venue": l.venue,
                    }
                    for l in lodging_list
                ]
            }
        except Exception as e:
            logger.error(
                "Ошибка при получении списка размещений: %s", str(e), exc_info=True
            )
            return {"message": "Error fetching lodgings", "error": str(e)}

    async def delete_lodging(self, lodging_id: int) -> dict[str, Any]:
        try:
            await self.lodging_service.delete(lodging_id)
            logger.info("Размещение ID %d успешно удалено", lodging_id)
            return {"message": "Lodging deleted successfully"}
        except Exception as e:
            logger.error(
                "Ошибка при удалении размещения ID %d: %s",
                lodging_id,
                str(e),
                exc_info=True,
            )
            return {"message": "Error deleting lodging", "error": str(e)}

    async def update_lodging_dates(
        self, lodging_id: int, request: Request
    ) -> dict[str, Any]:
        try:
            data = await request.json()
            check_in = datetime.fromisoformat(data["check_in"])
            check_out = datetime.fromisoformat(data["check_out"])

            lodging = await self.lodging_service.get_by_id(lodging_id)
            if not lodging:
                raise HTTPException(status_code=404, detail="Lodging not found")

            nights = (check_out - check_in).days
            old_nights = (lodging.check_out - lodging.check_in).days
            new_price = int(
                self.calculate_price(lodging.price / old_nights, nights)
            )

            lodging.check_in = check_in
            lodging.check_out = check_out
            lodging.price = new_price

            await self.lodging_service.update(lodging)

            logger.info(
                "Даты и цена размещения ID %d успешно обновлены", lodging_id
            )
            return {
                "message": "Lodging dates and price updated successfully",
                "updated_price": new_price,
            }

        except Exception as e:
            logger.error(
                "Ошибка при обновлении дат размещения ID %d: %s",
                lodging_id,
                str(e),
                exc_info=True,
            )
            raise HTTPException(status_code=400, detail=str(e))

    @staticmethod
    def calculate_price(base_price: float, nights: int) -> float:
        return base_price * nights
