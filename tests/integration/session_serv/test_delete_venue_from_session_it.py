from __future__ import annotations

import pytest

from services.session_service import SessionService


@pytest.mark.asyncio
async def test_delete_city_from_route_success(session_service: SessionService) -> None:
    await session_service.delete_city_from_route(1, 3)



