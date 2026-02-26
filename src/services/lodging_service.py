from __future__ import annotations

import logging

from abstract_repository.ilodging_repository import ILodgingRepository
from abstract_service.lodging_service import ILodgingService
from models.lodging import Lodging


logger = logging.getLogger(__name__)


class LodgingService(ILodgingService):
    def __init__(self, repository: ILodgingRepository) -> None:
        self.repository = repository
        logger.debug("LodgingService инициализирован")

    async def get_by_id(self, lodging_id: int) -> Lodging | None:
        logger.debug("Получение размещения по ID %d", lodging_id)
        return await self.repository.get_by_id(lodging_id)

    async def get_list(self) -> list[Lodging]:
        logger.debug("Получение списка размещений")
        return await self.repository.get_list()

    async def add(self, lodging: Lodging) -> Lodging:
        try:
            logger.debug("Добавления размещения с ID %d", lodging.lodging_id)
            lodging = await self.repository.add(lodging)
        except Exception:
            logger.error(
                "Размещение c таким ID %d уже существует.",
                lodging.lodging_id,
            )
            raise ValueError("Размещение c таким ID уже существует.")
        return lodging

    async def update(self, update_lodging: Lodging) -> Lodging:
        try:
            logger.debug("Обновление размещения с ID %d", update_lodging.lodging_id)
            await self.repository.update(update_lodging)
        except Exception:
            logger.error(
                "Размещение c таким ID %d не найдено.",
                update_lodging.lodging_id,
            )
            raise ValueError("Размещение c таким ID не найдено.")
        return update_lodging

    async def delete(self, lodging_id: int) -> None:
        try:
            logger.debug("Размещение с ID %d успешно удалено", lodging_id)
            await self.repository.delete(lodging_id)
        except Exception:
            logger.error("Размещение c таким ID %d не найдено.", lodging_id)
            raise ValueError("Размещение не найдено.")
