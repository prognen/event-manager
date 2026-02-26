from __future__ import annotations

import bcrypt
import pytest

from models.user import User
from services.user_service import AuthService
from services.user_service import UserService


@pytest.mark.asyncio
async def test_register_user_success(
    user_service: UserService, auth_service: AuthService
) -> None:
    password = "Register123!"
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    user = User(
        user_id=400,
        fio="Власов Егор Витальевич",
        number_passport="3311111111",
        phone_number="89261441111",
        email="ddd@dddd.info",
        login="registeruser",
        password=hashed,
    )
    added = await auth_service.registrate(user)

    assert added.login == "registeruser"
    fetched = await user_service.get_by_id(added.user_id)
    assert fetched is not None
    assert fetched.login == "registeruser"



