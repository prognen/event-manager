from __future__ import annotations

import pytest

from services.session_service import SessionService


@pytest.mark.asyncio
async def test_insert_city_after_success(session_service: SessionService) -> None:
    await session_service.insert_city_after(1, 4, 5, "Поезд")



