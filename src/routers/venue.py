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

venue_router = APIRouter()
templates = Jinja2Templates(directory="templates")
get_sl_dep = Depends(get_service_locator)


@venue_router.post("/api/venues", response_class=HTMLResponse)
async def create_venue(
    request: Request, service_locator: ServiceLocator = get_sl_dep
) -> HTMLResponse:
    result = await service_locator.get_venue_contr().create_new_venue(request)
    logger.info("Площадка успешно создана: %s", result)
    return templates.TemplateResponse("venue.html", {"request": request})


@venue_router.get("/venue.html", response_class=HTMLResponse)
async def get_all_venues(
    request: Request, service_locator: ServiceLocator = get_sl_dep
) -> HTMLResponse:
    venue_list = await service_locator.get_venue_contr().get_all_venues()
    venues = venue_list.get("venues", [])
    logger.info("Получено %d площадок", len(venues))
    return templates.TemplateResponse(
        "venue.html", {"request": request, "venues": venues}
    )


@venue_router.get("/venue.html")
async def get_venue(
    request: Request, service_locator: ServiceLocator = get_sl_dep
) -> dict[str, Any]:
    result = await service_locator.get_venue_contr().get_venue_details(request)
    if result is None:
        logger.warning("Площадка не найдена")
        return {"error": "Venue not found"}
    logger.info("Информация о площадке получена: %s", result)
    return result


@venue_router.put("/api/venues/{venue_id}", response_class=HTMLResponse)
async def update_venue(
    venue_id: int, request: Request, service_locator: ServiceLocator = get_sl_dep
) -> HTMLResponse:
    result = await service_locator.get_venue_contr().update_venue(venue_id, request)
    logger.info("Площадка ID %d успешно обновлена: %s", venue_id, result)
    return templates.TemplateResponse("venue.html", {"request": request})


@venue_router.post("/venue/delete/{venue_id}", response_class=HTMLResponse)
async def delete_venue(
    venue_id: int, service_locator: ServiceLocator = get_sl_dep
) -> RedirectResponse:
    result = await service_locator.get_venue_contr().delete_venue(venue_id)
    logger.info("Площадка ID %d успешно удалена: %s", venue_id, result)
    return RedirectResponse(url="/venue.html", status_code=303)
