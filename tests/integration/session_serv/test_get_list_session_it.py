from __future__ import annotations

import pytest

from services.session_service import SessionService


THIRD = 3
TWO = 2


@pytest.mark.asyncio
async def test_update_non_existing_route_raises(session_service: SessionService) -> None:
    routes = await session_service.get_all_routes()

    assert len(routes) == THIRD
    assert any(route.route_id == 1 for route in routes)
    assert any(route.route_id == TWO for route in routes)
    assert any(route.route_id == THIRD for route in routes)



