from __future__ import annotations

import pytest

from services.user_service import UserService


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(user_service: UserService) -> None:
    fetched = await user_service.get_by_id(9999)
    assert fetched is None



