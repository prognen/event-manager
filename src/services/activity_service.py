from __future__ import annotations

import logging

from abstract_repository.iactivity_repository import IActivityRepository
from abstract_service.activity_service import IActivityService
from models.activity import Activity


logger = logging.getLogger(__name__)


class ActivityService(IActivityService):
    def __init__(self, repository: IActivityRepository) -> None:
        self.repository = repository
        logger.debug("ActivityService инициализирован")

    async def get_by_id(self, activity_id: int) -> Activity | None:
        logger.debug("Получение активности по ID %d", activity_id)
        return await self.repository.get_by_id(activity_id)

    async def add(self, activity: Activity) -> Activity:
        try:
            logger.debug("Добавление активности с ID %d", activity.activity_id)
            activity = await self.repository.add(activity)
        except Exception:
            logger.error(
                "Активность c таким ID %d уже существует.",
                activity.activity_id,
            )
            raise ValueError("Активность c таким ID уже существует.")
        return activity

    async def update(self, update_activity: Activity) -> Activity:
        try:
            logger.debug("Обновление активности с ID %d", update_activity.activity_id)
            await self.repository.update(update_activity)
        except Exception:
            logger.error("Активность с ID %d не найдена.", update_activity.activity_id)
            raise ValueError("Активность не найдена.")
        return update_activity

    async def delete(self, activity_id: int) -> None:
        try:
            logger.debug("Удаление активности с ID %d", activity_id)
            await self.repository.delete(activity_id)
        except Exception:
            logger.error("Активность с ID %d не найдена.", activity_id)
            raise ValueError("Активность не найдена.")

    async def get_list(self) -> list[Activity]:
        logger.debug("Получение списка всех активностей")
        return await self.repository.get_list()
