from __future__ import annotations

import pytest

from services.venue_service import VenueService


@pytest.mark.asyncio
async def test_get_existing_venue(venue_service: VenueService) -> None:
    venue = await venue_service.get_by_id(1)

    assert venue is not None
    assert venue.name == "Москва"
