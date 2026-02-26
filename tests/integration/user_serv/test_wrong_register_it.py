from __future__ import annotations

import pytest

from models.user import User
from services.user_service import AuthService
from services.user_service import UserService


@pytest.mark.asyncio
async def test_register_user_duplicate_raises(
    user_service: UserService, auth_service: AuthService
) -> None:
    user = User(
        user_id=2,
        fio="Иванов Иван Иванович",
        number_passport="2222222222",
        phone_number="89262222222",
        email="ivanov@ivanov.com",
        login="user2",
        password="456!f6R89",
    )
    with pytest.raises(ValueError):
        await auth_service.registrate(user)



