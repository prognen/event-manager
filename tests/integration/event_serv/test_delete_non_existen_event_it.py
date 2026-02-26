from __future__ import annotations

import pytest

from services.event_service import EventService


@pytest.mark.asyncio
async def test_delete_event_not_found(event_service: EventService) -> None:
    with pytest.raises(ValueError):
        await event_service.delete(999)


