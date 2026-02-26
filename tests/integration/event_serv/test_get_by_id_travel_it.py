from __future__ import annotations

import pytest

from services.event_service import EventService


@pytest.mark.asyncio
async def test_get_by_id_success(event_service: EventService) -> None:
    result = await event_service.get_by_id(1)
    assert result is not None
    assert result.event_id == 1
    assert result.status == "Активное"



