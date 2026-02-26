from __future__ import annotations

import pytest

from services.venue_service import VenueService


@pytest.mark.asyncio
async def test_delete_non_existing_city_raises(venue_service: VenueService) -> None:
    await venue_service.delete(999)

    Venue = await venue_service.get_by_id(999)
    assert Venue is None



