from __future__ import annotations

import logging
import random
import string
import time

from datetime import datetime
from datetime import timedelta
from typing import ClassVar
from typing import Any, Dict

# from typing import Any

import bcrypt

from fastapi import HTTPException
from jose import jwt

from abstract_repository.iuser_repository import IUserRepository
from abstract_service.user_service import IAuthService
from abstract_service.user_service import IUserService
from models.user import User
from settings import settings


logger = logging.getLogger(__name__)

# Конфигурация
secret_key = settings.get_secret_key()
algorithm = settings.ALGORITHM
session_timeout = settings.SESSION_TIMEOUT


class UserService(IUserService):
    def __init__(self, repository: IUserRepository) -> None:
        self.repository = repository
        logger.debug("UserService инициализирован")
        self.reset_tokens: dict[str, str] = {}

    async def add(self, user: User) -> User:
        try:
            logger.debug("Добавление администратора с логином %s", user)
            user = await self.repository.add(user)
        except Exception:
            logger.error("Администратора с логином %s уже существует.", user.login)
            raise ValueError("Администратор c таким ID уже существует.")
        return user

    async def get_by_id(self, user_id: int) -> User | None:
        logger.debug("Получение пользователя по ID %d", user_id)
        return await self.repository.get_by_id(user_id)

    async def get_list(self) -> list[User]:
        logger.debug("Получение списка всех пользователей")
        return await self.repository.get_list()

    async def update(self, updated_user: User) -> User:
        try:
            logger.debug("Обновление пользователя с ID %d", updated_user.user_id)
            await self.repository.update(updated_user)
        except Exception:
            logger.error("Пользователь с ID %d не найден.", updated_user.user_id)
            raise ValueError("Пользователь не найден.")
        return updated_user

    async def delete(self, user_id: int) -> None:
        try:
            logger.debug("Удаление пользователя с ID %d", user_id)
            await self.repository.delete(user_id)
        except Exception:
            logger.error("Пользователь с ID %d не найден.", user_id)
            raise ValueError("Пользователь не найден.")

    async def get_user_by_reset_token(self, token: str) -> User | None:
        login = self.reset_tokens.get(token)
        if not login:
            return None
        return await self.repository.get_by_login(login)

    async def update_password(self, login: str, new_password: str) -> None:
        user = await self.repository.get_by_login(login)
        if not user:
            raise ValueError("User not found")
        user.password = new_password
        await self.repository.update(user)


class AuthService(IAuthService):
    failed_attempts: ClassVar[dict[str, list[float]]] = {}
    blocked_users: ClassVar[dict[str, float]] = {}
    two_fa_storage: ClassVar[dict[str, dict[str, float | str]]] = {}
    MAX_2FA_ATTEMPTS: ClassVar[int] = 5
    BLOCK_2FA_TIME: ClassVar[int] = 60

    def __init__(self, repository: IUserRepository) -> None:
        self.repository = repository
        logger.debug("AuthService инициализирован")

    async def generate_2fa_code(self, login: str) -> str:
        code = "".join(random.choices(string.digits, k=6))
        self.two_fa_storage[login] = {
            "code": code,
            "expires": time.time() + 300,  # 5 минут
        }
        return code

    async def verify_2fa_code(self, login: str, code: str) -> bool:
        data = self.two_fa_storage.get(login)
        if not data:
            return False
        if float(data["expires"]) < time.time():
            del self.two_fa_storage[login]
            return False
        if data["code"] != code:
            return False
        del self.two_fa_storage[login]
        return True

    async def registrate(self, user: User) -> User:
        user.password = self.get_password_hash(user.password)

        logger.debug("Регистрация пользователя с логином %s", user)
        try:
            await self.repository.add(user)
        except Exception as e:
            logger.error("Ошибка регистрации пользователя %s: %s", user.login, str(e))
            raise ValueError("Пользователь с таким логином уже существует")

        return user

    async def authenticate(self, login: str, password: str) -> User | None:
        if login in self.blocked_users:
            unblock_time = self.blocked_users[login]
            if time.time() < unblock_time:
                raise HTTPException(status_code=403, detail="User temporarily blocked")
            del self.blocked_users[login]
            self.failed_attempts[login] = []

        user = await self.repository.get_by_login(login)
        if not user:
            logger.info("Пользователь %s не найден", login)
            return None

        if not self.verify_password(password, user.password):
            logger.info("Неверный пароль для пользователя %s", login)
            self._register_failed_attempt(login)
            return None

        # успешный вход — сбрасываем неудачные попытки
        self.failed_attempts[login] = []
        return user

    def _register_failed_attempt(self, login: str) -> None:
        now = time.time()
        attempts = self.failed_attempts.get(login, [])
        attempts.append(now)
        self.failed_attempts[login] = attempts

        if len(attempts) >= self.MAX_2FA_ATTEMPTS:  # например, 3 неверных попытки
            self.blocked_users[login] = now + 60  # блокируем на 60 секунд
            logger.warning(f"Пользователь {login} заблокирован на 60 секунд")

    def is_blocked(self, login: str) -> bool:
        """Проверка, заблокирован ли пользователь."""
        if login not in self.blocked_users:
            return False
        unblock_time = self.blocked_users[login]
        if time.time() >= unblock_time:
            del self.blocked_users[login]
            if login in self.failed_attempts:
                self.failed_attempts[login] = []
            return False
        return True

    async def unblock_user(self, login: str) -> None:
        if login in self.blocked_users:
            del self.blocked_users[login]
            logger.info(f"Пользователь {login} разблокирован вручную")

        if login in self.failed_attempts:
            self.failed_attempts[login] = []

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str | bytes) -> bool:
        try:
            plain_bytes = plain_password.encode("utf-8")
            hash_bytes = (
                hashed_password.encode("utf-8")
                if isinstance(hashed_password, str)
                else hashed_password
            )
            return bcrypt.checkpw(plain_bytes, hash_bytes)
        except Exception as e:
            logger.error(f"Password verification failed: {e!s}")
            return False

    @staticmethod
    def create_access_token(user: User) -> str:
        expires_delta = timedelta(minutes=session_timeout)
        expire = datetime.utcnow() + expires_delta

        to_encode = {
            "sub": str(user.user_id),
            "login": user.login,
            "is_admin": user.is_admin,
            "exp": expire,
        }
        return str(jwt.encode(to_encode, secret_key, algorithm=algorithm))

    @staticmethod
    def get_password_hash(password: str) -> str:
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed_password.decode("utf-8")

    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        return jwt.decode(token, secret_key, algorithms=[algorithm])
