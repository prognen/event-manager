from __future__ import annotations

import bcrypt
import pytest

from models.user import User
from services.user_service import AuthService
from services.user_service import UserService


@pytest.mark.asyncio
async def test_update_user_password_success(user_service: UserService) -> None:
    user = User(
        user_id=4,
        fio="Семенов Семен Семенович",
        number_passport="4444444444",
        phone_number="89267753309",
        email="sem@sss.com",
        login="user4",
        password="6669!g7T90",
    )
    new_password = "NewPass!123"
    hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    user.password = hashed
    updated = await user_service.update(user)
    assert AuthService.verify_password(new_password, updated.password)



