from __future__ import annotations

import logging
import time

from email.message import EmailMessage
from typing import Any

import aiosmtplib

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi.responses import Response
from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from service_locator import ServiceLocator
from service_locator import get_service_locator


logger = logging.getLogger(__name__)

user_router = APIRouter()

templates = Jinja2Templates(directory="templates")

get_sl_dep = Depends(get_service_locator)

# MAIL_HOST = os.getenv("MAIL_HOST", "mailhog")
# MAIL_PORT = int(os.getenv("MAIL_PORT", "1025"))


async def send_email(to_email: str, subject: str, body: str) -> None:
    message = EmailMessage()
    message["From"] = "noreply@example.com"
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    try:
        await aiosmtplib.send(message, hostname="localhost", port=1025)
        logger.info("Письмо отправлено на %s", to_email)
    except Exception as e:
        logger.error("Ошибка отправки письма: %s", e)


@user_router.post("/api/register")
async def register_user(
    request: Request, service_locator: ServiceLocator = get_sl_dep
) -> JSONResponse:
    result = await service_locator.get_user_contr().registrate(request)
    logger.info("Пользователь успешно зарегистрирован: %s", result)

    return JSONResponse(
        {
            "access_token": result["access_token"],
            "user_id": result["user_id"],
            "message": "Регистрация прошла успешно",
        }
    )


@user_router.get("/profile")
async def show_profile(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("profile.html", {"request": request})


@user_router.post("/api/users", response_class=HTMLResponse)
async def register_admin(
    request: Request, service_locator: ServiceLocator = get_sl_dep
) -> HTMLResponse:
    result = await service_locator.get_user_contr().create_admin(request)
    logger.info("Администратор успешно зарегистрирован: %s", result)
    return templates.TemplateResponse("user.html", {"request": request})


@user_router.put("/api/users/{user_id}", response_class=HTMLResponse)
async def update_admin(
    user_id: int, request: Request, service_locator: ServiceLocator = get_sl_dep
) -> HTMLResponse:
    result = await service_locator.get_user_contr().update_admin(user_id, request)
    logger.info("Администратор успешно обновлен: %s", result)
    return templates.TemplateResponse("user.html", {"request": request})


@user_router.post("/api/login")
async def login_user(
    request: Request, service_locator: ServiceLocator = get_sl_dep
) -> dict[str, Any]:
    result = await service_locator.get_user_contr().login(request)
    logger.info("Результат входа: %s", result)
    return result


@user_router.post("/api/login1")
async def login1_user(
    request: Request, service_locator: ServiceLocator = get_sl_dep
) -> Response:
    data = await request.json()
    login = data.get("login")
    password = data.get("password")

    user = await service_locator.get_user_repo().get_by_login(login)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid login or password")

    if user.password == "W1rong_pas@s":  # или user.password_expired
        return JSONResponse(
            status_code=403,
            content={"password_expired": True, "message": "Password expired"},
        )
    valid = await service_locator.get_auth_serv().authenticate(login, password)
    if not valid:
        raise HTTPException(status_code=401, detail="Invalid login or password")

    code = await service_locator.get_auth_serv().generate_2fa_code(login)

    await send_email(user.email, "Ваш 2FA код", f"Ваш код: {code}")

    two_fa_token = f"2fa-{login}-{int(time.time())}"
    return JSONResponse(
        {
            "message": "2FA code sent to email",
            "two_fa_token": two_fa_token,
            "login": login,
        }
    )


@user_router.get("/profile_user/{user_id}", response_class=HTMLResponse)
async def get_user_profile(
    user_id: int, request: Request, service_locator: ServiceLocator = get_sl_dep
) -> HTMLResponse:
    profile_data = await service_locator.get_user_contr().get_user_profile(user_id)
    active_routes = (
        await service_locator.get_route_serv().get_routes_by_user_and_status_and_type(
            user_id, "В процессе", "Свои"
        )
    )
    completed_routes = (
        await service_locator.get_route_serv().get_routes_by_user_and_status_and_type(
            user_id, "Завершен", "Свои"
        )
    )
    logger.info("completed_routes %s", completed_routes)
    routes_active_data = []
    for route in active_routes:
        transport_cost = route.d_route.cost if route.d_route else 0
        accommodations = route.travels.accommodations if route.travels else []
        accommodation_cost = sum(acc.price for acc in accommodations)
        total_cost = transport_cost + accommodation_cost

        users = []
        if route.travels and route.travels.travel_id:
            users_raw = await service_locator.get_travel_serv().get_users_by_travel(
                route.travels.travel_id
            )
            users = [user for user in users_raw if user is not None]

        route_dict = {
            "route_id": route.route_id,
            "start_time": route.start_time,
            "end_time": route.end_time,
            "transport": route.d_route.type_transport if route.d_route else None,
            "cost": total_cost,
            "destination_city": (
                route.d_route.destination_city.name
                if route.d_route and route.d_route.destination_city
                else None
            ),
            "entertainments": route.travels.entertainments if route.travels else [],
            "accommodations": route.travels.accommodations if route.travels else [],
            "travel_id": route.travels.travel_id if route.travels else None,
            "users": users,
        }
        routes_active_data.append(route_dict)

    routes_completed_data = []
    for route in completed_routes:
        transport_cost = route.d_route.cost if route.d_route else 0
        accommodations = route.travels.accommodations if route.travels else []
        accommodation_cost = sum(acc.price for acc in accommodations)
        total_cost = transport_cost + accommodation_cost

        users = []
        if route.travels and route.travels.travel_id:
            users_raw = await service_locator.get_travel_serv().get_users_by_travel(
                route.travels.travel_id
            )
            users = [user for user in users_raw if user is not None]
        logger.info("archive users: ", users)
        route_dict = {
            "route_id": route.route_id,
            "start_time": route.start_time,
            "end_time": route.end_time,
            "transport": route.d_route.type_transport if route.d_route else None,
            "cost": total_cost,
            "destination_city": (
                route.d_route.destination_city.name
                if route.d_route and route.d_route.destination_city
                else None
            ),
            "entertainments": route.travels.entertainments if route.travels else [],
            "accommodations": route.travels.accommodations if route.travels else [],
            "travel_id": route.travels.travel_id if route.travels else None,
            "users": users,
        }
        routes_completed_data.append(route_dict)

    return templates.TemplateResponse(
        "profile_user.html",
        {
            "request": request,
            "user": profile_data,
            "active_routes": routes_active_data,
            "completed_routes": routes_completed_data,
            "current_user_id": profile_data["user"]["user_id"],
        },
    )


@user_router.get("/user.html", response_class=HTMLResponse)
async def get_all_users(
    request: Request, service_locator: ServiceLocator = get_sl_dep
) -> HTMLResponse:
    users_data = await service_locator.get_user_contr().get_all_users()
    users = users_data.get("users", [])
    logger.info("Получено %d пользователей", len(users))
    return templates.TemplateResponse("user.html", {"request": request, "users": users})


@user_router.post("/user/delete/{user_id}", response_class=HTMLResponse)
async def delete_user(
    user_id: int, service_locator: ServiceLocator = get_sl_dep
) -> RedirectResponse:
    result = await service_locator.get_user_contr().delete_user(user_id)
    logger.info("Пользователь ID %d успешно удален: %s", user_id, result)
    return RedirectResponse(url="/user.html", status_code=303)


@user_router.post("/api/users/json")
async def register_user_json(
    request: Request, service_locator: ServiceLocator = get_sl_dep
) -> JSONResponse:
    result = await service_locator.get_user_contr().registrate(request)
    return JSONResponse(
        {"user_id": result.get("user_id"), "message": result.get("message")}
    )


class RecoverPasswordRequest(BaseModel):
    login: str


@user_router.post("/api/recover-password")
async def recover_password(
    data: RecoverPasswordRequest, service_locator: ServiceLocator = get_sl_dep
) -> dict[str, Any]:

    user = await service_locator.get_user_repo().get_by_login(data.login)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await service_locator.get_auth_serv().unblock_user(user.login)

    return {"message": "Password recovery initiated"}


class ResetPasswordRequest(BaseModel):
    token: str
    password: str


@user_router.post("/api/reset-password")
async def reset_password(
    data: ResetPasswordRequest, service_locator: ServiceLocator = get_sl_dep
) -> dict[str, Any]:
    user = await service_locator.get_user_serv().get_user_by_reset_token(data.token)
    if not user:
        raise HTTPException(status_code=404, detail="Token invalid or expired")

    await service_locator.get_user_serv().update_password(user.login, data.password)
    return {"message": "Password has been reset successfully"}


class Verify2FARequest(BaseModel):
    login: str
    code: str
    two_fa_token: str


@user_router.post("/api/verify-2fa")
async def verify_2fa(
    data: Verify2FARequest, service_locator: ServiceLocator = get_sl_dep
) -> dict[str, Any]:
    valid = await service_locator.get_auth_serv().verify_2fa_code(data.login, data.code)
    if not valid:
        raise HTTPException(status_code=401, detail="Invalid 2FA code")

    # Возвращаем реальный access_token после подтверждения 2FA
    user = await service_locator.get_user_repo().get_by_login(data.login)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    access_token = service_locator.get_auth_serv().create_access_token(user)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.user_id,
        "user_login": user.login,
        "is_admin": user.is_admin,
    }


class TwoFARequest(BaseModel):
    login: str
    code: str


@user_router.post("/api/login2")
async def login_2fa(
    data: TwoFARequest, service_locator: ServiceLocator = get_sl_dep
) -> dict[str, Any]:
    is_valid = await service_locator.get_auth_serv().verify_2fa_code(
        data.login, data.code
    )
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid 2FA code")

    user = await service_locator.get_user_repo().get_by_login(data.login)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    token = service_locator.get_auth_serv().create_access_token(user)
    return {"access_token": token, "token_type": "bearer"}


@user_router.delete("/api/delete/{user_id}")
async def api_delete_user(
    user_id: int, service_locator: ServiceLocator = get_sl_dep
) -> dict[str, Any]:
    result = await service_locator.get_user_contr().delete_user(user_id)
    return {"message": "User deleted", "result": result}


class ExpirePasswordRequest(BaseModel):
    login: str


@user_router.post("/api/expire-password")
async def expire_password(
    req: ExpirePasswordRequest, service_locator: ServiceLocator = get_sl_dep
) -> dict[str, Any]:
    await service_locator.get_user_serv().update_password(req.login, "W1rong_pas@s")
    return {"expired": True}


class ChangePasswordRequest(BaseModel):
    login: str
    new_password: str


@user_router.post("/api/change-password")
async def change_password(
    data: ChangePasswordRequest, service_locator: ServiceLocator = get_sl_dep
) -> dict[str, Any]:
    user = await service_locator.get_user_repo().get_by_login(data.login)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await service_locator.get_user_serv().update_password(
        user.login, service_locator.get_auth_serv().get_password_hash(data.new_password)
    )

    return {"message": "Password changed successfully"}
