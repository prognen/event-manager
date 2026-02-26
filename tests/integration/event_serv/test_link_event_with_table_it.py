from __future__ import annotations

import pytest

from services.event_service import EventService


TWO = 2


@pytest.mark.asyncio
async def test_link_activities_success(event_service: EventService) -> None:
    await event_service.link_activities(1, [1, 2])
    result = await event_service.get_activities_by_event(1)
    assert len(result) == TWO



