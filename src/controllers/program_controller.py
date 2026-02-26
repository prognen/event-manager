from __future__ import annotations

import logging

from typing import Any

from fastapi import Request

from models.program import Program
from services.program_service import ProgramService
from services.venue_service import VenueService


logger = logging.getLogger(__name__)


class ProgramController:
    def __init__(
        self, program_service: ProgramService, venue_service: VenueService
    ) -> None:
        self.program_service = program_service
        self.venue_service = venue_service
        logger.debug("Инициализация ProgramController")

    async def create_new_program(self, request: Request) -> dict[str, Any]:
        try:
            data = await request.json()
            data["program_id"] = 1
            data["from_venue"] = await self.venue_service.get_by_id(
                data["from_venue"]
            )
            data["to_venue"] = await self.venue_service.get_by_id(
                data["to_venue"]
            )
            program = Program(**data)
            await self.program_service.add(program)
            logger.info("Программа успешно создана: %s", program)
            return {"message": "Program created successfully"}
        except Exception as e:
            logger.error(
                "Ошибка при создании программы: %s", str(e), exc_info=True
            )
            return {"message": "Error creating program", "error": str(e)}

    async def update_program(
        self, program_id: int, request: Request
    ) -> dict[str, Any]:
        try:
            data = await request.json()
            data["program_id"] = program_id
            data["from_venue"] = await self.venue_service.get_by_id(
                data["from_venue"]
            )
            data["to_venue"] = await self.venue_service.get_by_id(
                data["to_venue"]
            )
            program = Program(**data)
            await self.program_service.update(program)
            logger.info("Программа ID %d успешно обновлена", program_id)
            return {"message": "Program updated successfully"}
        except Exception as e:
            logger.error(
                "Ошибка при обновлении программы ID %d: %s",
                program_id,
                str(e),
                exc_info=True,
            )
            return {"message": "Error updating program", "error": str(e)}

    async def get_program_details(self, request: Request) -> dict[str, Any]:
        try:
            data = await request.json()
            program_id = data.get("id")
            if program_id is None:
                logger.warning("ID программы не передан в запросе")
                return {"message": "Missing 'id' in request"}
            program = await self.program_service.get_by_id(program_id)
            if program:
                logger.info("Программа ID %d найдена: %s", program_id, program)
                return {
                    "program": {
                        "id": program.program_id,
                        "type_transport": program.type_transport,
                        "cost": program.cost,
                        "distance": program.distance,
                        "from_venue": program.from_venue,
                        "to_venue": program.to_venue,
                    }
                }
            logger.warning("Программа ID %d не найдена", program_id)
            return {"message": "Program not found"}
        except Exception as e:
            logger.error(
                "Ошибка при получении информации о программе ID: %s",
                str(e),
                exc_info=True,
            )
            return {"message": "Error fetching details", "error": str(e)}

    async def get_all_programs(self) -> dict[str, Any]:
        try:
            program_list = await self.program_service.get_list()
            logger.info("Получено %d программ", len(program_list))
            return {
                "programs": [
                    {
                        "id": p.program_id,
                        "type_transport": p.type_transport,
                        "cost": p.cost,
                        "distance": p.distance,
                        "from_venue": p.from_venue,
                        "to_venue": p.to_venue,
                    }
                    for p in program_list
                ]
            }
        except Exception as e:
            logger.error(
                "Ошибка при получении списка программ: %s", str(e), exc_info=True
            )
            return {"message": "Error fetching programs", "error": str(e)}

    async def delete_program(self, program_id: int) -> dict[str, Any]:
        try:
            await self.program_service.delete(program_id)
            logger.info("Программа ID %d успешно удалена", program_id)
            return {"message": "Program deleted successfully"}
        except Exception as e:
            logger.error(
                "Ошибка при удалении программы ID %d: %s",
                program_id,
                str(e),
                exc_info=True,
            )
            return {"message": "Error deleting program", "error": str(e)}
