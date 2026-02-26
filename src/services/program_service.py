from __future__ import annotations

import logging

from abstract_repository.iprogram_repository import IProgramRepository
from abstract_service.program_service import IProgramService
from models.program import Program


logger = logging.getLogger(__name__)


class ProgramService(IProgramService):
    def __init__(self, repository: IProgramRepository) -> None:
        self.repository = repository
        logger.debug("ProgramService инициализирован")

    async def get_by_id(self, program_id: int) -> Program | None:
        logger.debug("Получение программы по ID %d", program_id)
        return await self.repository.get_by_id(program_id)

    async def get_list(self) -> list[Program]:
        logger.debug("Получение списка всех программ")
        return await self.repository.get_list()

    async def add(self, program: Program) -> Program:
        try:
            logger.debug("Добавление программы с ID %d", program.program_id)
            program = await self.repository.add(program)
        except Exception:
            logger.error(
                "Программа c таким ID %d уже существует.", program.program_id
            )
            raise ValueError("Программа c таким ID уже существует.")
        return program

    async def update(self, updated_program: Program) -> Program:
        try:
            logger.debug("Обновление программы с ID %d", updated_program.program_id)
            await self.repository.update(updated_program)
        except Exception:
            logger.error(
                "Программа с ID %d не найдена.", updated_program.program_id
            )
            raise ValueError("Программа не найдена.")
        return updated_program

    async def delete(self, program_id: int) -> None:
        try:
            logger.debug("Удаление программы с ID %d", program_id)
            await self.repository.delete(program_id)
        except Exception:
            logger.error("Не удалось удалить программу с ID %d", program_id)
            raise ValueError("Программу не получилось удалить.")

    async def change_transport(
        self, program_id: int, new_transport: str
    ) -> Program | None:
        try:
            logger.debug(
                "Изменение транспорта в программе %d на %s",
                program_id,
                new_transport,
            )
            return await self.repository.change_transport(program_id, new_transport)
        except Exception:
            logger.error("Не удалось изменить транспорт в программе %d", program_id)
            raise ValueError("Не получилось изменить транспорт.")

    async def get_by_venues(
        self, from_venue_id: int, to_venue_id: int, transport: str
    ) -> Program | None:
        try:
            logger.debug(
                "Поиск программы по площадкам %s и %s",
                from_venue_id,
                to_venue_id,
            )
            return await self.repository.get_by_venues(
                from_venue_id, to_venue_id, transport
            )
        except Exception:
            logger.error(
                "Не удалось найти программу по площадкам %s и %s",
                from_venue_id,
                to_venue_id,
            )
            raise ValueError("Программу не получилось найти.")
