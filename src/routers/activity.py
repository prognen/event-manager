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

activity_router = APIRouter()
templates = Jinja2Templates(directory="templates")
get_sl_dep = Depends(get_service_locator)


@activity_router.post("/api/activities", response_class=HTMLResponse)
async def create_activity(
    request: Request, service_locator: ServiceLocator = get_sl_dep
) -> HTMLResponse:
    result = await service_locator.get_activity_contr().create_new_activity(request)
    logger.info("Активность успешно создана: %s", result)
    return templates.TemplateResponse("activity.html", {"request": request})


@activity_router.get("/activity.html", response_class=HTMLResponse)
async def get_all_activities(
    request: Request, service_locator: ServiceLocator = get_sl_dep
) -> HTMLResponse:
    activity_list = await service_locator.get_activity_contr().get_all_activities()
    activities = activity_list.get("activities", [])
    logger.info("Получено %d активностей", len(activities))
    for a in activities:
        a["activity_time"] = datetime.fromisoformat(a["activity_time"])
    logger.info("Получение списка площадок")
    venues_list = await service_locator.get_venue_contr().get_all_venues()
    venues = venues_list.get("venues", [])
    logger.info("Получено %d площадок", len(venues))
    return templates.TemplateResponse(
        "activity.html",
        {"request": request, "activities": activities, "venues": venues},
    )


@activity_router.get("/activity/get/{activity_id}")
async def get_activity(
    activity_id: int, service_locator: ServiceLocator = get_sl_dep
) -> dict[str, Any]:
    try:
        result = await service_locator.get_activity_contr().get_activity_details(
            activity_id
        )
        if result is None:
            logger.warning("Активность с ID %d не найдена", activity_id)
            raise HTTPException(status_code=404, detail="Activity not found")
        logger.info("Информация об активности получена: %s", result)
        return result
    except Exception as e:
        logger.error(
            "Ошибка при получении информации об активности: %s", str(e), exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))


@activity_router.put("/api/activities/{activity_id}")
async def update_activity(
    activity_id: int,
    request: Request,
    service_locator: ServiceLocator = get_sl_dep,
) -> HTMLResponse:
    result = await service_locator.get_activity_contr().update_activity(
        activity_id, request
    )
    logger.info("Активность ID %d успешно обновлена: %s", activity_id, result)
    return templates.TemplateResponse("activity.html", {"request": request})


@activity_router.post(
    "/activity/delete/{activity_id}", response_class=HTMLResponse
)
async def delete_activity(
    activity_id: int,
    request: Request,
    service_locator: ServiceLocator = get_sl_dep,
) -> RedirectResponse:
    result = await service_locator.get_activity_contr().delete_activity(activity_id)
    logger.info("Активность ID %d успешно удалена: %s", activity_id, result)
    return RedirectResponse(url="/activity.html", status_code=303)


@activity_router.delete(
    "/session/activity/delete/{activity_id}", response_class=HTMLResponse
)
async def delete_activity_for_session(
    activity_id: int, session_id: int, service_locator: ServiceLocator = get_sl_dep
) -> RedirectResponse:
    result = await service_locator.get_activity_contr().delete_activity(activity_id)
    logger.info("Активность ID %d успешно удалена: %s", activity_id, result)
    return RedirectResponse(url=f"/session/edit/{session_id}", status_code=303)


@activity_router.post("/activity/add/{session_id}", response_class=HTMLResponse)
async def add_activity_to_session(
    session_id: int, request: Request, service_locator: ServiceLocator = get_sl_dep
) -> RedirectResponse:
    try:
        result = await service_locator.get_activity_contr().create_new_activity(request)
        logger.info("Активность успешно создана: %s", result)
        event = await service_locator.get_event_serv().get_event_by_session_id(
            session_id
        )
        if not event:
            raise ValueError(f"No event found for session_id={session_id}")
        activity_ids = []
        activities = (
            await service_locator.get_event_serv().get_activities_by_event(
                event.event_id
            )
        )
        activity_ids = [a.activity_id for a in activities]
        activity_ids.append(result["activity_id"])

        await service_locator.get_event_serv().link_activities(
            event.event_id, activity_ids
        )
        return RedirectResponse(url=f"/session/edit/{session_id}", status_code=303)

    except Exception as e:
        logger.error(f"Error adding activity: {e!s}")
        raise


@activity_router.put("/activity/{activity_id}")
async def update_activity_dates(
    activity_id: int,
    request: Request,
    service_locator: ServiceLocator = get_sl_dep,
) -> dict[str, Any]:
    return await service_locator.get_activity_contr().update_activity_dates(
        activity_id, request
    )
