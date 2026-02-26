from __future__ import annotations

import logging

from datetime import datetime
from typing import Any

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates

from service_locator import ServiceLocator
from service_locator import get_service_locator


logger = logging.getLogger(__name__)

event_router = APIRouter()
templates = Jinja2Templates(directory="templates")
get_sl_dep = Depends(get_service_locator)


@event_router.post("/api/events", response_class=HTMLResponse)
async def create_event(
    request: Request, service_locator: ServiceLocator = get_sl_dep
) -> HTMLResponse:
    result = await service_locator.get_event_contr().create_new_event(request)
    logger.info("Мероприятие успешно создано: %s", result)
    return templates.TemplateResponse("event.html", {"request": request})


@event_router.get("/event.html", response_class=HTMLResponse)
async def get_all_events(
    request: Request, service_locator: ServiceLocator = get_sl_dep
) -> HTMLResponse:
    event_list = await service_locator.get_event_contr().get_all_events()
    events = event_list.get("events", [])
    logger.info("Получено %d мероприятий", len(events))

    user_id = (
        events[0]["users"][0]["user_id"] if events and events[0]["users"] else None
    )
    user = None
    if user_id is not None:
        logger.info("Получение данных пользователя ID %s", user_id)
        user = await service_locator.get_user_contr().get_user_profile(user_id)
    users = await service_locator.get_user_contr().get_all_users()
    all_activities = await service_locator.get_activity_contr().get_all_activities()
    all_lodgings = await service_locator.get_lodging_contr().get_all_lodgings()

    activities = event_list.get("activities", [])
    for a in all_activities["activities"]:
        a["activity_time"] = datetime.fromisoformat(a["activity_time"])
    for a in activities:
        a["activity_time"] = datetime.fromisoformat(a["activity_time"])
    lodgings = event_list.get("lodgings", [])
    for l in lodgings:
        l["check_in"] = datetime.fromisoformat(l["check_in"])
        l["check_out"] = datetime.fromisoformat(l["check_out"])
    for l in all_lodgings["lodgings"]:
        l["check_in"] = datetime.fromisoformat(l["check_in"])
        l["check_out"] = datetime.fromisoformat(l["check_out"])

    for event in events:
        for activity in event["activities"]:
            if isinstance(activity.get("venue"), dict):
                activity["venue_name"] = activity["venue"].get("name", "Undefined")
            elif hasattr(activity.get("venue"), "name"):
                activity["venue_name"] = activity["venue"].name
            else:
                activity["venue_name"] = "Undefined"

        for lodging in event["lodgings"]:
            if isinstance(lodging.get("venue"), dict):
                lodging["venue_name"] = lodging["venue"].get("name", "Undefined")
            elif hasattr(lodging.get("venue"), "name"):
                lodging["venue_name"] = lodging["venue"].name
            else:
                lodging["venue_name"] = "Undefined"

    logger.info("Данные об активностях и размещениях обработаны")
    return templates.TemplateResponse(
        "event.html",
        {
            "request": request,
            "events": jsonable_encoder(events),
            "user": user["user"] if user else None,
            "activities": activities,
            "lodgings": lodgings,
            "users": users["users"],
            "all_activities": all_activities["activities"],
            "all_lodgings": all_lodgings["lodgings"],
        },
    )


@event_router.put("/api/events/{event_id}", response_class=HTMLResponse)
async def update_event(
    event_id: int, request: Request, service_locator: ServiceLocator = get_sl_dep
) -> HTMLResponse:
    result = await service_locator.get_event_contr().update_event(event_id, request)
    logger.info("Мероприятие ID %d успешно обновлено: %s", event_id, result)
    return templates.TemplateResponse("event.html", {"request": request})


@event_router.post("/event/delete/{event_id}", response_class=HTMLResponse)
async def delete_event(
    event_id: int, request: Request, service_locator: ServiceLocator = get_sl_dep
) -> RedirectResponse:
    result = await service_locator.get_event_contr().delete_event(event_id)
    logger.info("Мероприятие ID %d успешно удалено: %s", event_id, result)
    return RedirectResponse(url="/event.html", status_code=303)


@event_router.post("/event/complete/{event_id}")
async def complete_event(
    event_id: int, request: Request, service_locator: ServiceLocator = get_sl_dep
) -> Response:
    result = await service_locator.get_event_contr().complete_event(event_id)
    logger.info("Мероприятие успешно завершено: %s", result)
    event = await service_locator.get_event_contr().get_event_details(event_id)
    user_id = event["event"].get("user_id")
    if not user_id:
        logger.error("Не удалось получить user_id для мероприятия ID %d", event_id)
        return HTMLResponse(content="<h1>Пользователь не найден</h1>", status_code=404)
    return RedirectResponse(url=f"/profile_user/{user_id}", status_code=303)


@event_router.post("/search")
async def search_event(
    request: Request, service_locator: ServiceLocator = get_sl_dep
) -> dict[str, Any]:
    result = await service_locator.get_event_contr().search_event(request)
    logger.info(
        "Поиск завершен, найдено %d мероприятий", len(result.get("events", []))
    )
    return result
