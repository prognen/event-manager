from __future__ import annotations

import pytest

from services.user_service import UserService


TMP = 3


@pytest.mark.asyncio
async def test_get_user_list_returns_all(user_service: UserService) -> None:
    users = await user_service.get_list()
    assert len(users) >= TMP



