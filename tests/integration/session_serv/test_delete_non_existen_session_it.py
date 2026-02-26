from __future__ import annotations

import pytest

from services.session_service import SessionService


@pytest.mark.asyncio
async def test_delete_non_existing_route_raises(session_service: SessionService) -> None:
    await session_service.delete(999)
    res = await session_service.get_by_id(999)
    assert res is None



