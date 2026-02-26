from __future__ import annotations

import pytest

from services.session_service import SessionService


@pytest.mark.asyncio
async def test_get_route_by_id_not_found(session_service: SessionService) -> None:
    route = await session_service.get_by_id(999)

    assert route is None



