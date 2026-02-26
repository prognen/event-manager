from __future__ import annotations

import pytest

from models.user import User
from services.user_service import UserService


@pytest.mark.asyncio
async def test_get_user_by_id_success(user_service: UserService) -> None:
    user = User(
        user_id=2,
        fio="Иванов Иван Иванович",
        number_passport="2222222222",
        phone_number="89262222222",
        email="ivanov@ivanov.com",
        login="user2",
        password="456!f6R89",
    )
    fetched = await user_service.get_by_id(user.user_id)
    assert fetched is not None
    assert fetched.fio == user.fio



