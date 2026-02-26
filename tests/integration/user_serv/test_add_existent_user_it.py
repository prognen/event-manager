from __future__ import annotations

import pytest

from models.user import User
from services.user_service import UserService


@pytest.mark.asyncio
async def test_add_duplicate_user_raises(user_service: UserService) -> None:
    user = User(
        user_id=1,
        fio="Власов Егор Витальевич",
        number_passport="1111111111",
        phone_number="89261111111",
        email="egor@vlasov.info",
        login="user1",
        password="123!e5T78",
    )
    with pytest.raises(ValueError):
        await user_service.add(user)



