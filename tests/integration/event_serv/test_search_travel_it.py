from __future__ import annotations

import pytest

from services.event_service import EventService


@pytest.mark.asyncio
async def test_search_travels_success(event_service: EventService) -> None:
    result = await event_service.search({"from_venue": 3})
    assert len(result) == 1
    assert result is not None
    assert result[0].event_id == 1



