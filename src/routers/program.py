from __future__ import annotations

import logging

from typing import Any

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from service_locator import ServiceLocator
from service_locator import get_service_locator


logger = logging.getLogger(__name__)

program_router = APIRouter()
templates = Jinja2Templates(directory="templates")
get_sl_dep = Depends(get_service_locator)


@program_router.post("/api/programs", response_class=HTMLResponse)
async def create_program(
    request: Request, service_locator: ServiceLocator = get_sl_dep
) -> HTMLResponse:
    result = await service_locator.get_program_contr().create_new_program(request)
    logger.info("Программа успешно создана: %s", result)
    return templates.TemplateResponse("program.html", {"request": request})


@program_router.get("/program.html", response_class=HTMLResponse)
async def get_all_programs(
    request: Request, service_locator: ServiceLocator = get_sl_dep
) -> HTMLResponse:
    program_list = await service_locator.get_program_contr().get_all_programs()
    programs = program_list.get("programs", [])
    logger.info("Получено %d программ", len(programs))

    logger.info("Получение списка площадок")
    venues_list = await service_locator.get_venue_contr().get_all_venues()
    venues = venues_list.get("venues", [])
    logger.info("Получено %d площадок", len(venues))

    return templates.TemplateResponse(
        "program.html",
        {"request": request, "programs": programs, "venues": venues},
    )


@program_router.get("/program.html")
async def get_program(
    request: Request, service_locator: ServiceLocator = get_sl_dep
) -> dict[str, Any]:
    result = await service_locator.get_program_contr().get_program_details(request)
    if result is None:
        logger.warning("Программа не найдена")
        return {"error": "Program not found"}
    logger.info("Информация о программе получена: %s", result)
    return result


@program_router.put("/api/programs/{program_id}", response_class=HTMLResponse)
async def update_program(
    program_id: int, request: Request, service_locator: ServiceLocator = get_sl_dep
) -> HTMLResponse:
    result = await service_locator.get_program_contr().update_program(
        program_id, request
    )
    logger.info("Программа ID %d успешно обновлена: %s", program_id, result)
    return templates.TemplateResponse("program.html", {"request": request})


@program_router.post("/program/delete/{program_id}", response_class=HTMLResponse)
async def delete_program(
    program_id: int, service_locator: ServiceLocator = get_sl_dep
) -> RedirectResponse:
    result = await service_locator.get_program_contr().delete_program(program_id)
    logger.info("Программа ID %d успешно удалена: %s", program_id, result)
    return RedirectResponse(url="/program.html", status_code=303)
