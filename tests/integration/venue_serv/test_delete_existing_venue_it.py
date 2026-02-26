from __future__ import annotations

import pytest

from services.venue_service import VenueService


@pytest.mark.asyncio
async def test_delete_existing_venue(venue_service: VenueService) -> None:
    await venue_service.delete(1)
    venue_in_db = await venue_service.get_by_id(1)
    assert venue_in_db is None
