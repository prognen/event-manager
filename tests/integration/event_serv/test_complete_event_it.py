from __future__ import annotations

import pytest

from services.event_service import EventService


@pytest.mark.asyncio
async def test_complete_event_success(event_service: EventService) -> None:
    await event_service.complete(1)
    result = await event_service.get_by_id(1)
    assert result is not None
    assert result.status == "Завершено"



