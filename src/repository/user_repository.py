from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from abstract_repository.iuser_repository import IUserRepository
from models.user import User


logger = logging.getLogger(__name__)


class UserRepository(IUserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
        logger.debug("Инициализация UserRepository")

    async def add(self, user: User) -> User:
        query = text(
            """
            INSERT INTO users (full_name, passport, phone, email, login, password)
            VALUES (:full_name, :passport, :phone, :email, :login, :password)
            RETURNING id
        """
        )
        try:
            result = await self.session.execute(
                query,
                {
                    "full_name": user.fio,
                    "passport": user.number_passport,
                    "phone": user.phone_number,
                    "email": user.email,
                    "login": user.login,
                    "password": user.password,
                },
            )
            await self.session.commit()
            db_id = result.scalar_one()
            user.user_id = db_id

            logger.debug(f"Пользователь добавлен (ID: {db_id}): {user.login}")
        except IntegrityError:
            await self.session.rollback()
            logger.warning(
                "Ошибка: пользователь с таким паспортом, телефоном или email уже существует."
            )
            raise ValueError("Пользователь с такими данными уже существует")
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Ошибка при добавлении пользователя: {e}", exc_info=True)
            raise
        return user

    async def get_list(self) -> list[User]:
        query = text("SELECT * FROM users ORDER BY id")
        try:
            result = await self.session.execute(query)
            users = [
                User(
                    user_id=row["id"],
                    fio=row["full_name"],
                    number_passport=row["passport"],
                    phone_number=row["phone"],
                    email=row["email"],
                    login=row["login"],
                    password=row["password"],
                )
                for row in result.mappings()
            ]
            logger.debug(f"Получено {len(users)} пользователей")
            return users
        except SQLAlchemyError as e:
            logger.error(
                f"Ошибка при получении списка пользователей: {e}", exc_info=True
            )
            return []

    async def get_by_id(self, user_id: int) -> User | None:
        query = text("SELECT * FROM users WHERE id = :user_id")
        try:
            result = await self.session.execute(query, {"user_id": user_id})
            row = result.mappings().first()
            if row:
                logger.debug(f"Пользователь найден по ID {user_id}")
                return User(
                    user_id=row["id"],
                    fio=row["full_name"],
                    number_passport=row["passport"],
                    phone_number=row["phone"],
                    email=row["email"],
                    login=row["login"],
                    password=row["password"],
                )
            logger.debug(f"Пользователь с ID {user_id} не найден")
            return None
        except SQLAlchemyError as e:
            logger.error(
                f"Ошибка при получении пользователя по ID {user_id}: {e}", exc_info=True
            )
            return None

    async def get_by_login(self, login: str) -> User | None:
        query = text("SELECT * FROM users WHERE login = :login")
        try:
            result = await self.session.execute(query, {"login": login})
            row = result.mappings().first()
            if not row:
                logger.debug(f"Пользователь с логином {login} не найден")
                return None
            logger.debug(f"Пользователь найден по логину: {login}")
            return User(
                user_id=row["id"],
                fio=row["full_name"],
                number_passport=row["passport"],
                phone_number=row["phone"],
                email=row["email"],
                login=row["login"],
                password=row["password"],
                is_admin=row["is_admin"],
            )

        except SQLAlchemyError as e:
            logger.error(
                f"Ошибка при получении пользователя по логину: {e}", exc_info=True
            )
            return None

    async def update(self, update_user: User) -> None:
        query = text(
            """
            UPDATE users
            SET full_name = :fio,
                passport = :number_passport,
                phone = :phone_number,
                email = :email,
                login = :login,
                password = :password
            WHERE id = :user_id
        """
        )
        try:
            await self.session.execute(
                query,
                {
                    "fio": update_user.fio,
                    "number_passport": update_user.number_passport,
                    "phone_number": update_user.phone_number,
                    "email": update_user.email,
                    "login": update_user.login,
                    "password": update_user.password,
                    "user_id": update_user.user_id,
                },
            )
            await self.session.commit()
            logger.debug(f"Пользователь с ID {update_user.user_id} успешно обновлён")
        except IntegrityError:
            raise ValueError("Пользователь с такими данными уже существует")

        except SQLAlchemyError as e:
            logger.error(
                f"Ошибка при обновлении пользователя с ID {update_user.user_id}: {e}",
                exc_info=True,
            )

    async def delete(self, user_id: int) -> None:
        delete_events = text("DELETE FROM users_event WHERE users_id = :user_id")
        delete_user = text("DELETE FROM users WHERE id = :user_id")

        try:
            await self.session.execute(delete_events, {"user_id": user_id})
            await self.session.execute(delete_user, {"user_id": user_id})
            await self.session.commit()
            logger.debug(f"Пользователь с ID {user_id} удалён")
        except SQLAlchemyError as e:
            logger.error(
                f"Ошибка при удалении пользователя с ID {user_id}: {e}", exc_info=True
            )
