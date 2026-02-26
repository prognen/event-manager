from __future__ import annotations

import logging

from typing import Any

from fastapi import HTTPException
from fastapi import Request

from models.user import User
from services.user_service import AuthService
from services.user_service import UserService


logger = logging.getLogger(__name__)


class UserController:
    def __init__(self, user_service: UserService, auth_service: AuthService) -> None:
        self.user_service = user_service
        self.auth_service = auth_service
        logger.debug("Инициализация UserController")

    async def get_user_profile(self, user_id: int) -> dict[str, Any]:
        try:
            user = await self.user_service.get_by_id(user_id)
            if user:
                logger.info("Профиль пользователя ID %d найден: %s", user_id, user)
                return {
                    "user": {
                        "user_id": user.user_id,
                        "fio": user.fio,
                        "number_passport": user.number_passport,
                        "phone_number": user.phone_number,
                        "email": user.email,
                        "login": user.login,
                        "password": user.password,
                        "is_admin": user.is_admin,
                    }
                }
            logger.warning("Пользователь ID %d не найден", user_id)
            return {"message": "User not found"}
        except Exception as e:
            logger.error(
                "Ошибка при получении профиля пользователя ID: %s",
                str(e),
                exc_info=True,
            )
            return {"message": "Error fetching details", "error": str(e)}

    async def get_all_users(self) -> dict[str, Any]:
        try:
            user_list = await self.user_service.get_list()
            logger.info("Получено %d пользователей", len(user_list))
            return {
                "users": [
                    {
                        "user_id": u.user_id,
                        "fio": u.fio,
                        "number_passport": u.number_passport,
                        "phone_number": u.phone_number,
                        "email": u.email,
                        "login": u.login,
                        "password": u.password,
                        "is_admin": u.is_admin,
                    }
                    for u in user_list
                ]
            }
        except Exception as e:
            logger.error(
                "Ошибка при получении списка пользователей: %s", str(e), exc_info=True
            )
            return {"message": "Error fetching users", "error": str(e)}

    async def registrate(self, request: Request) -> dict[str, Any]:
        try:
            data = await request.json()
            data["user_id"] = 1
            # data['password'] = self.auth_service.get_password_hash(data['password'])
            user = User(**data)
            registered_user = await self.auth_service.registrate(user)
            token = self.auth_service.create_access_token(registered_user)
            logger.info("Пользователь успешно зарегистрирован: %s", registered_user)
            return {
                "access_token": token,
                "token_type": "bearer",
                "user_id": registered_user.user_id,
                "message": "User registered successfully",
            }
        except Exception as e:
            logger.error("Registration error: %s", str(e))
            raise HTTPException(status_code=400, detail=str(e))

    async def create_admin(self, request: Request) -> dict[str, Any]:
        try:
            data = await request.json()
            if "password" in data:
                data["password"] = self.auth_service.get_password_hash(data["password"])
            data["user_id"] = 1
            data["is_admin"] = True
            user = User(**data)
            registered_admin = await self.user_service.add(user)
            logger.info("Администратор успешно зарегистрирован: %s", registered_admin)
            return {
                "message": "Admin registered successfully",
                "user_id": registered_admin.user_id,
            }
        except Exception as e:
            logger.error(
                "Ошибка при регистрации администратора: %s", str(e), exc_info=True
            )
            return {"message": "Error during registration", "error": str(e)}

    async def login(self, request: Request) -> dict[str, Any]:
        try:
            data = await request.json()
            user = await self.auth_service.authenticate(data["login"], data["password"])
            if user is None:
                raise HTTPException(status_code=401, detail="Invalid login or password")
            logger.info("Пользователь успешно авторизировался: %s", user)
            token = self.auth_service.create_access_token(user)
            return {
                "access_token": token,
                "token_type": "bearer",
                "user_id": user.user_id,
                "user_login": user.login,
                "is_admin": user.is_admin,
                "message": "Login successfully",
            }
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(
                "Ошибка при авторизации пользователя: %s", str(e), exc_info=True
            )
            raise HTTPException(status_code=401, detail="Invalid login or password")

    async def delete_user(self, user_id: int) -> dict[str, Any]:
        try:
            await self.user_service.delete(user_id)
            logger.info("Пользователь ID %d успешно удален", user_id)
            return {"message": "User deleted successfully"}
        except Exception as e:
            logger.error(
                "Ошибка при удалении пользователя ID %d: %s",
                user_id,
                str(e),
                exc_info=True,
            )
            return {"message": "Error deleting user", "error": str(e)}

    async def update_admin(self, user_id: int, request: Request) -> dict[str, Any]:
        try:
            data = await request.json()
            admin_old = await self.user_service.get_by_id(user_id)
            if admin_old is None:
                return {
                    "message": "User not found",
                    "error": f"User with id {user_id} not found",
                }

            user_data = {
                "login": admin_old.login,
                "password": admin_old.password,
                "user_id": user_id,
                "is_admin": True,
                **data,
            }
            user = User(**user_data)
            admin = await self.user_service.update(user)
            logger.info("Администратор успешно зарегистрирован: %s", admin)
            return {"message": "Admin update successfully", "user_id": admin.user_id}
        except Exception as e:
            logger.error(
                "Ошибка при регистрации администратора: %s", str(e), exc_info=True
            )
            return {"message": "Error during update", "error": str(e)}
