from __future__ import annotations

import pytest

from services.event_service import EventService


TWO = 2


@pytest.mark.asyncio
async def test_get_all_events_success(event_service: EventService) -> None:
    result = await event_service.get_all_events()
    assert len(result) == TWO
    assert result[0].event_id == 1
    assert result[1].event_id == TWO



