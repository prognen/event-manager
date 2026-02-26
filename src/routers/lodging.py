from __future__ import annotations

import logging

from datetime import datetime
from typing import Any

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from service_locator import ServiceLocator
from service_locator import get_service_locator


logger = logging.getLogger(__name__)

lodging_router = APIRouter()
templates = Jinja2Templates(directory="templates")
get_sl_dep = Depends(get_service_locator)


@lodging_router.post("/api/lodgings", response_class=HTMLResponse)
async def create_lodging(
    request: Request, service_locator: ServiceLocator = get_sl_dep
) -> HTMLResponse:
    result = await service_locator.get_lodging_contr().create_new_lodging(request)
    logger.info("Размещение успешно создано: %s", result)
    return templates.TemplateResponse("lodging.html", {"request": request})


@lodging_router.get("/lodging.html", response_class=HTMLResponse)
async def get_all_lodgings(
    request: Request, service_locator: ServiceLocator = get_sl_dep
) -> HTMLResponse:
    lodging_list = await service_locator.get_lodging_contr().get_all_lodgings()
    lodgings = lodging_list.get("lodgings", [])
    logger.info("Получено %d размещений", len(lodgings))
    for ldg in lodgings:
        ldg["check_in"] = datetime.fromisoformat(ldg["check_in"])
        ldg["check_out"] = datetime.fromisoformat(ldg["check_out"])
    logger.info("Получение списка площадок")
    venues_list = await service_locator.get_venue_contr().get_all_venues()
    venues = venues_list.get("venues", [])
    logger.info("Получено %d площадок", len(venues))

    return templates.TemplateResponse(
        "lodging.html",
        {"request": request, "lodgings": lodgings, "venues": venues},
    )


@lodging_router.get("/lodging/get/{lodging_id}")
async def get_lodging(
    lodging_id: int, service_locator: ServiceLocator = get_sl_dep
) -> dict[str, Any]:
    try:
        lodging = await service_locator.get_lodging_contr().get_lodging_details(
            lodging_id
        )
        if lodging is None:
            logger.warning("Размещение с ID %d не найдено", lodging_id)
            raise HTTPException(status_code=404, detail="Lodging not found")
        logger.info("Информация о размещении ID %d получена", lodging_id)
        return lodging
    except Exception as e:
        logger.error(
            "Ошибка при получении информации о размещении: %s", str(e), exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))


@lodging_router.put(
    "/api/lodgings/{lodging_id}", response_class=HTMLResponse
)
async def update_lodging(
    lodging_id: int,
    request: Request,
    service_locator: ServiceLocator = get_sl_dep,
) -> HTMLResponse:
    result = await service_locator.get_lodging_contr().update_lodging(
        lodging_id, request
    )
    logger.info("Размещение ID %d успешно обновлено: %s", lodging_id, result)
    return templates.TemplateResponse("lodging.html", {"request": request})


@lodging_router.post(
    "/lodging/delete/{lodging_id}", response_class=HTMLResponse
)
async def delete_lodging(
    lodging_id: int, service_locator: ServiceLocator = get_sl_dep
) -> RedirectResponse:
    result = await service_locator.get_lodging_contr().delete_lodging(lodging_id)
    logger.info("Размещение ID %d успешно удалено: %s", lodging_id, result)
    return RedirectResponse(url="/lodging.html", status_code=303)


@lodging_router.delete(
    "/session/lodging/delete/{lodging_id}", response_class=HTMLResponse
)
async def delete_lodging_for_session(
    lodging_id: int, session_id: int, service_locator: ServiceLocator = get_sl_dep
) -> RedirectResponse:
    result = await service_locator.get_lodging_contr().delete_lodging(lodging_id)
    logger.info("Размещение ID %d успешно удалено: %s", lodging_id, result)
    return RedirectResponse(url=f"/session/edit/{session_id}", status_code=303)


@lodging_router.post("/lodging/add/{session_id}", response_class=HTMLResponse)
async def add_lodging_to_session(
    session_id: int, request: Request, service_locator: ServiceLocator = get_sl_dep
) -> RedirectResponse:
    try:
        result = await service_locator.get_lodging_contr().create_new_lodging(request)
        logger.info("Размещение успешно создано: %s", result)
        event = await service_locator.get_event_serv().get_event_by_session_id(
            session_id
        )
        if not event:
            raise ValueError(f"No event found for session_id={session_id}")

        lodging_ids = []
        lodgings = (
            await service_locator.get_event_serv().get_lodgings_by_event(
                event.event_id
            )
        )
        lodging_ids = [ldg.lodging_id for ldg in lodgings]
        lodging_ids.append(result["lodging_id"])

        await service_locator.get_event_serv().link_lodgings(
            event.event_id, lodging_ids
        )
        return RedirectResponse(url=f"/session/edit/{session_id}", status_code=303)

    except Exception as e:
        logger.error(f"Error adding lodging: {e!s}")
        raise


@lodging_router.put("/lodgings/{lodging_id}")
async def update_lodging_dates(
    lodging_id: int,
    request: Request,
    service_locator: ServiceLocator = get_sl_dep,
) -> dict[str, Any]:
    return await service_locator.get_lodging_contr().update_lodging_dates(
        lodging_id, request
    )
