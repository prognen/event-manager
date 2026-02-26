from __future__ import annotations

import pytest

from services.user_service import UserService


@pytest.mark.asyncio
async def test_delete_non_existent_user(user_service: UserService) -> None:
    await user_service.delete(999)
    result = await user_service.get_by_id(999)
    assert result is None



