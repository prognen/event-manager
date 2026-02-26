from __future__ import annotations

import pytest

from models.user import User
from services.user_service import UserService


@pytest.mark.asyncio
async def test_add_user_success(user_service: UserService) -> None:
    user = User(
        user_id=5,
        fio="Test",
        number_passport="1111001111",
        phone_number="89261111001",
        email="new@test.com",
        login="newuser",
        password="adsjIEDN23!",
    )
    added = await user_service.add(user)

    assert added.login == "newuser"
    fetched = await user_service.get_by_id(added.user_id)
    assert fetched is not None
    assert fetched.login == "newuser"



