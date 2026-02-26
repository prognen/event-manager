from __future__ import annotations

import pytest

from services.user_service import UserService


@pytest.mark.asyncio
async def test_update_user_success(user_service: UserService) -> None:
    user = await user_service.get_by_id(1)
    assert user is not None
    user.fio = "Обновленное имя"
    updated = await user_service.update(user)
    assert updated is not None
    assert updated.fio == "Обновленное имя"



