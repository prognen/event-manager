from __future__ import annotations

import pytest

from services.venue_service import VenueService


@pytest.mark.asyncio
async def test_get_existing_city(venue_service: VenueService) -> None:
    Venue = await venue_service.get_by_id(1)

    assert Venue is not None
    assert Venue.name == "Москва"



