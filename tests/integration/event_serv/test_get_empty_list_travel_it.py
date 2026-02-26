from __future__ import annotations

import pytest

from services.event_service import EventService


@pytest.mark.asyncio
async def test_get_empty_list(event_service: EventService) -> None:
    await event_service.delete(1)
    await event_service.delete(2)
    result = await event_service.get_all_events()
    assert len(result) == 0



