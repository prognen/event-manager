from __future__ import annotations

import pytest

from services.event_service import EventService


@pytest.mark.asyncio
async def test_delete_travel_success(event_service: EventService) -> None:
    await event_service.delete(2)
    result = await event_service.get_by_id(2)
    assert result is None



