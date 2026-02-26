from __future__ import annotations

import logging

from datetime import datetime
from json import JSONDecodeError
from typing import Any

from fastapi import HTTPException
from fastapi import Request

from models.activity import Activity
from services.activity_service import ActivityService
from services.venue_service import VenueService


logger = logging.getLogger(__name__)


class ActivityController:
    def __init__(
        self, activity_service: ActivityService, venue_service: VenueService
    ) -> None:
        self.activity_service = activity_service
        self.venue_service = venue_service
        logger.debug("Инициализация ActivityController")

    async def create_new_activity(self, request: Request) -> dict[str, Any]:
        try:
            data = await request.json()
            data["activity_id"] = 1
            data["venue"] = await self.venue_service.get_by_id(data["venue"])
            activity = Activity(**data)
            activity = await self.activity_service.add(activity)
            logger.info("Активность успешно создана: %s", activity)
            return {
                "message": "Activity created successfully",
                "activity_id": activity.activity_id,
            }
        except Exception as e:
            logger.error("Ошибка при создании активности: %s", str(e), exc_info=True)
            return {"message": "Error creating activity", "error": str(e)}

    async def update_activity(
        self, activity_id: int, request: Request
    ) -> dict[str, Any]:
        try:
            data = await request.json()
            data["activity_id"] = activity_id
            data["venue"] = await self.venue_service.get_by_id(data["venue"])
            activity = Activity(**data)
            await self.activity_service.update(activity)
            logger.info("Активность ID %d успешно обновлена", activity_id)
            return {"message": "Activity updated successfully"}
        except Exception as e:
            logger.error(
                "Ошибка при обновлении активности ID %d: %s",
                activity_id,
                str(e),
                exc_info=True,
            )
            return {"message": "Error updating activity", "error": str(e)}

    async def get_activity_details(self, activity_id: int) -> dict[str, Any]:
        try:
            activity = await self.activity_service.get_by_id(activity_id)
            if activity:
                logger.info("Активность ID %d найдена: %s", activity_id, activity)
                return {
                    "activity": {
                        "id": activity.activity_id,
                        "duration": activity.duration,
                        "address": activity.address,
                        "activity_type": activity.activity_type,
                        "activity_time": activity.activity_time.isoformat(),
                        "venue": activity.venue,
                    }
                }
            logger.warning("Активность ID %d не найдена", activity_id)
            return {"message": "Activity not found"}
        except JSONDecodeError:
            logger.warning("Некорректный JSON в теле запроса")
            return {"message": "Invalid JSON in request"}
        except Exception as e:
            logger.error(
                "Ошибка при получении информации об активности: %s",
                str(e),
                exc_info=True,
            )
            return {"message": "Error fetching details", "error": str(e)}

    async def get_all_activities(self) -> dict[str, Any]:
        try:
            activity_list = await self.activity_service.get_list()
            logger.info("Получено %d активностей", len(activity_list))
            return {
                "activities": [
                    {
                        "id": a.activity_id,
                        "duration": a.duration,
                        "address": a.address,
                        "activity_type": a.activity_type,
                        "activity_time": a.activity_time.isoformat(),
                        "venue": a.venue,
                    }
                    for a in activity_list
                ]
            }
        except Exception as e:
            logger.error(
                "Ошибка при получении списка активностей: %s", str(e), exc_info=True
            )
            return {"message": "Error fetching activities", "error": str(e)}

    async def delete_activity(self, activity_id: int) -> dict[str, Any]:
        try:
            await self.activity_service.delete(activity_id)
            logger.info("Активность ID %d успешно удалена", activity_id)
            return {"message": "Activity deleted successfully"}
        except Exception as e:
            logger.error(
                "Ошибка при удалении активности ID %d: %s",
                activity_id,
                str(e),
                exc_info=True,
            )
            return {"message": "Error deleting activity", "error": str(e)}

    async def update_activity_dates(
        self, activity_id: int, request: Request
    ) -> dict[str, Any]:
        try:
            data = await request.json()
            activity = await self.activity_service.get_by_id(activity_id)
            if not activity:
                raise HTTPException(status_code=404, detail="Activity not found")

            activity.activity_time = datetime.fromisoformat(data["activity_time"])
            activity.duration = data["duration"]

            await self.activity_service.update(activity)

            logger.info(
                "Дата и продолжительность активности ID %d успешно обновлены",
                activity_id,
            )
            return {"message": "Activity dates and duration updated successfully"}

        except Exception as e:
            logger.error(
                "Ошибка при обновлении дат активности ID %d: %s",
                activity_id,
                str(e),
                exc_info=True,
            )
            raise HTTPException(status_code=400, detail=str(e))
