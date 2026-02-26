from __future__ import annotations

import pytest

from services.event_service import EventService


@pytest.mark.asyncio
async def test_get_lodgings_by_event_error(
    event_service: EventService,
) -> None:
    result = await event_service.get_lodgings_by_event(999)
    assert result == []



