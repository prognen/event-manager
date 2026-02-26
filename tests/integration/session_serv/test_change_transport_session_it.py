from __future__ import annotations

import pytest

from services.session_service import SessionService


@pytest.mark.asyncio
async def test_change_transport_success(session_service: SessionService) -> None:
    result = await session_service.change_transport(1, 2, "Поезд")

    assert result is not None



