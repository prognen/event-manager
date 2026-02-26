from __future__ import annotations

import bcrypt
import pytest

from models.user import User
from services.user_service import AuthService
from services.user_service import UserService


@pytest.mark.asyncio
async def test_authenticate_with_wrong_password_returns_none(
    auth_service: AuthService, user_service: UserService
) -> None:
    password = "Auth12345!"
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    user = User(
        user_id=501,
        fio="Тестовый Пользователь",
        number_passport="0000000000",
        phone_number="89260000000",
        email="test@test.com",
        login="authfail",
        password=hashed,
    )
    await user_service.add(user)

    authenticated = await auth_service.authenticate("authfail", "wrongpassword")
    assert authenticated is None



