from __future__ import annotations

import logging

from datetime import datetime
from typing import Any

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse
from fastapi.responses import RedirectResponse
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates

from models.event import Event

from service_locator import ServiceLocator
from service_locator import get_service_locator


logger = logging.getLogger(__name__)

session_router = APIRouter()
templates = Jinja2Templates(directory="templates")
get_sl_dep = Depends(get_service_locator)


@session_router.post("/api/sessions", response_class=HTMLResponse)
async def create_session(
    request: Request, service_locator: ServiceLocator = get_sl_dep
) -> HTMLResponse:
    result = await service_locator.get_session_contr().create_new_session(request)
    logger.info("Сессия успешно создана: %s", result)
    return templates.TemplateResponse("session.html", {"request": request})


@session_router.post("/session/new", response_class=HTMLResponse)
async def create_session_user(
    request: Request, service_locator: ServiceLocator = get_sl_dep
) -> JSONResponse:
    logger.info("create_session_user\n")
    result = await service_locator.get_session_contr().create_new_session_user(request)
    logger.info("Сессия успешно создана: %s", result)
    return JSONResponse(content=result)


@session_router.get("/session/new", response_class=HTMLResponse)
async def get_session_page(
    request: Request, service_locator: ServiceLocator = get_sl_dep
) -> HTMLResponse:
    activities = await service_locator.get_activity_serv().get_list()
    lodgings = await service_locator.get_lodging_serv().get_list()
    venues = await service_locator.get_venue_serv().get_all_venues()
    return templates.TemplateResponse(
        "new.html",
        {
            "request": request,
            "activities": activities,
            "lodgings": lodgings,
            "venues": venues,
        },
    )


def _serialize_event_for_template(event: Event) -> dict[str, Any]:
    """Преобразует Event в словарь, сериализуемый в JSON для data-атрибутов."""
    return {
        "event_id": event.event_id,
        "status": event.status,
        "users": [{"user_id": u.user_id, "fio": u.fio, "email": u.email} for u in (event.users or [])],
        "activities": [
            {
                "id": a.activity_id,
                "activity_type": a.activity_type,
                "address": a.address,
                "duration": a.duration,
                "activity_time": a.activity_time.isoformat() if a.activity_time else None,
                "venue_name": a.venue.name if a.venue else "Не указан",
            }
            for a in (event.activities or [])
        ],
        "lodgings": [
            {
                "id": ldg.lodging_id,
                "name": ldg.name,
                "address": ldg.address,
                "price": ldg.price,
                "type": ldg.type,
                "rating": ldg.rating,
                "check_in": ldg.check_in.isoformat() if ldg.check_in else None,
                "check_out": ldg.check_out.isoformat() if ldg.check_out else None,
                "venue_name": ldg.venue.name if ldg.venue else "Не указан",
            }
            for ldg in (event.lodgings or [])
        ],
    }


@session_router.get("/session.html", response_class=HTMLResponse)
async def get_all_sessions(
    request: Request, service_locator: ServiceLocator = get_sl_dep
) -> HTMLResponse:
    session_list = await service_locator.get_session_contr().get_all_sessions()
    sessions = session_list.get("sessions", [])
    user = None

    for session in sessions:
        st = session.get("start_time")
        et = session.get("end_time")
        session["start_time"] = datetime.fromisoformat(st) if st else None
        session["end_time"] = datetime.fromisoformat(et) if et else None

        if session.get("event"):
            event = session["event"]
            serialized_activities = []
            for act in event["activities"]:
                venue_name = None
                if hasattr(act.get("venue"), "name"):
                    venue_name = act["venue"].name
                elif isinstance(act.get("venue"), dict):
                    venue_name = act["venue"].get("name", "Не указан")
                elif "venue_id" in act:
                    venue = await service_locator.get_venue_serv().get_by_id(
                        act["venue_id"]
                    )
                    venue_name = venue.name if venue else "Не указан"
                else:
                    venue_name = "Не указан"

                serialized_activities.append(
                    {
                        "id": act.get("id"),
                        "activity_type": act.get("activity_type"),
                        "address": act.get("address"),
                        "duration": act.get("duration"),
                        "activity_time": act.get("activity_time"),
                        "venue_name": venue_name,
                    }
                )
            event["activities"] = serialized_activities

        if "lodgings" in event:
            serialized_lodgings = []
            for lod in event["lodgings"]:
                venue_name = None
                if hasattr(lod.get("venue"), "name"):
                    venue_name = lod["venue"].name
                elif isinstance(lod.get("venue"), dict):
                    venue_name = lod["venue"].get("name", "Не указан")
                elif "venue_id" in lod:
                    venue = await service_locator.get_venue_serv().get_by_id(
                        lod["venue_id"]
                    )
                    venue_name = venue.name if venue else "Не указан"
                else:
                    venue_name = "Не указан"

                serialized_lodgings.append(
                    {
                        "id": lod.get("id"),
                        "name": lod.get("name"),
                        "type": lod.get("type"),
                        "address": lod.get("address"),
                        "price": lod.get("price"),
                        "rating": lod.get("rating"),
                        "check_in": lod.get("check_in"),
                        "check_out": lod.get("check_out"),
                        "venue_name": venue_name,
                    }
                )
            event["lodgings"] = serialized_lodgings

    events_raw = await service_locator.get_event_serv().get_all_events()
    events_serialized = [_serialize_event_for_template(e) for e in events_raw]

    return templates.TemplateResponse(
        "session.html",
        {
            "request": request,
            "sessions": sessions,
            "events": events_serialized,
            "programs": await service_locator.get_program_serv().get_list(),
            "user": user,
        },
    )


@session_router.put("/api/sessions/{session_id}", response_class=HTMLResponse)
async def update_session(
    session_id: int, request: Request, service_locator: ServiceLocator = get_sl_dep
) -> HTMLResponse:
    result = await service_locator.get_session_contr().update_session(
        session_id, request
    )
    logger.info("Сессия ID %d успешно обновлена: %s", session_id, result)
    return templates.TemplateResponse("session.html", {"request": request})


@session_router.post("/session/delete/{session_id}", response_class=HTMLResponse)
async def delete_session(
    session_id: int, request: Request, service_locator: ServiceLocator = get_sl_dep
) -> RedirectResponse:
    result = await service_locator.get_session_contr().delete_session(session_id)
    logger.info("Сессия ID %d успешно удалена: %s", session_id, result)
    return RedirectResponse(url="/session.html", status_code=303)


@session_router.get("/session/edit/{session_id}")
async def edit_page(
    session_id: int, request: Request, service_locator: ServiceLocator = get_sl_dep
) -> Response:
    session = await service_locator.get_session_serv().get_by_id(session_id)
    if not session:
        logger.error("Сессия с таким ID %s не найдена", session_id)
        return HTMLResponse(content="<h1>Сессия не найдена</h1>", status_code=404)
    lodgings = session.event.lodgings if session.event else []
    lodging_cost = sum(lod.price for lod in lodgings)
    total_cost = lodging_cost
    venues_list = await service_locator.get_venue_contr().get_all_venues()
    venues = venues_list.get("venues", [])
    session_parts = await service_locator.get_session_contr().get_session_parts(
        session_id
    )
    for s in session_parts:
        total_cost += s["price"]
    session_dict = {
        "session_id": session.session_id,
        "program_id": session.program.program_id if session.program else None,
        "start_time": session.start_time,
        "end_time": session.end_time,
        "transport": (
            ", ".join({part["transport"] for part in session_parts})
            if session_parts
            else None
        ),
        "cost": total_cost,
        "to_venue": (
            session.program.to_venue.name
            if session.program and session.program.to_venue
            else None
        ),
        "activities": session.event.activities if session.event else [],
        "lodgings": session.event.lodgings if session.event else [],
        "event_id": session.event.event_id if session.event else None,
    }
    logger.info(session_dict["program_id"])
    return templates.TemplateResponse(
        "edit.html",
        {
            "request": request,
            "session": session_dict,
            "session_parts": session_parts,
            "venues": venues,
        },
    )


@session_router.put("/session/change_transport/{session_id}")
async def change_transport(
    session_id: int, request: Request, service_locator: ServiceLocator = get_sl_dep
) -> dict[str, Any]:
    result = await service_locator.get_session_contr().change_transport(
        session_id, request
    )
    logger.info("Транспорт в сессии успешно изменен: %s", result)
    return {"session_id": session_id, "program_id": result["program_id"]}


@session_router.delete("/session/delete_venue")
async def delete_venue_from_session(
    request: Request, service_locator: ServiceLocator = get_sl_dep
) -> dict[str, Any]:
    result = await service_locator.get_session_contr().delete_venue_from_session(
        request
    )
    logger.info("Площадка успешно удалена из сессии: %s", result)
    return result


@session_router.post("/session/add_venue")
async def add_new_venue(
    request: Request, service_locator: ServiceLocator = get_sl_dep
) -> None:
    result = await service_locator.get_session_contr().add_new_venue(request)
    logger.info("Площадка успешно добавлена в сессию: %s", result)


@session_router.put("/session/extend/{session_id}")
async def api_change_session_duration(
    session_id: int, request: Request, service_locator: ServiceLocator = get_sl_dep
) -> dict[str, Any]:
    try:
        result = await service_locator.get_session_contr().change_session_duration(
            session_id, request
        )
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        logger.info("Сессия успешно продлена: %s", result)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Ошибка в API продления сессии: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@session_router.get("/tours", response_class=HTMLResponse)
async def get_tours(
    request: Request, service_locator: ServiceLocator = get_sl_dep
) -> HTMLResponse:
    sessions = await service_locator.get_session_serv().get_sessions_by_type(
        "Официальные"
    )
    sessions_data = []

    for session in sessions:
        transport_cost = (
            session.program.cost
            if hasattr(session, "program") and session.program
            else 0
        )
        lodging_cost = 0
        if (
            hasattr(session, "event")
            and session.event
            and hasattr(session.event, "lodgings")
        ):
            lodgings = session.event.lodgings or []
            lodging_cost = sum(getattr(lod, "price", 0) for lod in lodgings)

        lodgings_list = []
        if (
            hasattr(session, "event")
            and session.event
            and hasattr(session.event, "lodgings")
        ):
            for lod in getattr(session.event, "lodgings", []):
                logger.info("lod: %s", lod)
                check_in = getattr(lod, "check_in", None)
                check_out = getattr(lod, "check_out", None)

                lod_data = {
                    "name": getattr(lod, "name", "Не указано"),
                    "type": getattr(lod, "type", "Не указан"),
                    "address": getattr(lod, "address", "Не указан"),
                    "check_in": check_in.strftime("%d.%m.%Y") if check_in else "",
                    "check_out": check_out.strftime("%d.%m.%Y") if check_out else "",
                    "rating": getattr(lod, "rating", 0),
                    "price": getattr(lod, "price", 0),
                }
                lodgings_list.append(lod_data)

        activities = []
        if (
            hasattr(session, "event")
            and session.event
            and hasattr(session.event, "activities")
        ):
            for act in getattr(session.event, "activities", []):
                date = getattr(act, "activity_time", None)

                act_data = {
                    "name": getattr(act, "activity_type", "Не указано"),
                    "address": getattr(act, "address", "Не указан"),
                    "date": date.strftime("%d.%m.%Y") if date else "",
                    "duration": getattr(act, "duration", "Не указана"),
                }
                activities.append(act_data)

        start_time = getattr(session, "start_time", None)
        end_time = getattr(session, "end_time", None)

        session_dict = {
            "session_id": getattr(session, "session_id", 0),
            "from_venue": getattr(
                getattr(getattr(session, "program", None), "from_venue", None),
                "name",
                "Не указан",
            ),
            "to_venue": getattr(
                getattr(getattr(session, "program", None), "to_venue", None),
                "name",
                "Не указан",
            ),
            "transport": getattr(
                getattr(session, "program", None), "type_transport", "Не указан"
            ),
            "start_time": start_time.strftime("%d.%m.%Y") if start_time else "",
            "end_time": end_time.strftime("%d.%m.%Y") if end_time else "",
            "cost": transport_cost + lodging_cost,
            "lodgings": lodgings_list or [],
            "activities": activities or [],
        }
        logger.info(f"Сформированные данные сессии: {session_dict}")
        sessions_data.append(session_dict)

    return templates.TemplateResponse(
        "tours.html",
        {"request": request, "sessions": jsonable_encoder(sessions_data)},
    )


@session_router.get("/recommended", response_class=HTMLResponse)
async def get_recommended_tours(
    request: Request, service_locator: ServiceLocator = get_sl_dep
) -> HTMLResponse:
    sessions = await service_locator.get_session_serv().get_sessions_by_type(
        "Рекомендованные"
    )
    sessions_data = []

    for session in sessions:
        transport_cost = (
            session.program.cost
            if hasattr(session, "program") and session.program
            else 0
        )
        lodging_cost = 0
        if (
            hasattr(session, "event")
            and session.event
            and hasattr(session.event, "lodgings")
        ):
            lodgings = session.event.lodgings or []
            lodging_cost = sum(getattr(lod, "price", 0) for lod in lodgings)
        if (
            hasattr(session, "event")
            and session.event
            and hasattr(session.event, "users")
        ):
            user_ids = [
                u.user_id for u in session.event.users if hasattr(u, "user_id")
            ]
        lodgings_list = []
        if (
            hasattr(session, "event")
            and session.event
            and hasattr(session.event, "lodgings")
        ):
            for lod in getattr(session.event, "lodgings", []):
                logger.info("lod: %s", lod)
                check_in = getattr(lod, "check_in", None)
                check_out = getattr(lod, "check_out", None)

                lod_data = {
                    "name": getattr(lod, "name", "Не указано"),
                    "type": getattr(lod, "type", "Не указан"),
                    "address": getattr(lod, "address", "Не указан"),
                    "check_in": check_in.strftime("%d.%m.%Y") if check_in else "",
                    "check_out": check_out.strftime("%d.%m.%Y") if check_out else "",
                    "rating": getattr(lod, "rating", 0),
                    "price": getattr(lod, "price", 0),
                }
                lodgings_list.append(lod_data)

        activities = []
        if (
            hasattr(session, "event")
            and session.event
            and hasattr(session.event, "activities")
        ):
            for act in getattr(session.event, "activities", []):
                date = getattr(act, "activity_time", None)

                act_data = {
                    "name": getattr(act, "activity_type", "Не указано"),
                    "address": getattr(act, "address", "Не указан"),
                    "date": date.strftime("%d.%m.%Y") if date else "",
                    "duration": getattr(act, "duration", "Не указана"),
                }
                activities.append(act_data)

        start_time = getattr(session, "start_time", None)
        end_time = getattr(session, "end_time", None)

        session_dict = {
            "session_id": getattr(session, "session_id", 0),
            "from_venue": getattr(
                getattr(getattr(session, "program", None), "from_venue", None),
                "name",
                "Не указан",
            ),
            "to_venue": getattr(
                getattr(getattr(session, "program", None), "to_venue", None),
                "name",
                "Не указан",
            ),
            "transport": getattr(
                getattr(session, "program", None), "type_transport", "Не указан"
            ),
            "start_time": start_time.strftime("%d.%m.%Y") if start_time else "",
            "end_time": end_time.strftime("%d.%m.%Y") if end_time else "",
            "cost": transport_cost + lodging_cost,
            "lodgings": lodgings_list or [],
            "activities": activities or [],
            "user_ids": user_ids,
        }
        logger.info(f"Сформированные данные сессии: {session_dict}")
        sessions_data.append(session_dict)

    return templates.TemplateResponse(
        "recommended.html",
        {"request": request, "sessions": jsonable_encoder(sessions_data)},
    )


@session_router.post("/sessions/{session_id}/join")
async def join_session(
    session_id: int, request: Request, service_locator: ServiceLocator = get_sl_dep
) -> dict[str, Any]:
    logger.info("Присоединяемся к сессии %d ID", session_id)
    return await service_locator.get_session_contr().join_to_event(session_id, request)
