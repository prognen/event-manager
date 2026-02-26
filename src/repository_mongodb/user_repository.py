from __future__ import annotations

import logging

from typing import Any

from bson import Int64
from motor.motor_asyncio import AsyncIOMotorClient
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError
from pymongo.errors import PyMongoError

from abstract_repository.iuser_repository import IUserRepository
from models.user import User


logger = logging.getLogger(__name__)


class UserRepository(IUserRepository):
    def __init__(self, client: AsyncIOMotorClient[Any]):
        self.db: AsyncIOMotorDatabase[Any] = client["event_db"]
        self.client = client
        self.users = self.db["users"]
        logger.debug("Инициализация UserRepository для MongoDB")

    async def add(self, user: User) -> User:
        try:
            last_id = await self.users.find().sort("_id", -1).limit(1).next()
            new_id = Int64(last_id["_id"] + 1) if last_id else Int64(1)

            user_data = {
                "_id": int(new_id),
                "full_name": user.fio,
                "passport": user.number_passport,
                "phone": user.phone_number,
                "email": user.email,
                "login": user.login,
                "password": user.password,
                "is_admin": getattr(user, "is_admin", False),
            }

            result = await self.users.insert_one(user_data)
            user.user_id = result.inserted_id
            logger.debug(
                f"Пользователь добавлен (ID: {result.inserted_id}): {user.login}"
            )
            return user

        except PyMongoError as e:
            logger.error(f"Ошибка при добавлении пользователя: {e}", exc_info=True)
            raise

    async def get_list(self) -> list[User]:
        try:
            users = []
            async for doc in self.users.find().sort("_id"):
                users.append(
                    User(
                        user_id=int(doc["_id"]),
                        fio=doc["full_name"],
                        number_passport=doc["passport"],
                        phone_number=doc["phone"],
                        email=doc["email"],
                        login=doc["login"],
                        password=doc["password"],
                        is_admin=doc.get("is_admin", False),
                    )
                )
            logger.debug(f"Получено {len(users)} пользователей")
            return users

        except PyMongoError as e:
            logger.error(
                f"Ошибка при получении списка пользователей: {e}", exc_info=True
            )
            return []

    async def get_by_id(self, user_id: int) -> User | None:
        try:
            doc = await self.users.find_one({"_id": user_id})
            if doc:
                logger.debug(f"Пользователь найден по ID {user_id}")
                return User(
                    user_id=int(doc["_id"]),
                    fio=doc["full_name"],
                    number_passport=doc["passport"],
                    phone_number=doc["phone"],
                    email=doc["email"],
                    login=doc["login"],
                    password=doc["password"],
                    is_admin=doc.get("is_admin", False),
                )
            logger.debug(f"Пользователь с ID {user_id} не найден")
            return None

        except PyMongoError as e:
            logger.error(
                f"Ошибка при получении пользователя по ID {user_id}: {e}", exc_info=True
            )
            return None

    async def get_by_login(self, login: str) -> User | None:
        try:
            doc = await self.users.find_one({"login": login})
            if not doc:
                logger.debug(f"Пользователь с логином {login} не найден")
                return None

            logger.debug(f"Пользователь найден по логину: {login}")
            return User(
                user_id=int(doc["_id"]),
                fio=doc["full_name"],
                number_passport=doc["passport"],
                phone_number=doc["phone"],
                email=doc["email"],
                login=doc["login"],
                password=doc["password"],
                is_admin=doc.get("is_admin", False),
            )

        except PyMongoError as e:
            logger.error(
                f"Ошибка при получении пользователя по логину: {e}", exc_info=True
            )
            return None

    async def update(self, update_user: User) -> None:
        try:
            result = await self.users.update_one(
                {"_id": update_user.user_id},
                {
                    "$set": {
                        "full_name": update_user.fio,
                        "passport": update_user.number_passport,
                        "phone": update_user.phone_number,
                        "email": update_user.email,
                        "login": update_user.login,
                        "password": update_user.password,
                        "is_admin": getattr(update_user, "is_admin", False),
                    }
                },
            )

            if result.modified_count == 0:
                logger.warning(
                    f"Пользователь с ID {update_user.user_id} не найден для обновления"
                )
            else:
                logger.debug(
                    f"Пользователь с ID {update_user.user_id} успешно обновлён"
                )

        except DuplicateKeyError:
            # Handle duplicate field updates
            error_msg = "Нельзя изменить на уже существующие данные (паспорт, телефон, email или логин)"
            logger.error(f"Ошибка при обновлении пользователя: {error_msg}")
            raise ValueError(error_msg)

        except PyMongoError as e:
            logger.error(
                f"Ошибка при обновлении пользователя с ID {update_user.user_id}: {e}",
                exc_info=True,
            )
            raise

    async def delete(self, user_id: int) -> None:
        try:
            # Start a transaction if needed (MongoDB 4.0+)
            async with (
                await self.client.start_session() as session,
                session.start_transaction(),
            ):
                await self.db["events"].delete_many(
                    {"users": user_id}, session=session
                )

                # Then delete the user
                result = await self.users.delete_one({"_id": user_id}, session=session)

                if result.deleted_count == 0:
                    logger.warning(
                        f"Пользователь с ID {user_id} не найден для удаления"
                    )
                else:
                    logger.debug(f"Пользователь с ID {user_id} удалён")

        except PyMongoError as e:
            logger.error(
                f"Ошибка при удалении пользователя с ID {user_id}: {e}", exc_info=True
            )
            raise
