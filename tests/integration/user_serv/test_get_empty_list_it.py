from __future__ import annotations

import pytest

from services.user_service import UserService


@pytest.mark.asyncio
async def test_get_user_list_empty(user_service: UserService) -> None:
    for i in range(1, 4):
        await user_service.delete(i)
    users = await user_service.get_list()
    assert users == []



