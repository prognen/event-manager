from __future__ import annotations

import bcrypt
import pytest

from models.user import User
from services.user_service import AuthService
from services.user_service import UserService


@pytest.mark.asyncio
async def test_authenticate_with_hashed_password_success(
    auth_service: AuthService, user_service: UserService
) -> None:
    password = "Auth12345!"
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    user = User(
        user_id=500,
        fio="Семенов Семен Семенович",
        number_passport="4444444411",
        phone_number="89267753311",
        email="sem@sss.com",
        login="authsuccess",
        password=hashed,
    )
    await user_service.add(user)

    authenticated = await auth_service.authenticate("authsuccess", password)
    assert authenticated is not None
    assert authenticated.login == "authsuccess"



