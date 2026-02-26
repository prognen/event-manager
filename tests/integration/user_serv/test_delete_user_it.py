from __future__ import annotations

import pytest

from services.user_service import UserService


@pytest.mark.asyncio
async def test_delete_user_success(user_service: UserService) -> None:
    await user_service.delete(1)
    result = await user_service.get_by_id(1)
    assert result is None



