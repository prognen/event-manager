from __future__ import annotations

import pytest

from services.event_service import EventService


@pytest.mark.asyncio
async def test_update_travel_success(event_service: EventService) -> None:
    Event = await event_service.get_by_id(1)
    assert Event is not None

    Event.status = "Обновленный статус"
    result = await event_service.update(Event)
    assert result.status == "Обновленный статус"



