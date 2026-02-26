from __future__ import annotations

import pytest

from services.session_service import SessionService


@pytest.mark.asyncio
async def test_get_routes_by_type_success(session_service: SessionService) -> None:
    routes = await session_service.get_routes_by_type("Личные")

    assert len(routes) > 0
    assert all(route.type == "Личные" for route in routes)



